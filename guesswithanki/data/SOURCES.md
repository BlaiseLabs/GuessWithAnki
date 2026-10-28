kanji.json and readings.json are derived from KANJIDIC2 and JMdict, made by the Electronic Dictionary Research and
Development Group (EDRDG, https://www.edrdg.org/), used under the Creative Commons Attribution-ShareAlike 4.0
licence (https://www.edrdg.org/edrdg/licence.html). These derived files are shared under the same licence.
kanji.json holds each kanji's English meanings, on'yomi, kun'yomi, newspaper frequency rank and school grade.
readings.json holds, for each kanji, how many common JMdict words read it each way (split by GuessWithAnki's aligner).

hanzi.json and pinyin.json are derived from CC-CEDICT (https://cc-cedict.org/), used under the Creative Commons
Attribution-ShareAlike 4.0 licence, and these derived files are shared under the same licence. hanzi.json holds, for
each Chinese character, its English meanings (from the dictionary's one-character entries) and how many dictionary
words read it each way (pinyin syllable and tone). pinyin.json lists the pinyin syllables.

morphemes_english.json, morphemes_medical.json and morphemes_korean.json hold word parts and short meanings, as a
language model gave them when labelling the decks the README measures (gpt-5.6-terra for English and medical terms,
gpt-6.1-terra for Korean). A part is kept when two or more words used it. They hold no deck text, only a part and a
few words of meaning in each entry. Korean parts carry the Hanja a Sino-Korean syllable comes from, as in 학(學).
