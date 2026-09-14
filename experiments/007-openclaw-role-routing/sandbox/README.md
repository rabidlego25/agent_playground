# Sandbox

Build:

    docker build -t openclaw-007 experiments/007-openclaw-role-routing/sandbox

Run one turn against a workspace (verified 2026-09-10, OpenClaw 2026.9.3):

    docker run --rm \
      --env-file ~/Documents/scratch/keys/openclaw.env \
      -v "$PWD/experiments/007-openclaw-role-routing/sandbox/config/gemini.template.json:/cfg/openclaw.template.json:ro" \
      -v "$PWD/experiments/007-openclaw-role-routing/sandbox/entrypoint.sh:/entrypoint.sh:ro" \
      -v /path/to/ws:/work -v /path/to/state:/state \
      openclaw-007 bash /entrypoint.sh \
        --model gemini/gemini-2.5-flash --local-model-lean --code-mode direct \
        --cwd /work --state-dir /state --timeout 360 --json --message-file /work/TASK.md

Swap the mounted template to change provider; `config/` holds one per backend
(`openclaw.template.json` = Groq, `gemini.template.json` = Google AI Studio). Both use
`api: "openai-completions"` — Gemini through its OpenAI-compatibility endpoint at
`https://generativelanguage.googleapis.com/v1beta/openai`, which the pilot's proven request
shape reaches without a second code path. Neither `groq` nor `gemini` is a built-in provider
id; both are declared as custom providers.

**Gemini free tier is unverified as a backend for this experiment** — see `../PILOT.md`.
Google no longer publishes free-tier limits, and the request budget may not fit. The config
above is equally the paid-tier path: same endpoint, same shape, different quota.

`entrypoint.sh` renders the config inside the container, because `apiKey: {source: "env"}`
resolves through the gateway and fails headless. It fills every `__NAME__` placeholder in the
mounted template from the environment variable of the same name, JSON-escaping the value, and
fails loudly if one is unset. The key reaches the container only through `--env-file`; it is
never written to the host or committed.

The container is unprivileged (uid 1001, `CapEff` 0) and no channel
bindings exist — arm B's inter-agent traffic goes through `agentToAgent`, which is what 007
measures; the messaging surface is not under test and is not attached.

**See `../PILOT.md` for what was observed, including why the Groq free tier cannot run the
experiment.**
