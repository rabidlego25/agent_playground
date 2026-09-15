# OpenClaw sandbox for 007.
#
# The runtime has read/exec/edit/write core tools and can drive a browser and send mail.
# It does not run on the host: this repo's machine holds every trace in results/, and an
# agent loop with exec is not something to point at it. No channel bindings are configured
# here -- arm B's inter-agent traffic goes through agentToAgent, which is what 007 measures;
# the messaging surface is not under test and is not attached.
#
# Node 24 is recommended upstream, 22.19+ supported.
FROM node:24-bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        git python3 python3-venv ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g openclaw@latest

# jq is required by the arm B add-on's setup.sh. Without it the script still exits 0 but
# silently skips writing the agentToAgent block -- i.e. it installs nine agents that cannot
# talk to each other, which is the treatment 007 exists to measure.
RUN apt-get update && apt-get install -y --no-install-recommends jq \
    && rm -rf /var/lib/apt/lists/*

# Unprivileged: uid 1001, CapEff 0.
#
# The blast radius is NOT /work. Measured 2026-09-14 by tests/probe_sandbox.py (011):
# with the flags screen.py actually uses, this container reaches arbitrary hosts and
# DNS, carries GEMINI_API_KEY in its environment, writes to two host bind mounts
# (/work and /state), runs on a writable rootfs with NoNewPrivs=0 and a full capability
# bounding set, and has no pid or memory ceiling. 2 of 10 containment properties hold,
# and both are the mounts that are supposed to be writable.
#
# That is acceptable for an unbilled single-operator experiment on a machine whose
# owner is running the agent deliberately. It is not acceptable for reuse. See
# experiments/011-sandbox-containment/README.md for the egress-proxy configuration
# that makes `probe_sandbox.py --profile hardened` pass.
RUN useradd -m -u 1001 agent && mkdir -p /work && chown agent:agent /work
USER agent
WORKDIR /work

ENV OPENCLAW_HOME=/home/agent/.openclaw \
    PYTHONDONTWRITEBYTECODE=1

# Pinned at pilot time against the real CLI surface, not guessed from docs.
CMD ["bash"]
