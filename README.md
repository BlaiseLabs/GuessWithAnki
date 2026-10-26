# GuessWithAnki

**Any vocabulary deck, ordered so you can guess each new word from pieces you've already met.**

The sequel to [GuessWithKanji](https://github.com/BlaiseLabs/GuessWithKanji). GuessWithKanji orders a Japanese deck so
each word arrives right after the kanji it is built from, read the way the word reads them, so you can guess it on
first sight instead of memorizing it. GuessWithAnki asks whether that works beyond Japanese. The same approach covers
four kinds of deck, Japanese, Chinese, English for learners, and medical terminology.

```
Japanese  電車 でんしゃ, 天気 てんき (studied)  ->  電気 でんき   電 read でん + 気 read き, electric + spirit = electricity
Chinese   开 kāi, 大学生 dàxuéshēng (studied)  ->  开学 kāixué   open + study = the start of term
English   unemployment (studied)              ->  employer       employ + -er = one who employs
Medical   acr- (extremity), phob- (fear)       ->  acrophobia     fear of heights (of the extremes)
```

![How it works on a Japanese deck. A word arrives right after its kanji, so you can guess it](docs/explainer.gif)

**No extra software needed.** Install the add-on and it works on its own. [Ollama](https://ollama.com) is an optional
upgrade for sharper meaning judgments and model labels (see [Install](#install)).

## Does it work across languages?

Yes for Chinese and Japanese, partly for English, and only with a roots deck for medicine. Eight decks, two per
community, picked from what each community recommends to beginners on Reddit (see [The decks](#the-decks)).

#### How much of each deck is guessable

A word is guessable when its pieces' meanings (and, for Japanese and Chinese, their usual readings) give away the word.
"Pieces reused" is the share of words whose every piece appears in another word of the deck too. "On arrival" counts
the guessable words that arrive with all their pieces already met, in the first 500 cards.

| Deck | Kind | Words | With pieces | Meaning guessable | Reading guessable | Guessable | Pieces reused | Guessable on arrival in the first 500 (deck order → GuessWithAnki) |
|---|---|---|---|---|---|---|---|---|
| Kaishi 1.5k | Japanese | 1,500 | 86% | 77% | 96% | **64%** | 45% | 7 → **270** |
| Core 2k | Japanese | 2,000 | 80% | 78% | 95% | **60%** | 55% | 2 → **295** |
| New HSK 3.0, levels 1–4 | Chinese | 3,245 | 100% | 74% | 96% | **71%** | 90% | 31 → **373** |
| HSK (2012), levels 1–5 | Chinese | 2,495 | 100% | 68% | 97% | **66%** | 64% | 7 → **308** |
| 4000 Essential English Words | English | 3,596 | 42% | 49% | – | **20%** | 43% | 1 → **175** |
| Oxford 3000 | English | 3,377 | 41% | 66% | – | **27%** | 47% | 0 → **241** |
| Medical Terminology with Etymology | medical | 512 | 47% | 58% | – | **27%** | 29% | 14 → **31** |
| Hippocrates Code roots, then those terms | medical | 1,494 | 76% | 17% | – | **13%** | 33% | 2 → **83** |

#### How much faster

A card you guess right the first time you see it is a free card, because you never have to learn it. The table counts
the cards you have to learn to reach a number of words, in the deck's own order (normal Anki) and in GuessWithAnki's.
The speed-up is normal Anki's cards divided by GuessWithAnki's. The guess rate is how often you get a guessable word
right once its pieces are learned (rows for 50%, 33% and 25% are in `docs/results.md`).

| Deck | Guess rate | 100 words | 250 words | 500 words | 1,000 words |
|---|---|---|---|---|---|
| Kaishi 1.5k | 100% | **3.3×** (97 → 29) | **2.6×** (240 → 93) | **2.0×** (464 → 230) | **1.2×** (890 → 723) |
|  | 80% | **2.4×** (98 → 42) | **2.0×** (242 → 124) | **1.7×** (474 → 282) | **1.2×** (917 → 776) |
| Core 2k | 100% | **3.6×** (100 → 28) | **2.8×** (242 → 87) | **2.3×** (476 → 204) | **1.6×** (898 → 574) |
|  | 80% | **2.3×** (100 → 44) | **2.0×** (244 → 120) | **1.8×** (481 → 265) | **1.4×** (918 → 660) |
| New HSK 3.0, levels 1–4 | 100% | **4.1×** (95 → 23) | **3.6×** (216 → 60) | **2.8×** (359 → 126) | **2.5×** (697 → 280) |
|  | 80% | **2.5×** (96 → 38) | **2.3×** (223 → 97) | **2.0×** (392 → 200) | **1.8×** (762 → 422) |
| HSK (2012), levels 1–5 | 100% | **3.1×** (100 → 32) | **2.7×** (238 → 88) | **2.4×** (467 → 191) | **2.0×** (887 → 444) |
|  | 80% | **2.2×** (100 → 46) | **2.0×** (240 → 122) | **1.8×** (473 → 256) | **1.6×** (910 → 557) |
| 4000 Essential English Words | 100% | **2.1×** (100 → 48) | **1.9×** (249 → 133) | **1.5×** (493 → 321) | **1.2×** (978 → 784) |
|  | 80% | **1.7×** (100 → 57) | **1.6×** (249 → 156) | **1.4×** (494 → 356) | **1.2×** (983 → 827) |
| Oxford 3000 | 100% | **2.6×** (100 → 39) | **2.3×** (249 → 107) | **1.9×** (492 → 255) | **1.4×** (970 → 714) |
|  | 80% | **2.1×** (100 → 48) | **1.9×** (250 → 134) | **1.6×** (494 → 303) | **1.3×** (976 → 769) |
| Medical Terminology with Etymology | 100% | **1.4×** (97 → 70) | **1.1×** (241 → 219) | **1.0×** (478 → 468) | – |
|  | 80% | **1.3×** (98 → 76) | **1.1×** (243 → 225) | **1.0×** (482 → 474) | – |
| Hippocrates Code roots, then those terms | 100% | **1.7×** (100 → 59) | **1.5×** (250 → 168) | **1.2×** (486 → 416) | **1.1×** (979 → 916) |
|  | 80% | **1.5×** (100 → 65) | **1.4×** (250 → 182) | **1.1×** (489 → 431) | **1.1×** (983 → 931) |

#### What this shows

- **Chinese is the best case.** Every word is made of characters, a character has one usual reading, and the same
  characters come back again and again. In New HSK 3.0 levels 1–4, 90% of words share every character with another
  word. It keeps a 1.6–1.8× lead at 1,000 words at an 80% guess rate, where the Japanese decks are down to 1.2–1.4×.
- **Japanese is close behind.** About 60% of a beginner deck is guessable, and the gain is largest in the first few
  hundred words.
- **English works for a fifth to a quarter of a learner's deck.** The guessable words are derived forms, like employ,
  then employer, employment, unemployed, or separate, then separately, separation. It gives 1.7–2.1× for the first 100
  words at 80%, fading to 1.2–1.3× by 1,000. English has no reading to guess, and most common English words do not split.
- **A medical terminology deck alone gains little.** The one tested is small and mixed (abbreviations, drug names,
  everyday words). It's 27% guessable, but few of its parts come back in a second term.
- **With a roots deck, the path front-loads the medical terms.** Students are told to learn the Greek and Latin roots
  first. Studied in that order (the roots deck's 982 cards, then the terms), the terms start on day 50 and the learner
  has 61 free cards by day 90 (80% guess rate). GuessWithAnki brings in only the roots a word needs, right before it,
  for 68 free cards by day 14, after 280 cards studied.
- **Reviews come on top.** Free cards still come back for review, but they are rarely forgotten. By day 30 (600 words
  started, 80% guess rate) the Japanese, Chinese and English decks need 15–24% fewer card showings, and forgotten
  reviews fall by 28–62% (New HSK 3.0 goes from 118 to 49). The medical decks need 1–8% fewer showings.

#### How it was measured

Each deck was imported fresh (no prior knowledge), and every word was labelled by one model, gpt-5.6-terra (16,331
words, about 2.1M tokens, with the add-on's heuristics off). Then a learner was simulated day by day for 100 days at 20
new cards a day under FSRS-6 (Anki's default parameters, 90% retention), every review done, 4 simulated learners
averaged. Every day a word is shown counts as a sighting of its pieces, each piece has an FSRS memory of its own, and a
piece is learned after one sighting. GuessWithAnki's order was planned once at the start (the add-on plans again after
every session). The tools are `tools/label_parallel.py`, `tools/guess_index.py`, `tools/fsrs_sim.py` and
`tools/speedup_table.py`. The decks are not part of this repository.

## The general approach

The path planner, the labels, the dashboard and the simulation only see **pieces**. A word is a list of pieces, a piece
is learned when you study a word that has it, and a word is free when it is guessable and all its pieces are fresh.
What a piece is depends on the deck, so each kind of deck gets a **profile** that splits its words into pieces.

| Profile | A piece is | Split by | Guessable when | Data |
|---|---|---|---|---|
| japanese | a kanji with the reading it has in the word (会 read かい) | the reading field, aligned to the kanji (with rendaku and small tsu) | meaning and reading follow from the pieces | KANJIDIC2, JMdict |
| chinese | a character with its pinyin syllable and tone (电 read dian4) | the pinyin field, split into as many syllables as the word has characters (tone marks, tone numbers, spaces or none) | meaning and pinyin follow | CC-CEDICT |
| english | a prefix, root, suffix, or a word inside a compound (un-, employ, -ment) | the model, which gives each word's parts with their meanings, or without one, a table of the parts it found in the decks above (longest match) | meaning follows | model labels |
| medical | a Greek or Latin prefix, root or suffix (hepat, -itis), and a card for a word part itself (`cardi/o`, `-itis`) teaches that part | as english, and parts match across spellings (cardi/o, cardio and cardi are one root) | meaning follows | model labels |

The profile is told from the deck's fields (kana means Japanese, hanzi without kana Chinese, Latin letters English,
medical when the terms look medical), or you can set `profile` to choose. The planner is the same greedy path as
GuessWithKanji. It picks the next card that makes the most words guessable soon, and when nothing is guessable it
brings in a plain word with one new piece.

## The decks

Picked from about 1,600 Reddit threads read through Reddit's API (438 for Chinese, 280 for English, 900 for medicine).
A mention is a post or comment that names or links the deck. The full notes are in
[docs/deck_research.md](docs/deck_research.md).

| Community | Deck | AnkiWeb | Used | Mentions |
|---|---|---|---|---|
| Chinese | Mandarin Chinese: New HSK 3.0 Vocabulary and Characters | `1144807196` | the word notes of levels 1–4 | 26 |
| Chinese | Hanyu Shuiping Kaoshi (HSK) (all 5000 words) | `1855818143` | levels 1–5 | 3 (and 37 more for the 2012 HSK lists) |
| English | 4000 Essential English Words (all books) [en-en] | `413429709` | all | 22 |
| English | [English] The Oxford 3000 Most Important Words | `1575087857` | all | about 7 (Oxford lists) |
| medical | Medical Terminology & Abbreviations With Etymology | `1220822549` | all | 0 (the best text fit) |
| medical | The Hippocrates Code: Medical Greek and Latin | `1645339321` | the 980 word-part cards, studied before the terms deck | 0 |
| Japanese | Kaishi 1.5k, Core 2k (the GuessWithKanji decks) | | all | |

Some decks couldn't be tested. Spoonfed Chinese (183 mentions, the most recommended Chinese deck) has sentence cards
with no word field, Refold Mandarin 1k is not on AnkiWeb, Mosby's Medical Terminology Flash Cards (the terminology deck
Reddit names most) is scanned images, and AnKing (2,038 mentions) is a deck of medical facts, not terms.

## Limits

- **English and medical are judged on meaning only.** Whether the spelling or pronunciation follows from the parts
  is not judged.
- **Parts are matched by spelling.** Two morphemes spelled alike count as one (the -min- of the Latin suffix -men and
  the min of minor), and a model's split does not always use a roots deck's forms, so some terms stay unguessable
  after their roots are studied.
- **The labels come from one model.** For Japanese, GuessWithKanji measured Gemma 4 12B agreeing with a larger model
  on 86% of readings and 79% of meanings. Agreement was not measured for the new profiles.
- **Guessable assumes a part's meaning carries over.** A learner who met -er in teacher may not read it as "one who"
  in employer. The lower guess-rate rows show what is left when that often fails.
- **Two decks come shuffled.** 4000 Essential English Words and Oxford 3000 come in a mixed order, so their deck-order
  baseline is what you get with them in Anki, not an order by level.
- **One word per card.** Sentence decks, image decks and fact decks are out of reach.

## What it does

- **Reads your deck.** Any note type with a word field works. Fields are found by name and by what they hold (a short
  Japanese or Chinese word, kana or pinyin, an English meaning), so `Vocabulary-Kanji`, `Simplified` + `Pinyin`,
  `Term` + `Definition` or a word written with furigana (`漢字[かんじ]`) all work, and a reading field that holds a
  sentence is ignored. Your study history says which pieces you have met and when.
- **Splits each word into pieces** by its profile (above). In Japanese a piece is a kanji plus the reading it has in
  that word (だん in both 相談 and 面談), with the regular sound changes (rendaku, small tsu), and the split matches
  JmdictFurigana for 99.0% of 17,854 common words. In Chinese it's a character plus its pinyin syllable, and in
  English and medical terms it's the parts a model gives.
- **Judges guessability** from several sources, weighted when they disagree.
  - **Heuristic** (code, tunable). How common the word's reading of each piece is (in the dictionary, your deck, or
    both), and how close the word's meaning is to its pieces' meanings (embedding cosine with EmbeddingGemma, or plain
    word overlap when no embedding model is running). Tuned for Japanese on 2,038 labelled words, it scores an AUC of
    0.83 for meaning with EmbeddingGemma (0.73 with word overlap) and 0.83 for reading.
  - **Model labels.** Any model behind an OpenAI-style API (Gemma 4 through Ollama by default) labels words in
    batches, a daily cap at a time (100 a day by default), resumable, with a JSON schema that names the batch's words.
    Each profile has its own prompt, and for English and medical the model also gives the word's parts. For a whole
    deck at once with a cloud model, use `tools/label_parallel.py`.
  - **Crowd and deck labels.** You (or a group) label words while reviewing (Shift+G or right-click), share labels as
    a file, or ship them inside a deck you publish.
- **Plans the path.** A greedy order over your new cards makes as many words as possible guessable on arrival. When
  nothing is guessable yet it brings in an opener, one new piece at a time and a plain word first (見る before
  見っともない, 取る and 戻る before 取り戻す). It writes the order into Anki's new-card queue and plans again after
  each review session.
- **Options.** `deck_every` keeps part of a deck's own order (every n-th card), `need` asks for several sightings
  before a piece counts, and pattern spacing brings a learned piece back at growing gaps.
- **Dashboard.** It shows your free cards (cards studied, how many arrived guessable, words you could guess now), words
  guessable on arrival (deck order vs path), the next cards and why, your pieces, and for Japanese and Chinese the
  words whose characters have another common reading (could be confused).
- **Sentry tracing** (optional). Each labelling job is one trace in Sentry's AI agent format, a transaction per batch
  with its tokens, timing and unreadable words, plus a span per embedding call.

## Install

**No extra software needed.** Install the `.ankiaddon` from the
[releases](https://github.com/BlaiseLabs/GuessWithAnki/releases) (double-click it, or in Anki use Tools > Add-ons >
Install from file), or copy the `guesswithanki` folder into Anki's add-ons folder (Tools > Add-ons > View Files), then
restart Anki. Tools > GuessWithAnki > Dashboard plans for the first time.

Your deck options must let positions decide, so set the new card gather order to "Deck" or "Ascending position" and
the sort order to "Order gathered" or "Card type, then order gathered". The dashboard warns when they don't.

#### Recommended, Ollama for sharper judgments

Without a model, meanings are judged by word overlap and everything works. A model adds two things, sharper meaning
judgments (embeddings) and "Label with model", where a model judges each word. Since GuessWithAnki runs in desktop
Anki, we recommend installing [Ollama](https://ollama.com) on the same computer. It's free, runs models on your own
machine, and the add-on is already set up for it. Install it, then pull the two models.

```
ollama pull embeddinggemma        # meaning similarity (300M, runs on any computer)
ollama pull gemma4:12b-it-qat     # the labelling model (or any model, set it in the settings)
```

The embedding model is small and runs anywhere. The labelling model is much bigger, so if your computer struggles,
pull a smaller model and put its name in the `llm` setting. That's all. The add-on finds Ollama at its usual address
by itself.

#### Using another model server, or a cloud model

Ollama isn't required. The add-on talks to model servers through two separate settings, `embeddings` and `llm`, each
with its own address (`base_url`), model name and optional API key, so they can point to different places, for
example embeddings from a local Ollama and labels from a cloud model.

```json
"embeddings": {"base_url": "http://127.0.0.1:11434/v1", "model": "embeddinggemma", "api_key": ""},
"llm":        {"base_url": "http://127.0.0.1:11434/v1", "model": "gemma4:12b-it-qat", "api_key": ""}
```

It always speaks one format, OpenAI's API, which most model servers offer. For embeddings it calls
`{base_url}/embeddings`, and for labels it calls `{base_url}/chat/completions` and asks for a JSON answer that fits a
schema (if a server rejects schemas, it retries with plain JSON mode by itself). So any server that offers those two
endpoints works, including Ollama (its `/v1` address), LM Studio, llama.cpp's server, vLLM, OpenAI, and many cloud
providers through their OpenAI-compatible endpoints. A provider with its own format can be reached through a gateway
such as OpenRouter or LiteLLM. Use the address each server documents, including its `/v1` part.

- **API keys.** Cloud models need one. Put it in that block's `api_key` field, and the add-on sends it the standard
  way, as an `Authorization: Bearer` header. Local servers leave it empty. The key is stored in plain text in Anki's
  add-on settings on that computer.
- **Cloud models through Ollama.** Ollama also offers its own [cloud models](https://ollama.com/blog/cloud-models),
  which run on ollama.com's hardware but are used through your local Ollama. Sign in with `ollama signin`, then put a
  cloud model's name (they end in `:cloud`) in the `llm` setting, and the address stays the same, with no key in the
  add-on. Ollama doesn't pass requests on to other providers, though, so for a model from OpenAI or another company,
  point the add-on at that provider directly.
- **Picky models.** `reasoning_effort` is set to `"none"` by default, which stops thinking models such as Gemma 4 from
  spending their whole answer on hidden reasoning. Empty it for servers that reject the field. Some reasoning models
  also refuse a temperature, so add `"temperature": false` to the `llm` block for those.
- **Batch size.** Batches of 20 words fit Ollama's default 4,096-token context.

## Settings

Tools > GuessWithAnki > Settings (see `guesswithanki/config.md`). The ones that matter most are `search` (which notes),
`profile` (what kind of deck, `auto` by default), `path.window` (how many cards back a piece still counts as fresh),
`guessable` (the levels a word needs), `sources` (how much crowd, model and heuristic labels weigh), `llm.per_day`,
`free` (how the dashboard counts free cards) and `sentry_dsn`.

## Sharing a reordered deck

Anki's own export keeps the order. Use File > Export, pick "Anki Deck Package (.apkg)" and your deck, and leave
"Include scheduling information" off. Whoever imports it gets the new cards in GuessWithAnki's order, even without the
add-on. Cards you've already studied go back to their place in the path, since Anki remembers each card's original
position. (Tested with Anki 26.09, importing into a collection that already had cards.)

The order fits your own study history. Someone who imports the deck and also has GuessWithAnki gets it planned again
for theirs, the first time they open Anki. To share your guessability labels along with it, use Tools >
GuessWithAnki > Write labels into the deck before exporting (see below).

## Sharing labels

Labels are keyed by word and reading, so they work with any copy of a deck, and across decks that share words.

- **In a deck you publish.** Tools > GuessWithAnki > Write labels into the deck puts your votes (and the model's labels)
  into the notes as tags, `guesswithanki::reading::yes` and `guesswithanki::meaning::partly`, and into `_guesswithanki.json` in
  the deck's media (Anki keeps media files starting with `_` and exports them with the deck). Share the deck on
  AnkiWeb as usual, and anyone who installs it and GuessWithAnki gets the labels, counted as the source `deck`.
- **As a file.** Tools > GuessWithAnki > Export labels writes `{"schema": "guesswithanki-labels/1", "labels": [...]}`,
  and Import merges a file someone else exported (records already present are skipped). Several people's votes on the
  same word are averaged, one vote per person. Here's one record.

```json
{"word": "入口", "reading": "いりぐち", "reading_guessable": "yes", "meaning_guessable": "yes",
 "why_meaning": "enter + mouth", "helpers": ["入る", "出口"], "source": "crowd", "by": "a name"}
```

To go by people's votes only, set `"sources": {"crowd": 1, "deck": 1, "llm": 0, "heuristic": 0}`. There is no
central place to pool votes yet, so share files, or ask a deck's author to write them into the deck.

## Without Anki open

```
python tools/cli.py reorder collection.anki2      # close Anki first, or work on a copy
python tools/cli.py label collection.anki2 --n 100
python tools/import_deck.py deck.apkg out.anki2    # a shared deck into a collection of its own, fields shown
python tools/deck_report.py out.anki2 --files dir # what the path changes for a new learner
python tools/fsrs_sim.py out.anki2 --files dir --out sim.json   # the simulation behind the table above
python tools/fsrs_sim.py out.anki2 --files dir --out sim.json --params my_fsrs.json --retention 0.85   # with your FSRS
python tools/label_parallel.py out.anki2 --files dir --key-env OPENAI_API_KEY --threads 10   # a whole deck, cloud model
python tools/guess_index.py "Name=out.anki2=dir[=cfg.json]" ...   # the guessability table above
python tools/speedup_table.py "Name=sim.json" ...                 # the speed-up table above
```

## Development

```
pip install aqt pytest
bash tools/fetch_raw.sh             # KANJIDIC2, JMdict, JmdictFurigana into raw/ (EDRDG and Doublevil downloads)
python tools/build_data.py          # rebuilds guesswithanki/data/ and tools/common_words.json
python tools/build_hanzi.py         # hanzi.json, pinyin.json from CC-CEDICT (raw/cedict.txt.gz)
python tools/build_morphemes.py english labels.jsonl ...   # the english/medical part tables from model labels
python tools/make_demo.py demo.anki2 --n 2000 --study 150   # a demo deck from JMdict's common words
python -m pytest -q                 # core + a real Anki collection
GP_DEMO=demo.anki2 bash e2e/run.sh  # a real Anki under Xvfb, driven like a learner (menu, keyboard, dialogs)
bash tools/package.sh               # build/guesswithanki.ankiaddon
manim -qh docs/video/explainer.py Explainer   # the explainer video (Manim Community 0.19)
```

## Data and credits

- KANJIDIC2 and JMdict, by the Electronic Dictionary Research and Development Group (EDRDG), CC BY-SA 4.0, for kanji
  meanings and readings, the dictionary reading counts and the demo deck. JmdictFurigana (Doublevil, CC BY-SA 4.0)
  for checking the reading splitter.
- CC-CEDICT (MDBG, CC BY-SA 4.0) for Chinese character meanings, pinyin and reading counts.
- The English and medical part tables hold the parts and meanings a model (gpt-5.6-terra) gave while labelling the
  decks measured above, and no deck text. The derived files in `guesswithanki/data/` are shared under CC BY-SA 4.0.
- FSRS, by the open-spaced-repetition project. `tools/fsrs_sim.py` reimplements the FSRS-6 formulas of py-fsrs.
- Gemma and EmbeddingGemma (Google) through Ollama for the model labels and meaning similarity, and gpt-5.6-terra
  (OpenAI) for the labels behind the results.
- GuessWithKanji, the blueprint.

## Licence

The code is MIT (see `LICENSE`). The data in `guesswithanki/data/` is CC BY-SA 4.0 (see `guesswithanki/data/SOURCES.md`).
