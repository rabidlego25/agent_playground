"""Depth held fixed, distractor count varied.

Separates two failures usually reported as one: losing the chain because it is long, and
losing it because the context is noisy. They have different fixes, so conflating them
wastes effort.
"""
from _lab import require, run_cell, table
from lib.tasks import generate

N, LOADS, DEPTH, MODEL = 50, (0, 3, 6, 10, 14), 3, "ollama:qwen2.5"

if __name__ == "__main__":
    b = require(MODEL)
    cells = []
    for k in LOADS:
        tasks = [generate("multi_hop", 2000 + s, depth=DEPTH, distractors=k) for s in range(N)]
        cells.append(run_cell(
            b, tasks, label=f"distractors={k}", experiment="probe_distractor_load",
            config={"probe": "distractor_load", "model": MODEL, "depth": DEPTH, "distractors": k},
            temperature=0.0))
    print(table(cells, f"Distractor load -- multi_hop depth={DEPTH}, {MODEL}, n={N}"))
