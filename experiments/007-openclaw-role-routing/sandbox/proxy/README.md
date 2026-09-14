# Egress proxy

The only process on the agent's network with a route off the machine, and the only one holding
the provider credential. Built 2026-09-14 as the fix for what
`experiments/011-sandbox-containment/` measured: an agent container carrying `GEMINI_API_KEY`
in its own environment with unrestricted egress.

    docker build -t openclaw-proxy-007 experiments/007-openclaw-role-routing/sandbox/proxy

Started by `screen.py:ensure_proxy()`, not by hand — it needs two network attachments and the
env file, and getting either wrong fails in a way that looks like a model error.

## Why a reverse proxy

A forward proxy (`HTTP_PROXY`, `CONNECT`) would restrict *where* the agent can connect but
leave the credential with the agent, because `CONNECT` is an opaque TLS tunnel and whatever
authenticates inside it has to be inside the agent. Only half the problem solved, and the less
important half: 011 found five working routes out of that image, but the thing worth stealing
was the key.

Terminating plain HTTP on an internal network and re-originating over TLS from here moves the
credential out of the agent entirely. The provider config already exposes `baseUrl`, so this
costs one template swap and no code change in the agent.

## Security properties

| property | how |
|---|---|
| single upstream | `UPSTREAM_HOST` is a module constant, never read from a header, path, or parameter |
| allowlisted paths | `ALLOWED_PREFIXES`, checked before anything else happens |
| allowlisted methods | `ALLOWED_METHODS` — `POST`, `GET` |
| no tunnelling | `CONNECT` is explicitly refused |
| client credentials discarded | `authorization` and `x-goog-api-key` are dropped from the request, never relayed |
| unprivileged, contained | uid 1002, `--cap-drop=ALL --security-opt no-new-privileges --read-only --pids-limit 64 --memory 256m` |
| fails closed | anything not matched is 403 with a JSON error, and logged |

A proxy that takes its destination from the request is an open relay with extra steps. This
one cannot be redirected: there is no code path in which the upstream is anything but the
constant.

## What it does not do

- **No authentication.** Its boundary is the `--internal` network, whose only other member is
  the agent container for that run. Anything else you attach to `openclaw-egress` gets
  provider access with the operator's key.
- **No inspection of what is sent upstream.** The allowlist is a path prefix. A request that
  puts secrets in the request body reaches the provider like any other. This proxy stops
  exfiltration to *other hosts*; it does not stop a payload aimed at the allowed one.
- **The prefix constrains the path, and the path is all it constrains.** Anything the provider
  serves under `/v1beta/openai/` is reachable with the operator's credential. Narrowing that to
  the endpoints 007 actually uses (`chat/completions`, `models`) would be a strictly tighter
  allowlist and has not been done.
- **No rate limiting, quota accounting, or retry policy.** 007's own pacing handles that.
- **No persistent audit trail.** ALLOW/DENY lines go to stderr and vanish with the container.
- **No protection for the key at rest.** It arrives via `--env-file` and lives in this
  process's environment. This container is now the highest-value target in the setup; that is
  the trade, and it is why it runs with fewer capabilities than the agent does.

## What the probe found

`tests/probe_proxy.py` attacks the allowlist with raw HTTP from a container on the agent's own
network, one pre-registered verdict per case. Written 2026-09-14, after this proxy had been
verified to *work* and never once tested to see whether it could be made to do something else
— the same posture that produced four scorer defects in 011 arm C2.

**Finding 1: the path allowlist was bypassable.** `/v1beta/openai/../../v1beta/models` passes a
`str.startswith` test on an unnormalised path and was forwarded upstream with the credential
attached; `%2e%2e` likewise.

The impact is narrower than that sounds, and it was measured rather than assumed. Eight
traversal forms were tried and every one returned 302 or 404 — the provider normalises the path
and answers with a redirect to an absolute URL on a host the agent cannot reach, because the
agent's only route is this proxy. Nothing came back. **But that means the containment was being
performed by the upstream's normalisation, not by this proxy**, and a control enforced by the
thing it is meant to constrain is not a control. It fails the moment this proxy follows
redirects, the provider changes behaviour, or `UPSTREAM_HOST` moves to a server that serves
such paths directly.

Fixed in `forwardable_path()`: decode once, refuse double-encoding, refuse `..` `//` `\` `;`
and NUL, require `posixpath.normpath` to be a no-op, then test the prefix. The original request
line is what gets forwarded, so query strings survive.

**Finding 2: the method allowlist was dead code.** `ALLOWED_METHODS` is tested inside
`_handle`, which only `do_GET` and `do_POST` route to — every other method was answered 501 by
`BaseHTTPRequestHandler` before this class saw it. The denial was real, but it came from the
framework, was never logged here, and would have silently stopped being a denial the moment
someone added a handler. Now every other method has an explicit handler returning 405.

**What held.** A `Content-Length` + `Transfer-Encoding: chunked` request carrying a smuggled
second request produced two separate responses on one connection: the smuggled bytes were
parsed as their own request and faced the allowlist again. No response body contained the
credential. `Host` cannot redirect the upstream, a client-supplied `Authorization` is discarded
rather than relayed, `CONNECT` is refused, and an absolute-URI request line is refused.

**A defect in the probe itself, recorded because the direction is unusual.** Its first
classifier binned every unrecognised status as "forwarded", so it reported a 501 denial and a
malformed-never-forwarded request as allowlist failures: three surprises, two of them fiction.
Every other instrument defect in this project failed toward reporting safety. This one cried
wolf. Both are a probe telling you something that is not so.

## Operational notes, learned the hard way

Three bugs here presented as model failures — the agent reported `LLM request timed out` and
`Stream ended without finish_reason` while the proxy logged `upstream 200 OK`. If you touch
the relay, re-read these first:

- **A container is not ready when `docker run -d` returns.** Python still has to import and
  bind, and a caller that starts an agent container in that window gets connection refused,
  which surfaces as a provider error and reads like a quota problem. `screen.ensure_proxy()`
  now waits for the port to answer. Found by `probe_proxy.py` on its first run.
- **`read1`, never `read`.** `read(n)` blocks until it has `n` bytes or the stream ends, which
  stalls every partial server-sent event until the buffer fills.
- **Request framing.** A client may send a chunked body rather than `Content-Length`; reading
  only `Content-Length` bytes forwards an empty request.
- **Header case.** HTTP header names are case-insensitive, Python dict keys are not. The
  client's `accept-encoding: gzip` survived next to this proxy's `Accept-Encoding: identity`,
  the provider gzipped the stream, and the response's `Content-Encoding` was stripped on the
  way back — the agent received `\x1f\x8b…`. Every header the proxy sets itself must also be
  in `DROP_REQUEST_HEADERS`.

`PROXY_DEBUG=1` logs the first bytes of each relayed body, which is how the gzip was found.
Leave it off by default: the response body is model output, and it does not belong in a log
that outlives the run.

## Changing provider

`UPSTREAM_HOST` and `ALLOWED_PREFIXES` are the two constants that must move together, and they
must match the `baseUrl` in the agent's config template. A mismatch fails closed — 403, logged
— rather than silently forwarding somewhere unintended.
