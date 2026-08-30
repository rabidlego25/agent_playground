"""Procedurally generated tasks with programmatic oracles.

Generation rather than collection is what makes this cheap and honest: every run draws
fresh instances, so there is nothing for a model to have memorized; difficulty is a knob
rather than a property of a fixed corpus; and n is unbounded at zero token cost.

Every family exposes generate(seed, **knobs) -> Task, where Task.check(answer) is the
oracle. Families here are single-shot (episodes of length 1); the multi-step filesystem
world lands in lib/worlds/ and uses the same Task interface.
"""

from __future__ import annotations

import random
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from itertools import permutations
from typing import Any, Callable

__all__ = ["Task", "FAMILIES", "generate", "assignment_puzzle", "hidden_tests", "multi_hop"]


@dataclass
class Task:
    task_id: str
    family: str
    seed: int
    prompt: str
    check: Callable[[str], bool]         # the oracle: does this answer satisfy the task?
    answer: Any = None                   # ground truth, for analysis -- never shown to the model
    difficulty: dict[str, Any] = field(default_factory=dict)
    extract: Callable[[str], tuple[str, bool]] | None = None   # -> (choice, format_ok)

    def parse(self, raw: str) -> tuple[str, bool]:
        return self.extract(raw) if self.extract else (_tail_token(raw), True)

    def scored(self, raw: str) -> bool:
        try:
            return bool(self.check(raw))
        except Exception:
            return False                 # an un-parseable answer is a wrong answer


def _tail_token(text: str) -> str:
    """Models pad answers with prose. Take the last non-empty line, strip markup."""
    lines = [ln.strip() for ln in str(text).strip().splitlines() if ln.strip()]
    if not lines:
        return ""
    return lines[-1].strip("*`_ .").removeprefix("ANSWER:").removeprefix("Answer:").strip()



def extract_choice(raw: str, candidates: list[str]) -> tuple[str, bool]:
    """Pull an answer out of a response, and say whether the model obeyed the format.

    Free-form extraction is where evals quietly go wrong: score the last line verbatim and
    a model that narrates ("...is Altair.") reads as catastrophically worse than one that
    complies, so the comparison measures instruction-following instead of reasoning. So
    tasks ask for a delimited `ANSWER: x` line, and this returns (choice, format_ok):

      - strict  -- an `ANSWER:` line whose value is a valid candidate  -> format_ok True
      - lenient -- otherwise, the last candidate named anywhere        -> format_ok False

    Report both. The lenient path is still ambiguous for answer-first phrasings
    ("Sable is one level above Quill" extracts Quill), which is exactly why non-compliance
    is recorded rather than silently absorbed into the accuracy number.
    """
    text = str(raw)
    lowered = {c.lower(): c for c in candidates}

    field = None
    for m in re.finditer(r"ANSWER\s*[:\-]\s*(.+)", text, re.I):
        field = m.group(1)
    if field is not None:
        v = field.strip().strip("*`_ .,!\"'")
        if v.lower() in lowered:
            return lowered[v.lower()], True

    tail = _tail_token(text)
    if tail.lower() in lowered:
        return lowered[tail.lower()], True

    def last_hit(scope: str) -> str | None:
        hits = [(m.start(), m.group(0)) for c in candidates
                for m in re.finditer(rf"\b{re.escape(c)}\b", scope, re.I)]
        return lowered[max(hits)[1].lower()] if hits else None

    for scope in (tail, text):
        hit = last_hit(scope)
        if hit is not None:
            return hit, False
    return tail, False


