"""The order new cards come in: a greedy path that makes as many words as possible guessable when they arrive.

A word is guessable at its place when it is judged guessable (core/model.guessable) and every one of its patterns
(kanji + the reading it has there) is in hand:
  fresh    met in a word within the last `window` new words
  mature   (mature_counts) in a word whose card has a mature interval
  spaced   (spacing on) met in `spacing.after` or more words: the pattern itself is learned, and is now reviewed at
           growing gaps instead of back to back
Each place takes, of the words left, the one that is guessable right now (1 + 1/d, d = how many words back its
oldest fresh pattern was met), plus `setup` for each guessable word it brings to one missing pattern (a quarter for
two missing), divided by the number of new patterns the word itself brings: openers come one new pattern at a time,
so 取る and 戻る come before 取り戻す, which then arrives guessable; and an opener that is itself guessable counts
more (up to double), so the plain word opens the pattern rather than an irregular one. Ties keep the deck's own order. With spacing on, a word whose spaced pattern was met fewer than
gap(p) = window * growth^(n - after) words ago (n = words met with it so far, capped at max_gap) is held back by
the share of the gap still to go: the "SRS for patterns".
With `need` = k (default 1), a pattern is in hand only after k sightings, each within `window` cards of the one
before (for learners who need to meet a kanji reading a few times before they trust it).
With `deck_every` = k, every k-th place takes the deck's own next word instead (frequency decks keep part of their
order; 0 = off). Only the next `ahead` places are planned; the rest keep the deck's order after them."""
import collections


def _cfg(cfg):
    sp = cfg.get("spacing") or {}
    return (int(cfg.get("window", 40)), int(cfg.get("ahead", 500)), float(cfg.get("setup", 0.1)),
            bool(cfg.get("mature_counts", True)), bool(sp.get("on", False)), int(sp.get("after", 4)),
            float(sp.get("growth", 2.0)), int(sp.get("max_gap", 400)))


class State:
    """what the learner has in hand at a place in the path"""

    def __init__(self, started, cfg):
        self.W, _, _, mc, self.spacing, self.after, self.growth, self.max_gap = _cfg(cfg)
        self.need = int(cfg.get("need", 1))
        self.last, self.seen, self.streak, self.mature = {}, collections.Counter(), collections.Counter(), set()
        for i, it in enumerate(started):
            self.place(it, i - len(started))
            if mc and it.mature:
                self.mature.update(it.pieces)

    def spaced(self, p):
        return self.spacing and self.seen[p] >= self.after

    def gap(self, p):
        return min(self.max_gap, self.W * self.growth ** (self.seen[p] - self.after))

    def known(self, p, pos):
        return ((p in self.last and pos - self.last[p] <= self.W and self.streak[p] >= self.need)
                or p in self.mature or self.spaced(p))

    def place(self, it, pos):
        for p in set(it.pieces):
            self.streak[p] = self.streak[p] + 1 if p in self.last and pos - self.last[p] <= self.W else 1
            self.last[p] = pos
            self.seen[p] += 1


def value(it, pos, st, full):
    """(score, why) of placing `it` at pos: 0 unless it is guessable there"""
    if it.key not in full or not it.pieces or not all(st.known(p, pos) for p in it.pieces):
        return 0.0, None
    fresh = [(p, pos - st.last[p]) for p in it.pieces if p in st.last and pos - st.last[p] <= st.W and not st.spaced(p)]
    s = 1.0 + (min(1.0 / d for _, d in fresh) if fresh else 0.0)
    held = 1.0
    for p in it.pieces:
        if st.spaced(p) and p in st.last:
            held = min(held, max(0.05, (pos - st.last[p]) / st.gap(p)))
    return s * held, {"fresh": fresh, "spaced": [p for p in it.pieces if st.spaced(p)], "held": round(held, 2)}


def plan(started, new, full, cfg, progress=None):
    """(the new items in their planned order, {key: why}) -- started: studied items, oldest first; new: the new
    items in the deck's order; full: the keys judged guessable"""
    _, ahead, setup = _cfg(cfg)[:3]
    every = int(cfg.get("deck_every", 0))
    st = State(started, cfg)
    pool, out, why = list(new), [], {}
    left = {it.key for it in new if it.key in full}
    byk = {it.key: it for it in new}
    for pos in range(min(ahead, len(pool))):
        U, own = collections.Counter(), {}
        for k in left:
            miss = [p for p in set(byk[k].pieces) if not st.known(p, pos)]
            if len(miss) == 1:
                U[miss[0]] += 1.0
                own[k] = (miss[0], 1.0)
            elif len(miss) == 2:
                U[miss[0]] += 0.25
                U[miss[1]] += 0.25
                own[k] = (None, 0.5)
        best, bs, bw = 0, 0.0, None
        for i, c in enumerate(pool if not (every and (pos + 1) % every == 0) else ()):
            if not c.pieces:
                continue
            s, w = value(c, pos, st, full)
            su = sum(U[p] for p in set(c.pieces))
            if c.key in own and (own[c.key][0] is None or own[c.key][0] in c.pieces):
                su -= own[c.key][1]
            fresh_n = len({p for p in c.pieces if not st.known(p, pos)})
            own_g = min(c.reading_g if c.reading_g is not None else 0.5, c.meaning_g if c.meaning_g is not None else 0.5)
            # (an opener is a word to learn too: one new pattern at a time, and better a plain one: 見る, not 見っともない)
            s += setup * su / max(1, fresh_n) * (0.5 + 0.5 * own_g)
            if s > bs:
                best, bs, bw = i, s, (w, su)
        pick = pool.pop(best)
        st.place(pick, pos)
        left.discard(pick.key)
        out.append(pick)
        why[pick.key] = {"guessable": bool(bw and bw[0]), "fresh": (bw[0] or {}).get("fresh", []) if bw else [],
                         "spaced": (bw[0] or {}).get("spaced", []) if bw else [], "setup": round(bw[1], 2) if bw else 0}
        if progress and pos % 25 == 0:
            progress(pos, min(ahead, len(new)))
    return out + pool, why


def count_guessable(started, order, full, cfg, n=None):
    """how many of the first n words of `order` are guessable when they arrive (the path's measure, for any order)"""
    st = State(started, cfg)
    got = 0
    for pos, it in enumerate(order[:n] if n else order):
        if value(it, pos, st, full)[0] > 0:
            got += 1
        st.place(it, pos)
    return got
