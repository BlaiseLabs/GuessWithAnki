# Shared Anki decks recommended to beginners (research, 2026-10-25, Korean added 2026-10-28)

How the decks in the README's results were picked. The raw Reddit data and the quote list are not included.

## How this was done

- **Sources.** Reddit through the official OAuth API (app-only), searched with top and relevance sorting, then the
  comments of every matching thread were read.
  - **Chinese.** 438 threads from r/ChineseLanguage, r/MandarinChinese, r/learnchinese, r/Chinese, plus r/Anki and
    r/languagelearning (only where the post is about Chinese).
  - **English.** 280 threads from r/EnglishLearning, r/EnglishLearner, r/learnEnglishOnline, r/ENGLISH,
    r/EnglishGrammar, r/IELTS, r/TOEFL, r/Anki, r/languagelearning and r/Refold.
  - **Medical.** 900 threads from r/medicalschool, r/medicalschoolanki, r/step1, r/Step2, r/Anki, r/premed, r/nursing,
    r/StudentNurse, r/MedicalAssistant, r/MedicalCoding, r/NewToEMS, r/PAstudent and other allied-health subs.
  - **Korean.** 622 threads (about 6,900 posts and comments) from r/Korean and r/learnkorean, plus r/Anki where the
    post is about Korean.
- **What "mentions" means.** The number of separate posts or comments that name the deck (by name, by AnkiWeb link, or
  by download link). It's a rough count of how much a deck is talked about, not a count of endorsements.
- **Deck details.** Card counts, fields, sample notes and ratings come from AnkiWeb's own `item-info` endpoint, which
  still works. AnkiWeb's deck search (`list-decks`) blocked searching after 3 queries ("Please log in to perform more
  searches", HTTP 429), so extra deck IDs were found through links people posted and a web search limited to
  ankiweb.net.
- **Checks.** Every quote collected was checked word for word against the Reddit text and its permalink.
- Nothing was posted. The decks measured were downloaded from AnkiWeb afterwards, and none is part of this repository.

## Recommendations for testing the word-ordering add-on

### Mandarin Chinese

1. **Refold Mandarin 1k (and 5k).** Free, downloaded from Notion or Google Drive, not on AnkiWeb. 41 mentions.
   - One word per note, with hanzi, pinyin, meaning, an example sentence, audio and an image.
   - It's the deck most often suggested to beginners as a word-level start.
   - Commenters say it comes from the same deck as the "HSK 1-6 (2012)" Google Drive deck (37 more mentions).
     Together that deck family has about 76 mentions in 55 threads.
2. **Mandarin Chinese: New HSK 3.0 Vocabulary and Characters.** AnkiWeb `1144807196`, 26 mentions, and the launch
   post had 334 upvotes.
   - 14,092 notes, 11,092 words plus 3,000 characters, with CC-CEDICT definitions and audio.
   - Each character note lists the HSK words built from that character, so it's the best structural fit for ordering
     pieces before compounds.
   - Beginners filter it by level tag.
3. **Spoonfed Chinese.** AnkiWeb copy `1271086873` (7,335 notes), and the author sells an updated version on Gumroad.
   - The most recommended deck by a wide margin, with 183 mentions in about 136 threads.
   - The cards are **sentences** (English, pinyin, hanzi and audio) roughly in frequency order, not a single word with
     its meaning. It's worth noting because it's so popular, but the add-on would have to work out the new word in each
     sentence.

- A small, clean HSK 1 option is **HSK 1 - JK** (`132435921`). It has the highest AnkiWeb rating for an
  English-language HSK 1 deck (113 up, 2 down, 150 notes), but Reddit rarely names it.
- A character-level option is **Most Common 3000 Chinese Hanzi Characters** (`39888802`), which has radical and
  frequency-rank fields.

### Korean

TTMIK (Talk To Me In Korean) is by far the most named source, with 271 mentions, followed by the "2,000 or 3,000 most
common words" lists (70), Evita's decks (57), Go Billy (50) and Sejong (34). Most TTMIK mentions are about its lessons
and books rather than one Anki deck.

1. **Korean Vocabulary by Evita.** AnkiWeb `4066961604`, the most-linked vocabulary deck (7 links, and Evita is named
   57 times). 6,500 notes with Korean, English, Hanja, audio and a frequency number. It starts with common beginner
   words and gets harder, and its Hanja field is filled for many Sino-Korean words.
2. **2k Essential Beginner Vocab by Mar.** AnkiWeb `1367759589`, 1,794 notes, made to go with Darakwon's "2000
   Essential Words for Beginners" and fully edited for errors in 2023.
3. **LoveofLearningKorean's My First 500 Words.** AnkiWeb `1799066060`, 500 notes, every word from TTMIK's "My First
   500 Words" with review decks every hundred words.

