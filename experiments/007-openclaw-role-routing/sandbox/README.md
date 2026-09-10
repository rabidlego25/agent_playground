# Sandbox

Build:

    docker build -t openclaw-007 experiments/007-openclaw-role-routing/sandbox

Run one turn against a workspace (verified 2026-09-10, OpenClaw 2026.9.3):

    docker run --rm \
      --env-file ~/Documents/scratch/keys/openclaw.env \
      -v "$PWD/experiments/007-openclaw-role-routing/sandbox/config/openclaw.template.json:/cfg/openclaw.template.json:ro" \
      -v "$PWD/experiments/007-openclaw-role-routing/sandbox/entrypoint.sh:/entrypoint.sh:ro" \
      -v /path/to/ws:/work -v /path/to/state:/state \
      openclaw-007 bash /entrypoint.sh \
        --model groq/openai/gpt-oss-120b --local-model-lean --code-mode direct \
        --cwd /work --state-dir /state --timeout 360 --json --message-file /work/TASK.md

`entrypoint.sh` renders the config inside the container from `$GROQ_API_KEY`, because
`apiKey: {source: "env"}` resolves through the gateway and fails headless. The key reaches the
container only through `--env-file`; it is never written to the host or committed.

The container is unprivileged (uid 1001), the agent's blast radius is `/work`, and no channel
bindings exist — arm B's inter-agent traffic goes through `agentToAgent`, which is what 007
measures; the messaging surface is not under test and is not attached.

**See `../PILOT.md` for what was observed, including why the Groq free tier cannot run the
experiment.**
