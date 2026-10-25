"""Profiles: what a "piece" of a word is, for each kind of deck. The path (core/path.py), the labels, the dashboard
and the simulations only see pieces; a profile turns a deck's words into them.

  japanese  a kanji + the reading it has in the word (会:かい); KANJIDIC2 meanings, JMdict reading counts
  chinese   a character + the pinyin syllable it has in the word (电:dian4); CC-CEDICT meanings and reading counts
  english   a morpheme: prefix, root or suffix (un-, happy, -ness), or a word inside a compound; meaning only
  medical   a combining form, prefix or suffix (cardi/o, -itis, hyper-); meaning only

A word is guessable when its meaning follows from its pieces' meanings and, for japanese and chinese, its reading
follows from the pieces' usual readings. Japanese and Chinese split words with tables (the reading field says which
reading each character has); English and medical words are split by a model (core/llm.py asks for the parts with
their meanings) or, without one, by the morpheme table (data/morphemes_<profile>.json: the parts and meanings models
gave for the decks this add-on was measured on, longest match first)."""
import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from . import kana

DATA = Path(__file__).resolve().parents[1] / "data"
HAN = re.compile("[㐀-䶿一-鿿豈-﫿]")
LATIN = re.compile(r"^[A-Za-z][A-Za-z\-' ]*[A-Za-z]$|^[A-Za-z]$")
AFFIX = re.compile(r"^-?[A-Za-z]+(?:\([A-Za-z]+\)[A-Za-z]*)?(?:/[A-Za-z]+)?-?$")    # ante-, -itis, ben(e)-, cardi/o


@lru_cache(maxsize=None)
def _json(name):
    f = DATA / name
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


class Profile:
    name = ""
    reads = True                       # a reading/pronunciation dimension is judged
    unit_name = "piece"

    def accept(self, word):             # a term this profile handles
        return False

    def has_units(self, word):
        return False

    def units(self, word):              # the pieces' units in the word, in order (for display and prompts)
        return []

    def split(self, word, reading):     # [(unit, form)] or None
        return None

    def meanings(self, unit):
        return []

    def dict_readings(self, unit):      # {form: count} in a dictionary, or {}
        return {}

    def unit_info(self, unit):
        return ", ".join(self.meanings(unit)[:4]) or "?"

    def word_reading(self, word_raw, reading_raw):
        return kana.clean(word_raw), kana.clean(reading_raw or "")

    def content(self, role, v):         # does a field value look like this role's content?
        if role == "meaning":
            letters = sum(c.isalpha() for c in v)
            return len(v) >= 2 and letters >= 0.5 * len(v.replace(" ", ""))
        return False


# ---------------------------------------------------------------------------------------------------------- japanese
class Japanese(Profile):
    name, unit_name = "japanese", "kanji reading"

    def accept(self, word):
        return 0 < len(word) <= 20 and (kana.has_kanji(word) or kana.is_kana(word))

    def has_units(self, word):
        return kana.has_kanji(word)

    def units(self, word):
        return kana.kanji_of(word)

    def split(self, word, reading):
        from .align import split
        return split(word, reading) if kana.has_kanji(word) and reading else None

    def meanings(self, unit):
        from .kanjidata import meanings
        return meanings(unit)

    def dict_readings(self, unit):
        from .kanjidata import dict_readings
        return dict_readings(unit)

    def unit_info(self, unit):
        from .kanjidata import kanji
        k = kanji(unit)
        return "%s; on %s; kun %s" % (", ".join((k.get("m") or [])[:4]) or "?", "・".join(k.get("on") or []) or "-",
                                       "・".join((k.get("kun") or [])[:10]) or "-")

    def word_reading(self, word_raw, reading_raw):
        from .ankiio import word_reading
        return word_reading(word_raw, reading_raw)

    def content(self, role, v):
        base, rd = kana.furigana(v)
        base = base.strip()
        if role == "word":
            return (0 < len(base) <= 10 and " " not in base and not any(c in base for c in "。、！？!?")
                    and (kana.has_kanji(base) or kana.is_kana(base)))
        if role == "reading":
            r = (rd or base).replace(" ", "")
            return 0 < len(r) <= 20 and kana.is_kana(r)
        return Profile.content(self, role, v)


# ----------------------------------------------------------------------------------------------------------- chinese
TONE = {}
for _v, _marks in (("a", "āáǎà"), ("e", "ēéěè"), ("i", "īíǐì"), ("o", "ōóǒò"), ("u", "ūúǔù"), ("v", "ǖǘǚǜ")):
    for _t, _c in enumerate(_marks, 1):
        TONE[_c] = (_v, _t)


