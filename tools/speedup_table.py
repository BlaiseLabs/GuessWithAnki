"""The README's speed-up table from tools/fsrs_sim.py results: for each deck and guess rate, the cards a learner has to
learn (words started minus the ones guessed right on first sight) to reach n words, in the deck's own order and in
GuessWithAnki's; speed-up = deck's cards / GuessWithAnki's.

    python3 tools/speedup_table.py "Deck name=sim.json" ... [--n 100 500 1000 2000] [--setup anki-default-90]
                                   [--seen 1] [--sighting reviews] [--pace steady] [--json out.json]"""
import argparse
import json
from pathlib import Path


def rows(sim, ns, setup, seen, sighting, pace):
    res, out = sim["results"], []
    rates = sorted({float(k.split("|")[3]) for k in res}, reverse=True)
    for rate in rates:
        cells = []
        for n in ns:
            d = res.get("deck|%s|%d|%s|%s|%s" % (setup, seen, rate, sighting, pace))
            g = next((res[k] for k in ("%s|%s|%d|%s|%s|%s" % (p, setup, seen, rate, sighting, pace) for p in ("guesswithanki", "guesswithkanji", "guesspath")) if k in res), None)
            fd, fg = (d or {}).get("free_at", {}).get(str(n)), (g or {}).get("free_at", {}).get(str(n))
            if fd is None or fg is None or n > sim["words"]:
                cells.append(None)
            else:
                a, b = n - fd, n - fg
                cells.append((round(a), round(b), a / b if b else float("inf")))
        out.append((rate, cells))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("decks", nargs="+", help='"Deck name=sim.json"')
    ap.add_argument("--n", type=int, nargs="+", default=[100, 500, 1000, 2000])
    ap.add_argument("--setup", default="anki-default-90")
    ap.add_argument("--seen", type=int, default=1)
    ap.add_argument("--sighting", default="reviews")
    ap.add_argument("--pace", default="steady")
    ap.add_argument("--json")
    a = ap.parse_args()
    print("| Deck | Guess rate | " + " | ".join("%s words" % format(n, ",") for n in a.n) + " |")
    print("|---|---|" + "---|" * len(a.n))
    dump = {}
    for spec in a.decks:
        name, f = spec.split("=", 1)
        sim = json.loads(Path(f).read_text(encoding="utf-8"))
        rs = rows(sim, a.n, a.setup, a.seen, a.sighting, a.pace)
        dump[name] = {"words": sim["words"], "judged_guessable": sim["judged_guessable"],
                      "rows": {str(r): c for r, c in rs}}
        for i, (rate, cells) in enumerate(rs):
            head = "%s (%s words, %s guessable)" % (name, format(sim["words"], ","), format(sim["judged_guessable"], ",")) if i == 0 else ""
            print("| %s | %d%% | %s |" % (head, round(100 * rate), " | ".join(
                "–" if c is None else "**%.1f×** (%s → %s)" % (c[2], format(c[0], ","), format(c[1], ",")) for c in cells)))
    if a.json:
        Path(a.json).write_text(json.dumps(dump, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
