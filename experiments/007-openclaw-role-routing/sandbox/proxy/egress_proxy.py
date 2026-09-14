"""The one way out. Everything else on the agent's network is a dead end.

011 measured the shipped sandbox and found the agent holding `GEMINI_API_KEY` in its own
environment with unrestricted egress -- one command from exfiltration, through any of five
routes that work in that image. This process is the fix for both halves at once:

  * The agent container runs on an `--internal` Docker network. It has no route anywhere
    except to this proxy, so there is no "elsewhere" to send anything to.
  * The credential lives here, not there. The agent's config carries a `baseUrl` pointing at
    this process and no key at all, so there is nothing in its environment to steal.

A forward proxy would not achieve the second half: `CONNECT` makes an opaque TLS tunnel, so
the key would have to be inside the tunnel, which means inside the agent. A reverse proxy
terminates plain HTTP on the internal network and re-originates over TLS with the credential
added here. The provider's own config template already exposes `baseUrl`, so this costs the
experiment one template swap and no code change in the agent.

**Allowlist, enforced on every request:** method, path prefix, and upstream host. Anything
else is 403 and logged. The upstream is a single constant -- not a header, not a parameter --
because a proxy that takes its destination from the request is an open relay with extra steps.

Run: `python3 egress_proxy.py` with GEMINI_API_KEY in the environment.
"""
from __future__ import annotations

import http.client
import os
import posixpath
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

UPSTREAM_HOST = "generativelanguage.googleapis.com"
ALLOWED_PREFIXES = ("/v1beta/openai/",)
ALLOWED_METHODS = ("POST", "GET")
LISTEN_PORT = int(os.environ.get("PROXY_PORT", "8080"))
TIMEOUT = 180

# Hop-by-hop headers must not be forwarded, and the client's own auth header is discarded
# rather than relayed: the agent has no credential, and if it invents one we do not carry it.
# Every header this proxy sets itself must also be dropped from the client's request.
# HTTP header names are case-insensitive but dict keys are not: the client sends
# `accept-encoding: gzip`, we added `Accept-Encoding: identity`, and both went upstream --
# so the provider gzipped a stream whose Content-Encoding we then stripped, and the agent
# received `\x1f\x8b...` and reported "Stream ended without finish_reason". A proxy bug
# that reads as a model failure, which is the same costume every bug in this experiment
# has worn.
DROP_REQUEST_HEADERS = {
    "host", "authorization", "x-goog-api-key", "connection", "keep-alive",
    "proxy-authenticate", "proxy-authorization", "te", "trailers",
    "transfer-encoding", "upgrade", "content-length", "accept-encoding",
}
DROP_RESPONSE_HEADERS = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te",
    "trailers", "transfer-encoding", "upgrade", "content-encoding", "content-length",
}


# Anything that can change what a path *means* between this check and the upstream's
# interpretation of it. `tests/probe_proxy.py` found the original `str.startswith` check
# forwarding `/v1beta/openai/../../v1beta/models`: it passes a prefix test and normalises,
# upstream, to a path the allowlist exists to exclude. Upstream answered 302 to an absolute
# URL the agent cannot reach, so nothing came back -- but that is the provider's
# normalisation doing the containment, not this proxy's, and a control enforced by the
# thing it is supposed to constrain is not a control.
_SUSPICIOUS = ("..", "//", "\\", "\x00", ";")


def forwardable_path(raw: str) -> str | None:
    """The path to forward, or None to refuse.

    Strict by construction: the question is not "can this be made safe" but "is this
    exactly one of the shapes we intend to allow". Anything ambiguous is refused, because
    the cost of a false refusal here is a 403 in a log and the cost of a false accept is
    the operator's credential spent somewhere unintended.
    """
    if "://" in raw:                      # an absolute-URI request line is not a path
        return None
    decoded = unquote(raw)
    if unquote(decoded) != decoded:       # double-encoded: refuse rather than guess
        return None
    if any(t in decoded for t in _SUSPICIOUS):
        return None
    path = decoded.split("?", 1)[0]
    if posixpath.normpath(path) != path:  # normalisation must be a no-op
        return None
    if not any(path.startswith(pre) for pre in ALLOWED_PREFIXES):
        return None
    return raw


def log(*a):
    print("[egress-proxy]", *a, file=sys.stderr, flush=True)


