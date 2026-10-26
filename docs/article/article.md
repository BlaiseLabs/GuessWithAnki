---
title: "GuessWithAnki, let your Anki deck hand you words you can guess (Japanese, Chinese, English, medicine)"
published: false
tags: devchallenge, hf26challenge, gemma, sentry
cover_image: https://raw.githubusercontent.com/BlaiseLabs/GuessWithAnki/main/docs/article/cover.png
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 3, Slow and Steady](https://dev.to/challenges/hacktoberfest-week3-2026-10-19)*

**[VIDEO GOES HERE. Upload the video, then replace this line with the embed tag and the video's link]**

I've watched this happen so many times. Someone who's really good at Japanese, usually N2 or N1, goes through flashcards full of words they say they've never seen, and they just know them. The reading, the meaning, all of it. To me, as a beginner, that looked like black magic. Japanese text was basically hieroglyphics.

Then, after a while of doing my own vocab cards, I'd catch myself doing it every now and then. I'd see a word for the first time, guess what it meant, flip the card, and it was exactly right. It honestly blew my mind, and it made me wonder. How often does this actually happen? Is it a fluke, or something you can count on?

This post is about answering that with a bit of computer science and some Python, and turning the answer into an Anki add-on that does the lazy thing for you. It orders your cards so that a lot of them arrive already guessable.

Quick disclaimer, though. You'll see numbers like "two times fewer cards" below, and that isn't what this is about. I'm not in a race with anybody, and neither are you. This is about following a curiosity in a way that also makes learning the language more fun, and every hour you spend optimizing your study system is an hour you could have spent immersed in the language.

![A card for 電気, guessed on first sight](https://raw.githubusercontent.com/BlaiseLabs/GuessWithAnki/main/docs/article/hero_card.png)

## What I Built

**[GuessWithAnki](https://github.com/BlaiseLabs/GuessWithAnki)** is an Anki add-on that reorders a deck's new cards so each word arrives *guessable*. The pieces it's built from came up in the cards you just studied, and its meaning (and its reading, where there is one) follows from them. You stop memorizing a share of your words and start guessing them right on first sight. A card you get right the first time is a free card, because you never had to learn it.

It's the sequel to [GuessWithKanji](https://github.com/BlaiseLabs/GuessWithKanji), which did this for Japanese only. The question this time was whether the idea works beyond Japanese, so it handles four kinds of deck.

| Profile | A piece is | Guessable when |
|---|---|---|
| Japanese | a kanji with the reading it has in the word (電 read でん) | the meaning and the reading follow from the pieces |
| Chinese | a character with its pinyin syllable and tone (开 read kāi) | the meaning and the pinyin follow |
| English | a prefix, root or suffix (un-, employ, -ed) | the meaning follows |
| Medical | a Greek or Latin root or affix (hepat, -itis) | the meaning follows |

#### Why it rewards laziness

The whole point is doing less. The add-on finds the words you could guess, then hands them to you right after the pieces that give them away, so you get to skip learning them.

## Demo

The video at the top is the demo. It's the whole idea in about nine minutes, with the results for every language. Here's the add-on itself, running on a Chinese deck in Anki.

![The GuessWithAnki dashboard on an HSK deck, guessable on arrival 6 → 321](https://raw.githubusercontent.com/BlaiseLabs/GuessWithAnki/main/docs/video/assets/dashboard_zh.png)

Of the deck's next 500 new cards, 6 arrive guessable in the deck's own order and 321 in GuessWithAnki's.

## Code

- **[BlaiseLabs/GuessWithAnki](https://github.com/BlaiseLabs/GuessWithAnki)** has the add-on, the measurement tools, the results, and the video's source (Manim scenes, narration and build).
- **[BlaiseLabs/GuessWithKanji](https://github.com/BlaiseLabs/GuessWithKanji)** is the Japanese-only original.

## How I Built It

### 1. How guessable is a word?

The first thing I looked at was how much the kanji overlap between words. If every word used completely unique kanji, you could never guess anything. The more they overlap, the more often a new word is made of pieces you already know.

![A piece is a kanji plus the reading it has in that word](https://raw.githubusercontent.com/BlaiseLabs/GuessWithAnki/main/docs/article/pieces.png)

#### The reading

Nothing fancy here. Two free dictionaries, KANJIDIC2 and JMdict, list every kanji's readings and tens of thousands of words. A small Python function lines up each word's reading with its kanji (it agrees with JmdictFurigana on 99% of 17,854 common words), and then you just count. 気 is read き in 130 dictionary words and け in 14, so き is the usual reading, and a word that uses it is guessable.

#### The meaning

There are two ways, both with open models.

- **Embeddings.** EmbeddingGemma turns each meaning into a point in space. If the word's meaning lands close to its kanji's meanings, it's probably guessable. Tuned on labelled words, that scores an AUC of 0.83 (plain word overlap gets 0.73).
- **Ask a model.** Gemma 4 runs locally through Ollama and labels words in batches as yes, partly or no for the reading and the meaning, with a JSON schema that names the batch's exact words.

#### My own deck

Here's what that looked like for my deck of 2,038 words with kanji.

![Reading 96%, meaning 69% (95% at least a hint), no clue 5%](https://raw.githubusercontent.com/BlaiseLabs/GuessWithAnki/main/docs/article/guessable_share.png)

Both the reading and the meaning came out at **67%**. So two out of every three words I was about to study, I could in theory guess on first sight.

### 2. The order, and a greedy algorithm

Here's the catch. You can only guess a word if you've already met its pieces, so you can't guess 電気 if you've never seen 電. It becomes a min-max problem. How do I order my cards so I can guess as many words as possible, while learning as few cards as possible the hard way?

You can't just try every order, since 2,000 cards can be ordered in a number of ways with 5,736 digits. So I used one of the simplest ideas in computer science, a **greedy algorithm**. It builds the order one card at a time, and at every step it takes whatever looks best right now, never going back to change an earlier choice. It doesn't promise the perfect answer, but it's fast, and for a lot of problems it gets really close.

![A greedy algorithm takes the best-looking branch at every step](https://raw.githubusercontent.com/BlaiseLabs/GuessWithAnki/main/docs/article/greedy_tree.png)

Every step asks which of the cards left should come next.

- A card that's guessable right now wins, especially if you just saw its pieces.
- If nothing is guessable, it picks an *opener*, a card that brings in just one new piece, ideally one that unlocks other words. So 取る (toru, to take) comes first, then 戻る (modoru, to return), and then 取り戻す (torimodosu, to take back) shows up already guessable.

On my deck, of the next 500 cards, the number that arrive guessable goes from **66 to 307**.

![500 cards, 66 guessable in deck order and 307 on the guessable path](https://raw.githubusercontent.com/BlaiseLabs/GuessWithAnki/main/docs/article/path_grid.png)

### 3. Does it actually help?

Guessable on paper is one thing. To check, I simulated a learner doing Anki every day for 100 days, with 20 new cards a day and every review done, scheduled by FSRS-6 (the algorithm Anki uses, reimplemented and checked against py-fsrs). Each piece gets its own memory that fades and gets refreshed whenever a word with that piece shows up, and a guessable word can be guessed if its pieces are still remembered.

The best case is pretty wild. On a JLPT vocab deck, with perfect guessing, you'd learn 16 cards to know your first 100 words, and the other 84 you'd guess. Nobody guesses perfectly, though. I checked my own reviews, and when a word was guessable and I'd seen its kanji recently, I got it right about **73%** of the time. At 80%, the first 100 words take 35 cards instead of 100.

![At 80% guessing, 35 learned and 65 guessed, 2.9×](https://raw.githubusercontent.com/BlaiseLabs/GuessWithAnki/main/docs/article/free_grid.png)

And here's something I didn't expect. You also forget less. Every new word reinforces pieces you just learned, so you're not only learning words, you're practicing the pattern. In the simulation, forgotten reviews by day 30 drop from 189 to 72 on Core 2k.

### 4. Does it work beyond Japanese?

I went through about 1,600 Reddit threads (through Reddit's API) to find the decks each community actually recommends to beginners, and ran the same experiment on two decks each for Chinese learners, English learners and medical students. The only thing that changes between languages is what counts as a piece. (For speed, the 16,331 words across these decks were labelled in parallel by a cloud model, about 2.1M tokens. The add-on itself labels with Gemma, locally, a batch at a time.)

![开学, 开 kāi (open) plus 学 xué (study), the start of term](https://raw.githubusercontent.com/BlaiseLabs/GuessWithAnki/main/docs/article/chinese.png)

| Deck | Guessable | Cards to reach 500 words, at 80% guessing | Speed-up |
|---|---|---|---|
| New HSK 3.0, levels 1–4 (Chinese) | 71% | 392 → 200 | **2.0×** |
| HSK 2012, levels 1–5 (Chinese) | 66% | 473 → 256 | **1.8×** |
| Core 2k (Japanese) | 60% | 481 → 265 | **1.8×** |
| Kaishi 1.5k (Japanese) | 64% | 474 → 282 | **1.7×** |
| Oxford 3000 (English) | 27% | 494 → 303 | **1.6×** |
| 4000 Essential English Words | 20% | 494 → 356 | **1.4×** |
| Medical Terminology with Etymology | 27% | 482 → 474 | 1.0× |

![Speed-up at 500 words, Chinese 1.9×, Japanese 1.8×, English 1.5×, medical 1.1×](https://raw.githubusercontent.com/BlaiseLabs/GuessWithAnki/main/docs/article/ranking.png)

#### Chinese did even better than Japanese

A character usually has one reading, so for about 96% of words the pinyin follows from the characters, and 90% of HSK words share every character with another word. It keeps a 1.6–1.8× lead past a thousand words.

#### English is more modest

Most everyday English words don't break into meaningful parts (try guessing "beach" from its spelling). What works is word families. Once you know *employ*, then *employer*, *employment* and *unemployed* come almost free.

#### Medicine was the surprise

It looks like the perfect case, since it's built from Greek and Latin roots, but the terminology deck on its own barely gained. It's small and mixed (abbreviations, drug names, everyday words), so its roots rarely come back in a second term. Med students are told to learn all the roots first, and done that way, with a roots deck in front, you go through 982 root cards before your first term shows up, around day 50. The guessable order brings in only the roots a term needs, right before it, and you're guessing terms within the first two weeks.

So the ranking comes down to two things. How many words are built from reusable pieces, and how predictable those pieces are.

### 5. Making the video, with open models

The video is a 3Blue1Brown-style explainer built in Manim, with a mascot named Gaku (学, "study") who reacts while I talk. The narration is my own voice, cloned, and it all runs locally on a Mac mini.

- **The voice.** Qwen3-TTS (1.7B, open weights) through MLX, cloned from **5.7 seconds** of me reading. Whole paragraphs are voiced in one go so the delivery flows. Whisper then finds the pauses between sentences and the audio is cut there, so every animation beat lines up with its sentence.
- **Checking it.** Every take is transcribed with Whisper and compared word for word with the script, and bad takes are redone automatically.
- **Japanese pronunciation.** The clone kept saying とる (toru) as "toh-ruh", and no respelling fixed it. So I recorded that paragraph and the intro myself and ran them through **voice conversion** (CosyVoice2, also open, also on MLX). That keeps my pronunciation and timing, laughs and stumbles included, in the clone's voice.
- **Layout tests.** Overlap bugs are hard to spot by eye, so a checker runs after every animation and flags text over text, text sticking out of its box, anything over Gaku, and anything off the frame. It found 30 problems, plus a bug where Gaku's eyebrows collapsed into a dot at the center of the screen.

## Why Does Open Innovation Matter?

None of this exists without open work. The data is open (KANJIDIC2 and JMdict from EDRDG, CC-CEDICT for Chinese, all CC BY-SA). The scheduler is open (FSRS, from the open-spaced-repetition project). And the models are open and run on my own machines, with Gemma 4 and EmbeddingGemma for the add-on, and Qwen3-TTS, CosyVoice2 and Whisper for the video. That's what makes it possible for one learner to go from "how do they do that?" to actually measuring it.

It also means anyone can check it. The add-on works with no server at all, and the built-in heuristics alone judged 68% of a 4,995-word HSK deck guessable, about the same share as the model labels. Guessability labels are plain data you can share, or ship inside a deck you publish, so a community can improve them together.

## The Lazy Payoff

At an 80% guess rate, your first 500 words take about half the cards in Chinese, and a little over half in Japanese. You get a lot of words for free, you forget less, and you spend more of your time just recognizing patterns. Which, honestly, is exactly the intuition those advanced learners had.

![Black magic, crossed out, became a pattern](https://raw.githubusercontent.com/BlaiseLabs/GuessWithAnki/main/docs/article/gaku_end.png)

## Prize Categories

#### Best Use of Gemma

Gemma 4 labels the words' guessability locally through Ollama, in batches of 20 with a JSON schema naming the batch's words and a daily cap. EmbeddingGemma judges how close a word's meaning is to its pieces' meanings. On 1,839 words of my deck, Gemma 4 12B agreed with a much larger cloud model on 86% of readings and 79% of meanings.

#### Sentry Agent Tracing

Every labelling job is a trace in a self-hosted Sentry, in Sentry's AI agent format, with a transaction per batch (its tokens, timing and unreadable words) and a span per embedding call. The traces found real bugs.

- With thinking on, Gemma answered with nothing. The fix was `reasoning_effort` set to `none`.
- Batches of 40 overflowed Ollama's default 4,096-token context and crashed the parser. The fix was batches of 20.
- Gemma 4 E4B answered 1 word out of 20 with perfectly valid JSON. The schema now fixes the exact words and their count.
- Long jobs vanished from the tracer. Each batch is now its own transaction.

After those fixes, Gemma 12B labelled all 1,839 words with no failures in 2.3 hours.
