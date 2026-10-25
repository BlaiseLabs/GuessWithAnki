"""GuessWithAnki: orders an Anki deck's new words (Japanese, Chinese, English, medical) so that each one arrives
guessable from pieces you just met: kanji, characters, word parts.
The core (core/) needs no Anki window; ui.py hooks it into Anki when the add-on is loaded there."""
try:
    from aqt import mw
except ImportError:                    # (imported by the tests or the command line, outside Anki)
    mw = None

if mw is not None:
    from . import ui
    ui.setup()
