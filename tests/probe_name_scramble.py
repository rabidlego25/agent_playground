"""Real names replaced by nonsense tokens, structure untouched.

A drop here is the signature of recall doing work that should be done by reasoning. Run
against our own generator, this also checks that procedural generation is buying what it
claims to buy.
"""
import random
from _lab import rename_entities, require, run_cell, table
from lib.tasks import generate

N, DEPTH, MODEL = 60, 3, "ollama:qwen2.5"

if __name__ == "__main__":
    b = require(MODEL)
    rng = random.Random(0)
    base = [generate("multi_hop", 4000 + s, depth=DEPTH) for s in range(N)]
    cells = [
        run_cell(b, base, label="real names", experiment="probe_name_scramble",
                 config={"probe": "name_scramble", "model": MODEL, "names": "real"},
                 temperature=0.0),
        run_cell(b, [rename_entities(t, rng) for t in base], label="scrambled tokens",
                 experiment="probe_name_scramble",
                 config={"probe": "name_scramble", "model": MODEL, "names": "scrambled"},
                 temperature=0.0),
    ]
    print(table(cells, f"Name scrambling -- multi_hop depth={DEPTH}, {MODEL}, n={N}"))
