"""The journey test, run inside a real Anki (under Xvfb on the test box): it uses GuessWithAnki the way a learner does,
through the menu, the keyboard and the dialogs, takes screenshots, checks what it sees, writes e2e_result.json
next to the base folder and quits. Steps (each waits for the one before):
  1 the profile opens: the automatic reorder runs; Anki's new queue is the planned order
  2 Tools > GuessWithAnki > Dashboard: the page shows the before/after numbers
  3 study 6 new cards with the keyboard (space, 3): they come in the planned order
  4 Shift+G on a card: the crowd dialog, filled in and saved: a crowd label is stored
  5 back to the decks: the automatic reorder runs again
  6 Tools > GuessWithAnki > Label some words with the model: 20 words labelled by the model (Ollama, Gemma)
  7 the dashboard again"""
import json
import os
import time
import traceback
from pathlib import Path

from aqt import gui_hooks, mw
from aqt.qt import QApplication, QDialog, QInputDialog, QMessageBox, QRadioButton, QLineEdit, QTimer, Qt
from aqt.qt import QDialogButtonBox

OUT = Path(os.environ.get("GP_E2E_OUT", "/tmp/gp_e2e"))
DECK = os.environ.get("GP_E2E_DECK", "Common Words")      # (the demo deck; any deck with its word field named below)
FIELD = os.environ.get("GP_E2E_FIELD", "Expression")
R = {"steps": [], "ok": True}


def shot(widget, name):
    OUT.mkdir(parents=True, exist_ok=True)
    widget.grab().save(str(OUT / ("%s.png" % name)))


def log(step, ok, **kw):
    R["steps"].append(dict(step=step, ok=bool(ok), t=round(time.time() - T0, 1), **kw))
    R["ok"] = R["ok"] and bool(ok)
    (OUT / "e2e_result.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")


def guarded(fn):
    """a step's errors end the test with the traceback (instead of Anki's error dialog)"""
    import functools

    @functools.wraps(fn)
    def run(*a, **kw):
        try:
            return fn(*a, **kw)
        except Exception:
            log("error in %s" % fn.__name__, False, err=traceback.format_exc()[-2000:])
            finish()
    return run


def gp():
    import importlib
    return importlib.import_module("guesswithanki.ui")


def action(text):
    for a in mw.form.menuTools.actions():
        if a.menu() and a.menu().title() == "GuessWithAnki":
            for b in a.menu().actions():
                if b.text() == text:
                    return b
    raise LookupError(text)


def wait(cond, then, timeout=600, every=500):
    t = time.time()

    def tick():
        try:
            if cond():
                then()
            elif time.time() - t > timeout:
                log("timeout waiting (%s)" % then.__name__, False)
                finish()
            else:
                QTimer.singleShot(every, tick)
        except Exception:
            log("error in %s" % then.__name__, False, err=traceback.format_exc()[-1500:])
            finish()
    QTimer.singleShot(every, tick)


def last():
    f = Path(gp().files()) / "last.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def queue_words(n):
    return [mw.col.get_card(c.card.id).note()[FIELD] for c in mw.col.sched.get_queued_cards(fetch_limit=n).cards]


@guarded
def step1():
    s = last()
    did = mw.col.decks.id(DECK)
    mw.col.decks.select(did)
    planned = [r["word"] for r in s["next"][:6]]
    R["started0"] = s["totals"]["started"]
    q = queue_words(6)
    log("1 auto reorder at profile open", s["moved"] > 0 and q == planned, moved=s["moved"], effect=[s["effect"]["before"], s["effect"]["after"]],
        planned=planned, queue=q)
    shot(mw, "1_main")
    action("Dashboard…").trigger()
    QTimer.singleShot(4000, step2)


@guarded
def step2():
    d = next((w for w in QApplication.topLevelWidgets() if isinstance(w, QDialog) and w.windowTitle() == "GuessWithAnki" and w.isVisible()), None)
    if d is None:
        log("2 dashboard opens", False)
        return finish()
    shot(d, "2_dashboard")

    def got(text):
        log("2 dashboard shows the numbers", "Guessable on arrival" in (text or "") and "Next new cards" in (text or ""), text=(text or "")[:300])
        d.close()
        R["planned"] = [r["word"] for r in last()["next"][:6]]
        mw.moveToState("review")
        QTimer.singleShot(2500, step3)
    d.web.page().runJavaScript("document.body.innerText", got)


