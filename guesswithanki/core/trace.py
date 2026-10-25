"""Optional agent tracing to Sentry (the `sentry_dsn` setting), in Sentry's AI agent conventions. A labelling job is
one trace: each batch is sent as it finishes, as an `invoke_agent` transaction holding its `chat <model>` span (messages,
token counts, how many words came back unreadable); the job's end adds a summary transaction. Embedding calls are
`embeddings <model>` spans. Built by hand (standard library only), so the add-on needs no Sentry SDK. Without a DSN
nothing is made or sent.

(2026-10-24: the first version sent the whole job as one envelope at its end: a 2,000-word job, ~100 calls with their
prompts, never reached Sentry, and a job cut short sent nothing. One envelope per batch fixes both.)"""
import json
import time
import urllib.parse
import urllib.request
import uuid

RELEASE = "guesswithanki@0.1.0"


def _id(n):
    return uuid.uuid4().hex[:n]


def clip(s, n=6000):
    return s if len(s) <= n else s[:n] + "... (%d chars)" % len(s)


class Job:
    def __init__(self, tracer, name, model):
        self.t, self.name, self.model = tracer, name, model
        self.trace_id, self.t0, self.n = uuid.uuid4().hex, time.time(), 0

    def _root(self, start, end, extra=None, status="ok"):
        return {"trace_id": self.trace_id, "span_id": _id(16), "op": "gen_ai.invoke_agent", "status": status,
                "data": {"gen_ai.operation.name": "invoke_agent", "gen_ai.agent.name": self.name,
                         "gen_ai.request.model": self.model, **(extra or {})}}

    def chat(self, model, prompt, text, usage, seconds, error=None, **found):
        """one batch: sent now, as its own transaction in the job's trace"""
        end = time.time()
        self.n += 1
        root = self._root(end - seconds, end, {"guesswithanki.batch": self.n, **{"guesswithanki.%s" % k: v for k, v in found.items()}},
                          "internal_error" if error else "ok")
        i, o = usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
        span = {"trace_id": self.trace_id, "span_id": _id(16), "parent_span_id": root["span_id"], "op": "gen_ai.chat",
                "description": "chat %s" % model, "start_timestamp": end - seconds, "timestamp": end,
                "status": "internal_error" if error else "ok",
                "data": {"gen_ai.operation.name": "chat", "gen_ai.request.model": model, "gen_ai.agent.name": self.name,
                         "gen_ai.usage.input_tokens": i, "gen_ai.usage.output_tokens": o, "gen_ai.usage.total_tokens": i + o,
                         "gen_ai.input.messages": clip(json.dumps([{"role": "user", "parts": [{"type": "text", "content": prompt}]}], ensure_ascii=False)),
                         "gen_ai.output.messages": clip(json.dumps([{"role": "assistant", "parts": [{"type": "text", "content": text}]}], ensure_ascii=False)),
                         **{"guesswithanki.%s" % k: v for k, v in found.items()},
                         **({"guesswithanki.error": error} if error else {})}}
        self.t.send("invoke_agent %s" % self.name, end - seconds, end, root, [span])

    def finish(self, **found):
        end = time.time()
        self.t.send("invoke_agent %s (job)" % self.name, self.t0, end,
                    self._root(self.t0, end, {"guesswithanki.%s" % k: v for k, v in found.items()}), [])


class Tracer:
    def __init__(self, dsn, environment="anki", tags=None):
        u = urllib.parse.urlsplit(dsn)
        self.key, self.project = u.username, u.path.strip("/")
        self.url = "%s://%s%s/api/%s/envelope/" % (u.scheme, u.hostname, ":%d" % u.port if u.port else "", self.project)
        self.dsn, self.env, self.tags, self.last_error, self.sent = dsn, environment, dict(tags or {}), None, 0

    def agent(self, name, model):
        return Job(self, name, model)

    def embeddings(self, model, n_texts, seconds, error=None):
        """one embedding call, as a small transaction of its own"""
        end = time.time()
        root = {"trace_id": uuid.uuid4().hex, "span_id": _id(16), "op": "gen_ai.embeddings",
                "status": "internal_error" if error else "ok",
                "data": {"gen_ai.operation.name": "embeddings", "gen_ai.request.model": model,
                         "guesswithanki.texts": n_texts, **({"guesswithanki.error": error} if error else {})}}
        self.send("embeddings %s" % model, end - seconds, end, root, [])

    def send(self, name, start, end, root, spans):
        ev = {"type": "transaction", "event_id": uuid.uuid4().hex, "platform": "python", "release": RELEASE,
              "environment": self.env, "transaction": name, "start_timestamp": start, "timestamp": end,
              "spans": spans, "tags": self.tags, "contexts": {"trace": root}}
        body = "\n".join([json.dumps({"event_id": ev["event_id"], "dsn": self.dsn}), json.dumps({"type": "transaction"}),
                          json.dumps(ev, ensure_ascii=False)]).encode("utf-8")
        req = urllib.request.Request(self.url, data=body, headers={
            "Content-Type": "application/x-sentry-envelope",
            "X-Sentry-Auth": "Sentry sentry_version=7, sentry_key=%s, sentry_client=guesswithanki/0.1" % self.key})
        try:
            urllib.request.urlopen(req, timeout=15).read()
            self.last_error = None
            self.sent += 1
        except Exception as e:                       # noqa: BLE001  (tracing never breaks the job)
            self.last_error = str(e)
        return ev["event_id"]


def tracer(dsn, tags=None):
    return Tracer(dsn, tags=tags) if dsn else None
