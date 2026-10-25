"""Chinese data for the chinese profile, from CC-CEDICT (MDBG, CC BY-SA 4.0; raw/cedict.txt.gz):
  guesswithanki/data/hanzi.json   character -> {"m": its meanings (from its one-character entries),
                                                "r": {pinyin syllable with tone number: words of CEDICT using it}}
  guesswithanki/data/pinyin.json  every pinyin syllable CEDICT writes (no tone), for splitting a pinyin field
    python3 tools/build_hanzi.py"""
import collections
import gzip
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINE = re.compile(r"^(\S+) (\S+) \[([^\]]+)\] /(.*)/$")
HAN = re.compile("[㐀-䶿一-鿿]")


def main():
    reads = collections.defaultdict(collections.Counter)
    means = collections.defaultdict(list)
    sylls = set()
    for line in gzip.open(ROOT / "raw" / "cedict.txt.gz", "rt", encoding="utf-8"):
        if line.startswith("#"):
            continue
        m = LINE.match(line.strip())
        if not m:
            continue
        trad, simp, py, gl = m.groups()
        ps = py.lower().replace("u:", "v").split()
        for s in ps:
            b = re.sub(r"\d", "", s)
            if b.isalpha():
                sylls.add(b)
        for form in {trad, simp}:
            if len(form) != len(ps):
                continue                                  # (words with letters or erhua merged: skip)
            for ch, s in zip(form, ps):
                if HAN.match(ch):
                    reads[ch][s] += 1
            if len(form) == 1 and HAN.match(form):
                for g in gl.split("/"):
                    g = re.sub(r"\(.*?\)|\[.*?\]", "", g).strip()
                    if g and not g.startswith(("variant of", "old variant", "surname", "CL:", "see ", "used in")) and g not in means[form]:
                        means[form].append(g)
    data = {ch: {"m": means.get(ch, [])[:6], "r": dict(r.most_common(8))} for ch, r in reads.items()}
    out = ROOT / "guesswithanki" / "data"
    (out / "hanzi.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (out / "pinyin.json").write_text(json.dumps(sorted(sylls)), encoding="utf-8")
    print("%d characters, %d syllables" % (len(data), len(sylls)))
    for ch in "电话银行学":
        print(ch, data[ch])


if __name__ == "__main__":
    main()
