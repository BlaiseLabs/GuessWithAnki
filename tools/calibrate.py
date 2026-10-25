"""Tune the heuristic on words someone has already judged: how well each setting separates the words judged guessable
from the rest (AUC), and the threshold that agrees with the judges most often.

    python3 tools/calibrate.py LABELLED.json [--embed http://127.0.0.1:11434/v1 embeddinggemma] [--cache DIR]

LABELLED.json: [{"word", "reading", "meaning", "reading_guessable", "meaning_guessable", "first_right"?}], labels
"yes"/"partly"/"no" (from a model, a crowd file, ...). first_right (optional): 1/0, the learner's first answer, to
see how the judged and computed levels predict real first looks."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from guesswithanki.core import heuristic  # noqa: E402
from guesswithanki.core.model import Item  # noqa: E402
from guesswithanki.core.remote import Embedder, cosine  # noqa: E402


def auc(scores, ys):
    pos = [s for s, y in zip(scores, ys) if y]
    neg = [s for s, y in zip(scores, ys) if not y]
    if not pos or not neg:
        return None
    allv = sorted((s, y) for s, y in zip(scores, ys))
    rank, i, rs = {}, 0, 0.0
    while i < len(allv):                       # (Mann-Whitney U with average ranks for ties)
        j = i
        while j < len(allv) and allv[j][0] == allv[i][0]:
            j += 1
        for k in range(i, j):
            rs += (i + j + 1) / 2 if allv[k][1] else 0
        i = j
    return (rs - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def best_cut(scores, ys):
    best = (0, 0.5)
    for c in sorted(set(round(s, 3) for s in scores)):
        acc = sum((s >= c) == bool(y) for s, y in zip(scores, ys)) / len(ys)
        best = max(best, (acc, c))
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("labelled")
    ap.add_argument("--embed", nargs=2)
    ap.add_argument("--cache", default="work")
    a = ap.parse_args()
    rows = json.loads(Path(a.labelled).read_text(encoding="utf-8"))
    items = [Item(nid=i, word=r["word"], reading=r["reading"], meaning=r.get("meaning", "")) for i, r in enumerate(rows)]
    keep = [(it, r) for it, r in zip(items, rows) if it.has_kanji]
    print("words with kanji: %d (split kanji by kanji: %d)" % (len(keep), sum(1 for it, _ in keep if it.split)))
    yr = [r["reading_guessable"] == "yes" for _, r in keep]
    ym = [r["meaning_guessable"] == "yes" for _, r in keep]
    deck = heuristic.deck_counts(items)
    out = {}
    for src in ("dictionary", "deck", "both"):
        for dw in ((1, 3, 10) if src == "both" else (1,)):
            cfg = {"reading_from": src, "deck_weight": dw}
            s = [heuristic.reading_score(it, deck, cfg) for it, _ in keep]
            acc, cut = best_cut(s, yr)
            out["reading %s w%d" % (src, dw)] = (auc(s, yr), acc, cut)
    sw = [heuristic.meaning_words(it) for it, _ in keep]
    out["meaning words"] = (auc(sw, ym),) + best_cut(sw, ym)
    cos = None
    if a.embed:
        emb = Embedder({"base_url": a.embed[0], "model": a.embed[1]}, Path(a.cache) / "calib_embeddings.json")
        va = emb.vectors([heuristic.meaning_text(it) for it, _ in keep])
        vb = emb.vectors([heuristic.kanji_text(it.word) for it, _ in keep])
        emb.save()
        cos = [cosine(x, y) for x, y in zip(va, vb)]
        out["meaning embeddings (%s)" % a.embed[1]] = (auc(cos, ym),) + best_cut(cos, ym)
        mix = [0.5 * c + 0.5 * w * 0.6 for c, w in zip(cos, sw)]
        out["meaning embeddings+words"] = (auc(mix, ym),) + best_cut(mix, ym)
    print("%-34s %6s %8s %7s" % ("setting", "AUC", "agree", "cut"))
    for k, (u, acc, cut) in out.items():
        print("%-34s %6.3f %7.1f%% %7.3f" % (k, u or 0, 100 * acc, cut))
    print("base rates: reading yes %.0f%%, meaning yes %.0f%%" % (100 * sum(yr) / len(yr), 100 * sum(ym) / len(ym)))
    fr = [(it, r) for it, r in keep if r.get("first_right") is not None]
    if fr:
        y = [r["first_right"] for _, r in fr]
        print("\nfirst looks: %d words, right %.0f%%" % (len(fr), 100 * sum(y) / len(y)))
        judged = [1.0 * (r["reading_guessable"] == "yes") + (r["meaning_guessable"] == "yes") for _, r in fr]
        rs = [heuristic.reading_score(it, deck, {"reading_from": "both", "deck_weight": 3}) for it, _ in fr]
        print("AUC for right on first look: judges (reading+meaning yes) %.3f; heuristic reading %.3f"
              % (auc(judged, y), auc(rs, y)))
        if cos:
            cm = {it.key: c for (it, _), c in zip(keep, cos)}
            comb = [r_ + cm.get(it.key, 0) for (it, _), r_ in zip(fr, rs)]
            print("heuristic reading + meaning cosine %.3f" % auc(comb, y))
            for name, f in (("judged both yes", lambda it, r, rr, c: r["reading_guessable"] == "yes" and r["meaning_guessable"] == "yes"),):
                g = [r_["first_right"] for it, r_ in fr if f(it, r_, 0, 0)]
                ng = [r_["first_right"] for it, r_ in fr if not f(it, r_, 0, 0)]
                print("  %s: right first time %.0f%% (%d) vs others %.0f%% (%d)" % (name, 100 * sum(g) / max(1, len(g)), len(g), 100 * sum(ng) / max(1, len(ng)), len(ng)))


if __name__ == "__main__":
    main()
