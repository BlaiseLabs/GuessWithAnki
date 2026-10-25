"""Reading a deck's words out of an Anki collection and writing the new order back. Takes a Collection (anki pylib),
so it works inside Anki and headless (tests, the command line)."""
from .kana import clean, furigana, has_kanji, hira, is_kana
from .model import Item

GUESS = {
    "word": ["expression", "word", "vocab", "vocabulary", "vocab-kanji", "vocabkanji", "vocabulary-kanji", "kanji",
             "japanese", "term", "単語", "front"],
    "reading": ["reading", "kana", "vocab-kana", "vocabkana", "vocabulary-kana", "hiragana", "furigana",
                "vocab-furigana", "vocabfurigana", "vocabulary-furigana", "word reading", "読み", "yomi"],
    "meaning": ["meaning", "english", "vocab-english", "vocabenglish", "vocabulary-english", "vocab-meaning",
                "vocabmeaning", "definition", "english definition", "word meaning", "glossary", "gloss", "meanings",
                "意味", "back"],
}
HINT = {"word": ("word", "vocab", "expression", "kanji", "term", "front", "単語"),
        "reading": ("reading", "kana", "furigana", "hiragana", "yomi", "読み"),
        "meaning": ("meaning", "english", "definition", "gloss", "translation", "back", "意味")}
NOT = ("sentence", "example", "audio", "sound", "image", "picture", "pitch", "frequency", "freq", "index", "pos",
       "grammar", "caution", "cloze", "additional", "note", "tag", "context", "mnemonic", "story")


def _content(role, vals):
    """the share of sample values that look like the role's content"""
    if not vals:
        return 0.0
    from .model import profile
    p = profile()
    if p.name != "japanese":
        return sum(1 for v in vals if p.content(role, v)) / len(vals)
    ok = 0
    for v in vals:
        base, rd = furigana(v)
        base = base.strip()
        if role == "word":
            ok += (0 < len(base) <= 10 and " " not in base and not any(c in base for c in "。、！？!?")
                   and (has_kanji(base) or is_kana(base)))
        elif role == "reading":
            r = (rd or base).replace(" ", "")
            ok += 0 < len(r) <= 20 and is_kana(r)
        else:
            letters = sum(c.isascii() and c.isalpha() for c in base)
            ok += len(base) >= 2 and letters >= 0.5 * len(base.replace(" ", ""))
    return ok / len(vals)


def detect_fields(names, wanted=None, samples=None):
    """role -> field name for a note type's fields: the setting's names first; otherwise each field is scored by its
    name (common names, hints, and words like 'sentence' or 'audio' against) and, given sample notes ({field: [values]}),
    by what it holds (short Japanese = word, kana = reading, English = meaning)"""
    low = {n.lower(): n for n in names}
    out = {}
    for role in ("word", "reading", "meaning"):
        for c in (wanted or {}).get(role, []):
            if c.lower() in low and low[c.lower()] not in out.values():
                out[role] = low[c.lower()]
                break
    for role in ("word", "reading", "meaning"):
        if role in out:
            continue
        best = None
        for n in names:
            if n in out.values():
                continue
            ln = n.lower()
            sc = 2.0 if ln in GUESS[role] else 1.0 if any(h in ln for h in HINT[role]) else 0.0
            if any(x in ln for x in NOT):
                sc -= 3.0
            if samples is not None:
                c = _content(role, [clean(v) for v in samples.get(n, []) if clean(v)])
                if c < 0.5:
                    continue
                sc += 3.0 * c
            elif sc <= 0:
                continue
            if best is None or sc > best[0]:
                best = (sc, n)
        if best and best[0] > 0:
            out[role] = best[1]
    return out


def word_reading(word_raw, reading_raw):
    """(word, reading) from the fields, whichever way the deck writes them (plain, or 漢字[かんじ] furigana). A reading
    field is used only when it reads this word (kana, or furigana over the same word): some decks keep a sentence
    there"""
    w, wr = furigana(word_raw)
    w = w.strip()
    r = None
    if reading_raw:
        rb, rr = furigana(reading_raw)
        rb = rb.replace(" ", "")
        if rr and rb == w.replace(" ", ""):
            r = rr
        elif not rr and is_kana(rb) and len(rb) <= max(8, 4 * len(w)):
            r = rb
    r = r or wr or (w if is_kana(w) else "")
    r = r.replace(" ", "") if r else ""
    return w, hira(r) if r and is_kana(r) else ""


