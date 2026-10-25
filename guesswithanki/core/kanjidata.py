"""The bundled kanji tables (made by tools/build_data.py from KANJIDIC2 and JMdict, EDRDG, CC BY-SA 4.0):

  kanji.json     kanji -> {m: English meanings, on: on'yomi (katakana), kun: kun'yomi (KANJIDIC's 'い.る' form),
                 f: newspaper frequency rank or null, g: school grade or null}
  readings.json  kanji -> {reading: how many common dictionary words read it that way} (readings in their base form,
                 the way core/align.py gives them)"""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"
_CACHE = {}


def _load(name):
    if name not in _CACHE:
        f = DATA / name
        _CACHE[name] = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    return _CACHE[name]


def kanji(ch):
    return _load("kanji.json").get("k", {}).get(ch, {})


def dict_readings(ch):
    return _load("readings.json").get("k", {}).get(ch, {})


def meanings(ch):
    return kanji(ch).get("m") or []
