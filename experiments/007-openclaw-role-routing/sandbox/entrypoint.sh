#!/usr/bin/env bash
# Render the pinned config inside the container, then run one agent turn.
#
# The API key is a literal in the rendered file because `{source: "env"}` secret refs go
# through the gateway's resolver, which wants a paired device. The rendered file lives only
# in the container's /tmp, is mode 600, and never touches the host or the repo -- the key
# reaches this process through --env-file and nothing else.
#
# Provider-agnostic: every `__NAME__` placeholder in the mounted template is filled from the
# environment variable of the same name. Swapping providers is a template swap, not an edit
# here -- 007 compares configurations, and the backend has already had to change once.
set -euo pipefail

TEMPLATE=${OC_TEMPLATE:-/cfg/openclaw.template.json}
CFG=/tmp/oc/openclaw.json
mkdir -p /tmp/oc && chmod 700 /tmp/oc

# Python, not sed: an API key is arbitrary text and must not be reparsed as a sed script.
python3 - "$TEMPLATE" "$CFG" <<'PY'
import json, os, re, sys

src, dst = sys.argv[1], sys.argv[2]
text = open(src).read()
names = sorted(set(re.findall(r"__([A-Z0-9_]+)__", text)))
if not names:
    # Not an error since 011: the proxied template has no placeholder because it has no
    # secret. The credential lives in the egress proxy, and the agent's config carries a
    # baseUrl pointing at it. A template with nothing to fill in is the goal, not a
    # misconfiguration -- see sandbox/proxy/egress_proxy.py.
    print(f"{src}: no placeholders (proxied config -- no credential in this container)",
          file=sys.stderr)
missing = [n for n in names if not os.environ.get(n)]
if missing:
    sys.exit(f"{', '.join(missing)} not set (pass --env-file)")
for n in names:
    # The placeholder sits inside JSON string quotes, so escape the value as JSON would.
    # A raw backslash or quote in a key otherwise corrupts it silently, and a corrupted key
    # fails as an auth error that reads like a provider problem.
    text = text.replace(f"__{n}__", json.dumps(os.environ[n])[1:-1])
open(dst, "w").write(text)
print(f"rendered {src} -> {dst} ({', '.join(names)})", file=sys.stderr)
PY

chmod 600 "$CFG"

exec openclaw agent exec --config "$CFG" "$@"
