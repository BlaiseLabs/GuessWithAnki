#!/bin/bash
# the dictionary files tools/build_data.py reads, into raw/ (EDRDG: KANJIDIC2, JMdict; Doublevil: JmdictFurigana)
set -e
cd "$(dirname "$0")/.."
mkdir -p raw
curl -sL -o raw/kanjidic2.xml.gz http://www.edrdg.org/kanjidic/kanjidic2.xml.gz
curl -sL -o raw/JMdict_e.gz http://ftp.edrdg.org/pub/Nihongo/JMdict_e.gz
url=$(curl -s https://api.github.com/repos/Doublevil/JmdictFurigana/releases/latest |
      python3 -c 'import sys,json;print([a["browser_download_url"] for a in json.load(sys.stdin)["assets"] if a["name"]=="JmdictFurigana.txt"][0])')
curl -sL -o raw/JmdictFurigana.txt "$url"
ls -la raw
