"""Multi-step worlds: tasks an agent works in, rather than answers in one call.

`lib.tasks` families are episodes of length 1 — prompt in, string out, oracle over the
string. Everything in 001–006 is that shape. A tool-using agent needs a workspace it can
read, edit and test, and an oracle that scores the *workspace* after the agent stops.

Every world exposes:

    generate(seed, **knobs) -> World
    World.materialize(dir)          write the starting workspace
    World.check(dir) -> Verdict     score it, without trusting anything in dir

The oracle never lives inside the workspace. An agent with write access can edit any file
it can see, so hidden tests are applied to a copy at scoring time.
"""

from lib.worlds.repair import REPAIR_TEMPLATES, RepairWorld, Verdict, generate

__all__ = ["generate", "RepairWorld", "Verdict", "REPAIR_TEMPLATES"]
