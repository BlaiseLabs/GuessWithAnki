"""How far a model's labels agree with labels someone already made (a stronger model, a crowd file): runs the
labelling job on a sample of LABELLED.json and compares, per dimension, exact agreement and Cohen's kappa.

    python3 tools/agree.py LABELLED.json --model gemma4:12b-it-qat [--base-url http://127.0.0.1:11434/v1] [--n 200]
                           [--batch 20] [--store work/agree_labels.jsonl] [--sentry-dsn-file F]"""
import argparse
import collections
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from guesswithanki.core import llm, trace  # noqa: E402
from guesswithanki.core.labels import Store  # noqa: E402
from guesswithanki.core.model import Item  # noqa: E402


def kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = collections.Counter(a), collections.Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("labelled")
    ap.add_argument("--model", required=True)
    ap.add_argument("--base-url", default="http://127.0.0.1:11434/v1")
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--batch", type=int, default=20)
    ap.add_argument("--store", default="work/agree_labels.jsonl")
    ap.add_argument("--sentry-dsn-file")
    a = ap.parse_args()
    rows = [r for r in json.loads(Path(a.labelled).read_text(encoding="utf-8"))]
    random.Random(7).shuffle(rows)
    rows = rows[:a.n]
    items = [Item(i, r["word"], r["reading"], r.get("meaning", "")) for i, r in enumerate(rows)]
    store = Store(a.store)
    dsn = Path(a.sentry_dsn_file).read_text().strip() if a.sentry_dsn_file else ""
    res = llm.run(items, store, {"base_url": a.base_url, "model": a.model, "batch": a.batch, "per_day": 100000,
                                 "reasoning_effort": "none"},
                  progress=lambda i, n: print("\r  %d/%d" % (i, n), end="", file=sys.stderr, flush=True),
                  tracer=trace.tracer(dsn))
    print("\n" + json.dumps(res))
    mine = {}
    for r in store.records:
        if r.get("model") == a.model:
            mine[r["word"]] = r
    for dim in ("reading", "meaning"):
        pairs = [(r["%s_guessable" % dim], mine[r["word"]]["%s_guessable" % dim]) for r in rows if r["word"] in mine]
        if not pairs:
            continue
        x, y = zip(*pairs)
        yes = [(p == "yes", q == "yes") for p, q in pairs]
        print("%-8s n=%d  exact %.0f%%  kappa %.2f  | yes/not-yes agree %.0f%%  kappa %.2f  | reference yes %.0f%%, model yes %.0f%%"
              % (dim, len(pairs), 100 * sum(p == q for p, q in pairs) / len(pairs), kappa(x, y),
                 100 * sum(p == q for p, q in yes) / len(yes), kappa([p for p, _ in yes], [q for _, q in yes]),
                 100 * sum(p for p, _ in yes) / len(yes), 100 * sum(q for _, q in yes) / len(yes)))


if __name__ == "__main__":
    main()
