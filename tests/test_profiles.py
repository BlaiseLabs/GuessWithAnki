"""The profiles: Chinese characters with pinyin, English and medical words split into parts, and which profile a deck
gets; the path works on any profile's pieces."""
import json

from guesswithanki.core import llm, model, profiles
from guesswithanki.core.path import count_guessable, plan
from guesswithanki.core.profiles import detect, detect_profile, pinyin_syllables


def test_pinyin_splits_every_way_decks_write_it():
    assert pinyin_syllables("diànhuà", 2) == ["dian4", "hua4"]
    assert pinyin_syllables("dian4 hua4", 2) == ["dian4", "hua4"]
    assert pinyin_syllables("Xī'ān", 2) == ["xi1", "an1"]          # (the apostrophe keeps xi + an apart)
    assert pinyin_syllables("nǚ'ér", 2) == ["nv3", "er2"]
    assert pinyin_syllables("diànhuà", 3) is None                   # (not as many syllables as characters)


def test_chinese_words_split_into_character_readings():
    zh = profiles.get("chinese")
    assert zh.split("电话", "diànhuà") == [("电", "dian4"), ("话", "hua4")]
    assert zh.split("银行", "yínháng") == [("银", "yin2"), ("行", "hang2")]
    assert zh.dict_readings("行")["xing2"] > zh.dict_readings("行")["hang2"]   # (行 is xing2 more often)
    assert "electricity" in zh.meanings("电")


def test_which_profile_a_deck_gets():
    assert detect(["电话", "银行", "学生"]) == "chinese"
    assert detect(["会社", "たべる"]) == "japanese"
    assert detect(["happy", "unhappiness", "teacher"]) == "english"
    assert detect(["cardiomyopathy", "hepatitis", "nephrology", "artery"]) == "medical"
    assert detect_profile({0: ["电话", "银行"], 1: ["diànhuà", "yínháng"], 2: ["telephone", "bank"]}) == "chinese"
    assert detect_profile({0: ["会社", "電車"], 1: ["かいしゃ", "でんしゃ"], 2: ["company", "train"]}) == "japanese"


def test_latin_words_split_by_the_morpheme_table(monkeypatch):
    table = {"un-": "not", "happy": "glad", "-ness": "state", "kind": "nice"}
    monkeypatch.setattr(profiles, "_json", lambda name: table if "morphemes" in name else {})
    en = profiles.get("english")
    assert en.segment("unhappiness") is None or [p for p, _ in en.segment("unhappiness")] != []
    assert [p for p, _ in en.segment("unkindness")] == ["un-", "kind", "-ness"]
    assert en.segment("kind") is None                               # (one part is not a split)


def test_model_parts_become_pieces_and_reading_is_not_asked():
    model.set_profile("medical")
    it = model.Item(nid=1, word="hepatitis", reading="", meaning="inflammation of the liver")
    batch = [it]
    schema = llm.schema_for(batch)
    props = schema["properties"]["words"]["items"]["properties"]
    assert "parts" in props and "reading" not in props
    text = json.dumps({"words": [{"w": "hepatitis", "parts": [{"p": "hepat", "m": "liver"}, {"p": "-itis", "m": "inflammation"}],
                                  "meaning": "yes", "why_m": "liver + inflammation"}]})
    rec = llm.parse(text, batch, "m")[0]
    assert rec["pieces"] == [["hepat", "liver"], ["-itis", "inflammation"]] and rec["meaning_guessable"] == "yes"
    it.set_parts(rec["pieces"])
    it.meaning_g = 1.0
    assert it.pieces == ["hepat", "-itis"] and model.guessable(it, {"guessable": {"reading": 0.6, "meaning": 0.6}})
    model.set_profile("japanese")


def test_the_path_works_on_word_parts():
    model.set_profile("english")
    words = [("unkind", [("un-", "not"), ("kind", "nice")]), ("kindness", [("kind", "nice"), ("-ness", "state")]),
             ("unhappy", [("un-", "not"), ("happy", "glad")]), ("happiness", [("happy", "glad"), ("-ness", "state")]),
             ("unkindness", [("un-", "not"), ("kind", "nice"), ("-ness", "state")])]
    items = []
    for i, (w, parts) in enumerate(words):
        it = model.Item(nid=i, word=w, reading="", meaning=w)
        it.set_parts(parts)
        items.append(it)
    full = {"unkindness|"}                                          # (only the long word is judged guessable)
    order, _ = plan([], items, full, {"window": 40, "ahead": 10, "setup": 0.1})
    assert order[-1].word == "unkindness" or count_guessable([], order, full, {"window": 40}) == 1
    assert count_guessable([], order, full, {"window": 40}) == 1    # (it arrives after un-, kind and -ness)
    model.set_profile("japanese")


