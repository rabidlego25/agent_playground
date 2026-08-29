"""How much of a measured accuracy is noise?

Every later result is read against this number. Run the identical task set twice at each
temperature: the gap between two runs of the *same* condition is the smallest difference
any experiment here can honestly claim to detect.
"""
from _lab import Cell, require, run_cell, table, wilson
from lib.tasks import generate

N, MODEL = 60, "ollama:qwen2.5"

if __name__ == "__main__":
    b = require(MODEL)
    tasks = [generate("multi_hop", s, depth=3) for s in range(N)]
    cells = []
    for temp in (0.0, 0.7):
        for rep in (1, 2):
            cells.append(run_cell(
                b, tasks, label=f"temp={temp} rep{rep}", experiment="probe_variance_floor",
                config={"probe": "variance_floor", "model": MODEL, "rep": rep},
                temperature=temp, seed=lambda t, rep=rep: t.seed * 100 + rep))
    print(table(cells, f"Variance floor -- multi_hop depth=3, {MODEL}, n={N}"))
    gaps = []
    for i in (0, 2):
        gap = abs(cells[i].acc - cells[i + 1].acc)
        gaps.append(gap)
        print(f"  same-condition gap, {cells[i].label.split()[0]}: {gap:.3f}")
    print(f"  noise floor (largest same-condition gap): {max(gaps):.3f}")
    print("\n  Any effect smaller than the largest same-condition gap is not measurable at this n.")
