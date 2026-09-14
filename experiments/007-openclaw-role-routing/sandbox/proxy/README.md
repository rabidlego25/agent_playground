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
- **No rate limiting, quota accounting, or retry policy.** 007's own pacing handles that.
- **No persistent audit trail.** ALLOW/DENY lines go to stderr and vanish with the container.
- **No protection for the key at rest.** It arrives via `--env-file` and lives in this
  process's environment. This container is now the highest-value target in the setup; that is
  the trade, and it is why it runs with fewer capabilities than the agent does.

## Operational notes, learned the hard way

Three bugs here presented as model failures — the agent reported `LLM request timed out` and
`Stream ended without finish_reason` while the proxy logged `upstream 200 OK`. If you touch
the relay, re-read these first:

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
