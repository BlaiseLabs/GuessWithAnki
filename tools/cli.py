"""GuessWithAnki without the Anki window: the same pass over a collection file (close Anki first, or use a copy).

    python3 tools/cli.py reorder COLLECTION.anki2 [--files DIR] [--no-server] [--dry] [--config cfg.json]
    python3 tools/cli.py label   COLLECTION.anki2 [--files DIR] [--n 100] [--config cfg.json]
    python3 tools/cli.py report  COLLECTION.anki2 [--files DIR] [--out report.html]

--files: where labels, the embedding cache and the dashboard data live (default: next to the collection,
guesswithanki_files/). --config: settings to lay over config.json's defaults."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from guesswithanki.core import llm, run, trace  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["reorder", "label", "report"])
    ap.add_argument("collection")
    ap.add_argument("--files")
    ap.add_argument("--config")
    ap.add_argument("--n", type=int)
    ap.add_argument("--no-server", action="store_true")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()
    from anki.collection import Collection
    cfg = run.merged(json.loads(Path(a.config).read_text(encoding="utf-8")) if a.config else {})
    files = Path(a.files or Path(a.collection).parent / "guesswithanki_files")
    files.mkdir(parents=True, exist_ok=True)
    col = Collection(a.collection)
    try:
        prog = lambda i, n: print("\r  %d/%d" % (i, n), end="", file=sys.stderr, flush=True)
        if a.cmd == "label":
            an = run.analyse(col, cfg, files, use_server=False)
            order = an.new + an.started
            tags = {"job": "label", "deck": Path(a.collection).parent.name, "model": cfg["llm"]["model"]}
            res = llm.run(order, an.store, cfg["llm"], limit=a.n, progress=prog, tracer=trace.tracer(cfg.get("sentry_dsn"), tags))
            print(json.dumps(res, ensure_ascii=False))
        elif a.cmd == "reorder" and a.dry:
            an, order, why, before = run.compute(col, cfg, files, not a.no_server, prog)
            from guesswithanki.core.stats import summary
            s = summary(an, order, why, before, cfg)
            print(json.dumps({k: s[k] for k in ("totals", "labels", "guessable", "effect")}, ensure_ascii=False)[:2000])
        elif a.cmd == "reorder":
            s = run.reorder(col, cfg, files, not a.no_server, prog)
            print(json.dumps({k: s[k] for k in ("totals", "labels", "guessable", "moved", "seconds")}, ensure_ascii=False))
            print("guessable on arrival in the next %(n)d: %(before)d in the deck's order -> %(after)d" % s["effect"])
        elif a.cmd == "report":
            from guesswithanki.web import page
            last = json.loads((files / "last.json").read_text(encoding="utf-8"))
            out = Path(a.out or files / "report.html")
            out.write_text(page(last, standalone=True), encoding="utf-8")
            print(out)
    finally:
        col.close()


if __name__ == "__main__":
    main()