def test_affix_cards_teach_their_parts():
    med = profiles.get("medical")
    for w in ("ante-", "-itis", "ben(e)-", "cardi/o", "ced-, cess-, -cede", "in- (il-, im-, ir-, etc.) (1)"):
        assert med.is_affix(w) and med.accept(w), w
    for w in ("Latin", "x-ray", "hepatitis", "latior, latius", "V/A"):
        assert not med.is_affix(w), w
    assert med.affix_parts("ced-, cess-, -cede") == ["ced-", "cess-", "-cede"]
    assert med.affix_parts("ben(e)-") == ["ben(e)-"] and med.affix_parts("-ped(e)") == ["-ped(e)"] and med.affix_parts("ab- (a-, abs-)") == ["ab-", "a-", "abs-"]
    assert med.canon("cardi/o") == med.canon("cardio") == med.canon("cardi") == "card"
    assert med.canon("ben(e)-") == med.canon("bene-") == "ben" and med.canon("-itis") == "-itis"
    assert med.canon("-or") != med.canon("or-")
    model.set_profile("medical")
    card = model.Item(nid=1, word="cortic-, cortico-, cort-", reading="", meaning="bark, outer layer")
    model.judge([card], None, {}, {"sources": {}})
    assert card.pieces == ["cortic", "cort"] and not model.guessable(card, {"guessable": {"meaning": 0.6}})
    word = model.Item(nid=2, word="hepatitis", reading="", meaning="")
    word.set_parts([("hepat/o", "liver"), ("-itis", "inflammation")])
    assert word.pieces == ["hepat", "-itis"]
    assert llm.todo([card, word], type("S", (), {"records": []})(), "m") == [word]
    model.set_profile("japanese")


def test_korean_decks_are_detected_and_split_with_their_hanja():
    assert detect(["학교", "학생", "먹다", "눈물"]) == "korean"
    assert detect_profile({0: ["학교", "학생", "먹다"], 1: ["school", "student", "to eat"]}) == "korean"
    ko = profiles.get("korean")
    assert ko.accept("학교") and ko.accept("공부하다") and not ko.accept("school") and not ko.accept("学校")
    assert ko.canon("학 (學)") == "학(學)" and ko.canon("-하다") == "-하다"
    assert ko.canon("학(學)") != ko.canon("학(鶴)")             # (one syllable, two characters: two pieces)
    assert ko.word_reading("학교 (學校)", "") == ("학교", "")


def test_korean_labels_name_each_syllables_hanja():
    model.set_profile("korean")
    it = model.Item(nid=1, word="학교", reading="", meaning="school")
    schema = llm.schema_for([it])
    part = schema["properties"]["words"]["items"]["properties"]["parts"]["items"]["properties"]
    assert set(part) == {"p", "h", "m"}
    assert "Hanja" in llm.prompt_for([it])
    text = json.dumps({"words": [{"w": "학교", "parts": [{"p": "학", "h": "學", "m": "study"}, {"p": "교", "h": "校", "m": "school"}],
                                  "meaning": "yes", "why_m": "study + school building"}]})
    rec = llm.parse(text, [it], "m")[0]
    assert rec["pieces"] == [["학(學)", "study"], ["교(校)", "school"]] and rec["meaning_guessable"] == "yes"
    it.set_parts(rec["pieces"])
    it.meaning_g = 1.0
    assert it.pieces == ["학(學)", "교(校)"] and model.guessable(it, {"guessable": {"reading": 0.6, "meaning": 0.6}})
    model.set_profile("japanese")


def test_the_path_brings_in_korean_parts_first():
    model.set_profile("korean")
    words = [("학교", [("학(學)", "study"), ("교(校)", "school")]), ("학생", [("학(學)", "study"), ("생(生)", "life")]),
             ("교실", [("교(校)", "school"), ("실(室)", "room")])]
    items = []
    for i, (w, parts) in enumerate(words):
        it = model.Item(nid=i, word=w, reading="", meaning=w)
        it.set_parts(parts)
        items.append(it)
    order, _ = plan([], items, {"학교|"}, {"window": 40, "ahead": 10, "setup": 0.1})
    assert order[-1].word == "학교"                                  # (after 학생 and 교실 bring in 학 and 교)
    assert count_guessable([], order, {"학교|"}, {"window": 40}) == 1
    model.set_profile("japanese")