def collect(col, cfg):
    """the words of the notes matching the setting's search, as Items (new ones and studied ones)"""
    search = cfg.get("search") or ""
    nids = col.find_notes(search)
    if not nids:
        return []
    mature_days = int(cfg.get("mature_days", 21))
    roles = {}
    items = {}
    ids = ",".join(str(n) for n in nids)
    from .model import profile, set_profile
    from .profiles import detect_profile
    if (cfg.get("profile") or "auto") == "auto":                # which kind of deck: from the fields' text
        samples = {}
        for (flds,) in col.db.all("select flds from notes where id in (%s) limit 300" % ids):
            for i, v in enumerate(flds.split("\x1f")):
                samples.setdefault(i, []).append(clean(v))
        set_profile(detect_profile(samples))
    else:
        set_profile(cfg["profile"])
    p = profile()
    for nid, mid, flds in col.db.all("select id, mid, flds from notes where id in (%s)" % ids):
        if mid not in roles:
            nt = col.models.get(mid)
            names = [f["name"] for f in nt["flds"]] if nt else []
            sample = [f.split("\x1f") for f in col.db.list("select flds from notes where mid = ? limit 60", mid)]
            samples = {n: [row[i] for row in sample if i < len(row)] for i, n in enumerate(names)}
            roles[mid] = (names, detect_fields(names, cfg.get("fields"), samples))
        names, r = roles[mid]
        if "word" not in r:
            continue
        vals = dict(zip(names, flds.split("\x1f")))
        word, reading = p.word_reading(vals.get(r["word"], ""), vals.get(r.get("reading"), ""))
        if not word or not p.accept(word):
            continue
        items[nid] = Item(nid=nid, word=word, reading=reading, meaning=clean(vals.get(r.get("meaning"), ""))[:300])
    if not items:
        return []
    ids = ",".join(str(n) for n in items)
    for cid, nid, ctype, queue, ivl, due, ord_ in col.db.all(
            "select id, nid, type, queue, ivl, due, ord from cards where nid in (%s) order by nid, ord" % ids):
        it = items[nid]
        it.cids.append((cid, ctype, queue, due))
        if ctype != 0:
            it.new = False
        if ivl >= mature_days:
            it.mature = True
    for nid, first in col.db.all("select c.nid, min(r.id) from revlog r join cards c on c.id = r.cid "
                                 "where c.nid in (%s) group by c.nid" % ids):
        items[nid].first = first
        items[nid].new = False
    out = []
    for it in items.values():
        news = [c for c in it.cids if c[1] == 0 and c[2] != -1]
        it.pos = min((c[3] for c in news), default=0)
        if it.new and not news:
            continue                                   # (all its cards suspended)
        out.append(it)
    return out


def split_started(items):
    """(studied items oldest first, new items in the deck's order)"""
    started = sorted((it for it in items if not it.new), key=lambda it: it.first or 0)
    new = sorted((it for it in items if it.new), key=lambda it: (it.pos, it.nid))
    return started, new


def reposition(col, order):
    """give the new cards of `order` consecutive queue places from the lowest place they hold now (siblings stay
    together). Returns the number of cards moved, 0 when the order is already in place."""
    cids = [c[0] for it in order for c in it.cids if c[1] == 0 and c[2] != -1]
    if not cids:
        return 0
    have = {c[0]: c[3] for it in order for c in it.cids}
    start = min(have[c] for c in cids)
    if [have[c] for c in cids] == list(range(start, start + len(cids))):
        return 0
    col.sched.reposition_new_cards(card_ids=cids, starting_from=start, step_size=1, randomize=False,
                                   shift_existing=False)
    return len(cids)


def queue_settings(col, items):
    """the deck options of the decks holding these new cards that would ignore the new order (gather/sort by
    something other than position): [(options name, what is wrong)]"""
    out = []
    dids = {d for (d,) in col.db.all("select distinct did from cards where type = 0 and nid in (%s)"
                                     % ",".join(str(it.nid) for it in items))} if items else set()
    seen = set()
    for did in dids:
        conf = col.decks.config_dict_for_deck_id(did)
        if not conf or conf["id"] in seen:
            continue
        seen.add(conf["id"])
        g, s = conf.get("newGatherPriority", 0), conf.get("newSortOrder", 0)
        if g == 2:                                     # (0 deck, 1 lowest position: both follow the order)
            out.append((conf["name"], "new cards are gathered highest position first (the order backwards)"))
        elif g not in (0, 1):
            out.append((conf["name"], "new cards are gathered at random, not by position"))
        if s not in (0, 1):                            # (0 template then position, 1 order gathered)
            out.append((conf["name"], "new cards are sorted at random"))
    return out
