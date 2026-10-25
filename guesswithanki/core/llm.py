"""The model end of the spectrum: a model judges, for each word, whether its meaning and its reading follow from its
kanji. Any server with the OpenAI chat API works (Gemma through Ollama by default). Words go in batches; every
batch's labels are stored as it comes back, so a stopped job loses nothing and the next one starts where it ended.
`per_day` caps the words judged per day (big decks can be done 100 a day)."""
import json
import re
import time

from .model import profile

PROMPT = """You are helping a learner of Japanese who already knows the meanings and common readings of individual
kanji. For each word below, judge two things:

1. meaning: could a learner who knows what each kanji means work out what the WORD means?
   "yes"    the word's meaning follows directly from its kanji's meanings combined (e.g. 入口 enter+mouth = entrance)
   "partly" the kanji point in the right direction, but a real leap or extra knowledge is needed
   "no"     the kanji give little or a misleading clue (idiomatic, figurative, ateji, phonetic use)
2. reading: is the word read the way the typical readings of its kanji would suggest?
   "yes"    each kanji uses its most common reading for this kind of word (usual on'yomi in compounds, usual kun'yomi
            for a native word with okurigana); small regular sound changes (small tsu, rendaku) are fine
   "partly" the readings are real readings of these kanji but not the first one a learner would guess
   "no"     irregular or special reading (jukujikun, ateji, a reading the kanji do not normally have)

Use the kanji information given. Be strict but fair; judge as the learner would experience it.
Reply as JSON: {{"words": [{{"w": "<word>", "meaning": "yes|partly|no", "reading": "yes|partly|no",
"why_m": "<at most 12 words>", "why_r": "<at most 12 words>"}}]}}

WORDS
{words}"""


PROMPT_CHINESE = """You are helping a learner of Mandarin Chinese who already knows the meanings and common readings
(pinyin) of individual characters. For each word below, judge two things:

1. meaning: could a learner who knows what each character means work out what the WORD means?
   "yes"    the word's meaning follows directly from its characters' meanings combined (e.g. 电话 electric+speech =
            telephone)
   "partly" the characters point in the right direction, but a real leap or extra knowledge is needed
   "no"     the characters give little or a misleading clue (idiom, transliteration, figurative use)
2. reading: is the word read with the usual readings of its characters?
   "yes"    each character has its most common pronunciation; regular tone sandhi and neutral tones are fine
   "partly" a real but less common reading of a character (a polyphone like 行 hang instead of xing)
   "no"     a reading the characters do not normally have

Use the character information given. Be strict but fair; judge as the learner would experience it.
Reply as JSON: {{"words": [{{"w": "<word>", "meaning": "yes|partly|no", "reading": "yes|partly|no",
"why_m": "<at most 12 words>", "why_r": "<at most 12 words>"}}]}}

WORDS
{words}"""

PROMPT_PARTS = """You are helping a learner of {who}. They learn terms one by one and know the parts they have met before.
For each term below:

1. parts: split the term into the meaningful parts a learner would recognise ({parts}). Give each part in a
   standard dictionary form ({form}) with a short meaning (1-4 words). A term that does not break into at least two
   meaningful parts gets an empty list.
2. meaning: could a learner who knows what each part means work out what the TERM means?
   "yes"    the meaning follows directly from the parts ({example})
   "partly" the parts point in the right direction, but a real leap or extra knowledge is needed
   "no"     the parts give little or a misleading clue (or the term has no parts)

Reply as JSON: {{"words": [{{"w": "<term>", "parts": [{{"p": "<part>", "m": "<meaning>"}}], "meaning": "yes|partly|no",
"why_m": "<at most 12 words>"}}]}}

TERMS
{words}"""

PARTS = {
    "english": dict(who="English (a non-native speaker building vocabulary)",
                    parts="prefixes, roots, suffixes, or the words inside a compound",
                    form="prefixes end with a hyphen like un-, suffixes start with one like -ness, roots and words plain",
                    example="un- + happy + -ness = unhappiness, the state of not being happy"),
    "medical": dict(who="medical terminology (a medical student)",
                    parts="Greek and Latin prefixes, roots or combining forms, and suffixes",
                    form="prefixes like hyper-, roots like cardi, suffixes like -itis; no linking vowels",
                    example="hepat + -itis = inflammation of the liver"),
}


def prompt_for(batch):
    p = profile()
    words = "\n".join(line(it) for it in batch)
    if p.name == "chinese":
        return PROMPT_CHINESE.format(words=words)
    if p.name in PARTS:
        return PROMPT_PARTS.format(words=words, **PARTS[p.name])
    return PROMPT.format(words=words)


LEVEL = {"type": "string", "enum": ["yes", "partly", "no"]}