@guarded
def step3():
    from PyQt6.QtTest import QTest
    seen = []

    @guarded
    def one(i):
        if i == 6:
            log("3 study 6 new cards in the planned order", seen == R["planned"], seen=seen, planned=R["planned"])
            QTimer.singleShot(500, step4)
            return
        if mw.state != "review" or mw.reviewer.card is None:
            log("3 a card to study", False, state=mw.state)
            return finish()
        seen.append(mw.reviewer.card.note()[FIELD])
        if i == 0:
            shot(mw, "3_question")
        QTest.keyClick(mw, Qt.Key.Key_Space)
        if i == 0:
            QTimer.singleShot(800, lambda: shot(mw, "3_answer"))

        def good():
            QTest.keyClick(mw, Qt.Key.Key_3)
            QTimer.singleShot(1200, lambda: one(i + 1))
        QTimer.singleShot(1500, good)
    one(0)


@guarded
def step4():
    from PyQt6.QtTest import QTest
    word = mw.reviewer.card.note()[FIELD]

    def fill():
        d = QApplication.activeModalWidget()
        if d is None:
            log("4 crowd dialog opens", False)
            return
        for b in d.findChildren(QRadioButton):
            if b.text() == "yes":
                b.setChecked(True)                   # (the first 'yes' of each row: reading yes, meaning yes)
        edits = d.findChildren(QLineEdit)
        edits[0].setText("e2e: the kanji give it away")
        shot(d, "4_crowd_dialog")
        d.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Save).click()
    QTimer.singleShot(1500, fill)
    QTest.keyClick(mw, Qt.Key.Key_G, Qt.KeyboardModifier.ShiftModifier)
    labels = Path(gp().files()) / "labels.jsonl"
    recs = [json.loads(x) for x in labels.read_text(encoding="utf-8").splitlines()] if labels.exists() else []
    crowd = [r for r in recs if r["source"] == "crowd" and r["word"] == word]
    log("4 crowd label saved from the review screen", bool(crowd), word=word, record=crowd[-1] if crowd else None)
    R["at1"] = last()["at"]
    R["t5"] = time.time()
    mw.moveToState("deckBrowser")
    wait(lambda: not gp()._busy["reorder"] and time.time() - R["t5"] > 3, step5)


@guarded
def step5():
    s = last()
    log("5 auto reorder after the review session", s is not None and s["totals"]["started"] >= R["started0"] + 6, started=s["totals"]["started"],
        effect=[s["effect"]["before"], s["effect"]["after"]])

    def answer_int():
        d = QApplication.activeModalWidget()
        if isinstance(d, QInputDialog):
            d.setIntValue(20)
            d.accept()
    QTimer.singleShot(1200, answer_int)
    R["t6"] = time.time()
    action("Label some words with the model…").trigger()
    wait(lambda: isinstance(QApplication.activeModalWidget(), QMessageBox), step6, timeout=900, every=1000)


@guarded
def step6():
    box = QApplication.activeModalWidget()
    text = box.text()
    shot(box, "6_label_done")
    box.accept()
    labels = Path(gp().files()) / "labels.jsonl"
    recs = [json.loads(x) for x in labels.read_text(encoding="utf-8").splitlines()]
    llm = [r for r in recs if r["source"] == "llm"]
    log("6 the model labels 20 words", len(llm) >= 15, n=len(llm), text=text, seconds=round(time.time() - R["t6"]), example=llm[0] if llm else None)
    wait(lambda: not gp()._busy["reorder"], lambda: (action("Dashboard…").trigger(), QTimer.singleShot(4000, step7)))


@guarded
def step7():
    d = next((w for w in QApplication.topLevelWidgets() if isinstance(w, QDialog) and w.windowTitle() == "GuessWithAnki" and w.isVisible()), None)
    if d:
        shot(d, "7_dashboard_after")
    s = last()
    log("7 dashboard after labelling", d is not None and s["labels"].get("llm", 0) >= 15, labels=s["labels"])
    finish()


def finish():
    R["done"] = True
    (OUT / "e2e_result.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
    QTimer.singleShot(1000, mw.close)


def start():
    global T0
    T0 = time.time()
    QTimer.singleShot(1200 * 1000, lambda: (log("watchdog: 20 minutes", False), finish()))
    OUT.mkdir(parents=True, exist_ok=True)
    wait(lambda: last() is not None and not gp()._busy["reorder"], step1, timeout=900)


gui_hooks.profile_did_open.append(lambda: QTimer.singleShot(1000, start))
