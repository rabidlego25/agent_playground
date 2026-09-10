"""Export OpenClaw session state to lib.trace Episodes.

The README's rule is that a run which cannot be replayed will be paid for twice, and 007
is the most expensive design in this repo. This is the exporter that rule demands.

**Validated against a real session 2026-09-10** (Gemini 3.5 Flash Lite, OpenClaw
2026.9.3). That validation corrected two claims in PILOT.md, both of which had been
written from reading one pilot's tables and would have silently corrupted the experiment:

  - PILOT.md: "model.completed carries usage, so tokens per call come from here."
    Both halves are wrong. `model.completed` fires **once per run**, not once per model
    call -- a two-call run emits one -- so counting it undercounts requests, which is
    fatal on a tier metered in requests per day. And its usage fields read 0.
  - The per-request unit is an **assistant message in `transcript_events`**. A run with
    two `[model-fetch]` calls in the container log produces exactly two of them.

Usage is zero unless the provider config sets `compat.supportsUsageInStreaming: true`.
OpenClaw auto-detects that from the base URL and guesses wrong for
generativelanguage.googleapis.com, so every token count in the trace silently reads 0 and
H2 (the cost hypothesis) becomes unmeasurable while still producing plausible output.
Verified directly against the API: Gemini returns usage in a stream only when
`stream_options.include_usage` is sent. See sandbox/config/gemini.template.json.

Storage: <state-dir>/agents/<agentId>/agent/openclaw-agent.sqlite

  transcript_events(seq, event_json)      -- the primary source
    event.message.role = user | assistant | toolResult
      assistant  -> one API request; carries usage{input,output,cacheRead,cacheWrite,
                    totalTokens}, model, provider, stopReason, responseId, and
                    content[] entries of type toolCall{name,arguments,id}
      toolResult -> toolName, toolCallId, isError, details
  trajectory_runtime_events(seq, run_id, event_json)  -- run-level metadata only

Usage:
    uv run experiments/007-openclaw-role-routing/export.py describe <state-dir>
    uv run experiments/007-openclaw-role-routing/export.py export <state-dir> [--arm A]
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.trace import Episode  # noqa: E402

# Tool names that carry inter-agent traffic rather than work on the workspace. H3 is the
# claim that arm B's failures are more correlated than arm C's, and it is computable only
# if a message to another agent is distinguishable from a tool call. Confirmed shape:
# inter-agent sends appear as content entries of type "toolCall" with one of these names.
# **Still unverified** -- no arm B session has been run. Check against a real nine-agent
# session before computing H3, and widen this set if the shipped add-on names it
# differently.
AGENT_TO_AGENT_TOOLS = {"agentToAgent", "agent_to_agent", "sendToAgent", "mention"}

KNOWN_TRAJECTORY = {
    "session.started", "trace.metadata", "context.compiled", "prompt.submitted",
    "model.completed", "trace.artifacts", "session.ended",
}


def session_dbs(state_dir: str | Path) -> list[Path]:
    """Every agent's SQLite under a state dir. Arm B has nine agents, so this is a list
    and not a single path -- that is the whole reason H3 is computable.

    Deduplicated: the same file resolves through more than one glob path when a state dir
    is bind-mounted, and counting it twice would double every token and request total."""
    seen: dict[Path, Path] = {}
    for p in sorted(Path(state_dir).glob("agents/*/agent/openclaw-agent.sqlite")):
        seen.setdefault(p.resolve(), p)
    return list(seen.values())


def _events(db: Path, table: str) -> Iterator[dict[str, Any]]:
    """Yield parsed events, tolerating a table that does not exist."""
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        con.row_factory = sqlite3.Row
        try:
            cur = con.execute(f"SELECT * FROM {table} ORDER BY seq")  # noqa: S608
        except sqlite3.OperationalError as e:
            raise LookupError(f"{db.name}: {table}: {e}") from e
        for r in cur:
            d = dict(r)
            raw = d.pop("event_json", None)
            try:
                d["event"] = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                d["event"] = {"_unparsed": raw}
            yield d
    finally:
        con.close()


def _messages(db: Path) -> Iterator[tuple[int, dict[str, Any]]]:
    for e in _events(db, "transcript_events"):
        m = e["event"].get("message")
        if isinstance(m, dict) and m.get("role"):
            yield e["seq"], m


def _tool_calls(msg: dict[str, Any]) -> list[dict[str, Any]]:
    return [c for c in (msg.get("content") or [])
            if isinstance(c, dict) and c.get("type") == "toolCall"]


def count_model_calls(state_dir: str | Path) -> int:
    """Billed requests made under this state dir -- one per assistant message.

    This is what makes a request budget enforceable. A free tier metered in requests per
    day is spent by call count, not by tokens, and `model.completed` undercounts it."""
    n = 0
    for db in session_dbs(state_dir):
        try:
            n += sum(1 for _, m in _messages(db) if m.get("role") == "assistant")
        except LookupError:
            continue
    return n


def rate_limit_error(state_dir: str | Path) -> str | None:
    """The 429 message from this run, if it hit one, else None.

    Read from the trace rather than stderr: OpenClaw records the provider error on
    `model.completed` with stopReason "error", and a run killed this way aborts rather
    than backing off, leaving the workspace untouched. That makes a rate-limited run
    cleanly retryable -- and makes it a harness event, not a capability failure. Counting
    the two together is what made the first screen's headline number meaningless."""
    for db in session_dbs(state_dir):
        try:
            for e in _events(db, "trajectory_runtime_events"):
                # Scan the whole serialized event: errorMessage is nested inside the
                # message snapshot, not at the top of `data`. Reading only the top level
                # silently reports "no rate limit" on a run that died of one.
                blob = json.dumps(e["event"], default=str)
                if '"429' not in blob and "RESOURCE_EXHAUSTED" not in blob:
                    continue
                q = re.search(r'quotaId\\?"?:\s*\\?"([^"\\]+)', blob)
                delay = re.search(r'retryDelay\\?"?:\s*\\?"([^"\\]+)', blob)
                return (f"{q.group(1) if q else '429'} "
                        f"(retryDelay {delay.group(1) if delay else '?'})")
        except LookupError:
            continue
    return None