def schema_for(batch):
    """the answer's JSON schema for one batch: exactly these words, each once (2026-10-24, seen in a Sentry trace:
    with a free-length list, Gemma 4 E4B answered 20 words with one, 60 output tokens, schema-valid)"""
    words = [it.word for it in batch]
    if not profile().reads:
        part = {"type": "object", "required": ["p", "m"], "additionalProperties": False,
                "properties": {"p": {"type": "string"}, "m": {"type": "string"}}}
        item = {"type": "object", "required": ["w", "parts", "meaning", "why_m"], "additionalProperties": False,
                "properties": {"w": {"type": "string", "enum": words}, "parts": {"type": "array", "items": part},
                               "meaning": LEVEL, "why_m": {"type": "string"}}}
        return {"type": "object", "required": ["words"], "additionalProperties": False,
                "properties": {"words": {"type": "array", "items": item, "minItems": len(words), "maxItems": len(words)}}}
    item = {"type": "object", "required": ["w", "meaning", "reading", "why_m", "why_r"], "additionalProperties": False,
            "properties": {"w": {"type": "string", "enum": words}, "meaning": LEVEL, "reading": LEVEL,
                           "why_m": {"type": "string"}, "why_r": {"type": "string"}}}
    return {"type": "object", "required": ["words"], "additionalProperties": False,
            "properties": {"words": {"type": "array", "items": item, "minItems": len(words), "maxItems": len(words)}}}


def line(it):
    p = profile()
    if not p.reads:
        return "- %s = %s" % (it.word, (it.meaning or "")[:140])
    ks = ["%s: %s" % (ch, p.unit_info(ch)) for ch in p.units(it.word)]
    return "- %s (%s) = %s\n    %s" % (it.word, it.reading, (it.meaning or "")[:100], "\n    ".join(ks))


def parse(text, batch, model):
    """the valid labels in an answer. A cut-off answer (2026-10-24: 40 words overflowed Ollama's default 4k context
    and the JSON stopped mid-word, which crashed the whole job) keeps every word object that did come back whole"""
    try:
        got = json.loads(text)
    except ValueError:
        got = {"words": []}
        for m in re.finditer(r"\{[^{}]*\}", text or ""):
            try:
                got["words"].append(json.loads(m.group(0)))
            except ValueError:
                pass
    if not isinstance(got, dict):
        got = {"words": []}
    got = {x.get("w"): x for x in got.get("words", []) if isinstance(x, dict)}
    out = []
    reads = profile().reads
    for it in batch:
        x = got.get(it.word)
        if x and not reads and x.get("meaning") in ("yes", "partly", "no"):
            parts = [[str(q.get("p", "")).strip(), str(q.get("m", "")).strip()] for q in x.get("parts") or []
                     if isinstance(q, dict) and str(q.get("p", "")).strip()]
            out.append({"word": it.word, "reading": it.reading, "meaning_guessable": x["meaning"] if len(parts) >= 2 else "no",
                        "pieces": parts, "why_meaning": x.get("why_m", ""), "source": "llm", "model": model})
            continue
        if x and x.get("meaning") in ("yes", "partly", "no") and x.get("reading") in ("yes", "partly", "no"):
            out.append({"word": it.word, "reading": it.reading, "meaning_guessable": x["meaning"],
                        "reading_guessable": x["reading"], "why_meaning": x.get("why_m", ""),
                        "why_reading": x.get("why_r", ""), "source": "llm", "model": model})
    return out


def todo(items, store, model):
    """the items with kanji no label from this model covers yet, in study order (new cards' next first)"""
    have = {(r["word"], r.get("reading")) for r in store.records if r["source"] == "llm" and r.get("model") == model}
    return [it for it in items if it.has_kanji and (it.word, it.reading) not in have]


def run(items, store, cfg, limit=None, progress=None, tracer=None, cancelled=lambda: False):
    """label up to `limit` words (default: what is left of today's per_day); returns a summary dict"""
    model, size = cfg["model"], int(cfg.get("batch", 20))
    left = int(cfg.get("per_day", 100)) - store.count_today("llm")
    limit = max(0, min(left, limit if limit is not None else left))
    queue = todo(items, store, model)[:limit]
    done = calls = bad = 0
    unread = ""
    tokens = {"in": 0, "out": 0}
    t0 = time.time()
    job = tracer.agent("label words", model) if tracer else None
    for i in range(0, len(queue), size):
        if cancelled():
            break
        batch = queue[i:i + size]
        prompt = prompt_for(batch)
        t = time.time()
        try:
            from .remote import chat
            text, usage = chat(cfg, prompt, schema=schema_for(batch))
        except Exception as e:                                        # noqa: BLE001  (a server error ends the job)
            if job:
                job.chat(model, prompt, "", {}, time.time() - t, error=str(e), batch_size=len(batch))
            bad += len(batch)
            unread = "server error: %s" % str(e)[:200]
            break
        calls += 1
        tokens["in"] += usage.get("prompt_tokens", 0)
        tokens["out"] += usage.get("completion_tokens", 0)
        recs = parse(text, batch, model)
        if job:
            job.chat(model, prompt, text, usage, time.time() - t, batch_size=len(batch), labelled=len(recs),
                     unread=len(batch) - len(recs))
        done += store.add(recs)
        bad += len(batch) - len(recs)
        if len(recs) < len(batch) and not unread:
            unread = (text or "(an empty answer)")[:300]
        if progress:
            progress(min(i + size, len(queue)), len(queue))
    if job:
        job.finish(done=done, failed=bad, calls=calls)
    return {"labelled": done, "failed": bad, "calls": calls, "tokens": tokens, "seconds": round(time.time() - t0, 1),
            "left": len(todo(items, store, model)), "model": model, "unread": unread}