# --------------------------------------------------------------------------- family 1
def assignment_puzzle(seed: int, n: int = 4) -> Task:
    """Constraint satisfaction with a unique solution, verified by brute force.

    Constraints are emitted until exactly one permutation survives, so the task is
    guaranteed well-posed -- a generated benchmark that is sometimes ambiguous measures
    the generator, not the model.
    """
    rng = random.Random(seed)
    people = ["Ana", "Ben", "Cleo", "Dev", "Eli"][:n]
    houses = list(range(1, n + 1))
    truth = houses[:]
    rng.shuffle(truth)
    pos = dict(zip(people, truth))

    pool: list[tuple[str, Callable[[dict], bool]]] = []
    for a, b in permutations(people, 2):
        if pos[a] < pos[b]:
            pool.append((f"{a} lives in a lower-numbered house than {b}.",
                         lambda p, a=a, b=b: p[a] < p[b]))
        if abs(pos[a] - pos[b]) == 1:
            pool.append((f"{a} and {b} live in adjacent houses.",
                         lambda p, a=a, b=b: abs(p[a] - p[b]) == 1))
    for p in people:
        wrong = rng.choice([h for h in houses if h != pos[p]])
        pool.append((f"{p} does not live in house {wrong}.",
                     lambda c, p=p, wrong=wrong: c[p] != wrong))
    rng.shuffle(pool)

    def candidates(cs: list[Callable[[dict], bool]]) -> list[dict]:
        out = []
        for perm in permutations(houses):
            cand = dict(zip(people, perm))
            if all(c(cand) for c in cs):
                out.append(cand)
                if len(out) > 1:
                    return out
        return out

    chosen_txt: list[str] = []
    chosen_fn: list[Callable[[dict], bool]] = []
    for txt, fn in pool:
        if len(candidates(chosen_fn)) == 1 and chosen_fn:
            break
        chosen_txt.append(txt)
        chosen_fn.append(fn)
    if len(candidates(chosen_fn)) != 1:
        return assignment_puzzle(seed + 10_000, n)   # rare; redraw rather than ship ambiguity

    target = people[0]
    prompt = (
        f"{n} people live in houses numbered 1 to {n}, one person per house.\n"
        + "\n".join(f"- {t}" for t in chosen_txt)
        + f"\n\nWhich house does {target} live in? "
        f"End your reply with a final line of the form `ANSWER: <number>`."
    )
    gold = pos[target]

    def extract(raw: str) -> tuple[str, bool]:
        text = str(raw)
        field = None
        for m in re.finditer(r"ANSWER\s*[:\-]\s*(-?\d+)", text, re.I):
            field = m.group(1)
        if field is not None:
            return field, True
        tail = _tail_token(text)
        if tail.isdigit():
            return tail, True
        for scope in (tail, text):
            m = re.findall(r"-?\d+", scope)
            if m:
                return m[-1], False
        return tail, False

    def check(raw: str) -> bool:
        c, _ = extract(raw)
        try:
            return int(c) == gold
        except ValueError:
            return False

    return Task(f"assign-{n}-{seed}", "assignment_puzzle", seed, prompt, check,
                answer=gold, difficulty={"n": n, "constraints": len(chosen_txt)},
                extract=extract)


# --------------------------------------------------------------------------- family 2
_TEMPLATES = [
    ("Write a Python function `f(xs)` that returns the sum of elements of the list `xs` "
     "that are strictly greater than {k}.",
     lambda k: (lambda xs: sum(x for x in xs if x > k)),
     lambda rng, k: [[rng.randint(-20, 20) for _ in range(rng.randint(0, 8))] for _ in range(6)]),
    ("Write a Python function `f(s)` that returns the number of characters in the string "
     "`s` that appear exactly {k} times in `s`.",
     lambda k: (lambda s: sum(1 for c in set(s) if s.count(c) == k)),
     lambda rng, k: ["".join(rng.choice("aabbccdde") for _ in range(rng.randint(0, 12)))
                     for _ in range(6)]),
    ("Write a Python function `f(n)` that returns the sum of all positive integers below "
     "`n` that are divisible by {k}.",
     lambda k: (lambda n: sum(i for i in range(1, n) if i % k == 0)),
     lambda rng, k: [rng.randint(0, 60) for _ in range(6)]),
]