def pinyin_syllables(text, n=None):
    """'diànhuà' / 'dian4 hua4' / 'Diàn huà' -> ['dian4', 'hua4'] (neutral tone 5); n: the number of syllables wanted
    (the characters of the word), which settles splits like xian / xi'an; None when it does not split"""
    s = unicodedata.normalize("NFC", (text or "").lower()).replace("u:", "v").replace("ü", "v")
    letters, tones = [], {}
    for c in s:
        if c in TONE:
            b, t = TONE[c]
            tones[len(letters)] = t
            letters.append(b)
        elif c.isalpha():
            letters.append(c)
        elif c.isdigit() and letters:
            tones[len(letters) - 1] = int(c) if c in "12345" else 5
        elif c in " '’-·":
            letters.append("|")
    S = set(_json("pinyin.json"))
    if not S:
        return None
    seq = "".join(letters)
    best = {0: []}                       # position -> syllables (fewest, or exactly n)
    for i in range(len(seq) + 1):
        if i not in best:
            continue
        if i < len(seq) and seq[i] == "|":
            if i + 1 not in best or len(best[i]) < len(best[i + 1]):
                best[i + 1] = best[i]
            continue
        for j in range(i + 1, min(len(seq), i + 6) + 1):
            if "|" in seq[i:j] or seq[i:j] not in S:
                continue
            cand = best[i] + [(i, j)]
            if j not in best or len(cand) < len(best[j]):
                best[j] = cand
    spans = best.get(len(seq))
    if spans is None or (n is not None and len(spans) != n):
        return None
    out = []
    for i, j in spans:
        t = next((tones[k] for k in range(i, j) if k in tones), 5)
        out.append("%s%d" % (seq[i:j], t))
    return out


class Chinese(Profile):
    name, unit_name = "chinese", "character reading"

    def accept(self, word):
        return 0 < len(word) <= 12 and bool(HAN.search(word)) and not any(kana.is_kana(c) for c in word)

    def has_units(self, word):
        return bool(HAN.search(word))

    def units(self, word):
        return list(dict.fromkeys(c for c in word if HAN.match(c)))

    def split(self, word, reading):
        chars = [c for c in word if HAN.match(c)]
        if not chars or not reading or len(chars) != len([c for c in word if not c.isspace()]):
            return None
        ps = pinyin_syllables(reading, len(chars))
        if not ps and chars[-1] == "儿":                    # (erhua: 一点儿 yìdiǎnr)
            ps = pinyin_syllables(reading, len(chars) - 1)
            ps = ps + ["er5"] if ps else None
        return list(zip(chars, ps)) if ps else None

    def meanings(self, unit):
        return (_json("hanzi.json").get(unit) or {}).get("m") or []

    def dict_readings(self, unit):
        r = (_json("hanzi.json").get(unit) or {}).get("r") or {}
        return r

    def unit_info(self, unit):
        h = _json("hanzi.json").get(unit) or {}
        return "%s; read %s" % (", ".join((h.get("m") or [])[:4]) or "?", " / ".join(list((h.get("r") or {}))[:4]) or "-")

    def word_reading(self, word_raw, reading_raw):
        w = re.sub(r"[\s（）()\[\]]", "", kana.clean(word_raw))
        w = w.split("|")[0].split("/")[0].split("，")[0]
        return w, kana.clean(reading_raw or "")

    def content(self, role, v):
        v = kana.clean(v)
        if role == "word":
            return 0 < len(v) <= 8 and all(HAN.match(c) for c in v.replace(" ", ""))
        if role == "reading":
            return 0 < len(v) <= 40 and pinyin_syllables(v) is not None and any(c in TONE or c.isdigit() for c in v)
        return Profile.content(self, role, v)


