"""Identical tasks, fact order shuffled.

If accuracy moves, the family is partly measuring position rather than reasoning, and any
later claim about deliberation is confounded by presentation order.
"""
import random
from _lab import require, run_cell, shuffle_facts, table
from lib.tasks import generate

N, DEPTH, MODEL = 60, 3, "ollama:qwen2.5"

if __name__ == "__main__":
    b = require(MODEL)
    rng = random.Random(0)
    base = [generate("multi_hop", 3000 + s, depth=DEPTH) for s in range(N)]
    cells = [
        run_cell(b, base, label="as generated", experiment="probe_order_sensitivity",
                 config={"probe": "order_sensitivity", "model": MODEL, "order": "generated"},
                 temperature=0.0),
        run_cell(b, [shuffle_facts(t, rng) for t in base], label="facts shuffled",
                 experiment="probe_order_sensitivity",
                 config={"probe": "order_sensitivity", "model": MODEL, "order": "shuffled"},
                 temperature=0.0),
    ]
    print(table(cells, f"Order sensitivity -- multi_hop depth={DEPTH}, {MODEL}, n={N}"))
