"""A demo deck to try GuessWithAnki on: JMdict's most common words (news frequency order), as a plain vocabulary note type
(Expression / Reading / Meaning), in a fresh collection. The words and glosses are JMdict's (EDRDG, CC BY-SA 4.0).

    python3 tools/make_demo.py OUT.anki2 [--n 2000] [--study 150]

--study: answer the first N cards once (Good), so the deck has a learner's history to plan from."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--study", type=int, default=0)
    a = ap.parse_args()
    from anki.collection import Collection
    words = json.loads((ROOT / "tools" / "common_words.json").read_text(encoding="utf-8"))["words"]
    words = sorted((w for w in words if w[3] < 99), key=lambda w: w[3])
    seen, picked = set(), []
    for keb, reb, gl, nf in words:
        if keb not in seen:
            seen.add(keb)
            picked.append((keb, reb, "; ".join(gl[:3])))
        if len(picked) >= a.n:
            break
    Path(a.out).unlink(missing_ok=True)
    col = Collection(a.out)
    mm = col.models
    nt = mm.new("Japanese Vocab")
    for f in ("Expression", "Reading", "Meaning"):
        mm.add_field(nt, mm.new_field(f))
    t = mm.new_template("Recognition")
    t["qfmt"], t["afmt"] = "<div style='font-size:48px'>{{Expression}}</div>", "{{FrontSide}}<hr id=answer>{{Reading}}<br>{{Meaning}}"
    mm.add_template(nt, t)
    mm.add(nt)
    nt = mm.by_name("Japanese Vocab")
    did = col.decks.id("Common Words")
    for keb, reb, mean in picked:
        n = col.new_note(nt)
        n["Expression"], n["Reading"], n["Meaning"] = keb, reb, mean
        col.add_note(n, did)
    if a.study:
        col.decks.select(did)
        conf = col.decks.config_dict_for_deck_id(did)
        conf["new"]["perDay"] = 9999
        col.decks.update_config(conf)
        for _ in range(a.study):
            q = col.sched.get_queued_cards(fetch_limit=1)
            if not q.cards:
                break
            c = col.get_card(q.cards[0].card.id)
            c.start_timer()
            col.sched.answer_card(col.sched.build_answer(card=c, states=q.cards[0].states, rating=3))
        conf["new"]["perDay"] = 20
        col.decks.update_config(conf)
    print("%s: %d notes, %d studied" % (a.out, col.note_count(), a.study))
    col.close()


if __name__ == "__main__":
    main()
