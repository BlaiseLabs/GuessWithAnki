"""GuessWithAnki inside Anki: the Tools menu, the dashboard, labelling a word while reviewing (crowd), the model's
labelling job, and reordering after each review session."""
import json
import re
import time
from pathlib import Path

from aqt import gui_hooks, mw
from aqt.operations import CollectionOp, QueryOp
from aqt.qt import (QAction, QButtonGroup, QDialog, QDialogButtonBox, QGridLayout, QHBoxLayout, QInputDialog, QLabel,
                    QLineEdit, QMenu, QPushButton, QRadioButton, QVBoxLayout, Qt)
from aqt.utils import getFile, getSaveFile, showInfo, showWarning, tooltip

from .core import llm, run, trace
from .core.ankiio import collect, queue_settings
from .core.labels import Store, key
from .core.stats import summary

ADDON = __name__.split(".")[0]
_busy = {"reorder": False, "label": False}


def cfg():
    return run.merged(mw.addonManager.getConfig(ADDON) or {})


def files():
    d = Path(mw.addonManager.addonsFolder(ADDON)) / "user_files" / (mw.pm.name or "default")
    d.mkdir(parents=True, exist_ok=True)
    return d


def progress(label):
    def f(i, n):
        mw.taskman.run_on_main(lambda: mw.progress.update(label="%s %d/%d" % (label, i, n), value=i, max=n))
    return f


# --- reorder -------------------------------------------------------------------------------------------------------

def reorder(quiet=False, then=None):
    if _busy["reorder"] or not mw.col:
        return
    _busy["reorder"] = True
    c, fd = cfg(), files()

    def op(col):
        a, order, why, before = run.compute(col, c, fd, True, None if quiet else progress("GuessWithAnki"))
        cids = [x[0] for it in order for x in it.cids if x[1] == 0 and x[2] != -1]
        have = {x[0]: x[3] for it in order for x in it.cids}
        s = summary(a, order, why, before, c, queue_settings(col, a.new))
        return cids, have, s

    def done(res):
        cids, have, s = res
        start = min((have[x] for x in cids), default=0)
        same = [have[x] for x in cids] == list(range(start, start + len(cids)))

        def finish(moved):
            _busy["reorder"] = False
            s.update(moved=moved, at=time.strftime("%Y-%m-%d %H:%M"))
            (fd / "last.json").write_text(json.dumps(s, ensure_ascii=False), encoding="utf-8")
            e = s["effect"]
            msg = "GuessWithAnki reordered your new cards. Of the next %d, %d arrive guessable (%d in the deck's order)." % (
                e["n"], e["after"], e["before"])
            tooltip(msg, period=4000)
            if then:
                then(s)
        if same or not cids:
            finish(0)
            return
        CollectionOp(parent=mw, op=lambda col: col.sched.reposition_new_cards(
            card_ids=cids, starting_from=start, step_size=1, randomize=False, shift_existing=False)
        ).success(lambda out: finish(len(cids))).failure(lambda e: (_busy.update(reorder=False), showWarning(str(e)))
                                                        ).run_in_background()

    def failed(e):
        _busy["reorder"] = False
        showWarning("GuessWithAnki could not plan: %s" % e)
    q = QueryOp(parent=mw, op=op, success=done).failure(failed)
    (q if quiet else q.with_progress("GuessWithAnki: planning")).run_in_background()


# --- dashboard -----------------------------------------------------------------------------------------------------

class Dashboard(QDialog):
    def __init__(self):
        super().__init__(mw)
        from aqt.webview import AnkiWebView
        self.setWindowTitle("GuessWithAnki")
        self.resize(1080, 820)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.web = AnkiWebView(parent=self, title="guesswithanki dashboard")
        lay.addWidget(self.web)
        row = QHBoxLayout()
        row.setContentsMargins(10, 6, 10, 8)
        for text, fn in (("Reorder now", lambda: reorder(then=lambda s: self.show_data())),
                         ("Label with model", lambda: label_job()), ("Settings", settings)):
            b = QPushButton(text)
            b.clicked.connect(fn)
            row.addWidget(b)
        row.addStretch(1)
        close = QPushButton("Close")
        close.clicked.connect(self.close)
        row.addWidget(close)
        lay.addLayout(row)
        self.show_data()

    def show_data(self):
        from .web import page
        f = files() / "last.json"
        data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else None
        self.web.setHtml(page(data))


def dashboard():
    if not (files() / "last.json").exists():
        reorder(then=lambda s: Dashboard().show())
    else:
        Dashboard().show()


# --- model labelling -----------------------------------------------------------------------------------------------

