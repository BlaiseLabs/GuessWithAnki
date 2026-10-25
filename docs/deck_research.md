# Shared Anki decks recommended to beginners (research, 2026-10-25)

How the decks in the README's results were picked. The raw Reddit data and the quote list are not included.

## How this was done

- **Sources:**
  - Reddit through the official OAuth API (app-only). Searched with top and relevance sorting, then read the comments of every matching thread.
  - **Chinese:** 438 threads from r/ChineseLanguage, r/MandarinChinese, r/learnchinese, r/Chinese, plus r/Anki and r/languagelearning (only where the post is about Chinese).
  - **English:** 280 threads from r/EnglishLearning, r/EnglishLearner, r/learnEnglishOnline, r/ENGLISH, r/EnglishGrammar, r/IELTS, r/TOEFL, r/Anki, r/languagelearning, r/Refold.
  - **Medical:** 900 threads from r/medicalschool, r/medicalschoolanki, r/step1, r/Step2, r/Anki, r/premed, r/nursing, r/StudentNurse, r/MedicalAssistant, r/MedicalCoding, r/NewToEMS, r/PAstudent and other allied-health subs.
- **What "mentions" means:** the number of separate posts or comments that name the deck (by name, by AnkiWeb link, or by download link). It is a rough count of how much a deck is talked about, not a count of endorsements.
- **Deck details:** card counts, fields, sample notes and ratings come from AnkiWeb's own `item-info` endpoint, which still works.
  - AnkiWeb's deck search (`list-decks`) blocked searching after 3 queries ("Please log in to perform more searches", HTTP 429). Extra deck IDs were found through links people posted and a web search limited to ankiweb.net.
- **Checks:** every quote in the JSON was checked word for word against the collected Reddit text and its permalink.
- Nothing was posted. The decks measured were downloaded from AnkiWeb afterwards; none is part of this repository.

## Recommendations for testing the word-ordering add-on

### Mandarin Chinese

1. **Refold Mandarin 1k (and 5k)**: free; download from Notion/Google Drive, not on AnkiWeb. 41 mentions.
   - One word per note: hanzi, pinyin, meaning, example sentence, audio, image.
   - It is the deck most often suggested to beginners as a word-level start.
   - Commenters say it comes from the same deck as the "HSK 1-6 (2012)" Google Drive deck (37 more mentions). Together that deck family has about 76 mentions in 55 threads.
2. **Mandarin Chinese: New HSK 3.0 Vocabulary and Characters**: AnkiWeb `1144807196`. 26 mentions; the launch post had 334 upvotes.
   - 14,092 notes: 11,092 words plus 3,000 characters, with CC-CEDICT definitions and audio.
   - Each character note lists the HSK words built from that character, so it is the best structural fit for ordering pieces before compounds.
   - Beginners filter it by level tag.
3. **Spoonfed Chinese**: AnkiWeb copy `1271086873` (7,335 notes); the author sells an updated version on Gumroad.
   - The most recommended deck by a wide margin: 183 mentions in about 136 threads.
   - The cards are **sentences** (English / pinyin / hanzi + audio) roughly in frequency order, not single word + meaning. It is worth including because it is so popular, but the add-on would have to work out the new word in each sentence.

- A small, clean HSK 1 option: **HSK 1 - JK** (`132435921`). It has the highest AnkiWeb rating for an English-language HSK 1 deck (113 up / 2 down, 150 notes), but Reddit rarely names it.
- A character-level option: **Most Common 3000 Chinese Hanzi Characters** (`39888802`). It has radical and frequency-rank fields.

### English learners

There is little to go on here. English learners on Reddit mostly say "make your own deck from what you read". Only one shared deck comes up again and again.