# ------------------------------------------------------------------------------------------------- english, medical
class Latin(Profile):
    """morphemes found by a model, or by the table of the parts models found (longest match first)"""
    reads = False
    unit_name = "word part"
    table = ""

    def accept(self, word):
        return 0 < len(word) <= 40 and (bool(LATIN.match(word)) and len(word.split()) <= 3 or self.is_affix(word))

    def has_units(self, word):
        return self.accept(word)

    def is_affix(self, word):
        """a card for a word part itself (ante-, -itis, cardi/o; alternatives after a comma: 'ced-, cess-, -cede'):
        it teaches its parts, and is no word to guess"""
        first = re.split(r"[,;]\s*|\s+\(", word)[0].strip()
        return bool(AFFIX.match(first)) and any(c in first for c in "-/(") and not first.isupper()

    def affix_parts(self, word):
        """an affix card's forms: 'ced-, cess-, -cede' -> ['ced-', 'cess-', '-cede']"""
        out = []
        for a in re.split(r"[,;]\s*|\s+\(", word):
            a = a.strip()
            a = a.rstrip(")") if a.count(")") > a.count("(") else a.lstrip("(") if a.count("(") > a.count(")") else a
            if a and a != "etc." and AFFIX.match(a):
                out.append(a)
        return out

    def canon(self, part):
        """the form a part is matched by across words: lower case, no optional letters (ben(e)- -> ben), a suffix
        keeps its hyphen (-or, an ending, is not or-, the mouth); prefixes and roots lose theirs (decks write roots
        both ways: cerebr-, cerebr)"""
        suffix = part.strip().startswith("-")
        core = re.sub(r"[^a-z]", "", re.sub(r"\([a-z]*\)|/[a-z]*", "", part.lower()))
        core = self._core(core)
        return ("-" + core) if suffix and core else core

    def _core(self, core):
        return core

    def _table(self):
        return _json(self.table)

    def units(self, word):
        return [u for u, _ in (self.segment(word) or [])]

    def segment(self, word):
        """[(part, meaning)] by the morpheme table: the fewest known parts that spell the word, a word left whole
        when it does not split into at least two (None)"""
        T = self._table()
        w = word.lower().replace(" ", "").replace("-", "")
        if not T or len(w) < 4:
            return None
        keys = {}
        for k, m in T.items():
            keys.setdefault(k.strip("-").replace("/", "").lower(), (k, m))
        best = {0: []}
        for i in range(len(w)):
            if i not in best:
                continue
            for j in range(i + 2, len(w) + 1):
                s = w[i:j]
                if s in keys:
                    cand = best[i] + [keys[s]]
                    if j not in best or len(cand) < len(best[j]):
                        best[j] = cand
        parts = best.get(len(w))
        return parts if parts and len(parts) >= 2 else None

    def split(self, word, reading):
        return None                     # (from the labels a model made, else the table: model.judge)

    def meanings(self, unit):
        m = self._table().get(unit)
        return [m] if m else []

    def word_reading(self, word_raw, reading_raw):
        w = re.sub(r"\s+", " ", kana.clean(word_raw)).strip()
        if self.is_affix(w):
            return w, ""
        w = re.split(r"[(\[;,/]", w)[0].strip()
        return w, ""

    def content(self, role, v):
        v = kana.clean(v)
        if role == "word":
            return self.accept(v)
        if role == "reading":
            return False
        return len(v) >= 2 and v.lower() != v.upper() or bool(re.search(r"[^\x00-\x7f]", v))


class English(Latin):
    name, table = "english", "morphemes_english.json"


class Medical(Latin):
    name, table = "medical", "morphemes_medical.json"

    def _core(self, core):
        """and no linking vowel at the end (cardi/o, cardio, cardi -> card; hepat(o)-, hepato -> hepat)"""
        while len(core) > 3 and core[-1] in "aeiou":
            core = core[:-1]
        return core


PROFILES = {p.name: p for p in (Japanese(), Chinese(), English(), Medical())}
MEDICAL_HINTS = re.compile(r"(itis|osis|ectomy|otomy|ostomy|algia|emia|aemia|plasty|scopy|pathy|logy|megaly|"
                           r"cardi|hepat|nephr|neur|gastr|derm|hemat|haemat|oste|arthr|cyt|pneum|encephal|myo|"
                           r"hyper|hypo|tachy|brady|dys|leuk|erythr|angi|phleb|thromb|carcin|lymph|cholecyst)", re.I)


def get(name):
    return PROFILES.get(name) or PROFILES["japanese"]


def detect(words):
    """the profile a list of word-field values fits best"""
    words = [kana.clean(w) for w in words if w and kana.clean(w)]
    if not words:
        return "japanese"
    n = len(words)
    jp = sum(1 for w in words if any(kana.is_kana(c) for c in w))
    zh = sum(1 for w in words if HAN.search(w) and not any(kana.is_kana(c) for c in w))
    la = sum(1 for w in words if PROFILES["english"].accept(w))
    if jp >= 0.15 * n and jp + zh >= la:
        return "japanese"
    if zh >= la:
        return "chinese"
    med = sum(1 for w in words if MEDICAL_HINTS.search(w))
    return "medical" if med >= 0.2 * la else "english"


def detect_profile(samples):
    """the profile for a deck, from sample values of each field ({field: [values]}): Japanese when a field reads as
    Japanese words, Chinese when one holds Chinese words, else English or medical by the word field's terms"""
    best = {}
    for name in ("japanese", "chinese", "english"):
        p = PROFILES[name]
        best[name] = max((sum(1 for v in vals if v and p.content("word", v)) / max(1, sum(1 for v in vals if v)), f)
                         for f, vals in samples.items()) if samples else (0, None)
    if best["japanese"][0] >= 0.5 and any(any(kana.is_kana(c) for c in v) for vals in samples.values() for v in vals):
        return "japanese"
    if best["chinese"][0] >= 0.5:
        return "chinese"
    if best["english"][1] is None:
        return "japanese"
    return detect(samples[best["english"][1]])
