"""Against a real Anki collection (anki pylib): reading the words, the new order written back, the deck options check."""
import json

import pytest

anki = pytest.importorskip("anki")
from anki.collection import Collection  # noqa: E402

from guesswithanki.core import run  # noqa: E402
from guesswithanki.core.ankiio import collect, queue_settings  # noqa: E402

WORDS = [("天気", "てんき", "weather"), ("電車", "でんしゃ", "train"), ("会社", "かいしゃ", "company"),
         ("電気", "でんき", "electricity"), ("社員", "しゃいん", "employee"), ("会議", "かいぎ", "meeting"),
         ("大会", "たいかい", "tournament"), ("気分", "きぶん", "feeling"), ("社会", "しゃかい", "society"),
         ("話す", "はなす", "to speak"), ("会話", "かいわ", "conversation"), ("電話", "でんわ", "telephone")]


@pytest.fixture
def col(tmp_path):
    c = Collection(str(tmp_path / "c.anki2"))
    mm = c.models
    nt = mm.new("Vocab")
    for f in ("Expression", "Reading", "Meaning"):
        mm.add_field(nt, mm.new_field(f))
    t = mm.new_template("Card 1")
    t["qfmt"], t["afmt"] = "{{Expression}}", "{{Reading}} {{Meaning}}"
    mm.add_template(nt, t)
    mm.add(nt)
    nt = mm.by_name("Vocab")
    did = c.decks.id("JP")
    for w, r, m in WORDS:
        n = c.new_note(nt)
        n["Expression"], n["Reading"], n["Meaning"] = w, r, m
        c.add_note(n, did)
    # study the first one (会社 would be third in the deck's order)
    c.decks.select(did)
    q = c.sched.get_queued_cards(fetch_limit=1).cards[0]
    card = c.get_card(q.card.id)
    card.start_timer()
    c.sched.answer_card(c.sched.build_answer(card=card, states=q.states, rating=3))
    yield c
    c.close()


def test_collect_reads_words_and_history(col):
    items = collect(col, run.merged({}))
    assert len(items) == len(WORDS)
    studied = [it for it in items if not it.new]
    assert [it.word for it in studied] == ["天気"]
    assert all(it.reading and it.meaning for it in items)


def test_reorder_writes_the_path_into_the_new_queue(col, tmp_path):
    cfg = {"guessable": {"reading": 0.5, "meaning": 0.0}, "heuristic": {"meaning": "off"},
           "path": {"window": 3, "ahead": 20}}
    s = run.reorder(col, cfg, tmp_path / "files", use_server=False)
    assert s["moved"] > 0 and s["effect"]["after"] >= s["effect"]["before"]
    q = col.sched.get_queued_cards(fetch_limit=5).cards
    queue = [col.get_card(x.card.id).note()["Expression"] for x in q]
    assert queue == [r["word"] for r in s["next"][:5]]        # Anki now serves the planned order
    assert s["effect"]["after"] > s["effect"]["before"]
    assert json.loads((tmp_path / "files" / "last.json").read_text(encoding="utf-8"))["totals"]["words"] == len(WORDS)
    assert run.reorder(col, cfg, tmp_path / "files", use_server=False)["moved"] == 0      # (already in place)


def test_random_gather_order_is_reported(col):
    conf = col.decks.config_dict_for_deck_id(col.decks.id("JP"))
    conf["newGatherPriority"] = 4
    col.decks.update_config(conf)
    items = [it for it in collect(col, run.merged({})) if it.new]
    assert queue_settings(col, items)


def test_fields_found_by_content_when_names_mislead():
    from guesswithanki.core.ankiio import detect_fields
    names = ["Vocabulary-Kanji", "Vocabulary-Kana", "Vocabulary-English", "Expression", "Reading", "Sentence-English"]
    samples = {"Vocabulary-Kanji": ["話", "天気"], "Vocabulary-Kana": ["はなし", "てんき"],
               "Vocabulary-English": ["story", "weather"], "Expression": ["いい話だ。", "天気がいい。"],
               "Reading": ["いい 話[はなし]だ。", "天気[てんき]がいい。"], "Sentence-English": ["A nice story.", "Nice weather."]}
    assert detect_fields(names, samples=samples) == {"word": "Vocabulary-Kanji", "reading": "Vocabulary-Kana",
                                                      "meaning": "Vocabulary-English"}
    assert detect_fields(["Word", "Word Reading", "Word Meaning"], samples={"Word": ["話"], "Word Reading": ["はなし"],
                                                                             "Word Meaning": ["story"]}) == \
        {"word": "Word", "reading": "Word Reading", "meaning": "Word Meaning"}


