"""The core without Anki: alignment, labels, heuristic levels, the path, the model's answers, tracing."""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from guesswithanki.core import heuristic, llm, trace
from guesswithanki.core.align import split
from guesswithanki.core.kana import furigana
from guesswithanki.core.labels import Store, combine
from guesswithanki.core.model import Item
from guesswithanki.core.path import count_guessable, plan


def test_split_gives_each_kanji_its_reading_with_sound_changes():
    assert split("相談", "そうだん") == [("相", "そう"), ("談", "だん")]
    assert split("学校", "がっこう") == [("学", "がく"), ("校", "こう")]          # gemination
    assert split("入口", "いりぐち") == [("入", "いり"), ("口", "くち")]          # masu stem + rendaku
    assert split("受付", "うけつけ") == [("受", "うけ"), ("付", "つけ")]
    assert split("食べる", "たべる") == [("食", "た")]
    assert split("今日", "きょう") is None                                      # a whole-word reading


def test_furigana_field():
    assert furigana("会社[かいしゃ]に 行[い]く") == ("会社に行く", "かいしゃにいく")
    assert furigana("<b>会社</b>") == ("会社", None)


def test_store_keeps_latest_per_person_and_averages_people(tmp_path):
    s = Store(tmp_path / "l.jsonl")
    s.add([{"word": "入口", "reading": "いりぐち", "meaning_guessable": "no", "source": "crowd", "by": "a"}])
    s.add([{"word": "入口", "reading": "いりぐち", "meaning_guessable": "yes", "source": "crowd", "by": "a"},
           {"word": "入口", "reading": "いりぐち", "meaning_guessable": "partly", "source": "crowd", "by": "b"},
           {"word": "x", "source": "crowd"}])                                   # (no level: refused)
    latest = Store(tmp_path / "l.jsonl").latest()["入口|いりぐち"]
    assert len(latest["crowd"]) == 2
    r, m, parts = combine(latest, {"crowd": 1})
    assert r is None and m == 0.75


def test_export_import_round_trip(tmp_path):
    a = Store(tmp_path / "a.jsonl")
    a.add([{"word": "出口", "reading": "でぐち", "reading_guessable": "yes", "meaning_guessable": "yes", "source": "crowd", "by": "a"}])
    a.export(tmp_path / "share.json")
    b = Store(tmp_path / "b.jsonl")
    assert b.import_((tmp_path / "share.json").read_text(encoding="utf-8")) == 1
    assert b.import_((tmp_path / "share.json").read_text(encoding="utf-8")) == 0          # nothing twice


def test_crowd_outweighs_heuristic():
    per = {"heuristic": [{"reading_guessable": 1.0, "meaning_guessable": 1.0}],
           "crowd": [{"reading_guessable": "no", "meaning_guessable": "no"}]}
    r, m, _ = combine(per, {"crowd": 3, "llm": 2, "heuristic": 1})
    assert r == m == 0.25


def test_reading_level_prefers_the_usual_reading():
    a, b = Item(1, "会社", "かいしゃ"), Item(2, "会釈", "えしゃく")              # 会: かい (usual) vs え (rare)
    cfg = {"reading_from": "dictionary", "reading_full": 0.05}
    assert heuristic.reading_score(a, {}, cfg) == 1.0
    assert heuristic.reading_score(b, {}, cfg) < heuristic.reading_score(a, {}, cfg)


def _items():
    ws = [("会社", "かいしゃ"), ("社員", "しゃいん"), ("会議", "かいぎ"), ("議員", "ぎいん"), ("天気", "てんき"),
          ("電気", "でんき"), ("電話", "でんわ"), ("会話", "かいわ"), ("人気", "にんき"), ("大会", "たいかい")]
    return [Item(i, w, r) for i, (w, r) in enumerate(ws)]


def test_path_brings_a_word_right_after_its_kanji():
    items = _items()
    full = {it.key for it in items}
    cfg = {"window": 3, "ahead": 10, "mature_counts": False}
    started, new = items[:1], items[1:]                   # 会社 studied: 会:かい and 社:しゃ are fresh
    order, why = plan(started, new, full, cfg)
    # nothing is guessable yet; 議員 brings the one missing kanji of both 会議 and 社員, which come right after it
    assert order[0].word == "議員" and not why[order[0].key]["guessable"]
    assert {o.word for o in order[1:3]} == {"会議", "社員"} and all(why[o.key]["guessable"] for o in order[1:3])
    assert count_guessable(started, order, full, cfg) >= count_guessable(started, new, full, cfg)