def label_job(limit=None):
    if _busy["label"]:
        tooltip("GuessWithAnki: a labelling job is already running")
        return
    c, fd = cfg(), files()
    from .core.remote import reachable
    if not reachable(c["llm"]["base_url"]):
        showInfo("Labelling with a model needs a model server, and none is running at %s, so nothing was labelled."
                 "\n\nGuessWithAnki works without it, using its built-in judgments. To add model labels, install "
                 "Ollama from https://ollama.com and run \"ollama pull %s\". Any server with an OpenAI-style API works "
                 "too (LM Studio, llama.cpp, or a cloud API with a key), set under llm in the settings."
                 % (c["llm"]["base_url"], c["llm"]["model"]), parent=mw)
        return
    _busy["label"] = True
    stop = {"now": False}

    def op(col):
        items = collect(col, c)
        from .core.ankiio import split_started
        started, new = split_started(items)
        store = Store(fd / "labels.jsonl")
        return llm.run(new + started, store, c["llm"], limit=limit, progress=progress("GuessWithAnki: labelling"),
                       tracer=trace.tracer(c.get("sentry_dsn")), cancelled=lambda: stop["now"] or mw.progress.want_cancel())

    def done(res):
        _busy["label"] = False
        msg = ("GuessWithAnki labelled %(labelled)d words with %(model)s (%(calls)d calls, %(seconds)s s). "
               "%(failed)d could not be read. Words still to label: %(left)d." % res)
        if res.get("unread"):
            msg += "\n\nWhat came back where words could not be read:\n" + res["unread"]
        showInfo(msg, parent=mw)
        reorder(quiet=True)

    def failed(e):
        _busy["label"] = False
        showWarning("GuessWithAnki labelling stopped: %s" % e)
    QueryOp(parent=mw, op=op, success=done).failure(failed).with_progress("GuessWithAnki: labelling").run_in_background()


def label_some():
    n, ok = QInputDialog.getInt(mw, "GuessWithAnki", "Label how many words now? (today's cap still applies)", 20, 1, 5000)
    if ok:
        label_job(n)


# --- crowd: label the word under review ----------------------------------------------------------------------------

class LabelDialog(QDialog):
    def __init__(self, note):
        super().__init__(mw)
        from .core.ankiio import detect_fields
        from .core.kana import clean
        from .core.model import set_profile
        from .core.profiles import detect_profile
        names0 = [f["name"] for f in note.note_type()["flds"]]
        want = cfg().get("profile") or "auto"                 # (this note's kind: the setting, or its fields' text)
        pf = set_profile(want if want != "auto" else detect_profile({n: [clean(note[n])] for n in names0}))
        self.setWindowTitle("GuessWithAnki: is this word guessable?")
        names = [f["name"] for f in note.note_type()["flds"]]
        r = detect_fields(names, cfg().get("fields"))
        self.word, self.reading = pf.word_reading(note[r["word"]] if "word" in r else "", note[r["reading"]] if "reading" in r else "")
        meaning = note[r["meaning"]] if "meaning" in r else ""
        lay = QVBoxLayout(self)
        head = QLabel("<div style='font-size:28px'>%s</div><div>%s</div><div style='color:gray'>%s</div>"
                      % (self.word, self.reading, re.sub("<[^>]+>", " ", meaning)[:120]))
        head.setTextFormat(Qt.TextFormat.RichText)
        lay.addWidget(head)
        sp = pf.split(self.word, self.reading) or (pf.segment(self.word) if hasattr(pf, "segment") else None) or []
        if sp:
            lay.addWidget(QLabel("  ".join("%s %s (%s)" % (ch, rd if pf.reads else "", ", ".join(pf.meanings(ch)[:2]) or rd)
                                           for ch, rd in sp)))
        grid = QGridLayout()
        self.groups = {}
        dims = ((("reading_guessable", "Reading guessable from its %ss?" % pf.unit_name),) if pf.reads else ()) + (
            ("meaning_guessable", "Meaning guessable from its %ss?" % pf.unit_name),)
        for row, (dim, text) in enumerate(dims):
            grid.addWidget(QLabel(text), row, 0)
            g = QButtonGroup(self)
            for col, v in enumerate(("yes", "partly", "no")):
                b = QRadioButton(v)
                g.addButton(b)
                b.setProperty("v", v)
                grid.addWidget(b, row, col + 1)
            self.groups[dim] = g
        lay.addLayout(grid)
        self.why = QLineEdit()
        self.why.setPlaceholderText("what gives it away (or not), e.g. enter + mouth = entrance")
        lay.addWidget(self.why)
        self.helpers = QLineEdit()
        self.helpers.setPlaceholderText("words that help guess it, separated by 、 or commas")
        lay.addWidget(self.helpers)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self.save)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    def save(self):
        rec = {"word": self.word, "reading": self.reading, "source": "crowd", "by": cfg().get("crowd_name") or "me",
               "why_meaning": self.why.text().strip(),
               "helpers": [x.strip() for x in re.split("[、,，]", self.helpers.text()) if x.strip()]}
        for dim, g in self.groups.items():
            b = g.checkedButton()
            if b:
                rec[dim] = b.property("v")
        if Store(files() / "labels.jsonl").add([rec]):
            tooltip("GuessWithAnki: saved your label for %s" % self.word)
            self.accept()
        else:
            showWarning("Pick yes / partly / no for the reading or the meaning first.", parent=self)


