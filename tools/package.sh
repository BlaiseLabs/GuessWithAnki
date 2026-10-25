#!/bin/bash
# build/guesswithanki.ankiaddon: the add-on folder zipped (no caches, no user files)
set -e
cd "$(dirname "$0")/.."
mkdir -p build
rm -f build/guesswithanki.ankiaddon
(cd guesswithanki && zip -qr ../build/guesswithanki.ankiaddon . -x "__pycache__/*" "*/__pycache__/*" "user_files/*" "meta.json")
zip -qj build/guesswithanki.ankiaddon LICENSE
ls -la build/guesswithanki.ankiaddon
