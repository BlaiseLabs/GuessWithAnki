"""Calls to a model server that speaks the OpenAI API (Ollama, llama.cpp, vLLM, LM Studio, or a cloud provider):
chat completions and embeddings, with the standard library only (an Anki add-on cannot count on extra packages)."""
import hashlib
import json
import math
import time
import urllib.error
import urllib.request
from pathlib import Path


def reachable(base_url, timeout=1.5):
    """is anything listening at the server's host and port? (a quick check, so a missing local server costs
    a second and a half, not a long timeout)"""
    import socket
    from urllib.parse import urlparse
    u = urlparse(base_url)
    port = u.port or (443 if u.scheme == "https" else 80)
    try:
        with socket.create_connection((u.hostname or "127.0.0.1", port), timeout=timeout):
            return True
    except OSError:
        return False


def post(base_url, path, body, api_key="", timeout=600):
    req = urllib.request.Request(base_url.rstrip("/") + path, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    if api_key:
        req.add_header("Authorization", "Bearer " + api_key)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def chat(cfg, prompt, temperature=0.0, schema=None):
    """(text, usage) for one user prompt, asking for a JSON object back (one that fits `schema` when given and the
    setting json_schema is on; a server that refuses schemas gets the plain JSON request instead)"""
    fmt = {"type": "json_object"}
    if schema and cfg.get("json_schema", True):
        fmt = {"type": "json_schema", "json_schema": {"name": "answer", "schema": schema, "strict": True}}
    body = {"model": cfg["model"], "messages": [{"role": "user", "content": prompt}], "response_format": fmt}
    if cfg.get("temperature", True):          # (reasoning models such as gpt-5 take only their own temperature)
        body["temperature"] = temperature
    if cfg.get("reasoning_effort"):           # ("none" stops thinking models such as Gemma 4 spending the answer on it)
        body["reasoning_effort"] = cfg["reasoning_effort"]
    try:
        d = post(cfg["base_url"], "/chat/completions", body, cfg.get("api_key", ""))
    except urllib.error.HTTPError as e:
        if e.code != 400 or fmt["type"] != "json_schema":
            raise
        body["response_format"] = {"type": "json_object"}
        d = post(cfg["base_url"], "/chat/completions", body, cfg.get("api_key", ""))
    return d["choices"][0]["message"]["content"], d.get("usage") or {}


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


class Embedder:
    """text -> vector through the server's /embeddings, cached on disk by model and text"""

    def __init__(self, cfg, cache_path, tracer=None):
        self.cfg, self.path, self.tracer = cfg, Path(cache_path), tracer
        self.cache = {}
        if self.path.exists():
            try:
                self.cache = json.loads(self.path.read_text(encoding="utf-8"))
            except ValueError:
                self.cache = {}
        self.dirty = False

    def _k(self, text):
        return hashlib.sha1(("%s\n%s" % (self.cfg["model"], text)).encode("utf-8")).hexdigest()[:20]

    def vectors(self, texts, batch=64, progress=None):
        todo = list(dict.fromkeys(t for t in texts if self._k(t) not in self.cache))
        for i in range(0, len(todo), batch):
            chunk = todo[i:i + batch]
            t = time.time()
            d = post(self.cfg["base_url"], "/embeddings", {"model": self.cfg["model"], "input": chunk},
                     self.cfg.get("api_key", ""), timeout=120)
            if self.tracer:
                self.tracer.embeddings(self.cfg["model"], len(chunk), time.time() - t)
            for t, e in zip(chunk, sorted(d["data"], key=lambda x: x["index"])):
                self.cache[self._k(t)] = [round(x, 5) for x in e["embedding"]]
            self.dirty = True
            if progress:
                progress(min(i + batch, len(todo)), len(todo))
        return [self.cache[self._k(t)] for t in texts]

    def save(self):
        if self.dirty:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.cache), encoding="utf-8")
            self.dirty = False