class Proxy(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "egress-proxy/1"

    def _deny(self, code: int, why: str):
        log(f"DENY {self.command} {self.path} -- {why}")
        body = f'{{"error":{{"message":"egress proxy: {why}"}}}}'.encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_chunked(self) -> bytes:
        out = bytearray()
        while True:
            line = self.rfile.readline().strip()
            size = int(line.split(b";")[0] or b"0", 16)
            if size == 0:
                self.rfile.readline()          # trailing CRLF
                return bytes(out)
            out += self.rfile.read(size)
            self.rfile.readline()              # CRLF after each chunk

    def _handle(self):
        if self.command not in ALLOWED_METHODS:
            return self._deny(405, f"method {self.command} not allowed")
        if forwardable_path(self.path) is None:
            return self._deny(403, f"path not on the allowlist: {self.path}")

        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            return self._deny(500, "no upstream credential configured")

        # Request framing: a client may send a chunked body instead of Content-Length
        # (undici does, for streamed requests). Reading only Content-Length bytes would
        # forward an empty body and the provider would answer something that looks like a
        # model failure rather than a proxy one.
        if "chunked" in (self.headers.get("Transfer-Encoding") or "").lower():
            body, framing = self._read_chunked(), "chunked"
        else:
            length = int(self.headers.get("Content-Length") or 0)
            body, framing = (self.rfile.read(length) if length else None), "content-length"

        headers = {k: v for k, v in self.headers.items()
                   if k.lower() not in DROP_REQUEST_HEADERS}
        headers["Host"] = UPSTREAM_HOST
        headers["Authorization"] = f"Bearer {key}"
        # Ask upstream not to compress. We strip Content-Encoding from the response (it no
        # longer describes what we send once we re-frame the body), so a gzipped upstream
        # would reach the agent as undeclared gzip -- unreadable, and it looks like a model
        # error rather than a proxy error.
        headers["Accept-Encoding"] = "identity"
        if body is not None:
            headers["Content-Length"] = str(len(body))

        log(f"ALLOW {self.command} {self.path} -> {UPSTREAM_HOST} "
            f"({framing}, {len(body or b'')}B)")
        try:
            conn = http.client.HTTPSConnection(UPSTREAM_HOST, 443, timeout=TIMEOUT)
            conn.request(self.command, self.path, body=body, headers=headers)
            resp = conn.getresponse()
        except Exception as e:                                   # noqa: BLE001
            return self._deny(502, f"upstream failed: {type(e).__name__}")

        log(f"  upstream {resp.status} {resp.reason}, "
            f"content-type {resp.getheader('Content-Type')!r}")
        self.send_response(resp.status)
        for k, v in resp.getheaders():
            if k.lower() not in DROP_RESPONSE_HEADERS:
                self.send_header(k, v)
        # Chunked, because the agent streams completions: buffering the whole body here
        # would turn a streaming provider into a non-streaming one and change what 007
        # is measuring.
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        relayed, why = 0, "eof"
        try:
            while True:
                # read1, not read: `read(n)` blocks until it has all n bytes or the stream
                # ends, which for a server-sent-event stream means the proxy sits on every
                # partial event until 4 KiB accumulates. The agent times out waiting and
                # reports "Stream ended without finish_reason" -- a proxy bug wearing a
                # model failure's clothes. read1 returns whatever has arrived.
                chunk = resp.read1(65536)
                if not chunk:
                    break
                if relayed == 0 and os.environ.get("PROXY_DEBUG"):
                    log(f"  first bytes: {chunk[:400]!r}")
                relayed += len(chunk)
                self.wfile.write(b"%x\r\n%s\r\n" % (len(chunk), chunk))
                self.wfile.flush()
            self.wfile.write(b"0\r\n\r\n")
            self.wfile.flush()
        except BrokenPipeError:
            why = "client disconnected"
        except Exception as e:                                   # noqa: BLE001
            why = f"relay error {type(e).__name__}: {e}"
        finally:
            log(f"  relayed {relayed}B, ended: {why}")
            conn.close()

    do_GET = _handle                                             # noqa: N815
    do_POST = _handle                                            # noqa: N815

    def _refuse_method(self):
        self._deny(405, f"method {self.command} not allowed")

    # Explicit, because the ALLOWED_METHODS test inside _handle was unreachable for every
    # method without a do_* handler: BaseHTTPRequestHandler answered 501 "Unsupported
    # method" before this class saw the request. The denial was real but it came from the
    # framework, was not logged here, and would have silently stopped being a denial the
    # moment anyone added a handler. Found by tests/probe_proxy.py.
    do_PUT = do_DELETE = do_PATCH = do_OPTIONS = do_TRACE = _refuse_method   # noqa: N815
    do_HEAD = _refuse_method                                                 # noqa: N815

    def do_CONNECT(self):                                        # noqa: N802
        self._deny(403, "CONNECT is not proxied -- this is a reverse proxy, not a tunnel")

    def log_message(self, *a):
        pass

    def handle_one_request(self):
        """A client that hangs up mid-response is normal here -- the agent finishes a turn
        and drops the connection. Left unhandled it prints a traceback per turn, which
        buries the ALLOW/DENY lines that are the reason this process logs at all."""
        try:
            super().handle_one_request()
        except (ConnectionResetError, BrokenPipeError):
            self.close_connection = True


if __name__ == "__main__":
    if not os.environ.get("GEMINI_API_KEY"):
        sys.exit("GEMINI_API_KEY not set -- the proxy is the only place it belongs")
    log(f"listening on :{LISTEN_PORT}, upstream {UPSTREAM_HOST}, "
        f"allowlist {ALLOWED_PREFIXES}")
    ThreadingHTTPServer(("0.0.0.0", LISTEN_PORT), Proxy).serve_forever()
