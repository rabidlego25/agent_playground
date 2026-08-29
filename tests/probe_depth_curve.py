"""Accuracy against reasoning depth -- error compounding, measured directly.

Also sets the operating point for experiment 001: arms compared at a depth where the base
model is at floor or ceiling cannot separate, whatever the effect.
"""
from _lab import Cell, require, run_cell, table
from lib.tasks import generate

N, DEPTHS = 50, (1, 2, 3, 4, 5, 6)
MODELS = ("ollama:qwen2.5", "ollama:llama3.1")

if __name__ == "__main__":
    cells = []
    for spec in MODELS:
        b = require(spec)
        for d in DEPTHS:
            tasks = [generate("multi_hop", 1000 + s, depth=d) for s in range(N)]
            cells.append(run_cell(
                b, tasks, label=f"{spec.split(':')[1]} d={d}", experiment="probe_depth_curve",
                config={"probe": "depth_curve", "model": spec, "depth": d},
                temperature=0.0))
    print(table(cells, f"Depth curve -- multi_hop, n={N} per cell"))
