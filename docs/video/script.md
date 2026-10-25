# Script draft: "Guessing words you've never seen" (working title)

The story: using computer science and Python to build an intuition that advanced learners seem to have by magic,
and checking whether it works beyond Japanese. About 13 minutes at a relaxed pace (~1,900 spoken words).

Look: 3Blue1Brown style (Manim, dark background, ink-like kanji). A recurring mascot, **Ji**: the kanji 字 ("ji",
character) with two googly eyes and little feet. Ji reacts during the talking-heavy parts (nods, squints at a
flashcard, sweats at a greedy algorithm). VO = voice-over. [ON SCREEN] = what the viewer sees.

---

## 0. Cold open (0:00–0:30)

[ON SCREEN] A flashcard flips up: 電気. Dark screen, a timer ticks. A voice off-screen: "...electricity? でんき?"
The card flips: でんき, electricity. A small "✓".

VO: I've watched this happen over and over. Someone who's good at Japanese sees a word they have never seen before,
and they just... know it. The reading and the meaning. To me, that looked like magic. This video is about how I
stopped thinking it was magic, using a bit of computer science and some Python.

[ON SCREEN] Title: **Guessing words you've never seen**. Ji pops up under the title and blinks.

## 1. Disclaimer: this isn't a race (0:30–1:15)

[ON SCREEN] A race track with runners. A big red X stamps over it. Ji walks off the track and sits under a tree with a
book.

VO: Quick disclaimer before we start. Later in this video you'll see numbers like "two times faster" or even "six
times faster". That isn't what this is about. I'm not in a race with anybody, and neither are you. This is about
being curious about something and following that curiosity in a way that also makes learning the language more
fun.

And a warning about the trap I'm describing: you can spend endless hours optimizing your study system. Every one of
those hours could have been spent actually immersed in the language. So take this as a curiosity, not a
productivity hack.

## 2. Why Python (1:15–1:45)

[ON SCREEN] A Python logo on a podium, a gold medal. Floating text appears one line at a time, each with a tiny
"(citation needed)" underneath: "objectively the best", "the most performant", "perfectly consistent design",
"multithreading is trivially easy". Ji raises an eyebrow at each line.

VO: Everything in this video is written in Python. None of these ideas need Python: you could do all of it in any
language. I'm using Python because it is objectively the best programming language. It's the fastest, the most
consistently designed, and multithreading in it is famously easy. (Pause.) Moving on.

## 3. The story (1:45–3:15)

[ON SCREEN] Over-the-shoulder shot of an Anki review screen, blurred. Words fly past as unreadable shapes.

VO: When I was starting out, I'd watch people at N2 or N1 go through flashcards full of words they said they had
never seen. And again and again, they'd guess the reading and the meaning correctly. I saw it with many different
people. They all seemed to have this skill, and to me Japanese text still looked like hieroglyphics. I could not
imagine how anyone could have an intuition like that.

[ON SCREEN] Same review screen, now the narrator's own. A new card: a word the narrator has never studied. A pause.
A guess typed in. The card flips: correct.

VO: Then, after a while of doing my own vocabulary cards, it started happening to me. Rarely, but sometimes I'd see a
word for the first time, guess what it meant, flip the card, and it was exactly right. The first few times it
happened, it blew my mind.

And that made me wonder: how often does this happen? Is it a rare fluke, or is it something you could count on?

[ON SCREEN] Ji holds up a magnifying glass. Title card: **How guessable is a word?**

## 4. Measuring guessability (3:15–6:00)

[ON SCREEN] 電気 splits apart: 電 (でん, electric) and 気 (き, spirit / energy). Then other words that share them slide
in: 電車 (でんしゃ, train), 天気 (てんき, weather).

VO: Japanese words are mostly built from kanji, and kanji repeat. If every word used kanji no other word used, you
could never guess anything. But the more kanji overlap between words, the more often a new word is made of pieces
you already know.

So I made "a piece" precise: a kanji, together with the reading it has in that word. 電 read でん is one piece. Then
a word is guessable when two things are true. Its reading follows from its pieces' usual readings, and its meaning
follows from its pieces' meanings.

### The reading

[ON SCREEN] A dictionary page (JMdict) turns into a bar chart: how many words read 電 as でん. Then a word splits
under a "knife" that cuts the reading into kanji-sized slices: 電気 / でん・き.

VO: For readings, I didn't need anything fancy. Two free dictionaries, KANJIDIC2 and JMdict, list every kanji's
readings and tens of thousands of words. A small Python function lines up a word's reading with its kanji, and then
I can count: how often is this kanji read this way across the dictionary? If it's the usual reading, the reading
is guessable. I checked the splitter against a hand-checked dataset: it agrees on 99% of 17,854 common words.

### The meaning

[ON SCREEN] Words appear as dots in a 2-D space. "electricity" lands right next to "electric" and "energy". An arrow
measures the small distance between them.

VO: Meaning is harder. One way is embeddings: a small model turns each piece of text into a list of numbers, a point
in space, so that things with similar meanings land close together. If the word's meaning lands close to its kanji's
meanings, it's probably guessable.

