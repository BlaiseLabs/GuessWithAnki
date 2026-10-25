"""Free cards: of the first n cards a learner goes through, how many cost nothing to learn because they could be
guessed on sight, in the deck's own order and in GuessWithAnki's.

A pattern (kanji + reading) is learned once it has been seen in `seen` = k studied words:
  strict   each sighting within `window` cards of the one before (a reading met once every 300 cards never adds
           up); once learned it stays learned
  lenient  any k sightings, however far apart
A card arrives free when its word is judged guessable and all its patterns are learned; it is guessed right with
probability `rate`. Of n cards, effort = n - rate x free (the cards you really had to learn); speed-up = n / effort:
"you went through n cards for the work of effort". GuessWithAnki is planned for each k (path setting need = k).
Also counted: words not reached yet that could already be guessed (skip-ahead).

    python3 tools/free_cards.py COLLECTION.anki2 --files DIR --out OUT.json [--n 100 250 500 1000 2000]
                                [--seen 1 3 5 10] [--rate 1 0.8 0.5 0.25] [--window 40] [--config C.json]"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from guesswithanki.core import run  # noqa: E402
from guesswithanki.core.path import plan  # noqa: E402


def simulate(order, words, full, ns, k, window):
    """{n: {free_strict, free_lenient, ahead_strict, ahead_lenient, patterns_strict}}, first card that arrived free"""
    count, streak, last, learned = {}, {}, {}, set()
    out, studied, got_s, got_l, first = {}, set(), 0, 0, None
    ns = sorted(n for n in ns if n <= len(order))
    for i, it in enumerate(order, 1):
        if it.key in full and it.pieces:
            if all(p in learned for p in it.pieces):
                got_s += 1
                first = first or i
            if all(count.get(p, 0) >= k for p in it.pieces):
                got_l += 1
        studied.add(it.key)
        for p in set(it.pieces):
            count[p] = count.get(p, 0) + 1
            streak[p] = streak.get(p, 0) + 1 if p in last and i - last[p] <= window else 1
            last[p] = i
            if streak[p] >= k:
                learned.add(p)
        if i in ns:
            rest = [w for w in words if w.key not in studied and w.key in full and w.pieces]
            out[i] = {"free_strict": got_s, "free_lenient": got_l, "patterns_strict": len(learned),
                      "ahead_strict": sum(1 for w in rest if all(p in learned for p in w.pieces)),
                      "ahead_lenient": sum(1 for w in rest if all(count.get(p, 0) >= k for p in w.pieces))}
    return out, first


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("collection")
    ap.add_argument("--files", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, nargs="+", default=[100, 250, 500, 1000, 2000])
    ap.add_argument("--seen", type=int, nargs="+", default=[1, 3, 5, 10])
    ap.add_argument("--rate", type=float, nargs="+", default=[1.0, 0.8, 0.5, 0.25])
    ap.add_argument("--window", type=int, default=40)
    ap.add_argument("--config")
    ap.add_argument("--no-server", action="store_true")
    a = ap.parse_args()
    from anki.collection import Collection
    col = Collection(a.collection)
    cfg = run.merged(json.loads(Path(a.config).read_text()) if a.config else {})
    an = run.analyse(col, cfg, a.files, use_server=not a.no_server)
    col.close()
    before = run.original_order(a.files, an.new)
    ns = sorted(set([n for n in a.n if n <= len(before)] + ([len(before)] if len(before) <= max(a.n) else [])))
    res = {"deck": Path(a.collection).parent.name, "words": len(an.items), "judged_guessable": len(an.full),
           "window": a.window, "rates": a.rate, "ns": ns, "by_k": {}}
    for k in a.seen:
        order, _ = plan(an.started, before, an.full, dict(cfg["path"], ahead=max(ns), need=k, window=a.window))
        d, fd = simulate(before, an.items, an.full, ns, k, a.window)
        g, fg = simulate(order, an.items, an.full, ns, k, a.window)
        res["by_k"][k] = {"deck": d, "guesswithanki": g, "first_free": {"deck": fd, "guesswithanki": fg}}
    Path(a.out).write_text(json.dumps(res, indent=1), encoding="utf-8")
    print("%s: %d words, %d judged guessable" % (res["deck"], len(an.items), len(an.full)))
    print("%5s %3s %20s %24s %16s" % ("n", "k", "free (strict) d->gp", "speed-up at 80%: d -> gp", "first free card"))
    for k in a.seen:
        for n in ns:
            d, g = res["by_k"][k]["deck"][n], res["by_k"][k]["guesswithanki"][n]
            sd, sg = n / (n - 0.8 * d["free_strict"]), n / (n - 0.8 * g["free_strict"])
            print("%5d %3d %9d -> %-8d %10.2fx -> %.2fx %8s -> %s" % (n, k, d["free_strict"], g["free_strict"], sd, sg,
                                                                    res["by_k"][k]["first_free"]["deck"], res["by_k"][k]["first_free"]["guesswithanki"]))


if __name__ == "__main__":
    main()
