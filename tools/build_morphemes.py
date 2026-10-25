"""The morpheme tables the english and medical profiles split words with when no model has labelled them:
guesswithanki/data/morphemes_<profile>.json, part -> its meaning, from the parts a model gave in labels.jsonl files
(a part counts when two or more labelled words use it; its most given meaning is kept).

    python3 tools/build_morphemes.py PROFILE LABELS.jsonl [LABELS.jsonl ...]"""
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    prof, files = sys.argv[1], sys.argv[2:]
    uses, means = collections.Counter(), collections.defaultdict(collections.Counter)
    for f in files:
        for line in Path(f).read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            for p, m in r.get("pieces") or []:
                p = p.strip().lower()
                if len(p.strip("-")) >= 2:
                    uses[p] += 1
                    means[p][m.strip().lower()] += 1
    table = {p: means[p].most_common(1)[0][0] for p, n in uses.items() if n >= 2}
    out = ROOT / "guesswithanki" / "data" / ("morphemes_%s.json" % prof)
    out.write_text(json.dumps(dict(sorted(table.items())), ensure_ascii=False, indent=0), encoding="utf-8")
    print("%s: %d parts (of %d seen) -> %s" % (prof, len(table), len(uses), out))


if __name__ == "__main__":
    main()
