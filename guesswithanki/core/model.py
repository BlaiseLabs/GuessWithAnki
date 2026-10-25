"""A deck's words as the planner sees them, and the guessability each one ends up with."""
from dataclasses import dataclass, field

from . import profiles
from .labels import combine, key

ACTIVE = {"p": profiles.get("japanese")}


def set_profile(name):
    ACTIVE["p"] = profiles.get(name)
    return ACTIVE["p"]


def profile():
    return ACTIVE["p"]


@dataclass
class Item:
    nid: int
    word: str
    reading: str
    meaning: str = ""
    cids: list = field(default_factory=list)
    new: bool = True              # no card of the note has been studied
    first: float = 0.0            # when the note was first studied (revlog ms), 0 for new notes
    mature: bool = False          # a card of the note has an interval of mature_days or more
    pos: int = 0                  # the note's place in the new queue (its lowest card due), for new notes
    split: list = None
    has_kanji: bool = False       # has units the profile splits into pieces (kanji, characters, word parts)
    parts: dict = None            # (english, medical) part -> its meaning
    key: str = ""
    reading_g: float = None       # combined levels, 0..1 (None: nothing judged it)
    meaning_g: float = None
    sources: dict = None

    def __post_init__(self):
        p = profile()
        self.has_kanji = p.has_units(self.word)
        self.split = p.split(self.word, self.reading) if self.has_kanji else None
        self.key = key(self.word, self.reading)

    @property
    def pieces(self):
        return ["%s:%s" % p if p[1] else p[0] for p in self.split or []]

    def set_parts(self, parts, least=2):
        """(english, medical) the word's parts [(part, meaning)], from a label or the morpheme table (an affix card's
        own forms: least=1); parts are matched across words by the profile's canonical form"""
        p = profile()
        canon = getattr(p, "canon", lambda x: x.lower())
        parts = [(canon(str(a).strip()), str(b).strip()) for a, b in parts or [] if canon(str(a).strip())]
        parts = list(dict(parts).items())
        if len(parts) >= least:
            self.split = [(a, "") for a, _ in parts]
            self.parts = dict(parts)


def judge(items, store, heur, cfg, deck=None):
    """fill each item's reading_g / meaning_g from the stored labels, the labels the deck carries and the heuristic's
    levels"""
    weights = cfg.get("sources", {"crowd": 3, "deck": 3, "llm": 2, "heuristic": 1})
    latest = store.latest() if store else {}
    p = profile()
    for it in items:
        if it.has_kanji and it.split is None and hasattr(p, "is_affix") and p.is_affix(it.word):
            it.set_parts([(a, it.meaning) for a in p.affix_parts(it.word)], least=1)    # (a card for parts itself)
        if it.has_kanji and it.split is None and hasattr(p, "segment"):     # (english, medical: parts a model gave,
            got = [r.get("pieces") for src in ("crowd", "deck", "llm") for r in (latest.get(it.key, {}).get(src) or [])
                   if "pieces" in r]                                        #  else the morpheme table; a label that
            if deck and it.key in deck:                                     #  found no parts keeps the word whole)
                got = [r.get("pieces") for r in deck[it.key] if "pieces" in r] + got
            it.set_parts(next((g for g in got if g), None) if got else p.segment(it.word))
        per = dict(latest.get(it.key, {}))
        if deck and it.key in deck:
            per["deck"] = deck[it.key]
        if it.key in heur:
            r, m = heur[it.key]
            per["heuristic"] = [{"reading_guessable": r, "meaning_guessable": m}]
        it.reading_g, it.meaning_g, it.sources = combine(per, weights)


def guessable(it, cfg):
    """judged guessable in both reading and meaning (the words the path tries to make free)"""
    t = cfg.get("guessable", {})
    return (bool(it.split) and (not profile().reads or (it.reading_g or 0) >= t.get("reading", 0.6))
            and (it.meaning_g or 0) >= t.get("meaning", 0.6))