1. **4000 Essential English Words (all books) [en-en]**: 22 mentions in Anki/deck contexts.
   - One word per note: word, English definition, example, IPA, CEFR level, image, audio.
   - **Caveat:** the most-cited AnkiWeb copy (`1104981491`, "first in ratings") now returns `access_denied`, probably taken down. The content comes from a commercial textbook (Compass Publishing).
   - Copies still up: `413429709` "front and back (all books)" (3,598 notes, ~216 MB) and `1671103485` "Upgraded Version" (3,864 notes).
   - Bilingual copies: `989486361` [en-es] and `1813442257` [en-fa].
2. **[English] The Oxford 3000 Most Important Words**: AnkiWeb `1575087857`. 83 up / 3 down, 3,377 notes, English-only definitions, no audio.
   - The Oxford 3000/5000 list comes up as a family (about 7 mentions), not this exact deck. The list and definitions belong to Oxford University Press.
3. Optional advanced control: **Lifelong Learning - Advanced English Vocabulary** (`1748072575`, 174 up, 8,098 notes, 15 mentions). It is GRE/SAT level and **not a beginner deck**.

Not good test targets:
- **Refold English**: 28 mentions, but it is paid, and most mentions are Spanish speakers asking for copies.
- **English Grammar In Use Exercises** (`1337411742`): grammar cloze cards, not vocabulary.

### Medical students: terminology decks (main picks)

Reddit's medical communities almost never name a specific terminology Anki deck. The usual advice is "learn the Greek/Latin roots", Quizlet, or the free Des Moines University course. In the terminology threads collected, Quizlet comes up in 79 comments across 47 threads, and the Des Moines course in 14 mentions.

1. **Medical Terminology & Abbreviations With Etymology**: AnkiWeb `1220822549`. 520 notes, 25 up / 0 down, updated 2025-04.
   - Each term comes with an explicit breakdown into parts (e.g. "endarterium = en + artery").
   - This is the best text-based fit for the add-on, though Reddit never names it.
2. **The Hippocrates Code: Medical Greek and Latin**: AnkiWeb `1645339321`. 1,138 notes.
   - Clean fields (Term / Definition / Examples / Language / Part of speech), tagged as prefix, base or suffix.
   - Pair it with #1 to test "parts before whole terms".
   - If licence matters, swap in the **Wikipedia-based Medical Greek and Latin Affixes deck** instead (513 affixes, Google Drive link in the JSON).
3. Most cited on Reddit, but you can't really test with it: **Mosby's Medical Terminology Flash Cards** (`1588541422`, 82 up / 2 down, 600 notes).
   - Every card is a **scanned image** on both sides. With no text, the add-on can't parse it unless you OCR it first.
   - It is a commercial Elsevier product, so copyright risk is high.

- Larger set of composite terms if needed: **Concise Medical Dictionary deck** (about 11k terms, Google Drive). It was converted from Oxford's commercial dictionary, so the licence is a concern.

### Medical students: most popular fact deck (separate)

- **AnKing Step Deck v12**: by far the dominant deck (2,038 mentions in 641 threads in the med subs). Zanki, the older deck it was built on, has 921.
  - About 31,000 cloze fact cards with heavy tags. Beginners start it in M1 by unsuspending cards by tag.
  - It is distributed through an AnkiHub subscription (about $5/month, or a one-time snapshot); the free offline v11 was withdrawn in 2025.
  - The cards are not term + meaning, so it is a poor fit for a word-ordering add-on.

## Caveats

- **Licences:** almost no deck states a licence.
  - The clearest cases: New HSK 3.0 definitions come from CC-CEDICT (CC BY-SA), and the Wikipedia-based affix deck is probably CC BY-SA.
  - Several popular decks are built from commercial books: 4000 EEW, Oxford 3000, Mosby's, Hippocrates Code, Concise Medical Dictionary.
- **AnkiWeb availability changes:** several decks people linked are now missing, including the original Spoonfed Chinese uploads (`867291675`, `53920083`), "HSK 2012" (`775653465`) and 4000 EEW (`1104981491`). Check each ID again right before downloading.
- **Rankings:** order in the JSON is "best test candidate first" (beginner popularity, then fit for one term + meaning). It is not pure mention order; mention counts are in each entry.
