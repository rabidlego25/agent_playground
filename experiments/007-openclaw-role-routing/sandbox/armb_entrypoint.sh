#!/usr/bin/env bash
# Arm B: install the nine-agent add-on, then run one turn against `main`.
#
# Everything the add-on ships -- role prompts, identities, routing topology, its Chinese
# soul.md files -- is left as-is. Four things have to be repaired around it to make it run
# headless at all, and each is recorded here because they are deviations from
# "installed as shipped" and 007's whole reason for choosing this add-on was fidelity:
#
#   1. `agents add` is called without --non-interactive and the failure is swallowed by
#      `|| true`, so headless the script creates *no agents* and still exits 0. One flag.
#   2. jq is missing from the base image (added to the Dockerfile). Without it setup.sh
#      skips the agentToAgent block silently -- nine agents that cannot talk, which is
#      the treatment under test.
#   3. OPENCLAW_HOME must be left UNSET. setup.sh derives it as "$HOME/.openclaw"; if the
#      variable is already set, OpenClaw appends `.openclaw` to it again and the two
#      disagree by one directory -- setup.sh's jq then silently fails to write the
#      agentToAgent block. Unset, both land on /state/.openclaw and it writes correctly.
#   4. The add-on's agentToAgent block is written for an older runtime: it ships a
#      directed {from,to} edge list, but 2026.9.3's schema is a flat string match-list, and
#      the config is rejected outright. The restricted topology is not expressible here, so
#      what actually runs is all-to-all. setup.sh also writes `agents.list`, which this
#      runtime does not recognise (the live key is `agents.entries`); it is dropped.
#   5. main's workspace is pointed at the task directory. Sub-agents keep their own
#      workspaces and their own prompts; they reach the task by absolute path, which was
#      verified to work before this was relied on.
#
# Usage: armb_entrypoint.sh <task-file> <workspace> [extra openclaw args...]
set -euo pipefail

TASK_FILE=${1:?task file}
WORKSPACE=${2:?workspace}
shift 2

MODEL=${OC_MODEL:-gemini/gemini-3.5-flash-lite}
export HOME=/state
unset OPENCLAW_HOME            # let setup.sh derive it; step 3 above explains the nesting
CFG=/state/.openclaw/openclaw.json

if [[ ! -f "$CFG" ]]; then
  cp -r /addon /tmp/addon
  cd /tmp/addon && chmod +x setup.sh
  sed -i "s|openclaw agents add \${id} --model|openclaw agents add \${id} --non-interactive --model|" setup.sh
  ./setup.sh --mode local --model "$MODEL" >/tmp/setup.log 2>&1 || true
  [[ -f "$CFG" ]] || { echo "setup.sh produced no config:" >&2; tail -20 /tmp/setup.log >&2; exit 1; }
fi

python3 - "$CFG" "$WORKSPACE" <<'PY'
import json, os, re, sys

cfg_path, workspace = sys.argv[1], sys.argv[2]
cfg = json.load(open(cfg_path))

# Provider block, rendered from the same template arm A uses so the two arms hit the same
# endpoint with the same compat flags. Key comes from the environment and is never written
# anywhere but this file, inside the container.
tpl = open("/cfg/openclaw.template.json").read()
for name in sorted(set(re.findall(r"__([A-Z0-9_]+)__", tpl))):
    if not os.environ.get(name):
        sys.exit(f"{name} not set (pass --env-file)")
    tpl = tpl.replace(f"__{name}__", json.dumps(os.environ[name])[1:-1])
cfg.setdefault("models", {}).setdefault("providers", {}).update(
    json.loads(tpl)["models"]["providers"])

# agentToAgent. The add-on ships a directed edge list --
#   allow: [{from: "*", to: "planner"}, {from: "ideator", to: "critic"}, ...]
# -- and OpenClaw 2026.9.3 REJECTS it: the schema is `allow?: string[]`, "agent ids or `*`
# glob patterns; the requesting and target agent must both match". A config written for an
# older runtime. As shipped, arm B does not load at all.
#
# The restricted topology the add-on intends is therefore not expressible in this runtime,
# and every valid translation is all-to-all. Listing the ids explicitly rather than using
# "*" so the roster is visible in the config that gets archived with the run. Recorded
# because H3's correlation structure has to be computed over the topology that actually
# ran, which is all-to-all, not the graph the add-on's README describes.
cfg.setdefault("tools", {})["agentToAgent"] = {
    "enabled": True,
    "allow": sorted(cfg.get("agents", {}).get("entries", {})),
}

# setup.sh's jq step also writes `agents.list`, which this runtime does not recognise --
# the live key is `agents.entries`. Drop it rather than ship a config that fails validation.
cfg.get("agents", {}).pop("list", None)

entries = cfg.setdefault("agents", {}).setdefault("entries", {})
entries.setdefault("main", {})["workspace"] = workspace
entries["main"]["model"] = os.environ.get("OC_MODEL", "gemini/gemini-3.5-flash-lite")

json.dump(cfg, open(cfg_path, "w"), indent=2)
print(f"arm B: {len(entries)} agents, models="
      f"{sorted({e.get('model') for e in entries.values() if e.get('model')})}, "
      f"agentToAgent={cfg['tools']['agentToAgent']['enabled']}", file=sys.stderr)
PY

exec openclaw agent --agent main --local --message-file "$TASK_FILE" --json "$@"
