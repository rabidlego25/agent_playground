# Sandbox

Build:

    docker build -t openclaw-007 experiments/007-openclaw-role-routing/sandbox

Run one instance's workspace into it, network restricted to the model endpoint:

    docker run --rm -it -v "$PWD/ws:/work" openclaw-007

**Unverified.** Nothing here has been built or run — the Docker daemon was down and no
provider key was set when it was written (2026-09-10). The install command and Node floor
come from the OpenClaw docs, not from a successful build. Treat the first build as part of
the pilot, and fix this file from what actually happens rather than from what it says.

The pilot has to pin, empirically:

- the non-interactive invocation for a single task in a workspace;
- the session SQLite path and schema (docs say
  `~/.openclaw/agents/<agentId>/agent/openclaw-agent.sqlite`), so the trace exporter can be
  written against the real table layout;
- whether `--model-map` genuinely holds one model across all nine agents, since an unequal
  map would confound role specialisation with capability;
- what `agentToAgent` messages look like in the log — H3 is not computable without being
  able to tell an inter-agent message from a tool call.
