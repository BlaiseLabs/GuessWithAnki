"""The whole pass over a collection: read the words, judge them (stored labels + heuristic), plan the path, write the
new order back, and keep what the dashboard shows. Works headless (tools/cli.py) and inside Anki (__init__.py)."""
import json
import time
from dataclasses import dataclass
from pathlib import Path

from . import heuristic
from .ankiio import collect, queue_settings, reposition, split_started
from .labels import Store
from .model import guessable, judge
from .path import plan
from .remote import Embedder, reachable

DEFAULTS = Path(__file__).resolve().parents[1] / "config.json"


def defaults():
    return json.loads(DEFAULTS.read_text(encoding="utf-8"))


def merged(cfg):
    """the settings with every key the defaults have (an old config misses new keys)"""
    def deep(d, o):
        out = dict(d)
        for k, v in (o or {}).items():
            out[k] = deep(d[k], v) if isinstance(v, dict) and isinstance(d.get(k), dict) else v
        return out
    return deep(defaults(), cfg)


@dataclass
class Analysis:
    items: list
    started: list
    new: list
    full: set
    store: Store
    note: str = ""


NO_EMBEDDINGS = ("Meanings are judged by word overlap, since no local embedding model is running. That works fine, "
                 "nothing else is needed. For sharper meaning judgments you can optionally install Ollama (ollama.com) "
                 "and run \"ollama pull embeddinggemma\".")


def analyse(col, cfg, files, use_server=True, progress=None):
    files = Path(files)
    cfg = merged(cfg)
    items = collect(col, cfg)
    store = Store(files / "labels.jsonl")
    hc, note = cfg["heuristic"], ""
    from .trace import tracer
    emb = None
    if use_server and hc.get("meaning") == "embeddings":
        if reachable(cfg["embeddings"]["base_url"]):
            emb = Embedder(cfg["embeddings"], files / "embeddings.json", tracer(cfg.get("sentry_dsn")))
        else:
            note, hc = NO_EMBEDDINGS, dict(hc, meaning="words")
    try:
        heur = heuristic.score(items, hc, emb, progress)
    except Exception:                            # noqa: BLE001  (the server went away mid-way: word overlap)
        note = NO_EMBEDDINGS
        heur = heuristic.score(items, dict(hc, meaning="words"))
    from .embedded import read
    judge(items, store, heur, cfg, read(col, items))
    started, new = split_started(items)
    full = {it.key for it in items if guessable(it, cfg)}
    return Analysis(items, started, new, full, store, note)


def original_order(files, new):
    """the deck's own order of its new notes, kept the first time the add-on runs (the 'before' of the dashboard)"""
    f = Path(files) / "original_order.json"
    have = json.loads(f.read_text(encoding="utf-8")) if f.exists() else []
    known = set(have)
    add = [it.nid for it in new if it.nid not in known]
    if add:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(have + add), encoding="utf-8")
    at = {n: i for i, n in enumerate(have + add)}
    return sorted(new, key=lambda it: at.get(it.nid, len(at)))


def compute(col, cfg, files, use_server=True, progress=None):
    """(analysis, planned order, why, before order) without touching the collection"""
    cfg = merged(cfg)
    a = analyse(col, cfg, files, use_server, progress)
    before = original_order(files, a.new)
    order, why = plan(a.started, before, a.full, cfg["path"], progress)      # (ties keep the deck's own order)
    return a, order, why, before


def reorder(col, cfg, files, use_server=True, progress=None):
    """plan and write the order; returns the dashboard's numbers (also kept in files/last.json)"""
    from .stats import summary
    t = time.time()
    a, order, why, before = compute(col, cfg, files, use_server, progress)
    moved = reposition(col, order)
    s = summary(a, order, why, before, merged(cfg), queue_settings(col, a.new))
    s.update(moved=moved, seconds=round(time.time() - t, 1), at=time.strftime("%Y-%m-%d %H:%M"))
    Path(files, "last.json").write_text(json.dumps(s, ensure_ascii=False), encoding="utf-8")
    return s