def input_tokens(state_dir: str | Path) -> int:
    """Billed input tokens: the `input` field alone, excluding the cached prefix."""
    return _sum_usage(state_dir, lambda u: int(u.get("input") or 0))


def quota_tokens(state_dir: str | Path) -> int:
    """Tokens as the *quota* counts them, which is what pacing must budget on.

    Measured 2026-09-10: `totalTokens` = input + output + cacheRead, and cacheRead is
    ~16,200 per call -- the system prompt and tool schemas, cached. Google's
    GenerateContentInputTokensPerModelPerMinute quota counts the cached prefix, so real
    consumption is ~21,000 per call against a 250,000/min cap, not the ~5,000 the `input`
    field reports. One 10-call instance is 87% of a minute's quota on its own.

    Pacing on `input` under-counts by 3-4x, which is why the second screen run lost 7 of
    10 instances to 429s that the pacer believed it had headroom for."""
    return _sum_usage(state_dir, lambda u: int(u.get("totalTokens") or 0))


def _sum_usage(state_dir: str | Path, pick) -> int:
    n = 0
    for db in session_dbs(state_dir):
        try:
            n += sum(pick(m.get("usage") or {})
                     for _, m in _messages(db) if m.get("role") == "assistant")
        except LookupError:
            continue
    return n


def rate_limit_delay(state_dir: str | Path, default: float = 30.0) -> float:
    """Seconds Google asked us to wait, from the 429 body. Retrying without honouring it
    just spends another request on another 429 -- which is what the second screen run did,
    twice per instance, for seven instances."""
    msg = rate_limit_error(state_dir)
    if not msg:
        return 0.0
    m = re.search(r"retryDelay ([0-9.]+)s", msg)
    return float(m.group(1)) if m else default


def describe(state_dir: str | Path) -> dict[str, Any]:
    """What is actually in these tables. Run this against a new provider or a new
    OpenClaw version before trusting export(): it is what caught both PILOT.md errors."""
    out: dict[str, Any] = {"dbs": [], "unknown_trajectory_types": Counter()}
    dbs = session_dbs(state_dir)
    if not dbs:
        out["error"] = (f"no agent SQLite under {state_dir} -- "
                        "wrong --state-dir, or the container did not persist it")
        return out
    for db in dbs:
        info: dict[str, Any] = {"path": str(db), "agent_id": db.parts[-3]}
        try:
            msgs = list(_messages(db))
        except LookupError as e:
            info["transcript_events"] = {"error": str(e)}
            msgs = []
        roles = Counter(m.get("role") for _, m in msgs)
        assistants = [m for _, m in msgs if m.get("role") == "assistant"]
        zero_usage = sum(1 for m in assistants
                         if not (m.get("usage") or {}).get("totalTokens"))
        info["transcript_events"] = {
            "messages": len(msgs), "roles": dict(roles),
            "api_requests": len(assistants),
            "assistants_with_zero_usage": zero_usage,
            "tools_called": dict(Counter(
                c.get("name") for m in assistants for c in _tool_calls(m))),
        }
        if assistants and zero_usage == len(assistants):
            info["WARNING"] = ("all usage is 0 -- set compat.supportsUsageInStreaming on "
                               "the model row, or every token figure here is fiction")
        try:
            traj = list(_events(db, "trajectory_runtime_events"))
            types = Counter((e["event"].get("type") or "?") for e in traj)
            info["trajectory_runtime_events"] = {"rows": len(traj), "types": dict(types)}
            for t, n in types.items():
                if t not in KNOWN_TRAJECTORY:
                    out["unknown_trajectory_types"][t] += n
        except LookupError as e:
            info["trajectory_runtime_events"] = {"error": str(e)}
        out["dbs"].append(info)
    out["unknown_trajectory_types"] = dict(out["unknown_trajectory_types"])
    return out


