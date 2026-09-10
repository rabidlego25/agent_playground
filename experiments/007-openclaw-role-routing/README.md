# 007 — Does role-specialised inter-agent routing beat one well-prompted agent?

**Status:** designed, not run. **Created:** 2026-09-10. **Prediction committed in this file
before any run.**

## Question

001–005 measured, on a synthetic task with a programmatic oracle, that agents which read each
other underperform agents that do not, at matched tokens:

| result | source |
|---|---|
| deliberation costs 1.85× independent sampling for identical accuracy | 001 |
| at the prompt ceiling, deliberation 0.71 vs 0.86 for silent draws, p<0.0001, at 1.2× cost | 004 |
| deliberation cost the strongest panel member −0.123 | 005 |
| the mechanism: communication raises conditional-on-wrong agreement `c` | 003/004/005 |

Every one of those is a single-call model on `multi_hop` depth 4. The stated weakness of all five
is the same: **one task family, no tools, no loop.** This experiment moves the claim to a real
tool-using agent runtime and a configuration that people actually deploy.

`shenhao-stu/openclaw-agents` installs nine role-specialised agents on OpenClaw — Planner,
Ideator, Critic, Surveyor, Coder, Writer, Reviewer, Scout, and a Main orchestrator that acts as
"final arbiter" — communicating either through `@mention` routing in a group channel or directly
via an `agentToAgent` tool, with non-matching messages "stored for context". That is a
deliberating panel with a coordinator, which is the configuration 004 found significantly worse
than not communicating.

**If the 001–005 account is right, this configuration loses to one agent with a good prompt.**
That prediction is committed here, before the first run.

## Arms

All three run the same task instances, in the same sandbox, with the same tool policy.

- **A — single agent, prompt at ceiling.** One OpenClaw agent, tools enabled, no
  `agentToAgent`. The prompt is tuned first (see *Procedure*), because a configuration effect
  measured below the prompt ceiling is a measurement of how much the configuration compensates
  for a bad prompt (`notes/2026-08-30-prompt-dominates-configuration.md`).
- **B — the 9-agent group routing config**, installed as shipped, `agentToAgent` enabled,
  Local Workflow Mode (no channel bindings — see *Safety*).
- **C — k parallel agents, no communication.** k independent copies of arm A on the same
  instance, `agentToAgent` disabled, the candidate selected by the task's own test oracle.
  This is the "ensemble without communication" arm that 004 found dominant, and on a task with
  runnable tests the selector is available at runtime, so it is a deployable configuration and
  not an oracle cheat.

k in arm C is set to the number of agents arm B actually invokes on the same instance, measured
from the session log, so the panels are matched on calls rather than on nominal size.

## Task family and oracle

**Small self-contained repair tasks with hidden unit tests.** Pass = the hidden tests pass.
Binary, programmatic, no judge — the repo has no result yet on whether an LLM judge can be
trusted here, and `experiments/002-rhetoric-vs-information/` exists precisely because the
suspicion is that judges reward confident packaging. Do not introduce one as the primary
measure.

n=40 instances, identical across arms, all comparisons paired (exact McNemar), Wilson intervals
on the marginals. n is small and stated: this is a token-expensive design and 40 paired
instances is what the budget allows. Report the discordant-pair count, not just the p-value.

## The prediction, committed before any run

- **H1 (direction).** Pass rate: **C > A > B**. The 9-agent routing config is beaten by one
  well-prompted agent.
- **H2 (cost).** Arm B spends **≥3×** arm A's total tokens for that worse result. 004's
  deliberation arm was only 1.2× at k=3; nine roles with an arbiter should be far worse.
