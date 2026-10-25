"""A word's kanji, each with the reading it has in that word: the patterns a learner carries from one word to the
next (談 read だん in 相談 and 面談).

    split("相談", "そうだん")  -> [("相", "そう"), ("談", "だん")]
    split("入口", "いりぐち")  -> [("入", "いり"), ("口", "くち")]      (readings come back in their base form)
    split("今日", "きょう")    -> None                                  (a whole-word reading: no kanji-by-kanji split)

Each kanji may take one of its KANJIDIC readings (on'yomi; kun'yomi stem, whole, or as a verb's -masu stem), with
the regular sound changes: rendaku (か->が), h->p (は->ぱ) and gemination (がく->がっ)."""
from .kana import KANJI, hira
from .kanjidata import kanji

DAK = dict(zip("かきくけこさしすせそたちつてとはひふへほ", "がぎぐげござじずぜぞだぢづでどばびぶべぼ"))
HAN = dict(zip("はひふへほ", "ぱぴぷぺぽ"))
I_ROW = dict(zip("うくぐすつぬぶむる", "いきぎしちにびみり"))
_R = {}


def readings(ch, extra=()):
    """ch's readings in hiragana, longest first (ties keep KANJIDIC's order: its first readings are the common ones)"""
    if ch not in _R:
        k = kanji(ch)
        out = [hira(x) for x in k.get("on", [])]
        for x in k.get("kun", []):
            x = x.replace("-", "")
            stem, _, oku = x.partition(".")
            out.append(stem)
            if oku:
                out.append(stem + oku)                       # 入口 いりぐち needs いり; 取消 とりけし
                if oku[-1] in I_ROW:
                    out.append(stem + oku[:-1] + I_ROW[oku[-1]])
                if oku.endswith("る") and len(oku) >= 2:
                    out.append(stem + oku[:-1])              # (ichidan: 受付 うけつけ)
        _R[ch] = sorted(dict.fromkeys(x for x in out if x), key=len, reverse=True)
    return list(dict.fromkeys(list(extra) + _R[ch]))


def _variants(r):
    out = [(r, r)]
    if r[0] in DAK:
        out.append((DAK[r[0]] + r[1:], r))
    if r[0] in HAN:
        out.append((HAN[r[0]] + r[1:], r))
    if len(r) > 1 and r[-1] in "きくちつ":
        out.append((r[:-1] + "っ", r))
        if r[0] in DAK:
            out.append((DAK[r[0]] + r[1:-1] + "っ", r))
    return out


def split(word, reading, surface=False):
    """[(kanji, base reading), ...] in word order, or None (see the module's docstring); surface: (kanji, base reading,
    reading as said in this word)"""
    if not word or not reading or not KANJI.search(word):
        return None
    reading = hira(reading)
    word = hira(word)
    memo = {}

    def go(i, j):
        if (i, j) in memo:
            return memo[i, j]
        if i == len(word):
            res = [] if j == len(reading) else None
        elif not KANJI.match(word[i]):
            res = go(i + 1, j + 1) if reading.startswith(word[i], j) else None
        else:
            res = None
            ch = word[i - 1] if word[i] == "々" and i else word[i]
            for base in readings(ch):
                for said, b in _variants(base):
                    if reading.startswith(said, j):
                        rest = go(i + 1, j + len(said))
                        if rest is not None:
                            res = [(ch, b, said)] + rest
                            break
                if res is not None:
                    break
        memo[i, j] = res
        return res
    res = go(0, 0)
    return res if res is None or surface else [(c, b) for c, b, _ in res]


def pieces(word, reading):
    """the word's patterns as 'kanji:reading' strings (empty when it does not split)"""
    return ["%s:%s" % p for p in split(word, reading) or []]
