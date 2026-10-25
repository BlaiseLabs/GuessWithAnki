"""A deck's guessability index: how much of it a learner could guess from pieces met before, before any ordering.

  words          the deck's words the profile handles
  with pieces    words that split into two or more pieces (or, for Japanese and Chinese, a character with its reading)
  meaning yes    of those, judged guessable in meaning (level 0.6 or more: "yes", or most votes)
  reading yes    the same for the reading (Japanese, Chinese)
  guessable      both (or meaning, for English and medical): the words the path can make free
  pieces         distinct pieces; reuse = the share of words whose every piece appears in another word too
  on arrival     guessable words that arrive guessable in the next `n` words: deck order -> GuessWithAnki's path

    python3 tools/guess_index.py "Name=COLLECTION.anki2=FILES_DIR[=cfg.json]" ... [--config cfg.json] [--n 500]
                                 [--json out.json]

(a deck's own cfg.json, merged over --config: its search, profile or fields)"""
import argparse
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from guesswithanki.core import run  # noqa: E402
from guesswithanki.core.path import count_guessable, plan  # noqa: E402


def index(colpath, files, cfg, n):
    from anki.collection import Collection
    from guesswithanki.core.model import profile
    col = Collection(colpath)
    try:
        an = run.analyse(col, cfg, files, use_server=False)
    finally:
        col.close()
    items = an.items
    withp = [it for it in items if it.split]
    t = cfg["guessable"]
    p = profile()
    by_piece = collections.Counter(pc for it in withp for pc in set(it.pieces))
    reuse = sum(1 for it in withp if all(by_piece[pc] >= 2 for pc in it.pieces))
    before = run.original_order(files, an.new)
    order, _ = plan(an.started, before, an.full, dict(cfg["path"], ahead=min(len(before), max(n, 500))))
    return {"profile": p.name, "words": len(items), "with_pieces": len(withp),
            "meaning_yes": sum(1 for it in withp if (it.meaning_g or 0) >= t["meaning"]),
            "reading_yes": sum(1 for it in withp if (it.reading_g or 0) >= t["reading"]) if p.reads else None,
            "guessable": len(an.full), "pieces": len(by_piece), "reuse": reuse,
            "pieces_per_word": round(sum(len(set(it.pieces)) for it in withp) / max(1, len(withp)), 2),
            "labelled": sum(1 for it in items if it.sources and "llm" in it.sources),
            "arrival_n": n, "arrival_deck": count_guessable(an.started, before, an.full, cfg["path"], n),
            "arrival_path": count_guessable(an.started, order, an.full, cfg["path"], n)}


def pct(a, b):
    return "%d%%" % round(100 * a / b) if b else "–"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("decks", nargs="+", help='"Name=COLLECTION.anki2=FILES_DIR[=cfg.json]"')
    ap.add_argument("--config")
    ap.add_argument("--n", type=int, default=500)
    ap.add_argument("--json")
    a = ap.parse_args()
    base = json.loads(Path(a.config).read_text(encoding="utf-8")) if a.config else {}
    out = {}
    print("| Deck | Kind | Words | With pieces | Meaning guessable | Reading guessable | Guessable | Pieces reused | "
          "Guessable on arrival in the first %d (deck order → path) |" % a.n)
    print("|---|---|---|---|---|---|---|---|---|")
    for spec in a.decks:
        name, colpath, files, *own = spec.split("=")
        cfg = run.merged(dict(base, **(json.loads(Path(own[0]).read_text(encoding="utf-8")) if own else {})))
        r = index(colpath, files, cfg, a.n)
        out[name] = r
        w = r["with_pieces"]
        print("| %s | %s | %s | %s | %s | %s | **%s** | %s | %d → **%d** |" % (
            name, r["profile"], format(r["words"], ","), pct(w, r["words"]), pct(r["meaning_yes"], w),
            "–" if r["reading_yes"] is None else pct(r["reading_yes"], w), pct(r["guessable"], r["words"]),
            pct(r["reuse"], w), r["arrival_deck"], r["arrival_path"]))
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
