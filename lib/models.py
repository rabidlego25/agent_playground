"""One thin interface over every model this project can reach.

Experiment code never imports a vendor SDK. It asks for a model by name and gets back a
Completion with token counts and latency attached, so any arm of any experiment can be
run against any backend and the traces stay comparable.

Backends:
  ollama:<model>   local HTTP, free and unlimited -- where sweeps should run
  claude:<model>   the `claude` CLI in print mode; the Pro subscription is scriptable this
                   way, so cross-capability checks need no third-party API key
"""

from __future__ import annotations

import json
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_TIMEOUT = 180


@dataclass
class Completion:
    text: str
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: float = 0.0
    raw: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def __bool__(self) -> bool:
        return self.error is None


class ModelError(RuntimeError):
    pass


class Backend:
    name = "base"

    def complete(self, prompt: str, *, system: str | None = None,
                 temperature: float = 0.7, max_tokens: int = 1024,
                 seed: int | None = None) -> Completion:
        raise NotImplementedError

    def available(self) -> bool:
        raise NotImplementedError


class Ollama(Backend):
    """Local models. Free and unbounded n, which is why arms should be piloted here."""

    name = "ollama"

    def __init__(self, model: str, url: str = OLLAMA_URL):
        self.model, self.url = model, url

    def available(self, retries: int = 2) -> bool:
        # A freshly started `ollama serve` refuses connections for a second or two, so a
        # single probe reports False on a server that is merely still booting.
        for attempt in range(retries + 1):
            try:
                with urllib.request.urlopen(f"{self.url}/api/tags", timeout=10) as r:
                    tags = json.load(r).get("models", [])
                return any(m.get("name", "").startswith(self.model.split(":")[0]) for m in tags)
            except (urllib.error.URLError, OSError, ValueError):
                if attempt == retries:
                    return False
                time.sleep(1.5)
        return False

    def complete(self, prompt, *, system=None, temperature=0.7, max_tokens=1024,
                 seed=None) -> Completion:
        opts: dict[str, Any] = {"temperature": temperature, "num_predict": max_tokens}
        if seed is not None:
            opts["seed"] = seed          # ollama honours this, so arms can be made replayable
        body = {"model": self.model, "prompt": prompt, "stream": False, "options": opts}
        if system:
            body["system"] = system
        req = urllib.request.Request(
            f"{self.url}/api/generate",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
        )
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as r:
                d = json.load(r)
        except (urllib.error.URLError, OSError, ValueError) as e:
            return Completion("", self.model, latency_ms=(time.perf_counter() - t0) * 1000,
                              error=f"{type(e).__name__}: {e}")
        return Completion(
            text=d.get("response", ""),
            model=self.model,
            tokens_in=d.get("prompt_eval_count", 0),
            tokens_out=d.get("eval_count", 0),
            latency_ms=(time.perf_counter() - t0) * 1000,
            raw={k: v for k, v in d.items() if k != "response"},
        )


class ClaudeCLI(Backend):
    """Claude through `claude -p`. Subscription-metered, so use it for confirmation
    slices after a local sweep has already located the effect -- not for the sweep."""

    name = "claude"

    def __init__(self, model: str = "sonnet"):
        self.model = model

    def available(self) -> bool:
        try:
            return subprocess.run(["claude", "--version"], capture_output=True,
                                  timeout=15).returncode == 0
        except (OSError, subprocess.SubprocessError):
            return False

    def complete(self, prompt, *, system=None, temperature=0.7, max_tokens=1024,
                 seed=None) -> Completion:
        cmd = ["claude", "-p", "--model", self.model, "--output-format", "json"]
        if system:
            cmd += ["--append-system-prompt", system]
        t0 = time.perf_counter()
        try:
            r = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                               timeout=DEFAULT_TIMEOUT)
        except (OSError, subprocess.SubprocessError) as e:
            return Completion("", self.model, latency_ms=(time.perf_counter() - t0) * 1000,
                              error=f"{type(e).__name__}: {e}")
        lat = (time.perf_counter() - t0) * 1000
        if r.returncode != 0:
            return Completion("", self.model, latency_ms=lat, error=r.stderr.strip()[:500])
        try:
            d = json.loads(r.stdout)
        except ValueError:
            return Completion(r.stdout.strip(), self.model, latency_ms=lat)
        usage = d.get("usage", {}) or {}
        return Completion(
            text=d.get("result", ""),
            model=d.get("modelUsage") and next(iter(d["modelUsage"]), self.model) or self.model,
            tokens_in=usage.get("input_tokens", 0),
            tokens_out=usage.get("output_tokens", 0),
            latency_ms=lat,
            raw={k: v for k, v in d.items() if k != "result"},
        )


def get(spec: str) -> Backend:
    """`get("ollama:qwen2.5")` / `get("claude:haiku")`. A bare name is assumed local."""
    backend, _, model = spec.partition(":")
    if not model:
        return Ollama(backend)
    if backend == "ollama":
        return Ollama(model)
    if backend == "claude":
        return ClaudeCLI(model)
    raise ModelError(f"unknown backend {backend!r} in {spec!r}")