- **H3 (mechanism).** The `c` analogue — P(a second agent's attempt fails | the first failed),
  computed across arm C's independent runs versus across arm B's role agents — is **higher in
  B**. If communication is what destroys independence, B's failures are more correlated than C's
  on the same instances.

**What would falsify the account:** B ≥ A on pass rate. That would mean role specialisation buys
something on tool-using tasks that it does not buy on single-call reasoning, and the working
order out of 001–005 ("fix the prompt, ensemble without communication, do not deliberate") does
not transfer out of this repo's task family.

## Procedure

1. **Find the prompt ceiling for arm A first**, on 10 held-out instances not used in the main
   run. Sweep 3–4 prompts; take the best. Report where on that axis the main run sits.
2. Install the 9-agent config unmodified. Record its shipped prompts verbatim into `runs/` —
   they are part of the treatment.
3. Run A, B, C on the same 40 instances, same day, same model, same sandbox image.
4. Export traces (see below) to `results/` as step-level JSONL before any analysis.

## Instrumentation

OpenClaw stores sessions in SQLite at
`~/.openclaw/agents/<agentId>/agent/openclaw-agent.sqlite`, with legacy transcript JSONL under
session folders. **Write the exporter before the first real run** — a run that cannot be
replayed will be paid for twice, and this design is the most expensive thing in the repo so far.
Per step, record: agent id, role, model, tokens in/out, tool name, tool exit status, wall time,
and whether the step was an `agentToAgent` message. The last field is what makes H3 computable.

Also record, per instance and arm: total calls, total tokens, wall time, whether a patch was
produced at all (the tool-using analogue of the `format_ok` column that 001 had to add after
`notes/2026-08-29-oracle-format-confound.md`), and whether any step hit a step or token cap —
a truncated agent loop is indistinguishable from a failed one unless the cap is recorded.

## Model plan — the blocking decision

The add-on defaults to `zai/glm-5` and supports `--model` for a unified model and `--model-map`
for per-agent assignment. This repo's constraints (`CLAUDE.md`) are a Claude Pro subscription,
which is not API-accessible to an external daemon, and three local 7–8B models measured at
0.51 / 0.22 / 0.18 on `multi_hop`.

**A nine-agent tool-using loop on a 0.51 local model will floor out**, and a floor is not a
comparison — it is 003's failure repeated in a more expensive setting. So one of:

- a free-tier key (Groq / Google AI Studio / Cohere — $0, no card, and CLAUDE.md already flags
  this as the cheapest way to widen the roster), same model in every arm; or
- a paid key for a frontier model, run at n=40 with a hard token budget; or
- local `ollama` for a **pilot only** (n=10), to debug the harness and the exporter, with the
  result reported as a harness check and never as a finding.

Do not run the main comparison until every arm's base rate is off the floor. **Verify first:**
that the chosen provider works through OpenClaw's `provider/model` resolution, and that
`--model-map` genuinely holds the model fixed across all nine agents — an unequal model map
would confound role specialisation with capability.

## Safety

The runtime has `read/exec/edit/write` core tools and can drive a browser and send mail.

- Run in Docker, not on the host. The repo machine holds every trace in `results/`.
- **No channel bindings.** Local Workflow Mode only — no Telegram, WhatsApp, Slack or mail
  account attached. Arm B's inter-agent traffic goes through `agentToAgent`, which is the part
  under test; the messaging surface is not.
- Restrict tool policy to the workspace. Network off except the model endpoint.
- The injection experiment (an agent whose input arrives from an untrusted channel) is a
  separate design against a throwaway instance, and is not this experiment.

## Known weaknesses, stated in advance

- **The scaffold is a confound.** Arm B ships its own nine role prompts. A loss could be role
  specialisation, or it could be that those particular prompts are worse than arm A's tuned one.
  Mitigation: report arm B's shipped prompts verbatim, and treat H3 (correlated failure) as the
  claim that separates the two accounts — a prompt-quality deficit does not predict *correlated*
  failure, and a communication effect does.
- **Token matching is approximate.** Agent loops choose their own step counts, so arms cannot be
  matched exactly the way 001's arms were. Report tokens per arm and accuracy per token; do not
  claim a matched-token comparison.
- **n=40, one task family, one model.** Same limitation this repo has had since 001, now at
  higher cost per instance.
- **Nondeterminism is larger here than in 001–006.** Tool errors, timeouts and network variance
  add variance that `tests/probe_variance_floor.py` (0.050 run-to-run on single calls) does not
  bound. Run arm A twice on the same instances to get a floor for *this* setting before reading
  any effect.
- **OpenClaw is unverified in this repo.** Everything above about its runtime, CLI, config
  layout and storage comes from the docs read 2026-09-10
  (`docs.openclaw.ai/concepts/agent`, `docs.openclaw.ai/cli/agents`) and the add-on's README,
  not from having run it. Confirm the SQLite path, the `agentToAgent` semantics and the
  `--model-map` behaviour empirically in the pilot before trusting the design.
