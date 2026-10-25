"""GuessWithAnki on a sentence course (one sentence per card, words given as lemmas), e.g. the Tae Kim / anime deck:
each card's NEW kanji words (lemmas not met in an earlier card) are the items. A new word arrives guessable when it is
judged guessable and each of its kanji readings was met in the last `window` cards (in any word of those sentences).
Courses teach grammar in order, so cards may only move `shift` places from where the course puts them.

    python3 tools/sentence_deck.py COLLECTION.anki2 --note JlabNote --lemma Jlab-Lemma --order Sequence
                                   --files DIR [--window 40] [--shift 0 10 25 50] [--no-server]

Readings and meanings of the lemmas come from JMdict's common words (tools/common_words.json)."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from guesswithanki.core import heuristic, run  # noqa: E402
from guesswithanki.core.kana import clean, has_kanji  # noqa: E402
from guesswithanki.core.labels import Store  # noqa: E402
from guesswithanki.core.model import Item, guessable, judge  # noqa: E402
from guesswithanki.core.remote import Embedder  # noqa: E402


def cards(col, note, lemma, order):
    nt = next(m for m in col.models.all() if m["name"].startswith(note))
    names = [f["name"] for f in nt["flds"]]
    rows = [dict(zip(names, f.split("\x1f"))) for f in col.db.list("select flds from notes where mid = ?", nt["id"])]
    rows.sort(key=lambda r: int(clean(r.get(order, "0")) or 0))
    return [[w for w in clean(r[lemma]).split() if w] for r in rows]


def simulate(seq, items, full, window):
    """per card in seq: (new words guessable on arrival, new kanji words) -- seq: list of word lists"""
    last, seen, got, tot = {}, set(), 0, 0
    for i, words in enumerate(seq):
        for w in dict.fromkeys(words):
            if w in seen or w not in items:
                continue
            tot += 1
            it = items[w]
            if it.key in full and it.pieces and all(p in last and i - last[p] <= window for p in it.pieces):
                got += 1
        for w in words:
            seen.add(w)
            for p in (items[w].pieces if w in items else []):
                last[p] = i
    return got, tot


def plan(seq, items, full, window, shift):
    """greedy over cards, each kept within `shift` places of its course place: the card whose new words arrive
    guessable most, else the earliest (a card past its window is taken at once)"""
    left = list(range(len(seq)))
    out, last, seen = [], {}, set()
    for pos in range(len(seq)):
        due = [c for c in left if c <= pos - shift]
        if due:
            pick = due[0]
        else:
            best, bs = left[0], -1.0
            for c in left:
                if c > pos + shift:
                    break
                s = 0.0
                for w in dict.fromkeys(seq[c]):
                    if w in seen or w not in items:
                        continue
                    it = items[w]
                    if it.key in full and it.pieces and all(p in last and pos - last[p] <= window for p in it.pieces):
                        s += 1
                    elif it.key in full:
                        s -= 0.25                          # (a guessable word arriving early is a chance spent)
                if s > bs:
                    best, bs = c, s
            pick = best
        left.remove(pick)
        out.append(seq[pick])
        for w in seq[pick]:
            seen.add(w)
            for p in (items[w].pieces if w in items else []):
                last[p] = pos
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("collection")
    ap.add_argument("--note", required=True)
    ap.add_argument("--lemma", required=True)
    ap.add_argument("--order", required=True)
    ap.add_argument("--files", required=True)
    ap.add_argument("--window", type=int, default=40)
    ap.add_argument("--shift", type=int, nargs="+", default=[0, 10, 25, 50])
    ap.add_argument("--no-server", action="store_true")
    a = ap.parse_args()
    from anki.collection import Collection
    col = Collection(a.collection)
    seq = cards(col, a.note, a.lemma, a.order)
    col.close()
    jm = {}
    for keb, reb, gl, _ in json.loads((ROOT / "tools" / "common_words.json").read_text(encoding="utf-8"))["words"]:
        jm.setdefault(keb, (reb, "; ".join(gl[:3])))
    words = list(dict.fromkeys(w for s in seq for w in s if has_kanji(w)))
    items = {w: Item(i, w, jm[w][0], jm[w][1]) for i, w in enumerate(words) if w in jm}
    cfg = run.merged({})
    files = Path(a.files)
    files.mkdir(parents=True, exist_ok=True)
    emb = None if a.no_server else Embedder(cfg["embeddings"], files / "embeddings.json")
    heur = heuristic.score(list(items.values()), cfg["heuristic"], emb)
    judge(list(items.values()), Store(files / "labels.jsonl"), heur, cfg)
    full = {it.key for it in items.values() if guessable(it, cfg)}
    out = {"cards": len(seq), "kanji_words": len(words), "with_dictionary_entry": len(items), "judged_guessable": len(full),
           "runs": []}
    for shift in a.shift:
        order = seq if shift == 0 else plan(seq, items, full, a.window, shift)
        got, tot = simulate(order, items, full, a.window)
        out["runs"].append({"shift": shift, "guessable_on_arrival": got, "new_kanji_words": tot})
        print("shift %3d: %d of %d new kanji words arrive guessable" % (shift, got, tot), flush=True)
    (files / "sentence_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "runs"}))


if __name__ == "__main__":
    main()
