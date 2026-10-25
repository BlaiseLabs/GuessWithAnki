"""Kana and field text helpers: no Anki imports, so the core runs in tests and from the command line."""
import html
import re

KANJI = re.compile("[㐀-䶿一-鿿豈-﫿々]")
_TAG = re.compile(r"<[^>]+>")
_FURI = re.compile(r"\s?([^\s\[\]]+?)\[([^\]]+)\]")   # Anki's furigana syntax: 漢字[かんじ]
_SOUND = re.compile(r"\[sound:[^\]]*\]")


def hira(s):
    """katakana -> hiragana (the long-vowel mark and other signs are kept)"""
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)


def is_kana(s):
    return bool(s) and all("ぁ" <= c <= "ゖ" or "ァ" <= c <= "ヺ" or c in "ーゝゞヽヾ・" for c in s)


def has_kanji(s):
    return bool(KANJI.search(s or ""))


def kanji_of(s):
    """the distinct kanji of s, in order (々 repeats the one before it, so it is not one of its own)"""
    return list(dict.fromkeys(c for c in s if KANJI.match(c) and c != "々"))


def clean(s):
    """a field's plain text: no HTML, no sound tags, entities decoded, spaces trimmed"""
    s = _SOUND.sub("", s or "")
    s = re.sub(r"<br\s*/?>|<div>|</div>|<p>|</p>", " ", s, flags=re.I)
    return html.unescape(_TAG.sub("", s)).replace("\xa0", " ").strip()


def furigana(s):
    """'会社[かいしゃ]に 行[い]く' -> ('会社に行く', 'かいしゃにいく'); text without brackets comes back as it is"""
    s = clean(s)
    if "[" not in s:
        return s, None
    base = _FURI.sub(lambda m: m.group(1), s).replace(" ", "")
    read = _FURI.sub(lambda m: m.group(2), s).replace(" ", "")
    return base, hira(read)
