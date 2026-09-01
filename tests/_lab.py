"""Shared plumbing for lab probes.

A probe is a cheap, local measurement that characterises the instrument -- the models,
the task families, the noise floor -- rather than answering a headline question. Probes
run on ollama, cost nothing, and their traces land in results/ like any other run.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.models import Backend, get                      # noqa: E402
from lib.tasks import Task                               # noqa: E402
from lib.trace import Episode, TraceWriter               # noqa: E402


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval. Reported instead of a bare mean because at the n a local
    sweep can afford, the normal approximation is wrong in exactly the regime we care
    about -- near 0 and near 1."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))



def mcnemar(a: list[bool], b: list[bool]) -> tuple[int, int, float]:
    """Exact McNemar on paired outcomes. Returns (a_only, b_only, two-sided p).

    Arms in this repo run on identical task instances, so the marginal intervals are the
    wrong test -- task-set variance (0.163) is three times run-to-run variance (0.050),
    and a paired test removes it. Exact rather than chi-square because the discordant
    count is routinely under 25.
    """
    if len(a) != len(b):
        raise ValueError(f"unpaired: {len(a)} vs {len(b)}")
    x = sum(1 for u, v in zip(a, b) if u and not v)
    y = sum(1 for u, v in zip(a, b) if v and not u)
    n = x + y
    if n == 0:
        return x, y, 1.0
    tail = sum(math.comb(n, i) for i in range(min(x, y) + 1)) / (2 ** n)
    return x, y, min(1.0, 2 * tail)

@dataclass
class Cell:
    """One condition of a probe: a set of tasks run under one configuration."""

    label: str
    config: dict[str, Any]
    n: int = 0
    hits: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: float = 0.0
    errors: int = 0
    fmt_ok: int = 0          # responses that obeyed the ANSWER: format

    @property
    def acc(self) -> float:
        return self.hits / self.n if self.n else 0.0

    @property
    def ci(self) -> tuple[float, float]:
        return wilson(self.hits, self.n)

    @property
    def compliance(self) -> float:
        return self.fmt_ok / self.n if self.n else 0.0

    def row(self) -> str:
        lo, hi = self.ci
        return (f"{self.label:<26} {self.acc:>6.2f}  [{lo:.2f},{hi:.2f}]  "
                f"n={self.n:<4} fmt={self.compliance:>4.2f}  tok={self.tokens_out:<6} "
                f"{self.latency_ms / max(self.n, 1) / 1000:>5.1f}s/call"
                + (f"  ERR={self.errors}" if self.errors else ""))


def run_cell(backend: Backend, tasks: Iterable[Task], *, label: str, experiment: str,
             config: dict[str, Any], temperature: float = 0.0, max_tokens: int = 400,
             seed: Callable[[Task], int | None] | None = None,
             writer: TraceWriter | None = None, verbose: bool = True) -> Cell:
    w = writer or TraceWriter(experiment)
    cell = Cell(label=label, config=config)
    for t in tasks:
        s = seed(t) if seed else t.seed
        ep = Episode(task_id=t.task_id, seed=t.seed,
                     config={**config, "label": label, "temperature": temperature,
                             "family": t.family, "difficulty": t.difficulty,
                             "sample_seed": s})
        c = backend.complete(t.prompt, temperature=temperature, max_tokens=max_tokens, seed=s)
        ep.step(state_before=t.prompt, action=c.text, tokens_in=c.tokens_in,
                tokens_out=c.tokens_out, latency_ms=c.latency_ms,
                meta={"error": c.error})
        choice, fmt_ok = t.parse(c.text)
        ok = False if c.error else t.scored(c.text)
        ep.steps[-1].meta["format_ok"] = fmt_ok
        ep.steps[-1].meta["parsed"] = choice
        ep.finish(verdict=ok, outcome=choice)
        ep.error = c.error
        w.write(ep)
        cell.n += 1
        cell.hits += int(ok)
        cell.errors += int(bool(c.error))
        cell.fmt_ok += int(fmt_ok)
        cell.tokens_in += c.tokens_in
        cell.tokens_out += c.tokens_out
        cell.latency_ms += c.latency_ms
        if verbose:
            print(f"\r  {label}: {cell.n} run, {cell.hits} correct", end="", flush=True)
    if verbose:
        print()
    return cell


def table(cells: list[Cell], title: str) -> str:
    head = f"\n{title}\n{'-' * len(title)}\n"
    head += (f"{'condition':<26} {'acc':>6}  {'95% CI':<13} {'n':<6} {'fmt':<5} "
             f"{'out-tok':<10} {'latency'}\n")
    return head + "\n".join(c.row() for c in cells)


def require(spec: str) -> Backend:
    b = get(spec)
    if not b.available():
        sys.exit(f"backend {spec} unavailable (is `ollama serve` running?)")
    return b


# --------------------------------------------------------------- task transforms
import random as _random                                  # noqa: E402
import re as _re                                           # noqa: E402
from lib.tasks import _tail_token                          # noqa: E402


def shuffle_facts(t: Task, rng: _random.Random) -> Task:
    """Same task, fact lines reordered. If accuracy moves, the family is measuring
    position as much as reasoning."""
    lines = t.prompt.splitlines()
    idx = [i for i, ln in enumerate(lines) if ln.startswith("- ")]
    facts = [lines[i] for i in idx]
    rng.shuffle(facts)
    for i, f in zip(idx, facts):
        lines[i] = f
    return Task(t.task_id + "-shuf", t.family, t.seed, "\n".join(lines), t.check,
                answer=t.answer, difficulty={**t.difficulty, "shuffled": True})


def rename_entities(t: Task, rng: _random.Random) -> Task:
    """Replace recognisable names with nonsense tokens. A drop in accuracy here is the
    signature of recall rather than reasoning -- the structure is identical."""
    names = sorted({n for ln in t.prompt.splitlines() if ln.startswith("- ")
                    for n in ln[2:].rstrip(".").split(" reports to ")})
    alphabet = "bcdfghjklmnpqrstvwxz"
    seen: set[str] = set()
    mapping: dict[str, str] = {}
    for n in names:
        while True:
            tok = ("".join(rng.choice(alphabet) for _ in range(3))
                   + str(rng.randint(10, 99))).capitalize()
            if tok not in seen:
                seen.add(tok)
                break
        mapping[n] = tok
    prompt = t.prompt
    for old, new in sorted(mapping.items(), key=lambda kv: -len(kv[0])):
        prompt = _re.sub(rf"\b{_re.escape(old)}\b", new, prompt)
    gold = mapping.get(str(t.answer), str(t.answer))

    def check(raw: str, gold=gold) -> bool:
        return _tail_token(raw).strip(".,!").lower() == gold.lower()

    return Task(t.task_id + "-scram", t.family, t.seed, prompt, check,
                answer=gold, difficulty={**t.difficulty, "scrambled": True})


def majority(answers: list[str]) -> str:
    """Plurality over normalised final-line answers; ties break toward the first seen,
    which is the conservative choice (no free lunch from tie-breaking)."""
    norm = [_tail_token(a).strip(".,!").lower() for a in answers]
    best, seen = None, {}
    for a in norm:
        seen[a] = seen.get(a, 0) + 1
    for a in norm:
        if best is None or seen[a] > seen[best]:
            best = a
    return best or ""