def test_spacing_holds_a_learned_pattern_back():
    items = [Item(i, w, r) for i, (w, r) in enumerate([("会社", "かいしゃ"), ("会議", "かいぎ"), ("会話", "かいわ"),
                                                       ("大会", "たいかい"), ("会場", "かいじょう"), ("天気", "てんき")])]
    full = {it.key for it in items}
    cfg = {"window": 2, "ahead": 2, "mature_counts": False, "spacing": {"on": True, "after": 3, "growth": 2, "max_gap": 50}}
    started, new = items[:4], items[4:]                   # 会:かい met 4 times: spaced, gap 2*2^(4-3) = 4
    order, why = plan(started, new, full, cfg)
    w = why[order[0].key]
    assert "会:かい" in w["spaced"] or not w["guessable"]


def test_llm_parse_keeps_only_valid_answers():
    batch = [Item(1, "入口", "いりぐち", "entrance"), Item(2, "今日", "きょう", "today")]
    text = json.dumps({"words": [{"w": "入口", "meaning": "yes", "reading": "yes", "why_m": "enter+mouth"},
                                 {"w": "今日", "meaning": "maybe", "reading": "no"}]})
    recs = llm.parse(text, batch, "gemma")
    assert [r["word"] for r in recs] == ["入口"] and recs[0]["source"] == "llm" and recs[0]["model"] == "gemma"


def test_llm_job_against_a_fake_server_with_a_trace(tmp_path):
    got = {"chat": 0, "envelopes": []}

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            body = self.rfile.read(int(self.headers["Content-Length"]))
            if self.path.endswith("/chat/completions"):
                got["chat"] += 1
                words = [l[2:].split(" ")[0] for l in json.loads(body)["messages"][0]["content"].splitlines() if l.startswith("- ")]
                content = json.dumps({"words": [{"w": w, "meaning": "yes", "reading": "partly"} for w in words]})
                out = {"choices": [{"message": {"content": content}}], "usage": {"prompt_tokens": 100, "completion_tokens": 20}}
            else:
                got["envelopes"].append(body.decode("utf-8"))
                out = {"id": "x"}
            data = json.dumps(out).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *a):
            pass
    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]
    items = _items()
    store = Store(tmp_path / "l.jsonl")
    cfg = {"base_url": "http://127.0.0.1:%d/v1" % port, "model": "gemma-test", "batch": 4, "per_day": 7}
    tr = trace.tracer("http://pubkey@127.0.0.1:%d/2" % port)
    res = llm.run(items, store, cfg, tracer=tr)
    srv.shutdown()
    assert res["labelled"] == 7 and got["chat"] == 2 and res["left"] == 3            # capped at per_day
    evs = [json.loads(e.splitlines()[2]) for e in got["envelopes"]]
    assert len(evs) == 3                                  # one per batch as it finishes, then the job's summary
    assert len({e["contexts"]["trace"]["trace_id"] for e in evs}) == 1                # (one trace)
    assert all(e["contexts"]["trace"]["op"] == "gen_ai.invoke_agent" for e in evs)
    assert evs[0]["spans"][0]["data"]["gen_ai.usage.input_tokens"] == 100
    assert evs[0]["spans"][0]["data"]["guesswithanki.unread"] == 0 and evs[1]["spans"][0]["data"]["guesswithanki.batch_size"] == 3
    assert llm.run(items, store, cfg)["labelled"] == 0                                # today's cap spent


def test_deck_every_keeps_part_of_the_deck_order():
    items = _items()
    full = {it.key for it in items}
    started, new = items[:1], items[1:]
    order, _ = plan(started, new, full, {"window": 3, "ahead": 9, "mature_counts": False, "deck_every": 2})
    # every 2nd place takes the deck's next word not yet placed
    placed = []
    for i, it in enumerate(order[:8]):
        if (i + 1) % 2 == 0:
            assert it is next(x for x in new if x not in placed)
        placed.append(it)


def test_free_cards_counts_cards_that_arrived_guessable_and_words_guessable_now():
    from guesswithanki.core.stats import free_cards
    items = _items()                        # 会社 社員 会議 議員 天気 電気 電話 会話 人気 大会
    full = {it.key for it in items}
    started = [items[0], items[2], items[7]]          # 会社, 会議, 会話: 会議 and 会話 still had a new kanji each
    f = free_cards(started, items[3:7] + items[8:], full, seen=1, window=40, rate=1.0)
    assert f["studied"] == 3 and f["arrived_free"] == 0
    assert f["guessable_now"] == 0                   # (議員 needs 員, 電話 needs 電 ... nothing is all-known yet)
    f = free_cards([items[0], items[1], items[2], items[3]], [], full, seen=1, window=40)
    assert f["arrived_free"] == 1                    # 議員: 議 (会議) and 員 (社員) were met


def test_a_cut_off_answer_keeps_the_whole_words_and_never_raises():
    batch = [Item(1, "入口", "いりぐち", "entrance"), Item(2, "出口", "でぐち", "exit")]
    text = '{"words": [{"w": "入口", "meaning": "yes", "reading": "yes", "why_m": "a", "why_r": "b"}, {"w": "出口", "mea'
    assert [r["word"] for r in llm.parse(text, batch, "g")] == ["入口"]
    assert llm.parse("not json at all", batch, "g") == []
