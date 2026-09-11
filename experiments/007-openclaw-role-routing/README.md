# 007 — Does role-specialised inter-agent routing beat one well-prompted agent?

**Status:** pre-registered; harness verified; backend chosen; pool calibrated to 0.75.
**Arm B pilot 2026-09-11 (`ARM-B-PILOT.md`): the chosen add-on cannot serve as arm B on a
repair task — it ran as one agent, 0 inter-agent messages, because its delegation is
triggered by named research-paper workflows and no repair-shaped workflow exists. H1 is
not testable against this scaffold without authoring the treatment ourselves. Awaiting a
decision on scaffold vs. task family.** **Created:** 2026-09-10. **Prediction committed in this file before any run**, and no run has been taken
against it. The pilot of 2026-09-10 (`PILOT.md`) wired OpenClaw 2026.9.3 end to end and then
found that the Groq free tier's 8,000 TPM cap makes the comparison unattributable: arm B would
hit rate limits far more often than arm A, so its predicted loss could not be read as
deliberation. The task world, oracle, sandbox and trace export all work and are unchanged by
this.

**Update, 2026-09-10 (`SCREEN.md`).** Backend resolved: Google AI Studio free tier,
`gemini-3.5-flash-lite`, the only free text model with a usable daily budget (500 RPD; every
Flash tier is 20 RPD after Google's December 2025 cut). The arm A screen came back at **7/7
= 1.00 on instances that ran to completion, with zero instances where the agent worked the
task and got it wrong.** That is the pre-registered *ceiling* condition, not the floor that
was feared. **The 12-defect pool cannot separate three arms and must be parameterised
before the main run** — the weakness this README already flagged under *Task family and
oracle* is now the binding one. The binding quota is input tokens per minute (250,000), not
requests, and arm B at 30-60 turns needs 165K-330K input tokens per instance, so it must be
paced across several minutes.

## Amendment 1 — 2026-09-11, before any main-run instance

The design below was pre-registered on 2026-09-10 and is amended here, **before any arm B
call has been made**, because the screen exposed two errors in it. Both amendments are
recorded with their reasons rather than quietly applied; the original text is left intact
below so the change is auditable.

**1. Arm C is dropped. The main run is A vs B, n=160.**

n=40 was chosen as "what the budget allows" and never checked against an effect size. At
the magnitudes 004 and 006 measured (+0.15 ensembling, −0.20 deliberation), paired McNemar
with rho=0.3 gives:

| n | C>A (.80 vs .65) | A>B (.65 vs .45) |
|---|---|---|
| 40 | 0.14 | 0.22 |
| 80 | 0.33 | 0.46 |
| 160 | 0.65 | **0.81** |
| 240 | 0.84 | 0.95 |

n=40 had 14–22% power: a null result would have meant nothing, and would have been
reported against a prediction this repo has spent five experiments building. Arm C is cut
because it is the most expensive arm (k parallel copies per instance), because its
ensembling leg is the part 004 and 006 already established, and because at arm A's
measured rate the C>A comparison is unreachable at any n the budget allows — with arm A at
0.90, even a *perfect* arm C gives p=0.125 at n=40.

**H1 is therefore narrowed to its A > B leg**, which is the claim 001–005 actually built
toward: the 9-agent routing config loses to one well-prompted agent. **H2 (cost) is
unchanged.** **H3 needs a new independence baseline** — it was defined against arm C's
independent runs, which no longer exist. The variance-floor runs this README already
requires (arm A twice on the same instances) supply it, and that has to be confirmed
before H3 is claimed, not after.

**2. Full tool surface, not `--local-model-lean`.**

Lean cuts a call from ~21,000 to 8,708 tokens, and an instance still passed 11/11 under it.
It is rejected anyway: 007 predicts arm B loses, so a flag that reduces every agent's
capability pushes in the direction of the hypothesis, and arm B is the arm the experiment is
about. It also buys nothing on the schedule — RPD meters *requests*, lean cuts *tokens per
request*, so the day count is identical either way.

**Cost of the amended design.** Arm A 11 calls/instance (measured); arm B 30–60
(PILOT.md's estimate, **never measured**). At n=160 that is 6,560–11,360 requests, or
**13–23 days** at 500 RPD. The 10-day spread is arm B's unmeasured cost, and the run is not
committed to until a short arm B pilot has measured it — the same pilot that must confirm
the `agentToAgent` message shape H3 depends on.

**Open, and gating the main run:** arm A is at 0.90 on the parameterised pool, above the
0.85 ceiling. `lib/worlds/repair.py` gained multi-edit defects on 2026-09-11 to bring it
toward 0.60–0.70; whether it lands there is unmeasured at the time of writing.

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

> **Amendment 1 (2026-09-11): arm C is dropped and n is 160.** The three-arm text below is
> the original pre-registration, kept for the record.

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

**`lib/worlds/repair.py`** (built 2026-09-10). A generated workspace: a small Python module
with one injected defect, a task statement, and a visible smoke suite. Pass = a hidden suite
passes. Binary, programmatic, no judge — the repo has no result yet on whether an LLM judge can
be trusted here, and `experiments/002-rhetoric-vs-information/` exists precisely because the
suspicion is that judges reward confident packaging. Do not introduce one as the primary
measure.

Three properties make it a repair task rather than a test-running task, and
`tests/probe_repair_world.py` asserts all of them on every instance before any run:

- the hidden suite fails on the workspace as shipped;
- **the visible smoke suite passes on it** — so running the shipped tests does not locate the
  bug, and the work is in reading the specification against the code;
- the hidden suite passes on the reference source, so the oracle is not measuring its own bugs.

The hidden tests are never written into the workspace. `check()` copies the workspace, deletes
any `test_*.py` the agent left behind, and runs the suite there — an agent with write access can
edit any test it can see, and in this design it will have write access.

**Stated limitation: the pool is 12 distinct defects** (3 modules × 4 mutation operators), so
n=40 draws repeats. Paired comparisons across arms remain valid — every arm sees the same
instances — but the instances are not independent, and the effective n for any claim about
*repair tasks in general* is 12, not 40. Parameterising the templates (constants, grid shapes,
transaction sequences) is the fix, and it should happen before the main run if 007 is to say
anything beyond "on these twelve defects".

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

- **Arm B as shipped cannot do a shared-file repair task at all.** Read out of the cloned
  add-on 2026-09-11, not from its README. `setup.sh:162` pins every sub-agent to its own
  private workspace:

      openclaw agents add ${id} --workspace ${OPENCLAW_HOME}/workspace-${id}

  Only `main` sits at the cwd we pass. So Planner, Critic, Coder and the rest **cannot read
  or edit `/work`**. Arm B does not degrade to a worse panel; it degrades to *main working
  alone while eight agents who cannot see the code offer advice*. If that loses, the
  explanation is trivial and has nothing to do with deliberation.

  That topology is coherent for the workflow the add-on was built for — each role produces
  its own artefact (a survey, a draft, a review) and they exchange text. It is incoherent
  for a task whose whole content is a shared file.

  Minimal fix: point every agent's workspace at the task workspace. One field, and it makes
  the comparison test what 007 says it tests. It is still a **deviation from "installed as
  shipped"**, which was the reason this add-on was chosen, and must be reported as one.

- **The shipped prompts are ~25% Chinese** (12,650 CJK characters across the agent
  prompts; every `soul.md` identity block is Chinese) while the task statement and the
  codebase are English. Part of the treatment, reported verbatim, and another reason an
  arm B loss would have a cheaper explanation than deliberation.

- **The nine roles are built for a different task family, and this is now the sharpest
  threat to H1.** Confirmed 2026-09-11 by reading the add-on rather than the summary of
  it: the roles are Planner, Ideator, Critic, Surveyor (*literature research*), Coder,
  Writer (*paper writing and LaTeX*), Reviewer (*peer review and rebuttal*), Scout (*daily
  paper digests*). That is a research-paper pipeline. On `lib/worlds/repair.py` roughly
  four of nine agents have any applicable function and four have none.

  So if arm B loses — which 007 predicts — the most economical explanation is role-task
  mismatch, not deliberation. That is a *different claim* from the one 001–005 built, and
  it would not transfer. Three ways out, none free:

  1. Accept it, report the roles verbatim, and rest the deliberation claim on H3
     (correlated failure), which a prompt-quality or role-fit deficit does not predict.
     Weaker than it was: Amendment 1 dropped arm C, so H3's independence baseline is now
     the arm-A-twice variance runs and is unconfirmed.
  2. Swap the task family for one the nine roles fit. The repair world is built, probed
     and validated; a research-shaped task with a programmatic oracle is not, and 002
     exists because judges cannot be trusted to score one.
  3. Use a code-oriented multi-agent config instead. Changes what is being tested from
     "the configuration people deploy" to "a configuration we chose", which is most of
     why this add-on was picked.

  **Decide before the main run, not in the analysis.** `agentToAgent.allow` is also a
  restricted graph (`planner ↔ all, ideator ↔ critic, writer ↔ reviewer`), not all-to-all,
  so H3's correlation structure has to be computed over that topology rather than assumed.

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