def test_a_sentence_in_the_reading_field_is_not_taken_as_the_reading():
    from guesswithanki.core.ankiio import word_reading
    assert word_reading("兄[あに]", "兄[あに]はアンです。") == ("兄", "あに")
    assert word_reading("会社", "かいしゃ") == ("会社", "かいしゃ")
    assert word_reading("大空", "大空[おおぞら]") == ("大空", "おおぞら")
    assert word_reading("会社", "会社[かいしゃ]に 行[い]く") == ("会社", "")


def test_labels_the_deck_carries_count_as_the_deck_source(col, tmp_path):
    from guesswithanki.core import embedded
    from guesswithanki.core.model import judge
    from guesswithanki.core.labels import Store
    items = collect(col, run.merged({}))
    by = {it.word: it for it in items}
    note = col.get_note(by["会社"].nid)
    note.tags = ["guesswithanki::reading::yes", "guesswithanki::meaning::no"]
    col.update_note(note)
    embedded.media_file(col).write_text(json.dumps({"schema": "guesswithanki-labels/1", "labels": [
        {"word": "電話", "reading": "でんわ", "reading_guessable": "yes", "meaning_guessable": "yes", "by": "author"}]}),
        encoding="utf-8")
    deck = embedded.read(col, items)
    assert set(deck) == {by["会社"].key, by["電話"].key}
    judge(items, Store(tmp_path / "none.jsonl"), {}, {"sources": {"deck": 1}}, deck)
    assert (by["会社"].reading_g, by["会社"].meaning_g) == (1.0, 0.0) and by["電話"].meaning_g == 1.0


def test_write_into_the_deck_round_trip(col, tmp_path):
    from guesswithanki.core import embedded
    from guesswithanki.core.labels import Store
    items = collect(col, run.merged({}))
    store = Store(tmp_path / "labels.jsonl")
    store.add([{"word": "電気", "reading": "でんき", "reading_guessable": "yes", "meaning_guessable": "partly",
                "source": "crowd", "by": "me"},
               {"word": "天気", "reading": "てんき", "reading_guessable": "no", "meaning_guessable": "yes",
                "source": "llm", "model": "gemma"}])
    n, recs, _ = embedded.write(col, items, store)
    assert n == 2 and recs == 2
    tags = {it.word: col.get_note(it.nid).tags for it in items if it.word in ("電気", "天気")}
    assert set(tags["電気"]) == {"guesswithanki::reading::yes", "guesswithanki::meaning::partly"}
    assert set(tags["天気"]) == {"guesswithanki::reading::no", "guesswithanki::meaning::yes"}
    back = embedded.read(col, items)
    assert {r["by"] for rs in back.values() for r in rs} >= {"tags", "me", "gemma"}
    store.add([{"word": "電気", "reading": "でんき", "reading_guessable": "no", "meaning_guessable": "no",
                "source": "crowd", "by": "me"}])
    embedded.write(col, items, store)                       # (a new vote replaces the old tags)
    assert set(col.get_note([it for it in items if it.word == "電気"][0].nid).tags) == {"guesswithanki::reading::no", "guesswithanki::meaning::no"}


def test_reorder_without_an_embedding_server_still_works(col, tmp_path):
    """(a first user, 2026-10-26: no Ollama on their Mac, Errno 61; the reorder must finish, quickly, and say so calmly)"""
    import time
    cfg = {"guessable": {"reading": 0.5, "meaning": 0.0}, "heuristic": {"meaning": "embeddings"},
           "embeddings": {"base_url": "http://127.0.0.1:9/v1", "model": "x"}, "path": {"window": 3, "ahead": 20}}
    t = time.time()
    s = run.reorder(col, cfg, tmp_path / "files", use_server=True)
    assert time.time() - t < 10
    assert s["moved"] > 0 and s["note"] == run.NO_EMBEDDINGS
    assert "not reachable" not in s["note"] and "Errno" not in s["note"]


def test_the_server_check_is_quick():
    import time
    from guesswithanki.core.remote import reachable
    assert reachable("http://127.0.0.1:9/v1") is False
    t = time.time()
    assert reachable("http://10.255.255.1:11434/v1", timeout=1.0) is False     # (nothing answers at all)
    assert time.time() - t < 2.5
