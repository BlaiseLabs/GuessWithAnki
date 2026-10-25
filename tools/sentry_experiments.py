"""The labelling job under several settings, on the same words, each run traced to Sentry with an `experiment` tag:
what the model does with thinking on or off, with or without a JSON schema, at different batch sizes, and two Gemma
sizes. Each run's labels are compared with reference labels (LABELLED.json, e.g. a stronger model's).

    python3 tools/sentry_experiments.py LABELLED.json --dsn-file F --out DIR [--n 100] [--only name ...]"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from guesswithanki.core import llm, trace  # noqa: E402
from guesswithanki.core.labels import Store  # noqa: E402
from guesswithanki.core.model import Item  # noqa: E402

BASE = {"base_url": "http://127.0.0.1:11434/v1", "model": "gemma4:12b-it-qat", "batch": 20, "per_day": 100000,
        "reasoning_effort": "none", "json_schema": True}
RUNS = [  # (name, settings, words)
    ("thinking-on", {"reasoning_effort": "", "json_schema": False}, 20),
    ("no-schema", {"json_schema": False}, None),
    ("schema", {}, None),
    ("batch-10", {"batch": 10}, None),
    ("batch-40", {"batch": 40}, None),
    ("e4b", {"model": "gemma4:e4b-it-qat"}, None),
    ("e4b-batch-40", {"model": "gemma4:e4b-it-qat", "batch": 40}, None),
]


def agreement(rows, recs):
    got = {r["word"]: r for r in recs}
    out = {}
    for dim in ("reading", "meaning"):
        pairs = [(r["%s_guessable" % dim] == "yes", got[r["word"]]["%s_guessable" % dim] == "yes") for r in rows if r["word"] in got]
        out[dim] = round(100 * sum(a == b for a, b in pairs) / len(pairs), 1) if pairs else None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("labelled")
    ap.add_argument("--dsn-file", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args()
    rows = json.loads(Path(a.labelled).read_text(encoding="utf-8"))
    random.Random(11).shuffle(rows)
    rows = rows[:a.n]
    dsn = Path(a.dsn_file).read_text().strip()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%m%d%H%M")
    results = json.loads((out / "results.json").read_text()) if (out / "results.json").exists() else {}
    for name, over, n in RUNS:
        if a.only and name not in a.only:
            continue
        cfg = dict(BASE, **over)
        part = rows[:n] if n else rows
        items = [Item(i, r["word"], r["reading"], r.get("meaning", "")) for i, r in enumerate(part)]
        store = Store(out / ("%s_%s.jsonl" % (name, stamp)))
        tr = trace.tracer(dsn, tags={"experiment": name, "model": cfg["model"], "batch": str(cfg["batch"])})
        print("== %s: %d words, %s" % (name, len(items), {k: v for k, v in over.items()}), flush=True)
        res = llm.run(items, store, cfg, tracer=tr,
                      progress=lambda i, n_: print("   %d/%d" % (i, n_), flush=True))
        recs = [r for r in store.records if r["source"] == "llm"]
        tok = res["tokens"]
        row = {"words": len(items), "labelled": res["labelled"], "unread": res["failed"], "calls": res["calls"],
               "seconds": res["seconds"], "s_per_word": round(res["seconds"] / max(1, len(items)), 2),
               "tokens_in_per_word": round(tok["in"] / max(1, len(items)), 1),
               "tokens_out_per_word": round(tok["out"] / max(1, len(items)), 1),
               "agree": agreement(part, recs), "sentry_sent": tr.sent, "sentry_error": tr.last_error,
               "settings": over}
        results[name] = row
        print("   ", json.dumps(row), flush=True)
        (out / "results.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    print("\n%-14s %6s %6s %8s %8s %8s %8s %8s" % ("run", "words", "unread", "s/word", "in/word", "out/word", "read%", "mean%"))
    for name, r in results.items():
        print("%-14s %6d %6d %8.2f %8.1f %8.1f %8s %8s" % (name, r["words"], r["unread"], r["s_per_word"], r["tokens_in_per_word"],
                                                          r["tokens_out_per_word"], r["agree"]["reading"], r["agree"]["meaning"]))


if __name__ == "__main__":
    main()
