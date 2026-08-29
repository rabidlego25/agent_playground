"""Append-only, step-level run traces.

The schema here is the one thing in this repo that is expensive to change: it decides
whether a run recorded today is still comparable to one recorded in a year. It is an
*episode of steps*, never a single (prompt, answer, verdict) triple. A single-shot task
is an episode of length 1, so multi-step task families need no migration.
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO_ROOT / "results"


def _git_commit() -> str | None:
    """Commit sha of the code that produced the run. A reproducibility claim without
    this is unfalsifiable, so it is recorded automatically rather than by convention."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=5,
        )
        if out.returncode != 0:
            return None
        sha = out.stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=5,
        ).stdout.strip()
        return f"{sha}-dirty" if dirty else sha
    except (OSError, subprocess.SubprocessError):
        return None


@dataclass
class Step:
    """One agent action and what came back. `state_before` is whatever the agent could
    see at decision time -- for a tool-using world that is the observation history, for a
    single-shot task it is the prompt."""

    i: int
    state_before: Any
    action: Any
    observation: Any = None
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class Episode:
    task_id: str
    seed: int
    config: dict[str, Any]
    steps: list[Step] = field(default_factory=list)
    verdict: bool | None = None          # oracle result; None = not yet scored
    subgoals_hit: int = 0                # partial credit, so premature stopping has its
    subgoals_total: int = 0              # own signature distinct from a wrong answer
    outcome: Any = None                  # final answer / final state digest
    error: str | None = None

    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    schema_version: int = SCHEMA_VERSION
    commit: str | None = field(default_factory=_git_commit)
    started_at: float = field(default_factory=time.time)
    ended_at: float | None = None
    env: dict[str, Any] = field(
        default_factory=lambda: {"python": platform.python_version(),
                                 "platform": platform.platform()}
    )

    def step(self, **kwargs: Any) -> Step:
        s = Step(i=len(self.steps), **kwargs)
        self.steps.append(s)
        return s

    @property
    def tokens(self) -> tuple[int, int]:
        return (sum(s.tokens_in for s in self.steps),
                sum(s.tokens_out for s in self.steps))

    def finish(self, verdict: bool | None = None, outcome: Any = None) -> "Episode":
        if verdict is not None:
            self.verdict = verdict
        if outcome is not None:
            self.outcome = outcome
        self.ended_at = time.time()
        return self

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        ti, to = self.tokens
        d["tokens_in_total"], d["tokens_out_total"] = ti, to
        d["wall_ms"] = None if self.ended_at is None else (self.ended_at - self.started_at) * 1000
        return d


class TraceWriter:
    """Append-only JSONL. One file per experiment; never rewrite a past run."""

    def __init__(self, experiment: str, results_dir: Path | None = None):
        self.experiment = experiment
        base = results_dir or RESULTS_DIR
        base.mkdir(parents=True, exist_ok=True)
        self.path = base / f"{experiment}.jsonl"

    def write(self, ep: Episode) -> Episode:
        line = json.dumps(ep.to_dict(), default=str, ensure_ascii=False)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
            os.fsync(f.fileno())   # a sweep that dies mid-run keeps everything before it
        return ep

    def __enter__(self) -> "TraceWriter":
        return self

    def __exit__(self, *exc: object) -> None:
        return None


def read(path: str | Path) -> list[dict[str, Any]]:
    """Load a trace file for analysis. Replay beats re-run: this is how a finding gets
    re-examined without paying for the tokens twice."""
    with open(path, encoding="utf-8") as f:
        return [json.loads(ln) for ln in f if ln.strip()]
