"""Labels that travel inside a deck, so a deck's author can ship them with the deck (AnkiWeb shares a deck's notes,
tags and media together):

  tags   guesswithanki::reading::yes|partly|no and guesswithanki::meaning::yes|partly|no on a note
  file   _guesswithanki.json in the collection's media folder, in the shared-file format (schema guesswithanki-labels/1).
         Anki keeps media files whose names start with "_" and exports them with the deck.

Both count as the source "deck". write() puts the labels you made (yours and the model's) into the deck the same two
ways; the deck is then shared on AnkiWeb as usual."""
import json
from pathlib import Path

from .labels import SCHEMA, level

TAG = "guesswithanki::"
FILE = "_guesswithanki.json"
WORD = {1.0: "yes", 0.5: "partly", 0.0: "no"}


def word_level(v):
    """a level as yes / partly / no (0.75 and up yes, 0.25 and up partly)"""
    return "yes" if v >= 0.75 else "partly" if v >= 0.25 else "no"


def media_file(col):
    return Path(col.media.dir()) / FILE


def read(col, items):
    """{word|reading: [records]} from the notes' tags and the deck's _guesswithanki.json"""
    out = {}
    if items:
        by_nid = {it.nid: it for it in items}
        for nid, tags in col.db.all("select id, tags from notes where id in (%s)" % ",".join(str(n) for n in by_nid)):
            rec = {}
            for t in tags.split():
                if t.lower().startswith(TAG):
                    parts = t.split("::")
                    if len(parts) == 3 and parts[1].lower() in ("reading", "meaning") and level(parts[2]) is not None:
                        rec["%s_guessable" % parts[1].lower()] = parts[2].lower()
            if rec:
                it = by_nid[nid]
                out.setdefault(it.key, []).append(dict(rec, word=it.word, reading=it.reading, source="deck", by="tags"))
    f = media_file(col)
    if f.exists():
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            recs = d.get("labels", []) if isinstance(d, dict) else d
        except ValueError:
            recs = []
        for r in recs:
            if isinstance(r, dict) and r.get("word") and (level(r.get("reading_guessable")) is not None
                                                          or level(r.get("meaning_guessable")) is not None):
                key = "%s|%s" % (r["word"], r.get("reading") or "")
                out.setdefault(key, []).append(dict(r, source="deck", by=r.get("by") or r.get("model") or "deck file"))
    return out


def plan_write(items, store):
    """what write() would put in: ({note id: (reading word, meaning word)}, the records for the file). A word's tags
    come from your own votes when there are any, else from the model's labels"""
    from .labels import combine
    latest = store.latest()
    tags, recs = {}, []
    for it in items:
        per = latest.get(it.key, {})
        mine = {k: v for k, v in per.items() if k in ("crowd", "llm")}
        if not mine:
            continue
        src = {"crowd": per["crowd"]} if "crowd" in per else {"llm": per["llm"]}
        r, m, _ = combine(src, {"crowd": 1, "llm": 1})
        tags[it.nid] = (None if r is None else word_level(r), None if m is None else word_level(m))
        recs.extend(x for xs in mine.values() for x in xs)
    seen, uniq = set(), []
    for r in recs:
        k = json.dumps(r, sort_keys=True, ensure_ascii=False)
        if k not in seen:
            seen.add(k)
            uniq.append(r)
    return tags, uniq


def write(col, items, store):
    """your labels into the deck: guesswithanki:: tags on the notes (old ones replaced) and _guesswithanki.json; returns
    (notes tagged, records in the file, the last OpChanges for Anki's window to refresh)"""
    tags, recs = plan_write(items, store)
    changes = None
    old = {}
    for nid, t in col.db.all("select id, tags from notes where id in (%s)" % ",".join(str(n) for n in tags)) if tags else []:
        for tag in t.split():
            if tag.lower().startswith(TAG):
                old.setdefault(tag, []).append(nid)
    for tag, nids in old.items():
        changes = col.tags.bulk_remove(nids, tag)
    groups = {}
    for nid, (r, m) in tags.items():
        groups.setdefault(" ".join(x for x in (r and TAG + "reading::" + r, m and TAG + "meaning::" + m) if x), []).append(nid)
    for tagstr, nids in groups.items():
        if tagstr:
            changes = col.tags.bulk_add(nids, tagstr)
    media_file(col).write_text(json.dumps({"schema": SCHEMA, "labels": recs}, ensure_ascii=False, indent=1), encoding="utf-8")
    return len(tags), len(recs), changes
