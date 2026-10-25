"""What the dashboard shows: coverage (how many words are guessable, judged by whom), what the path changes (words
guessable on arrival, the deck's own order against the path), the next cards and why, the patterns, and the words
that could be confused (a kanji with another common reading, in this deck or in the dictionary)."""
import collections

from .heuristic import deck_counts
from .model import profile
from .path import State, value


def arrivals(started, order, full, cfg, n):
    """1/0 per place: guessable when it arrives"""
    st, out = State(started, cfg), []
    for pos, it in enumerate(order[:n]):
        out.append(1 if value(it, pos, st, full)[0] > 0 else 0)
        st.place(it, pos)
    return out


def curve(flags, step=10):
    out, c = [], 0
    for i, f in enumerate(flags, 1):
        c += f
        if i % step == 0 or i == len(flags):
            out.append([i, c])
    return out


def free_cards(started, new, full, seen=1, window=40, rate=0.8):
    """the learner's own history, counted as free cards: a pattern is learned after `seen` sightings in studied words,
    each within `window` cards of the one before (learned stays learned). Of the studied cards, those whose word was
    judged guessable with all its patterns learned when it arrived were free; of the words not studied yet, those that
    are so now could be guessed today. virtual = studied + rate x guessable now"""
    streak, last, learned, free = {}, {}, set(), 0
    for i, it in enumerate(started, 1):
        if it.key in full and it.pieces and all(p in learned for p in it.pieces):
            free += 1
        for p in set(it.pieces):
            streak[p] = streak.get(p, 0) + 1 if p in last and i - last[p] <= window else 1
            last[p] = i
            if streak[p] >= seen:
                learned.add(p)
    now = sum(1 for it in new if it.key in full and it.pieces and all(p in learned for p in it.pieces))
    n = len(started)
    return {"studied": n, "arrived_free": free, "guessable_now": now, "patterns": len(learned), "seen": seen,
            "rate": rate, "effort": round(n - rate * free), "virtual": round(n + rate * now)}


def confusable(a, cfg, limit=40):
    """guessable new words whose kanji have another reading that is common here or in the dictionary"""
    deck = deck_counts(a.items)
    words_by = collections.defaultdict(list)
    for it in a.items:
        for p in set(it.split or []):
            words_by[p].append(it.word)
    out = []
    for it in a.new:
        if it.key not in a.full:
            continue
        worst = None
        for ch, r in it.split if profile().reads else ():
            d, k = profile().dict_readings(ch), deck.get(ch, {})
            dt, kt = sum(d.values()) or 1, sum(k.values()) or 1
            others = []
            for r2 in set(d) | set(k):
                if r2 == r:
                    continue
                share = max(d.get(r2, 0) / dt, k.get(r2, 0) / kt)
                if share >= 0.2:
                    others.append({"r": r2, "dict": round(d.get(r2, 0) / dt, 2), "deck": k.get(r2, 0),
                                   "examples": [w for w in words_by[(ch, r2)] if w != it.word][:3]})
            if others:
                risk = max(o["dict"] for o in others) + 0.1 * sum(o["deck"] for o in others)
                if not worst or risk > worst["risk"]:
                    worst = {"word": it.word, "reading": it.reading, "meaning": it.meaning[:60], "kanji": ch,
                             "here": r, "here_dict": round(d.get(r, 0) / dt, 2), "others": others,
                             "risk": round(risk, 2)}
        if worst:
            out.append(worst)
    out.sort(key=lambda x: -x["risk"])
    return out[:limit], len(out)


def patterns(a, order, cfg, limit=40):
    st = State(a.started, cfg)
    pos0 = 0
    count = collections.Counter(p for it in a.items for p in set(it.pieces))
    out = []
    for p, n in count.most_common(limit):
        ago = pos0 - st.last[p] if p in st.last else None
        status = ("spaced" if st.spaced(p) else "mature" if p in st.mature else
                  "fresh" if ago is not None and ago <= st.W else "faded" if ago is not None else "not met")
        nxt = next((i for i, it in enumerate(order) if p in it.pieces), None)
        out.append({"p": p, "words": n, "seen": st.seen[p], "ago": ago, "status": status, "next": nxt,
                    "gap": round(st.gap(p)) if st.spaced(p) else None})
    return out


def summary(a, order, why, before, cfg, warnings=()):
    pc = cfg["path"]
    n = min(int(pc.get("ahead", 500)), len(order))
    fb, fa = arrivals(a.started, before, a.full, pc, n), arrivals(a.started, order, a.full, pc, n)
    newk = [it for it in a.new if it.has_kanji]
    t = cfg["guessable"]
    srcs = collections.Counter()
    for it in a.items:
        if it.has_kanji:
            for s in (it.sources or {}):
                srcs[s] += 1
    conf, nconf = confusable(a, cfg)
    nxt = []
    for i, it in enumerate(order[:60]):
        w = why.get(it.key, {})
        nxt.append({"i": i + 1, "word": it.word, "reading": it.reading, "meaning": it.meaning[:70],
                    "guessable": bool(fa[i]) if i < len(fa) else False, "judged": it.key in a.full,
                    "fresh": [[p, d] for p, d in w.get("fresh", [])], "spaced": w.get("spaced", []),
                    "setup": w.get("setup", 0), "r": None if it.reading_g is None else round(it.reading_g, 2),
                    "m": None if it.meaning_g is None else round(it.meaning_g, 2),
                    "src": {k: [None if x is None else round(x, 2) for x in v] for k, v in (it.sources or {}).items()}})
    from .model import profile
    prof = profile()
    return {
        "profile": {"name": prof.name, "reads": prof.reads},
        "totals": {"words": len(a.items), "kanji": sum(1 for it in a.items if it.has_kanji),
                   "split": sum(1 for it in a.items if it.split), "irregular": sum(1 for it in a.items if it.has_kanji and not it.split),
                   "kana": sum(1 for it in a.items if not it.has_kanji), "new": len(a.new), "started": len(a.started)},
        "labels": dict(srcs),
        "guessable": {"new_kanji": len(newk), "both": sum(1 for it in newk if it.key in a.full),
                      "reading": sum(1 for it in newk if (it.reading_g or 0) >= t["reading"]),
                      "meaning": sum(1 for it in newk if (it.meaning_g or 0) >= t["meaning"])},
        "effect": {"n": n, "before": sum(fb), "after": sum(fa), "before_curve": curve(fb), "after_curve": curve(fa),
                   # the cost: how many of the deck's own next n the path still brings in its next n
                   "kept": len({it.key for it in order[:n]} & {it.key for it in before[:n]})},
        "free": free_cards(a.started, a.new, a.full, int(cfg.get("free", {}).get("seen", 1)), int(pc.get("window", 40)),
                           float(cfg.get("free", {}).get("rate", 0.8))),
        "next": nxt, "patterns": patterns(a, order, pc), "confusable": conf, "confusable_total": nconf,
        "warnings": ["%s: %s" % w for w in warnings], "note": a.note,
        "settings": {"window": pc["window"], "ahead": pc["ahead"], "spacing": pc["spacing"]["on"],
                     "thresholds": t, "sources": cfg["sources"], "search": cfg["search"] or "(whole collection)"},
    }
