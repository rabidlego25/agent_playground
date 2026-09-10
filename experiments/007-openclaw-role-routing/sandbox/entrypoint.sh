#!/usr/bin/env bash
# Render the pinned config inside the container, then run one agent turn.
#
# The API key is a literal in the rendered file because `{source: "env"}` secret refs go
# through the gateway's resolver, which wants a paired device. The rendered file lives only
# in the container's /tmp, is mode 600, and never touches the host or the repo -- the key
# reaches this process through --env-file and nothing else.
set -euo pipefail

: "${GROQ_API_KEY:?GROQ_API_KEY not set (pass --env-file)}"

CFG=/tmp/oc/openclaw.json
mkdir -p /tmp/oc && chmod 700 /tmp/oc
sed "s|__GROQ_API_KEY__|${GROQ_API_KEY}|" /cfg/openclaw.template.json > "$CFG"
chmod 600 "$CFG"

exec openclaw agent exec --config "$CFG" "$@"