- Also linked often is **How To Study Korean Vocab, Unit 1** (`844864289`, 8 links), the vocabulary of
  HowToStudyKorean.com's first unit.
- **Korean Grammar Sentences by Evita** (`3614346923`) is popular too, but it's a sentence deck for grammar, not
  vocabulary.

### English learners

There's little to go on here. English learners on Reddit mostly say "make your own deck from what you read", and only
one shared deck comes up again and again.

1. **4000 Essential English Words (all books) [en-en].** 22 mentions in Anki and deck contexts.
   - One word per note, with the word, an English definition, an example, IPA, CEFR level, an image and audio.
   - The most-cited AnkiWeb copy (`1104981491`, "first in ratings") now returns `access_denied`, probably taken down.
     The content comes from a commercial textbook (Compass Publishing).
   - Copies still up are `413429709` "front and back (all books)" (3,598 notes, about 216 MB) and `1671103485`
     "Upgraded Version" (3,864 notes).
   - There are bilingual copies too, `989486361` [en-es] and `1813442257` [en-fa].
2. **[English] The Oxford 3000 Most Important Words.** AnkiWeb `1575087857`, 83 up and 3 down, 3,377 notes,
   English-only definitions, no audio.
   - The Oxford 3000 and 5000 lists come up as a family (about 7 mentions), not this exact deck. The list and the
     definitions belong to Oxford University Press.
3. An optional advanced comparison is **Lifelong Learning - Advanced English Vocabulary** (`1748072575`, 174 up, 8,098
   notes, 15 mentions). It's GRE and SAT level, and **not a beginner deck**.

Two more aren't good test targets.
- **Refold English** has 28 mentions, but it's paid, and most mentions are Spanish speakers asking for copies.
- **English Grammar In Use Exercises** (`1337411742`) is grammar cloze cards, not vocabulary.

### Medical students, terminology decks (the main picks)

Reddit's medical communities almost never name a specific terminology Anki deck. The usual advice is "learn the Greek
and Latin roots", Quizlet, or the free Des Moines University course. In the terminology threads collected, Quizlet comes
up in 79 comments across 47 threads, and the Des Moines course in 14 mentions.

1. **Medical Terminology & Abbreviations With Etymology.** AnkiWeb `1220822549`, 520 notes, 25 up and 0 down, updated
   April 2025.
   - Each term comes with an explicit breakdown into parts (for example "endarterium = en + artery").
   - It's the best text-based fit for the add-on, though Reddit never names it.
2. **The Hippocrates Code, Medical Greek and Latin.** AnkiWeb `1645339321`, 1,138 notes.
   - Clean fields (Term, Definition, Examples, Language, Part of speech), tagged as prefix, base or suffix.
   - Pair it with the first deck to test "parts before whole terms".
   - If the licence matters, the **Wikipedia-based Medical Greek and Latin Affixes deck** is the cleaner choice (513
     affixes, on Google Drive).
3. The most cited on Reddit, though it can't really be tested, is **Mosby's Medical Terminology Flash Cards**
   (`1588541422`, 82 up and 2 down, 600 notes).
   - Every card is a **scanned image** on both sides. With no text, the add-on can't read it unless it's OCR'd first.
   - It's a commercial Elsevier product, so the copyright risk is high.

- A larger set of composite terms is the **Concise Medical Dictionary deck** (about 11,000 terms, on Google Drive). It
  was converted from Oxford's commercial dictionary, so the licence is a concern.

### Medical students, the most popular fact deck (separate)

- **AnKing Step Deck v12** is by far the dominant deck, with 2,038 mentions in 641 threads in the medical subs. Zanki,
  the older deck it was built on, has 921.
  - About 31,000 cloze fact cards with heavy tags. Beginners start it in their first year by unsuspending cards by tag.
  - It's distributed through an AnkiHub subscription (about $5 a month, or a one-time snapshot), and the free offline
    v11 was withdrawn in 2025.
  - The cards aren't a term with its meaning, so it's a poor fit for a word-ordering add-on.

## Caveats

- **Licences.** Almost no deck states a licence. The clearest cases are New HSK 3.0, whose definitions come from
  CC-CEDICT (CC BY-SA), and the Wikipedia-based affix deck, which is probably CC BY-SA. Several popular decks are
  built from commercial books, including 4000 EEW, Oxford 3000, Mosby's, the Hippocrates Code, the Concise Medical
  Dictionary, Darakwon's 2000 Essential Words and TTMIK's My First 500 Words.
- **AnkiWeb availability changes.** Several decks people linked are now missing, including the original Spoonfed
  Chinese uploads (`867291675`, `53920083`), "HSK 2012" (`775653465`) and 4000 EEW (`1104981491`). Check each ID again
  right before downloading.
- **Rankings.** The order within each section is "best test candidate first" (beginner popularity, then fit for one
  word with its meaning). It's not pure mention order, and the mention counts are given with each deck.
