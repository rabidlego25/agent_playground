# Sandbox

The container 007 runs one agent turn in, and — since 2026-09-14 — the egress proxy that is
its only route off the machine.

    docker build -t openclaw-007 experiments/007-openclaw-role-routing/sandbox
    docker build -t openclaw-proxy-007 experiments/007-openclaw-role-routing/sandbox/proxy

**Do not hand-write the `docker run`.** The isolation flags are a single list in
`screen.py:docker_flags()`, and the probes in `tests/` import that function rather than
restating it, so a copied command silently gets a different sandbox than the one under test.
`screen.py run` calls `ensure_proxy()` first; to drive a turn by hand, import the module and
use the same two calls (`experiments/011-sandbox-containment/README.md` shows the exact
shape).

## Threat model

One operator, one laptop, one agent turn at a time, on a workspace and a task the operator
wrote. The agent is not assumed hostile. What *is* assumed, and is the entire reason this
container is shaped the way it is:

1. **The agent reads content it did not author** — defect files, task descriptions, anything
   in `/work`. Content that instructs is indistinguishable from content that informs, so the
   realistic failure is an injected instruction, not a model deciding on its own to misbehave.
2. **An agent turn is a program with a shell.** Whatever the configuration permits, some turn
   eventually does. Behaviour is not a control.
3. **This image is reused.** A sandbox described as safe becomes the starting point for the
   next experiment, and an inaccurate description outlives the run it was written for.

Out of scope: a hostile *host*, a malicious base image, and anything requiring a kernel
exploit — Docker Desktop on macOS puts a Linux VM under the container, so a capability or
seccomp escape lands in the VM rather than on macOS.

## What is enforced, and how

Measured 2026-09-14 by `tests/probe_sandbox.py --profile hardened` (10/10) and
`tests/probe_escape.py` (T4 0/6). Both import the real flags; neither takes this README's word
for anything.

| property | mechanism | verified by |
|---|---|---|
| no route to any host but the proxy | `--network openclaw-egress`, an `--internal` network | `egress_ip`, `egress_dns` both False |
| **no credential in the container at all** | no `--env-file`; the key lives in the proxy | `key_in_env` False |
| only one upstream, only two paths | proxy allowlist, constant upstream | 200 allowlisted / 403 off-allowlist |
| no privilege escalation | `--cap-drop=ALL --security-opt no-new-privileges` | `CapBnd 0000000000000000`, `NoNewPrivs 1` |
| no writes outside the mounts | `--read-only` plus a `tmpfs` at `/tmp` | `rootfs_ro` True |
| bounded blast radius on resources | `--pids-limit 256 --memory 2g` | `pids.max 256`, `memory.max 2147483648` |
| no container escape | no docker socket, own PID namespace, no host fs, no privileged devices | 0 of 6 routes open |

**The credential property is the one that matters most, and it is structural rather than
procedural.** The agent's config (`config/gemini-proxied.template.json`) carries a `baseUrl`
pointing at `http://openclaw-proxy:8080/v1beta/openai` and no key. `key_in_env` is False
because there is nothing in that container to find — not because something is hiding it. A
forward proxy could not achieve this: `CONNECT` builds an opaque TLS tunnel, so the credential
would have to travel inside the tunnel, which means inside the agent.

`entrypoint.sh` still renders the config inside the container, because `apiKey:
{source: "env"}` resolves through the gateway and fails headless. It fills every `__NAME__`
placeholder from the environment variable of the same name, JSON-escaping the value, and fails
loudly if one is unset. With the proxied template there are no placeholders at all, which it
now treats as normal rather than as an error. The rendered file lands in `/tmp/oc`, which is a
tmpfs — it dies with the container and never touches the host.

## What is *not* protected, stated plainly

- **`/work` and `/state` are writable host bind mounts** and survive the container. That is
  sanctioned — the task needs them — but it is real persistence, and it is the one channel by
  which a turn can leave something behind. `probe_escape.py` treats a file appearing on the
  host as a finding for exactly this reason.
- **Anything that can reach the proxy can spend the quota.** The proxy authenticates nobody;
  its boundary is the internal network, whose only other member is the agent container for
  that run. Put a second container on `openclaw-egress` and it inherits provider access.
- **The proxy container holds the key.** It is the highest-value target in this setup, which
  is why it also runs `--cap-drop=ALL --read-only --pids-limit 64 --memory 256m` as an
  unprivileged user. See `proxy/README.md`.
- **The allowlist is a path prefix, not a semantic filter.** Any request under
  `/v1beta/openai/` reaches the provider with the credential attached. It stops exfiltration
  to *other hosts*; it does not inspect what is being sent to this one.
- **No egress logging is retained.** The proxy logs ALLOW/DENY lines to stderr and nothing
  else; there is no audit trail after the container is removed.

## Reusing this elsewhere

`probe_sandbox.py --profile hardened` exiting 0 is the definition of hardened here — not this
README. Run it against whatever you change. If you swap the provider, the proxy's
`UPSTREAM_HOST` and `ALLOWED_PREFIXES` are the two constants that must change with it, and
leaving the old ones in place fails closed (403) rather than open.

The full measurement history, including what this sandbox looked like before hardening
(2 of 10 properties held, and the credential sat in the agent's environment next to
unrestricted egress), is `experiments/011-sandbox-containment/`.

## Provider configuration

`config/` holds one template per backend: `openclaw.template.json` (Groq),
`gemini.template.json` (Google AI Studio, **direct — pre-hardening, keeps the key in the
container**), and `gemini-proxied.template.json` (the default since 2026-09-14). All use
`api: "openai-completions"`; Gemini goes through its OpenAI-compatibility endpoint, which the
pilot's proven request shape reaches without a second code path. Neither `groq` nor `gemini`
is a built-in provider id; both are declared as custom providers.

The direct template is kept because it is the control that isolates proxy bugs from agent
bugs — it is what proved the agent itself was healthy while the proxy was mangling gzip. Using
it for real runs puts the credential back in the agent's environment and re-opens egress.

**Gemini free tier is unverified as a backend for this experiment** — see `../PILOT.md`.
Google no longer publishes free-tier limits, and the request budget may not fit. The config is
equally the paid-tier path: same endpoint, same shape, different quota.

No channel bindings exist — arm B's inter-agent traffic goes through `agentToAgent`, which is
what 007 measures; the messaging surface is not under test and is not attached.

**See `../PILOT.md` for what was observed, including why the Groq free tier cannot run the
experiment.**