def hidden_tests(seed: int, k_range: tuple[int, int] = (2, 5)) -> Task:
    """A short function specified in prose, scored by unit tests the model never sees.

    Constants are drawn per-instance, so a memorized solution to last week's instance
    fails this one -- the cheapest contamination probe available.
    """
    rng = random.Random(seed)
    text, ref_factory, arg_factory = rng.choice(_TEMPLATES)
    k = rng.randint(*k_range)
    ref = ref_factory(k)
    args = arg_factory(rng, k)
    cases = [(a, ref(a)) for a in args]
    prompt = text.format(k=k) + "\n\nReply with a Python code block defining `f` and nothing else."

    def check(raw: str) -> bool:
        m = re.search(r"```(?:python)?\s*(.*?)```", str(raw), re.S)
        code = m.group(1) if m else str(raw)
        if "def f" not in code:
            return False
        harness = code + "\n\nCASES = " + repr(cases) + """
for _a, _want in CASES:
    assert f(_a) == _want, (_a, f(_a), _want)
print("PASS")
"""
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as fh:
            fh.write(harness)
            p = fh.name
        try:
            r = subprocess.run([sys.executable, p], capture_output=True, text=True, timeout=10)
            return r.returncode == 0 and "PASS" in r.stdout
        except subprocess.SubprocessError:
            return False

    return Task(f"tests-{seed}", "hidden_tests", seed, prompt, check,
                answer=cases, difficulty={"k": k, "cases": len(cases)})


# --------------------------------------------------------------------------- family 3
def multi_hop(seed: int, depth: int = 3, distractors: int = 6, above: int = 2) -> Task:
    """A fact chain of a given depth, where each hop is only reachable from the previous.

    `depth` is the knob that makes error compounding measurable: accuracy against depth is
    the quantity of interest, not accuracy at any single depth.

    `above` is a correctness requirement, not a knob to tune. The chain continues `above`
    levels past the gold answer so the answer is an *interior* node. Without it (the
    2026-08-29 bug) the gold answer was always the unique root of the graph, and "walk up
    until you cannot" scored 100% at every depth without counting a single hop — so `depth`
    changed prompt length and nothing else. Keep `above >= 1`.
    """
    if above < 1:
        raise ValueError("above must be >= 1, or the answer is the graph root and depth is decorative")
    rng = random.Random(seed)
    names = ["Vega", "Rigel", "Altair", "Mira", "Deneb", "Lyra", "Orin", "Cass",
             "Talos", "Nyx", "Sable", "Quill", "Wren", "Zephyr", "Corvus", "Draco",
             "Elara", "Fenrir", "Halcy", "Iris", "Juno", "Kepler", "Lumen", "Mensa",
             "Norne", "Ophir", "Pavo", "Rhea", "Solen", "Tycho"]
    need = depth + 1 + above + distractors
    if need > len(names):
        raise ValueError(f"need {need} distinct names, have {len(names)}")
    rng.shuffle(names)
    chain = names[: depth + 1 + above]
    facts = [f"{chain[i]} reports to {chain[i + 1]}." for i in range(depth + above)]
    pool = names[depth + 1 + above:]
    placed = list(chain)                 # valid managers: nobody gains a second manager
    for a in pool[:distractors]:
        facts.append(f"{a} reports to {rng.choice(placed)}.")
        placed.append(a)                 # append after, so edges can never form a cycle
    rng.shuffle(facts)
    prompt = (
        "Facts:\n" + "\n".join(f"- {f}" for f in facts)
        + f"\n\nFollowing the reporting chain upward from {chain[0]}, who is {depth} level{'s' if depth != 1 else ''} above "
        f"{chain[0]}? End your reply with a final line of the form `ANSWER: <name>`."
    )
    gold = chain[depth]

    cands = sorted({n for f in facts for n in f.rstrip(".").split(" reports to ")})

    def extract(raw: str) -> tuple[str, bool]:
        return extract_choice(raw, cands)

    def check(raw: str) -> bool:
        return extract(raw)[0].lower() == gold.lower()

    return Task(f"hop-{depth}-{seed}", "multi_hop", seed, prompt, check,
                answer=gold, difficulty={"depth": depth, "distractors": distractors, "above": above},
                extract=extract)


FAMILIES: dict[str, Callable[..., Task]] = {
    "assignment_puzzle": assignment_puzzle,
    "hidden_tests": hidden_tests,
    "multi_hop": multi_hop,
}


def generate(family: str, seed: int, **knobs: Any) -> Task:
    return FAMILIES[family](seed, **knobs)
