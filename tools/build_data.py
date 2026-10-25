"""Build the add-on's bundled tables from the EDRDG files in raw/ (KANJIDIC2, JMdict; CC BY-SA 4.0) and check the
aligner against JmdictFurigana (CC BY-SA 4.0).

    python3 tools/build_data.py            writes guesswithanki/data/kanji.json, readings.json, common_words.json

common words = JMdict entries whose kanji spelling carries a priority tag (news1, ichi1, spec1, spec2, gai1), read with
their first reading that applies to that spelling."""
import collections
import gzip
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "raw", ROOT / "guesswithanki" / "data"
sys.path.insert(0, str(ROOT))
PRI = {"news1", "ichi1", "spec1", "spec2", "gai1"}
ATTR = "KANJIDIC2 and JMdict by the Electronic Dictionary Research and Development Group (EDRDG), CC BY-SA 4.0"


def kanjidic():
    out = {}
    for _, el in ET.iterparse(gzip.open(RAW / "kanjidic2.xml.gz")):
        if el.tag != "character":
            continue
        ch = el.findtext("literal")
        rm = el.find("reading_meaning/rmgroup")
        if rm is None:
            el.clear()
            continue
        m = [x.text for x in rm.findall("meaning") if not x.get("m_lang")]
        on = [x.text for x in rm.findall("reading") if x.get("r_type") == "ja_on"]
        kun = [x.text for x in rm.findall("reading") if x.get("r_type") == "ja_kun"]
        f, g = el.findtext("misc/freq"), el.findtext("misc/grade")
        if m or on or kun:
            out[ch] = {"m": m, "on": on, "kun": kun, "f": int(f) if f else None, "g": int(g) if g else None}
        el.clear()
    return out


def jmdict_common():
    """[(spelling, reading, glosses, news frequency band: 1 = the 500 most common, 99 = none)] for the common
    spellings"""
    out = []
    raw = gzip.open(RAW / "JMdict_e.gz").read().decode("utf-8")
    raw = re.sub(r"&([\w-]+);", r"\1", raw)                       # (entity names kept as plain text)
    root = ET.fromstring(raw.split("]>", 1)[1] if "]>" in raw[:400000] else raw)
    for e in root.iter("entry"):
        ks = [(k.findtext("keb"), {p.text for p in k.findall("ke_pri")}) for k in e.findall("k_ele")]
        rs = [(r.findtext("reb"), {x.text for x in r.findall("re_restr")}, r.find("re_nokanji") is not None)
              for r in e.findall("r_ele")]
        gl = [g.text for s in e.findall("sense") for g in s.findall("gloss")][:6]
        for keb, pri in ks:
            if not pri & PRI:
                continue
            reb = next((r for r, restr, nok in rs if not nok and (not restr or keb in restr)), None)
            if reb:
                nf = min((int(p[2:]) for p in pri if p.startswith("nf")), default=99)
                out.append((keb, reb, gl, nf))
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    kd = kanjidic()
    (OUT / "kanji.json").write_text(json.dumps({"source": ATTR, "k": kd}, ensure_ascii=False, separators=(",", ":")),
                                    encoding="utf-8")
    print("kanji: %d" % len(kd))
    from guesswithanki.core import kanjidata
    kanjidata._CACHE.clear()
    from guesswithanki.core.align import split
    from guesswithanki.core.kana import has_kanji
    words = jmdict_common()
    counts, failed = collections.defaultdict(collections.Counter), 0
    for w, r, *_ in words:
        sp = split(w, r)
        if sp is None:
            failed += 1
            continue
        for ch, base in sp:
            counts[ch][base] += 1
    (OUT / "readings.json").write_text(json.dumps({"source": ATTR, "k": counts}, ensure_ascii=False,
                                                  separators=(",", ":")), encoding="utf-8")
    (ROOT / "tools" / "common_words.json").write_text(json.dumps({"source": ATTR, "words": words}, ensure_ascii=False,
                                                      separators=(",", ":")), encoding="utf-8")
    print("common spellings: %d, split: %d, no split (whole-word readings etc.): %d" % (len(words), len(words) - failed, failed))
    # the aligner against JmdictFurigana, over the common words
    fur = {}
    for line in (RAW / "JmdictFurigana.txt").read_text(encoding="utf-8-sig").splitlines():
        p = line.split("|")
        if len(p) == 3:
            fur[p[0], p[1]] = p[2]
    agree = differ = theirs_only = 0
    ex = []
    for w, r, *_ in words:
        f = fur.get((w, r))
        if not f or not has_kanji(w):
            continue
        # JmdictFurigana: '0:かん;1:じ' -> per-kanji surface readings (a range '0-1:きょう' = a whole-word reading)
        parts = [x.split(":") for x in f.split(";") if x]
        whole = any("-" in a for a, _ in parts)
        sp = split(w, r)
        if sp is None:
            theirs_only += not whole
            continue
        if whole:
            differ += 1
            continue
        theirs = {int(a): x for a, x in parts}
        kpos = [i for i, c in enumerate(w) if has_kanji(c)]
        ours = [x for _, _, x in split(w, r, surface=True)]
        if [theirs.get(i) for i in kpos] == ours:
            agree += 1
        else:
            differ += 1
            if len(ex) < 15:
                ex.append((w, r, f, ours))
    print("vs JmdictFurigana: same split %d; different (or they read it as a whole) %d; they split, we do not %d"
          % (agree, differ, theirs_only))
    for e in ex:
        print("   ", e)


if __name__ == "__main__":
    main()