[ON SCREEN] A chat bubble: "Could a learner who knows 電 (electric) and 気 (spirit) guess 電気 (electricity)?" A reply
with a JSON card: meaning: yes, reading: yes.

VO: The easier way is to just ask a language model, with a fixed answer format, for a few dozen words at a time. That's
what I used for the numbers you're about to see.

### The result

[ON SCREEN] My deck: 2,038 words with kanji. Three bars fill up one by one:
- Reading guessable: **96%**
- Meaning guessable: **69%** (and **95%** at least partly)
- Both: **67%**

Ji's jaw drops.

VO: Here's my own deck: 2,038 words. The reading follows from the kanji for 96% of them. The meaning clearly
follows for 69%, and at least points in the right direction for 95%. Only about one word in twenty gives you no
clue at all. And two thirds of the deck, 67%, are guessable in both reading and meaning.

So two out of three words I was about to study, I could, in principle, guess on first sight. The question became:
how do I take advantage of that?

## 5. The ordering problem and the greedy algorithm (6:00–8:30)

[ON SCREEN] A shuffled stack of 2,000 cards. Some glow (guessable), most don't. A counter below: "guessable when they
arrive: 66 of the next 500".

VO: Here's the catch. A word is only guessable if you've already met its kanji. You can't guess 電気 if you've never
seen 電. So the order matters. If the deck shows you 電気 before any other word with 電, you just have to memorize
it.

So the real question is a sorting problem: in what order should I learn these words so that as many of them as
possible arrive guessable, using as few memorized cards as possible?

[ON SCREEN] The number 2,000! appears, then expands into a number with 5,736 digits that scrolls off the screen.

VO: You can't try every order. 2,000 cards can be ordered in a number of ways with over five thousand digits. So I
used one of the simplest ideas in computer science: a greedy algorithm.

[ON SCREEN] Ji at a buffet, taking the best-looking dish at each step without looking at the rest of the table.

VO: A greedy algorithm builds an answer one step at a time, and at every step it takes whatever looks best right
now. It never goes back to change an earlier choice. It doesn't promise the perfect answer, but it's fast, and for
a lot of problems it gets very close.

Here, every step asks: of all the cards left, which one should come next?

[ON SCREEN] Three cards: 取る (とる, to take), 戻る (もどる, to return), 取り戻す (とりもどす, to take back). Scores
appear over each card as the narrator explains.

VO: Each card gets a score.
- A card that's guessable right now, because all its pieces were seen recently, scores best. And the more recently
  you met its pieces, the better.
- If nothing is guessable, the algorithm picks an "opener": a card that brings in one new piece, preferably one that
  unlocks other guessable words.
- And it would rather bring in pieces one at a time. So 取る comes first, then 戻る, and then 取り戻す arrives
  already guessable: take, plus return, gives "take back".

[ON SCREEN] The shuffled stack re-sorts itself into a path. Guessable cards light up in long runs. The counter climbs:
"66 → 307 of the next 500".

VO: Run that over my deck, and of the next 500 cards, the number that arrive guessable goes from 66 to 307.

## 6. Does it actually help? The simulation (8:30–10:15)

[ON SCREEN] Two identical stick-figure learners, side by side, each with a calendar. Left: "deck order". Right:
"guessable order". Days flip by.

VO: Guessable on paper is one thing. Does it help an actual learner? To check, I simulated one. Every day, the
simulated learner studies 20 new cards and does all their reviews, using FSRS, the scheduling algorithm Anki itself
uses, with the same formulas. Each kanji piece has its own memory that fades and gets refreshed whenever a word with
it shows up. When a guessable word arrives and its pieces are still remembered, the learner guesses it, and gets it
right at some rate. A card you get right on first sight is a free card: you never had to learn it.

[ON SCREEN] A slider: "guess accuracy". At 100%: "100 words: 16 cards learned instead of 100". The other 84 cards
fall into a "free" bin.

VO: The best case is striking. On a JLPT vocabulary deck, with perfect guessing, you'd learn just 16 cards to know
the first 100 words. The other 84 you'd guess. That's over six times fewer cards.

[ON SCREEN] Slider slides to 80%. Numbers update: "100 → 35, 2.9×". A small note: "my own guesses: 73% right".

VO: Nobody guesses perfectly, though. I checked my own reviews: when a word was judged guessable and I'd seen its
kanji recently, I got it right about 73% of the time. At 80%, that first hundred words takes 35 cards instead of
100. Still almost three times fewer.

[ON SCREEN] The speed-up curve over 100, 500, 1,000 words, dropping off for small decks.

VO: The effect is biggest early. In smaller beginner decks it fades by a thousand words, because by then both orders
have shown you most of the kanji anyway.

[ON SCREEN] Two "forgotten" counters. Deck order: 155. Guessable order: 76.

VO: And something I didn't expect: you also forget less. In the simulation, the guessable order had far fewer
forgotten reviews, because every word you meet reinforces pieces you just learned. You're not only learning words,
you're practicing the pattern, which is exactly the intuition those advanced learners had.