def label_current():
    card = getattr(mw.reviewer, "card", None)
    if card is None:
        tooltip("GuessWithAnki: no card under review")
        return
    LabelDialog(card.note()).exec()


# --- import / export / settings --------------------------------------------------------------------------------------

def import_labels():
    def got(path):
        n = Store(files() / "labels.jsonl").import_(Path(path).read_text(encoding="utf-8"))
        tooltip("GuessWithAnki: imported %d labels" % n)
        reorder(quiet=True)
    getFile(mw, "Import GuessWithAnki labels", got, filter="*.json *.jsonl")


def export_labels():
    path = getSaveFile(mw, "Export GuessWithAnki labels", "guesswithanki_labels", "Labels", ".json", "guesswithanki_labels.json")
    if path:
        n = Store(files() / "labels.jsonl").export(path)
        tooltip("GuessWithAnki: exported %d labels" % n)


def write_into_deck():
    """your votes and the model's labels into the notes in GuessWithAnki's search, as guesswithanki:: tags and _guesswithanki.json,
    so the deck carries them when you share it"""
    from aqt.utils import askUser
    from .core import embedded
    c, fd = cfg(), files()
    items = collect(mw.col, c)
    tags, recs = embedded.plan_write(items, Store(fd / "labels.jsonl"))
    if not tags:
        showInfo("GuessWithAnki has no labels of yours or the model's for these notes yet.", parent=mw)
        return
    if not askUser("Write GuessWithAnki labels into %d notes (guesswithanki:: tags, replacing earlier ones) and %s with %d "
                   "records? Share the deck afterwards and its users get the labels." % (len(tags), embedded.FILE, len(recs)),
                   parent=mw):
        return
    CollectionOp(parent=mw, op=lambda col: embedded.write(col, items, Store(fd / "labels.jsonl"))[2]).success(
        lambda out: tooltip("GuessWithAnki: labels written into %d notes" % len(tags))).run_in_background()


def settings():
    from aqt.addons import ConfigEditor
    mw.mgr = mw.addonManager      # ConfigEditor reads dlg.mgr, and the main window has no such attribute
    ConfigEditor(mw, ADDON, mw.addonManager.getConfig(ADDON))


# --- hooks ---------------------------------------------------------------------------------------------------------

def on_state(new, old):
    if old == "review" and new in ("overview", "deckBrowser") and cfg().get("auto_reorder"):
        reorder(quiet=True)


def on_shortcuts(state, shortcuts):
    if state == "review":
        shortcuts.append(("Shift+G", label_current))


def on_context(reviewer, menu):
    a = menu.addAction("GuessWithAnki: is this word guessable?")
    a.triggered.connect(label_current)


def on_profile():
    if cfg().get("auto_reorder"):
        mw.progress.single_shot(3000, lambda: reorder(quiet=True), False)


def setup():
    menu = QMenu("GuessWithAnki", mw)
    for text, fn in (("Dashboard…", dashboard), ("Reorder new cards now", reorder),
                     ("Label words with the model (today's batch)", label_job), ("Label some words with the model…", label_some),
                     (None, None), ("Import labels…", import_labels), ("Export labels…", export_labels),
                     ("Write labels into the deck…", write_into_deck),
                     (None, None), ("Settings…", settings)):
        if text is None:
            menu.addSeparator()
            continue
        a = QAction(text, mw)
        a.triggered.connect(lambda _=False, f=fn: f())
        menu.addAction(a)
    mw.form.menuTools.addMenu(menu)
    gui_hooks.state_did_change.append(on_state)
    gui_hooks.state_shortcuts_will_change.append(on_shortcuts)
    gui_hooks.reviewer_will_show_context_menu.append(on_context)
    gui_hooks.profile_did_open.append(on_profile)
