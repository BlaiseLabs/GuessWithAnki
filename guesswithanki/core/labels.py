"""Guessability labels: for a word, how far its reading and its meaning can be guessed from its kanji.

Sources, on a spectrum from code to people to models:
  heuristic  computed every run (core/heuristic.py): never stored
  llm        a model's judgement (core/llm.py), stored when made
  crowd      a person's judgement, made while reviewing or imported from a shared file
  deck       labels the deck itself carries, from its author (core/embedded.py): read from the deck, never stored

A label record (one line of labels.jsonl, and the unit of a shared file, schema SCHEMA):
  {"word": "入口", "reading": "いりぐち", "reading_guessable": "yes", "meaning_guessable": "yes",
   "why_reading": "usual kun'yomi", "why_meaning": "enter + mouth", "helpers": ["入る", "出口"],
   "source": "crowd", "by": "a name", "at": "2026-10-24T01:00:00Z"}
"yes" / "partly" / "no", or a number from 0 to 1. helpers: words that make it guessable (they share its kanji).
The latest record per (word, reading, source, by) counts; several people's records are averaged."""
import datetime
import json
from pathlib import Path

SCHEMA = "guesswithanki-labels/1"
LEVEL = {"yes": 1.0, "partly": 0.5, "no": 0.0}
SOURCES = ("crowd", "deck", "llm", "heuristic")


def level(v):
    if isinstance(v, (int, float)):
        return max(0.0, min(1.0, float(v)))
    return LEVEL.get(str(v).strip().lower())


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def key(word, reading):
    return "%s|%s" % (word, reading or "")


class Store:
    """the labels kept for one Anki profile (a JSON-lines file; appended to, never rewritten)"""

    def __init__(self, path):
        self.path = Path(path)
        self.records = []
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if self.valid(r):
                    self.records.append(r)

    @staticmethod
    def valid(r):
        return (isinstance(r, dict) and r.get("word") and r.get("source") in SOURCES
                and (level(r.get("reading_guessable")) is not None or level(r.get("meaning_guessable")) is not None))

    def add(self, recs):
        recs = [dict(r, at=r.get("at") or now()) for r in recs if self.valid(r)]
        if not recs:
            return 0
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        self.records.extend(recs)
        return len(recs)

    def latest(self):
        """(word|reading) -> source -> [the latest record of each person or model]"""
        by = {}
        for r in self.records:
            by[key(r["word"], r.get("reading")), r["source"], r.get("by") or r.get("model") or ""] = r
        out = {}
        for (k, src, _), r in by.items():
            out.setdefault(k, {}).setdefault(src, []).append(r)
        return out

    def count_today(self, source):
        day = now()[:10]
        return sum(1 for r in self.records if r["source"] == source and str(r.get("at", "")).startswith(day))

    def export(self, path, sources=("crowd", "llm")):
        recs = [r for rs in self.latest().values() for src, xs in rs.items() if src in sources for r in xs]
        Path(path).write_text(json.dumps({"schema": SCHEMA, "labels": recs}, ensure_ascii=False, indent=1),
                              encoding="utf-8")
        return len(recs)

    def import_(self, text):
        """a shared file's labels (a schema file, a JSON list, or JSON lines); records already here are skipped"""
        text = text.strip()
        try:
            d = json.loads(text)
            recs = d.get("labels", []) if isinstance(d, dict) else d
        except ValueError:
            recs = [json.loads(x) for x in text.splitlines() if x.strip()]
        seen = {json.dumps(r, sort_keys=True, ensure_ascii=False) for r in self.records}
        new = [r for r in recs if json.dumps(r, sort_keys=True, ensure_ascii=False) not in seen]
        return self.add(new)


def combine(per_source, weights):
    """one (reading, meaning) pair of levels from the sources' records: each source's records averaged, then the sources
    weighted. Returns (reading, meaning, {source: (reading, meaning)}); a level is None when nothing judged it"""
    parts = {}
    for src, recs in per_source.items():
        rs = [level(r.get("reading_guessable")) for r in recs]
        ms = [level(r.get("meaning_guessable")) for r in recs]
        rs, ms = [x for x in rs if x is not None], [x for x in ms if x is not None]
        parts[src] = (sum(rs) / len(rs) if rs else None, sum(ms) / len(ms) if ms else None)

    def mix(i):
        num = den = 0.0
        for src, v in parts.items():
            if v[i] is not None and weights.get(src, 0) > 0:
                num += weights[src] * v[i]
                den += weights[src]
        return num / den if den else None
    return mix(0), mix(1), parts
