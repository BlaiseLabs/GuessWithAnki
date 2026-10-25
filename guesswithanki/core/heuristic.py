"""The code end of the spectrum: guessability computed from tables, with settings a person can tune.

reading  each kanji's reading in the word, as a share of how that kanji is read: in the dictionary's common words
         (data/readings.json), in this deck, or both (the deck's counts weighted by `deck_weight`). A word is as
         guessable as its least predictable kanji (the minimum share); a word that does not split kanji by kanji
         (今日 きょう) scores 0. The share becomes a level by `reading_full`: a reading used by that share of the
         kanji's words (or more) is fully guessable (calibrated on a model's labels of a 2,000-word deck: only
         readings almost never used were judged unguessable).
meaning  how close the word's meaning is to its kanji's meanings put together:
         "embeddings"  cosine of the two texts' embeddings (any embedding model; EmbeddingGemma by default), mapped
                       from [meaning_lo, meaning_hi] to [0, 1]
         "words"       the share of the word's kanji that have a meaning word in the word's meaning (no model)
         "off"         no meaning heuristic"""
import collections
import re

from .model import profile

_W = re.compile(r"[a-z]+")
STOP = set("a an the of to in on for and or be is as at by with one's someone something sth sb".split())


def deck_counts(items):
    """kanji -> Counter(reading) over the deck's words (each word once)"""
    c = collections.defaultdict(collections.Counter)
    for it in items:
        for ch, r in it.split or []:
            c[ch][r] += 1
    return c


def reading_share(ch, r, deck, cfg):
    src, dw = cfg.get("reading_from", "both"), float(cfg.get("deck_weight", 3))
    d = profile().dict_readings(ch) if src in ("both", "dictionary") else {}
    k = deck.get(ch, {}) if src in ("both", "deck") else {}
    tot = sum(d.values()) + dw * sum(k.values())
    return (d.get(r, 0) + dw * k.get(r, 0)) / tot if tot else 0.0


def reading_score(it, deck, cfg):
    if not profile().reads:
        return None
    if not it.split:
        return 0.0
    share = min(reading_share(ch, r, deck, cfg) for ch, r in it.split)
    return min(1.0, share / float(cfg.get("reading_full", 0.05)))


def kanji_text(word, it=None):
    p = profile()
    if it is not None and it.parts:
        return " + ".join(m or u for u, m in it.parts.items())
    return " + ".join(", ".join(p.meanings(ch)[:2]) or "?" for ch in p.units(word))


def meaning_text(it):
    m = re.split(r"[;；/\n]", it.meaning or "")[0]
    return m.strip()[:120] or it.meaning[:120]


def _stems(s):
    return {w[:5] for w in _W.findall(s.lower()) if w not in STOP and len(w) >= 3}


def meaning_words(it):
    p = profile()
    if it.parts:
        ms = list(it.parts.values())
    else:
        ms = [" ".join(p.meanings(ch)) for ch in p.units(it.word)]
    if not ms or not it.meaning:
        return 0.0
    gloss = _stems(it.meaning)
    return sum(1 for m in ms if _stems(m) & gloss) / len(ms)


def score(items, cfg, embedder=None, progress=None):
    """{key: (reading level, meaning level)} for the items with kanji"""
    deck = deck_counts(items)
    mode = cfg.get("meaning", "embeddings")
    if mode == "embeddings" and not embedder:
        mode = "words"
    ks = [it for it in items if it.split is not None or it.has_kanji]
    cos = {}
    if mode == "embeddings" and embedder and ks:
        a = embedder.vectors([meaning_text(it) for it in ks], progress=progress)
        b = embedder.vectors([kanji_text(it.word, it) for it in ks], progress=progress)
        from .remote import cosine
        lo, hi = float(cfg.get("meaning_lo", 0.3)), float(cfg.get("meaning_hi", 0.6))
        for it, x, y in zip(ks, a, b):
            cos[it.key] = max(0.0, min(1.0, (cosine(x, y) - lo) / (hi - lo)))
        embedder.save()
    out = {}
    for it in ks:
        m = cos.get(it.key) if mode == "embeddings" else meaning_words(it) if mode == "words" else None
        out[it.key] = (reading_score(it, deck, cfg), m)
    return out
