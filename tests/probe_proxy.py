"""Attack the egress proxy's allowlist. 011 arm A's fix, put under the same scrutiny as the
thing it replaced.

The proxy is now the highest-value target in 007: it holds the provider credential and it is
the only process on the agent's network with a route off the machine. It was written on
2026-09-14, verified to *work*, and never once tested to see whether it can be made to do
something else. That is the same posture that produced four scorer defects in arm C2, every one
of them failing in the direction its author expected.

So: raw HTTP, sent from a container on the agent's own network, with a pre-registered verdict
for every case. Exits non-zero only on a **surprise** -- an observation that differs from the
prediction in either direction -- because a probe that flags everything is a red light nobody
reads.

**Pre-registered, written before the first execution (2026-09-14):**

  absolute_uri      403  -- `POST http://elsewhere/x` gives self.path the whole URI, which
                            does not start with the allowed prefix
  dot_traversal     FINDING expected: the prefix test is `str.startswith` on an unnormalised
                            path, so `/v1beta/openai/../../v1/other` passes it and is
                            forwarded verbatim. The upstream is fixed, so this cannot reach
                            another host -- but generativelanguage.googleapis.com serves more
                            than the OpenAI shim (`/v1beta/files`, `/v1beta/tunedModels`,
                            which create and delete), so it widens what the credential can do
  encoded_traversal FINDING expected, same mechanism with %2e%2e
  bad_method_put    405
  bad_method_delete 405
  connect           403
  host_override     forwarded to the real upstream anyway; `host` is dropped from the
                            request, so the Host header cannot redirect this proxy
  client_auth_hdr   forwarded, but the client's own Authorization is discarded, not relayed
  crlf_in_path      not forwarded -- http.client validates the request line and raises, which
                            this proxy turns into 502
  te_and_cl         the request is read as chunked; any smuggled remainder is parsed as a
                            *new* request on the same connection and faces the allowlist
                            again, so no bypass -- but it has never been checked
  key_not_echoed    no response body on any path contains the credential

    uv run tests/probe_proxy.py
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCREEN = ROOT / "experiments/007-openclaw-role-routing/screen.py"
OUT = ROOT / "results/011_proxy.jsonl"

# (key, observed on the shipped proxy, required after the fix, what is being attacked)
#
# Two columns for the same reason probe_sandbox.py has two profiles: the first is the
# measurement, the second is the definition of done. `--profile shipped` reproduces the
# 2026-09-14 pre-fix behaviour; `--profile fixed` is the acceptance test.
CASES = [
    ("absolute_uri",      "403",      "403",      "absolute-URI request line redirects the upstream"),
    ("dot_traversal",     "FORWARD",  "403",      "../ escapes the allowlisted path prefix"),
    ("encoded_traversal", "FORWARD",  "403",      "%2e%2e escapes the allowlisted path prefix"),
    ("bad_method_put",    "501",      "405",      "PUT outside the allowed method set"),
    ("bad_method_delete", "501",      "405",      "DELETE outside the allowed method set"),
    ("connect",           "403",      "403",      "CONNECT tunnelling"),
    ("host_override",     "FORWARD",  "FORWARD",  "Host header redirects the upstream"),
    ("client_auth_hdr",   "FORWARD",  "FORWARD",  "client Authorization relayed upstream"),
    ("crlf_in_path",      "MALFORMED","MALFORMED","CRLF in the path injects a header upstream"),
    ("te_and_cl",         "NO_DESYNC","NO_DESYNC","Content-Length + Transfer-Encoding desync"),
    ("key_not_echoed",    "CLEAN",    "CLEAN",    "the credential appears in a response body"),
]

# Sent over a raw socket: some of these are deliberately malformed and no HTTP client will
# emit them. Each returns the status line the proxy answered with, or a marker.
PAYLOAD = r'''
import socket, sys, json

HOST, PORT = "openclaw-proxy", 8080
OK = "/v1beta/openai/models"

def send(raw: bytes, read_all: bool = False) -> str:
    s = socket.create_connection((HOST, PORT), timeout=25)
    try:
        s.sendall(raw)
        buf = b""
        while True:
            try:
                b = s.recv(65536)
            except socket.timeout:
                break
            if not b:
                break
            buf += b
            if not read_all and b"\r\n\r\n" in buf:
                break
        return buf.decode("latin-1", "replace")
    finally:
        s.close()

def status(resp: str) -> str:
    return resp.split("\r\n", 1)[0] if resp else "(no response)"

def code(resp: str) -> str:
    parts = status(resp).split()
    return parts[1] if len(parts) > 1 else "?"

out = {}

# 1. absolute-URI request line
r = send(b"POST http://example.invalid/steal HTTP/1.1\r\nHost: openclaw-proxy\r\n"
         b"Content-Length: 0\r\nConnection: close\r\n\r\n")
out["absolute_uri"] = code(r)

# 2/3. traversal out of the allowlisted prefix
for key, path in (("dot_traversal", "/v1beta/openai/../../v1beta/models"),
                  ("encoded_traversal", "/v1beta/openai/%2e%2e/%2e%2e/v1beta/models")):
    r = send(f"GET {path} HTTP/1.1\r\nHost: openclaw-proxy\r\nConnection: close\r\n\r\n"
             .encode())
    out[key] = code(r)

# 4/5. methods outside the allowlist
for key, meth in (("bad_method_put", "PUT"), ("bad_method_delete", "DELETE")):
    r = send(f"{meth} {OK} HTTP/1.1\r\nHost: openclaw-proxy\r\nContent-Length: 0\r\n"
             f"Connection: close\r\n\r\n".encode())
    out[key] = code(r)

# 6. CONNECT
r = send(b"CONNECT example.invalid:443 HTTP/1.1\r\nHost: example.invalid\r\n"
         b"Connection: close\r\n\r\n")
out["connect"] = code(r)

# 7. Host header pointed elsewhere
r = send(f"GET {OK} HTTP/1.1\r\nHost: example.invalid\r\nConnection: close\r\n\r\n".encode())
out["host_override"] = code(r)

# 8. client supplies its own Authorization
r = send(f"GET {OK} HTTP/1.1\r\nHost: openclaw-proxy\r\n"
         f"Authorization: Bearer client-supplied-token\r\nConnection: close\r\n\r\n".encode())
out["client_auth_hdr"] = code(r)

# 9. CRLF injection through the path
r = send(b"GET /v1beta/openai/models HTTP/1.1\r\nHost: openclaw-proxy\r\n"
         b"X-Injected: no\r\nConnection: close\r\n\r\n")
out["crlf_baseline"] = code(r)
r = send(b"GET /v1beta/openai/mo\r\nX-Injected: yes\r\ndels HTTP/1.1\r\n"
         b"Host: openclaw-proxy\r\nConnection: close\r\n\r\n")
out["crlf_in_path"] = code(r)

# 10. Content-Length and Transfer-Encoding together, with a smuggled second request
smuggled = (b"POST /v1beta/openai/chat/completions HTTP/1.1\r\nHost: openclaw-proxy\r\n"
            b"Content-Length: 4\r\nTransfer-Encoding: chunked\r\n\r\n"
            b"0\r\n\r\nGET /v1beta/openai/models HTTP/1.1\r\nHost: openclaw-proxy\r\n"
            b"Connection: close\r\n\r\n")
r = send(smuggled, read_all=True)
out["te_and_cl"] = code(r)
out["te_and_cl_responses"] = r.count("HTTP/1.0 ") + r.count("HTTP/1.1 ")

# 11. does any response body contain something key-shaped?
r = send(f"GET {OK} HTTP/1.1\r\nHost: openclaw-proxy\r\nConnection: close\r\n\r\n".encode(),
         read_all=True)
out["body_sample"] = r[-1500:]

print("PROBE_JSON:" + json.dumps(out))
'''


def load_screen():
    spec = importlib.util.spec_from_file_location("screen_007", SCREEN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def classify(obs: dict, key: str, secret: str) -> str:
    """Collapse a raw observation into the vocabulary the table uses.

    The first version of this binned anything it did not recognise as FORWARD, which
    reported two denials (501 from the framework, and a malformed request that was never
    forwarded) as allowlist failures. A probe that over-reports is a different failure from
    the ones this experiment kept finding -- it cries wolf rather than hiding one -- but it
    is still a probe telling you something that is not so.
    """
    if key == "key_not_echoed":
        return "LEAKED" if secret and secret in obs.get("body_sample", "") else "CLEAN"
    if key == "te_and_cl":
        # The assertion is not the status code: it is that the smuggled bytes were answered
        # as their own request, having faced the allowlist, rather than being appended to
        # the first one's body.
        return "NO_DESYNC" if obs.get("te_and_cl_responses", 0) >= 2 else "DESYNC"
    code = obs.get(key, "?")
    if code == "?":
        return "MALFORMED"   # no parsable response: refused before any forwarding
    if code == "501":
        return "501"         # denied, but by BaseHTTPRequestHandler, not by this proxy
    if code in ("400", "403", "405", "502"):
        return code
    return "FORWARD"         # anything the proxy actually relayed upstream


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", choices=["shipped", "fixed"], default="fixed",
                    help="'shipped' reproduces the pre-fix behaviour measured 2026-09-14; "
                         "'fixed' is the acceptance test for the normalisation fix")
    args = ap.parse_args()

    screen = load_screen()
    screen.ensure_proxy()

    p = subprocess.run(
        ["docker", "run", "--rm", "--network", screen.EGRESS_NETWORK,
         screen.IMAGE, "python3", "-c", PAYLOAD],
        capture_output=True, text=True, timeout=300)
    line = next((l for l in p.stdout.splitlines() if l.startswith("PROBE_JSON:")), None)
    if not line:
        print("probe payload produced no result", file=sys.stderr)
        print(p.stdout[-2000:], p.stderr[-2000:], file=sys.stderr)
        return 2
    obs = json.loads(line[len("PROBE_JSON:"):])

    env = Path(screen.ENV_FILE).read_text()
    secret = next((l.split("=", 1)[1].strip() for l in env.splitlines()
                   if l.startswith("GEMINI_API_KEY=")), "")

    print(f"\n007 egress proxy -- allowlist probe [profile: {args.profile}]\n")
    idx = 1 if args.profile == "shipped" else 2
    print(f"  {'case':18s} {'observed':10s} {'expected':10s} meaning")
    surprises = []
    for row in CASES:
        key, meaning = row[0], row[3]
        pred = row[idx]
        got = classify(obs, key, secret)
        mark = "" if got == pred else "   <-- SURPRISE"
        if mark:
            surprises.append((key, got, pred, meaning))
        print(f"  {key:18s} {got:10s} {pred:10s} {meaning}{mark}")

    print(f"\n  smuggled-request responses on one connection: "
          f"{obs.get('te_and_cl_responses')}")

    rec = {"ts": datetime.now(timezone.utc).isoformat(), "probe": "proxy_allowlist",
           "observed": {k: v for k, v in obs.items() if k != "body_sample"},
           "profile": args.profile,
           "verdicts": {r[0]: classify(obs, r[0], secret) for r in CASES},
           "expected": {r[0]: r[idx] for r in CASES},
           "surprises": [s[0] for s in surprises]}
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("a") as fh:
        fh.write(json.dumps(rec) + "\n")
    print(f"  appended to {OUT.relative_to(ROOT)}")

    forwarded = [k for k in ("dot_traversal", "encoded_traversal")
                 if classify(obs, k, secret) == "FORWARD"]
    if forwarded:
        print(f"\n  ALLOWLIST BYPASS: {forwarded} reached the upstream outside the "
              f"allowed prefix.\n  The upstream host is fixed, so this cannot reach another "
              f"server -- but it widens\n  what the credential can be spent on beyond the "
              f"OpenAI-compatibility shim.")
    if surprises:
        print(f"\n{len(surprises)} SURPRISE(S):")
        for k, got, pred, meaning in surprises:
            print(f"  {k}: observed {got}, pre-registered {pred} -- {meaning}")
        return 1
    print("\n  no surprises: the proxy behaves exactly as pre-registered.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