def export(state_dir: str | Path, task_id: str, seed: int, arm: str,
           config: dict[str, Any] | None = None) -> Episode:
    """One instance-run as an Episode: every agent's requests, with the fields H1-H3
    need. Arm B's nine agents collapse into one Episode because the instance, not the
    agent, is the unit the arms are compared on -- per-agent detail lives in step meta."""
    ep = Episode(task_id=task_id, seed=seed, config={"arm": arm, **(config or {})})
    capped = zero_usage = a2a = 0
    models: Counter = Counter()

    for db in session_dbs(state_dir):
        agent_id = db.parts[-3]
        try:
            msgs = list(_messages(db))
        except LookupError as e:
            ep.error = f"{ep.error or ''}{e}; "
            continue
        # Tool outcomes arrive as their own message; index them so each request records
        # what its calls actually did. A tool that errored and one that was never called
        # are different failures.
        results = {m.get("toolCallId"): m for _, m in msgs
                   if m.get("role") == "toolResult"}
        for seq, m in msgs:
            if m.get("role") != "assistant":
                continue
            u = m.get("usage") or {}
            if not u.get("totalTokens"):
                zero_usage += 1
            calls = _tool_calls(m)
            names = [c.get("name") for c in calls]
            if any(n in AGENT_TO_AGENT_TOOLS for n in names):
                a2a += 1
            stop = m.get("stopReason")
            if stop in ("length", "maxTokens", "max_tokens", "maxSteps", "budget"):
                capped += 1
            models[m.get("model")] += 1
            ep.step(
                state_before=None,   # prompts are reconstructable from the same table and
                                     # would dominate the file; the comparison needs counts
                action=names or None,
                observation=[
                    {"tool": (results.get(c.get("id")) or {}).get("toolName") or c.get("name"),
                     "error": bool((results.get(c.get("id")) or {}).get("isError"))}
                    for c in calls
                ] or None,
                tokens_in=int(u.get("input") or 0),
                tokens_out=int(u.get("output") or 0),
                meta={
                    "agent_id": agent_id,
                    "seq": seq,
                    # Recorded per request, not per run: a free-tier run spans days at
                    # 500 RPD, so an alias can move mid-run and that must stay visible.
                    "model": m.get("model"),
                    "provider": m.get("provider"),
                    "response_id": m.get("responseId"),
                    "stop_reason": stop,
                    "cache_read": u.get("cacheRead"),
                    "cache_write": u.get("cacheWrite"),
                    "total_tokens": u.get("totalTokens"),
                    "agent_to_agent": any(n in AGENT_TO_AGENT_TOOLS for n in names),
                },
            )

    ep.config.update({
        "agents_seen": len(session_dbs(state_dir)),
        "api_requests": len(ep.steps),
        # A truncated loop and a failed one are different failures; the README requires
        # the distinction be recorded rather than inferred.
        "capped_steps": capped,
        "agent_to_agent_steps": a2a,
        "models_used": dict(models),
    })
    if zero_usage:
        ep.config["zero_usage_steps"] = zero_usage
        ep.config["usage_suspect"] = (zero_usage == len(ep.steps))
    return ep


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("describe", help="what is actually in the tables")
    d.add_argument("state_dir")
    x = sub.add_parser("export", help="emit one Episode as JSON")
    x.add_argument("state_dir")
    x.add_argument("--task-id", default="unknown")
    x.add_argument("--seed", type=int, default=-1)
    x.add_argument("--arm", default="A")
    a = p.parse_args()

    if a.cmd == "describe":
        print(json.dumps(describe(a.state_dir), indent=2, default=str))
    else:
        print(json.dumps(export(a.state_dir, a.task_id, a.seed, a.arm).to_dict(),
                         indent=2, default=str))


if __name__ == "__main__":
    main()
