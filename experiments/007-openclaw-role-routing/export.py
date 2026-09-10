"""Export OpenClaw session state to lib.trace Episodes.

The README's rule is that a run which cannot be replayed will be paid for twice, and 007
is the most expensive design in this repo. This is the exporter that rule demands.

**Unvalidated against real data as of 2026-09-10.** The schema below comes from PILOT.md,
which read it off one observed pilot session; no session SQLite was persisted from that
pilot, so nothing here has been run against real rows. It is therefore written to fail
loudly rather than quietly: every event type it does not recognise is counted and
reported by `describe()`, never dropped. Run `describe()` on the first real session
before trusting any Episode it produces.

Storage, per PILOT.md:
  <state-dir>/agents/<agentId>/agent/openclaw-agent.sqlite
    transcript_events(session_id, seq, event_json)
      -- message | custom | session | model_change | thinking_level_change
    trajectory_runtime_events(session_id, seq, run_id, event_json)
      -- traceSchema "openclaw-trajectory", schemaVersion 1
      -- session.started | context.compiled | prompt.submitted | model.completed
         | trace.artifacts | session.ended
      -- model.completed carries usage, so tokens per call come from here

Usage:
    uv run experiments/007-openclaw-role-routing/export.py describe <state-dir>
    uv run experiments/007-openclaw-role-routing/export.py export <state-dir> [--arm A]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.trace import Episode  # noqa: E402

# The event that corresponds to one billed API request. Counting these is what makes a
# request budget enforceable against a metered free tier, so it is named once here.
MODEL_CALL_EVENT = "model.completed"

KNOWN_TRAJECTORY = {
    "session.started", "context.compiled", "prompt.submitted",
    MODEL_CALL_EVENT, "trace.artifacts", "session.ended",
}


def session_dbs(state_dir: str | Path) -> list[Path]:
    """Every agent's SQLite under a state dir. Arm B has nine agents, so this is a list
    and not a single path -- that is the whole reason H3 is computable."""
    return sorted(Path(state_dir).glob("agents/*/agent/openclaw-agent.sqlite"))


def _rows(db: Path, table: str) -> Iterator[dict[str, Any]]:
    """Yield parsed events, tolerating a table that does not exist. A missing table is a
    schema guess that was wrong; the caller reports it rather than crashing mid-sweep."""
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


def _dig(obj: Any, *names: str) -> Any:
    """First value found under any of `names`, at any depth. The trace schema is known
    from one observation, so exact key paths are not yet trustworthy; the field names
    are the more stable part of that observation."""
    if isinstance(obj, dict):
        for n in names:
            if n in obj and obj[n] is not None:
                return obj[n]
        for v in obj.values():
            got = _dig(v, *names)
            if got is not None:
                return got
    elif isinstance(obj, list):
        for v in obj:
            got = _dig(v, *names)
            if got is not None:
                return got
    return None


def describe(state_dir: str | Path) -> dict[str, Any]:
    """What is actually in these tables. Run this on the first real session before
    trusting export(): it is the check that separates a schema that was observed from a
    schema that was assumed."""
    out: dict[str, Any] = {"dbs": [], "unknown_event_types": Counter()}
    dbs = session_dbs(state_dir)
    if not dbs:
        out["error"] = (f"no agent SQLite under {state_dir} -- "
                        "wrong --state-dir, or the container did not persist it")
        return out
    for db in dbs:
        info: dict[str, Any] = {"path": str(db), "agent_id": db.parts[-3]}
        for table in ("trajectory_runtime_events", "transcript_events"):
            try:
                evs = list(_rows(db, table))
            except LookupError as e:
                info[table] = {"error": str(e)}
                continue
            types = Counter(
                (e["event"].get("type") or e["event"].get("event") or "?") for e in evs
            )
            info[table] = {"rows": len(evs), "types": dict(types)}
            if table == "trajectory_runtime_events":
                for t, n in types.items():
                    if t not in KNOWN_TRAJECTORY:
                        out["unknown_event_types"][t] += n
                # One sample of the call event, so its real usage keys are visible
                # rather than inferred.
                sample = next((e["event"] for e in evs
                               if (e["event"].get("type") == MODEL_CALL_EVENT)), None)
                if sample is not None:
                    info["model_completed_sample"] = sample
        out["dbs"].append(info)
    out["unknown_event_types"] = dict(out["unknown_event_types"])
    return out


def count_model_calls(state_dir: str | Path) -> int:
    """Billed requests made under this state dir. The request-budget guard reads this
    after every instance, because a free tier metered in requests per day is spent by
    call count and not by tokens."""
    n = 0
    for db in session_dbs(state_dir):
        try:
            n += sum(1 for e in _rows(db, "trajectory_runtime_events")
                     if e["event"].get("type") == MODEL_CALL_EVENT)
        except LookupError:
            continue
    return n


def export(state_dir: str | Path, task_id: str, seed: int, arm: str,
           config: dict[str, Any] | None = None) -> Episode:
    """One instance-run as an Episode: every agent's calls, in sequence, with the fields
    H1-H3 need. Arm B's nine agents collapse into one Episode because the instance, not
    the agent, is the unit the arms are compared on."""
    ep = Episode(task_id=task_id, seed=seed,
                 config={"arm": arm, **(config or {})})
    unknown: Counter = Counter()
    capped = False

    for db in session_dbs(state_dir):
        agent_id = db.parts[-3]
        try:
            evs = list(_rows(db, "trajectory_runtime_events"))
        except LookupError as e:
            ep.error = f"{ep.error or ''}{e}; "
            continue
        for e in evs:
            ev = e["event"]
            etype = ev.get("type") or ev.get("event") or "?"
            if etype not in KNOWN_TRAJECTORY:
                unknown[etype] += 1
            if etype != MODEL_CALL_EVENT:
                continue
            usage = _dig(ev, "usage", "tokenUsage") or {}
            stop = _dig(ev, "stopReason", "finishReason", "stop_reason")
            if stop in ("length", "max_tokens", "max_steps"):
                capped = True
            ep.step(
                state_before=None,          # prompts live in transcript_events; the
                                            # comparison does not need them inline and
                                            # they would dominate the file size
                action=_dig(ev, "toolName", "tool_name", "tool"),
                observation=_dig(ev, "toolStatus", "exitStatus", "status"),
                tokens_in=int(_dig(usage, "inputTokens", "input_tokens", "promptTokens") or 0),
                tokens_out=int(_dig(usage, "outputTokens", "output_tokens", "completionTokens") or 0),
                latency_ms=float(_dig(ev, "durationMs", "latencyMs", "duration_ms") or 0.0),
                meta={
                    "agent_id": agent_id,
                    "role": _dig(ev, "agentRole", "role"),
                    # Recorded per call, not per run: a multi-day run on a free tier can
                    # have an alias move under it, and that has to be visible afterwards.
                    "model": _dig(ev, "modelId", "model", "model_id"),
                    "run_id": e.get("run_id"),
                    "session_id": e.get("session_id"),
                    "stop_reason": stop,
                    # H3 is not computable without this field. It is a guess at the key
                    # name until a real arm B session is inspected -- see PILOT.md,
                    # "what is still unpinned".
                    "agent_to_agent": bool(_dig(ev, "agentToAgent", "agent_to_agent")),
                },
            )

    ep.config["capped"] = capped          # a truncated loop and a failed one are
                                          # different failures; the README requires the
                                          # distinction be recorded, not inferred
    ep.config["agents_seen"] = len(session_dbs(state_dir))
    ep.config["model_calls"] = len(ep.steps)
    if unknown:
        ep.config["unknown_event_types"] = dict(unknown)
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
        ep = export(a.state_dir, a.task_id, a.seed, a.arm)
        print(json.dumps(ep.to_dict(), indent=2, default=str))


if __name__ == "__main__":
    main()