## 7. Does it work for other languages? (10:15–12:30)

[ON SCREEN] A world map. Pins: Japan, China, an "ABC" pin for English learners, a stethoscope pin for medical
students. Ji puts on a backpack.

VO: Then the obvious question: is this a Japanese thing, or does it work in general? I picked three more communities
that use Anki a lot: people learning Chinese, people learning English, and medical students. I read about 1,600
Reddit threads to find the decks each community recommends to beginners, and ran the same experiment on two decks
for each.

The only thing that changes between languages is what counts as a piece.

[ON SCREEN] Three side-by-side splits:
- 开学: 开 kāi (open) + 学 xué (study) = start of term
- unemployed: un- + employ + -ed
- hepatitis: hepat (liver) + -itis (inflammation)

### Chinese

VO: In Chinese, a piece is a character with its pinyin syllable, and the data comes from a free dictionary,
CC-CEDICT. Chinese did even better than Japanese. A character usually has just one reading, so for 96 to 97% of
words the pronunciation follows from the characters. And the same characters come back constantly: in the HSK deck,
90% of words share every character with some other word.

[ON SCREEN] The Chinese path: 大, 好, then 好人 (good person) lights up; 开, 大学生, then 开学 lights up. The explorer
chart with Chinese bold: about 2× at 500 words, at 80% accuracy.

### English

VO: For English learners, a piece is a word part: a prefix, a root or a suffix. A language model splits each word into
parts with their meanings. Here the gains are more modest, because most common English words don't split into
meaningful parts: try guessing "beach" or "rock" from their spelling. What does work is families of words: once you
know "employ", then "employer", "employment" and "unemployed" come almost free. About a fifth to a quarter of these
decks is guessable, and it's about 1.5× at 500 words.

### Medicine

VO: Medical terminology looked like the perfect case: it's literally built from Greek and Latin roots. But the
terminology deck on its own barely gained, and the reason was surprising. That deck is small and mixed, with
abbreviations, drug names and everyday words, and the roots in it rarely come back in a second term.

[ON SCREEN] Two timelines. "Roots first": 982 root cards, then terms starting on day 50. "Guessable path": roots and
terms interleaved, 68 free terms by day 14.

VO: Medical students are usually told to learn all the roots first. So I added a roots deck in front of the terms.
Learned that way, you study about 980 roots before your first term even shows up, on day 50. The guessable order
brings in only the roots a term needs, right before it, and you're guessing terms within the first two weeks.

[ON SCREEN] The explorer chart, all four lines: Chinese on top, then Japanese, English, medicine.

VO: So the ranking: Chinese, then Japanese, then English, then medicine. It depends on two things: how many words
are built from reusable pieces, and how predictable those pieces are.

## 8. The add-on and the close (12:30–13:15)

[ON SCREEN] The GuessWithAnki dashboard on a Chinese deck: "Guessable on arrival, next 500: 6 → 321". Then the GitHub
page.

VO: I packaged all of this into an Anki add-on called GuessWithAnki. It reorders your own deck's new cards this way,
for Japanese, Chinese, English or medical decks. It's free and on GitHub.

[ON SCREEN] Back to the opening flashcard, 電気. This time it's the narrator guessing. Ji gives a thumbs up.

VO: But if you take one thing from this video, don't let it be the speed-up. Let it be this: the thing that looked like
magic to me turned out to be a pattern, and patterns are something you can measure, play with, and learn. Stay
curious. And then go spend that time in the language.

---

## Facts used, and where they come from

| Claim | Number | Source |
|---|---|---|
| My deck's guessability | 2,038 words: reading 96%, meaning 69% (95% at least partly), both 67% | terra labels of the BJT deck (GuessWithKanji work) |
| Reading splitter check | 99.0% of 17,854 common words | GuessWithKanji README (vs JmdictFurigana) |
| Path on my deck | 66 → 307 guessable in the next 500 | GuessWithKanji measurement |
| Best case | JLPT N5–N1: 100 words from 16 cards (6.2×), 100% guess rate | GuessWithKanji README table |
| 80% guess rate | JLPT: 100 words from 35 cards (2.9×) | same |
| My real guess rate | 73% right when judged guessable and kanji recent | my own Anki reviews |
| Forgetting | Kaishi, day 30, 80%: 160 → 115 forgotten; Core 2k 189 → 72 | GuessWithAnki docs/results.md |
| Chinese | reading guessable 96–97%; 90% of HSK 3.0 words share every character; 1.8–2.0× at 500 words (80%) | GuessWithAnki README |
| English | 20–27% guessable; 1.4–1.6× at 500 words (80%) | same |
| Medical | terminology deck 1.0×; roots first: terms start day 50; path: 68 free by day 14 | same |
| Reddit research | ~1,600 threads | docs/deck_research.md |

Note on the forgetting beat: the 155 → 76 shown on screen is Kaishi at a 100% guess rate (day 30); use 160 → 115 if
the scene stays at 80%.
