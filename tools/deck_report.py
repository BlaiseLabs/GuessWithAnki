"""GuessWithAnki on a shared deck as a new learner would start it (no history): what it finds in the deck, and what the
path changes over the first N new cards against the deck's own order, with the deck_every trade-off.

    python3 tools/deck_report.py COLLECTION.anki2 --files DIR [--ahead 500 1500] [--every 0 3] [--no-server]
Writes DIR/report.json (and DIR/last.json, the dashboard's data, for the first setting)."""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from guesswithanki.core import run  # noqa: E402
from guesswithanki.core.path import count_guessable, plan  # noqa: E402
from guesswithanki.core.stats import summary  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("collection")
    ap.add_argument("--files", required=True)
    ap.add_argument("--ahead", type=int, nargs="+", default=[500])
    ap.add_argument("--every", type=int, nargs="+", default=[0, 3])
    ap.add_argument("--no-server", action="store_true")
    a = ap.parse_args()
    from anki.collection import Collection
    files = Path(a.files)
    files.mkdir(parents=True, exist_ok=True)
    col = Collection(a.collection)
    cfg = run.merged({})
    t = time.time()
    an = run.analyse(col, cfg, files, use_server=not a.no_server,
                     progress=lambda i, n: print("\r  embeddings %d/%d" % (i, n), end="", file=sys.stderr, flush=True))
    before = run.original_order(files, an.new)
    out = {"deck": a.collection, "words": len(an.items), "kanji": sum(1 for it in an.items if it.has_kanji),
           "split": sum(1 for it in an.items if it.split), "judged_guessable": len(an.full),
           "reading_ok": sum(1 for it in an.items if it.has_kanji and (it.reading_g or 0) >= cfg["guessable"]["reading"]),
           "meaning_ok": sum(1 for it in an.items if it.has_kanji and (it.meaning_g or 0) >= cfg["guessable"]["meaning"]),
           "no_reading": sum(1 for it in an.items if it.has_kanji and not it.reading), "note": an.note, "runs": []}
    first = True
    for ahead in a.ahead:
        for every in a.every:
            pc = dict(cfg["path"], ahead=ahead, deck_every=every)
            t1 = time.time()
            order, why = plan(an.started, before, an.full, pc)
            n = min(ahead, len(order))
            r = {"ahead": ahead, "every": every, "n": n, "before": count_guessable(an.started, before, an.full, pc, n),
                 "after": count_guessable(an.started, order, an.full, pc, n),
                 "kept": len({it.key for it in order[:n]} & {it.key for it in before[:n]}), "seconds": round(time.time() - t1, 1)}
            out["runs"].append(r)
            print("\n  ahead %(ahead)d every %(every)d: guessable on arrival %(before)d -> %(after)d, kept %(kept)d (%(seconds)ss)" % r,
                  file=sys.stderr, flush=True)
            if first:
                s = summary(an, order, why, before, dict(cfg, path=pc))
                s.update(moved=None, at=time.strftime("%Y-%m-%d %H:%M"), seconds=None)
                (files / "last.json").write_text(json.dumps(s, ensure_ascii=False), encoding="utf-8")
                out["next20"] = [x["word"] for x in s["next"][:20]]
                out["confusable_total"] = s["confusable_total"]
                first = False
    out["seconds"] = round(time.time() - t, 1)
    (files / "report.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "runs"}, ensure_ascii=False))
    col.close()


if __name__ == "__main__":
    main()
