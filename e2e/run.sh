#!/bin/bash
# The journey test: a fresh throwaway Anki base from a demo collection, Anki under Xvfb driven by e2e/gp_e2e, results
# in $GP_E2E_DIR/out (e2e_result.json and screenshots). Needs Xvfb and the Qt runtime libraries (libxcb-cursor0 etc.).
#   GP_DEMO      the demo collection (python tools/make_demo.py demo.anki2 --n 2000 --study 150)
#   GP_PYTHON    a Python with aqt installed (default: python3)
#   GP_E2E_DIR   where the throwaway base and results go (default: ~/gp-e2e)
#   GP_EMBED     optional: an embeddings.json cache to start from (skips minutes of embedding)
#   GP_E2E_DECK, GP_E2E_FIELD   another deck to drive and its word field (default: the demo's Common Words, Expression)
set -e
cd "$(dirname "$0")/.."
PY=${GP_PYTHON:-python3}
DIR=${GP_E2E_DIR:-$HOME/gp-e2e}
[ -f "${GP_DEMO:?set GP_DEMO to a demo collection}" ] || { echo "no demo collection at $GP_DEMO"; exit 1; }
$PY e2e/setup_base.py "$DIR/base" "$GP_DEMO" guesswithanki e2e/gp_e2e > /dev/null
if [ -n "$GP_EMBED" ]; then
  mkdir -p "$DIR/base/addons21/guesswithanki/user_files/e2e" && cp "$GP_EMBED" "$DIR/base/addons21/guesswithanki/user_files/e2e/embeddings.json"
fi
rm -rf "$DIR/out"
export GP_E2E_OUT=$DIR/out QTWEBENGINE_CHROMIUM_FLAGS="--no-sandbox --disable-gpu"
timeout 1500 xvfb-run -a -s "-screen 0 1400x1000x24" $PY -c "import sys, aqt; sys.argv = ['anki'] + sys.argv[1:]; aqt.run()" -b "$DIR/base" -p e2e > "$DIR/anki.log" 2>&1 || true
python3 -c "import json;r=json.load(open('$DIR/out/e2e_result.json'));[print(('PASS' if s['ok'] else 'FAIL'),s['step'],s['t']) for s in r['steps']];print('ALL OK' if r['ok'] and r.get('done') else 'NOT OK')"
