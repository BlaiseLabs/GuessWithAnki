# GuessWithAnki: narration script

Read one paragraph per take; each paragraph is one recording (name the files by their number, 01, 02, ...).
A short pause between paragraphs is fine; any flubbed take can just be read again.

Recording tips without a good mic:
- a small, soft room (a closet or a room with a bed and curtains) beats a big empty one: less echo;
- phone about a hand's width (15-20 cm) from your mouth, a little off to the side so the p's and b's don't pop;
- airplane mode, and keep the phone still (no handling noise);
- read at your normal pace; the pauses between sentences give the video its timing.

## Intro

**01.** I've watched this happen so many times. Someone who's really good at Japanese sees a word they've never seen before, and they just know it. The reading, the meaning, all of it. And to me, honestly, that looked like black magic. So this video is about how I stopped thinking it was magic, using a bit of computer science and some Python.

## Disclaimer

**02.** Okay, quick disclaimer before we get into it. Later on you're going to see numbers like two times faster, maybe even six times faster. But that's not what this is about, right? This isn't a race. I'm not in a race with anybody, I'm not in a competition with anybody, and neither are you.

**03.** This is really just about being curious about something, and following that curiosity in a way that also makes learning the language more fun. And I don't want to push anyone into the over-optimization trap either. Every hour you spend optimizing your study system is an hour you could have spent actually immersed in the language.

## Why Python

**04.** Also, everything here is written in Python. None of this actually needs Python. You could do it in pretty much any language. I'm using Python because it's objectively the best programming language. It's the fastest, it's the most consistently designed, and multithreading in Python is famously easy.

**05.** Anyway. Moving on.

## The story

**06.** So, a bit of background. I'm still a beginner in Japanese. And over time I've watched people who are way further along, usually N2 or N1, go through flashcards full of words they say they've never seen. And again and again, they'd guess the reading and the meaning, and they'd be right. And not just one person, either. I saw it with a lot of different people. Meanwhile, to me, Japanese text basically looked like hieroglyphics. I couldn't even begin to understand how someone could have that kind of intuition.

**07.** Then, after a while of doing my own vocab cards, every now and then I'd catch myself doing it. I'd see a word for the first time, guess what it meant, flip the card, and it was exactly right. The first couple of times that happened, it honestly blew my mind. And it kind of flipped a light bulb on. How often does this actually happen? Is it just a fluke, or is it something you can count on?

## How guessable is a word?

**08.** So the first thing I looked at was how much the kanji overlap between words. Because if every word used completely unique kanji, you could never guess anything. But the more the kanji overlap, the more often a new word is made of pieces you already know. So I needed to pin down what a piece is. A piece is a kanji, together with the reading it has in that word. So den, in denki, is one piece. And a word is guessable when two things are true. Its reading follows from the usual readings of its pieces, and its meaning follows from what its pieces mean.

**09.** For the reading part, I didn't need anything fancy. There are two free dictionaries, KANJIDIC2 and JMdict, that list every kanji's readings and tens of thousands of words. A small Python function lines up each word's reading with its kanji, and then you just count. How often is this kanji read this way? If it's the usual reading, the reading is guessable.

**10.** The meaning part is harder. One way is embeddings. A small model turns text into a list of numbers, basically a point in space, where things with similar meanings end up close together. So if a word's meaning lands close to the meanings of its kanji, it's probably guessable. The easier way, honestly, is to just ask a language model. Give it a batch of words, and it tells you yes, partly, or no for each one.

**11.** So here's what that looked like for my own deck. Two thousand and thirty-eight words with kanji. The reading was guessable for 96% of them. The meaning was clearly guessable for 69%, and at least pointed you in the right direction for 95%. Only about one word in twenty gave you no clue at all. And both the reading and the meaning? 67%. So two out of every three words I was about to study, I could in theory guess on first sight. And that's where it got interesting, right? Because then the question is, how do I take advantage of that?

## The ordering problem and the greedy algorithm

**12.** Here's the catch. You can only guess a word if you've already met its kanji. You can't guess denki if you've never seen den. So the order you learn things in really matters. It basically turns into a min-max problem. How do I order my cards so I can guess as many words as possible, while learning as few cards as possible the hard way? And you can't just try every order. Two thousand cards can be ordered in so many ways that the number has over five thousand digits.

**13.** So I used one of the simplest ideas in computer science: a greedy algorithm. A greedy algorithm builds an answer one step at a time, and at every step it just takes whatever looks best right now. It never goes back and changes an earlier choice. It doesn't promise the perfect answer, but it's fast, and for a lot of problems it gets really close.

**14.** Here, every step asks one question. Of all the cards left, which one should come next? A card that's guessable right now wins, especially if you just saw its kanji. If nothing is guessable, it picks an opener: a card that brings in just one new piece. So toru, to take, comes first. Then modoru, to return. And then torimodosu, to take back, shows up already guessable. Run that over my deck, and of the next five hundred cards, the number that arrive guessable goes from 66 to 307.

## Does it actually help? The simulation

**15.** But guessable on paper is one thing. Does it actually help? To check, I simulated a learner doing Anki every day, twenty new cards a day, using FSRS, the same scheduling algorithm Anki uses. Each kanji piece gets its own memory that fades over time, and gets refreshed whenever a word with that piece shows up. And when a guessable word comes up and its pieces are still remembered, the learner can guess it. A card you get right the first time you see it is basically a free card. You never had to learn it.

**16.** And the best case is pretty wild. On a JLPT vocab deck, if you guessed perfectly, you'd learn just 16 cards to know your first 100 words. The other 84, you'd guess. That's over six times fewer cards. Nobody guesses perfectly, though. I checked my own reviews, and when a word was guessable and I'd seen its kanji recently, I got it right about 73% of the time. At 80%, those first hundred words take 35 cards instead of 100. Still almost three times fewer.

**17.** The gains are biggest early on. In smaller beginner decks they fade out by around a thousand words, because by then both orders have shown you most of the kanji anyway. And here's something I didn't expect. You also forget less. Every new word reinforces pieces you just learned, so you're not only learning words, you're practicing the pattern. Which, honestly, is exactly the intuition those advanced learners had.

## Other languages

**18.** So then the obvious next question was, does this only work for Japanese? I tried it with three more groups that use Anki a lot: people learning Chinese, people learning English, and medical students. I went through about sixteen hundred Reddit threads to find the decks each community actually recommends to beginners, and ran the same experiment on two decks for each. The only thing that changes between languages is what counts as a piece.

**19.** In Chinese, a piece is a character with its pinyin. And Chinese actually did even better than Japanese. A character usually has just one reading, so for about 96% of words the pronunciation follows straight from the characters. And the same characters show up over and over. In the HSK deck, 90% of words share every one of their characters with some other word. At 80% guessing, your first five hundred words take about half the cards. Roughly two times fewer, and it holds up even past a thousand words.

**20.** For English, a piece is a word part: a prefix, a root, or a suffix. And here the gains are a lot more modest, because most everyday English words just don't break into meaningful parts. Try guessing beach, or rock, from the spelling. What does work is word families. Once you know employ, then employer, employment and unemployed basically come for free. About a fifth to a quarter of these decks is guessable, and you're looking at about one and a half times fewer cards at five hundred words.

**21.** Medical terminology looked like the perfect case, right? It's literally built out of Greek and Latin roots. But the terminology deck on its own barely gained anything. That deck turned out to be small and pretty mixed. Abbreviations, drug names, everyday words. So the roots in it almost never come back in a second term.

**22.** Med students are usually told to learn all the roots first, so I tried putting a roots deck in front of it. Done that way, you go through almost a thousand roots before your first term even shows up, around day fifty. The guessable order only brings in the roots a term actually needs, right before that term. And you're guessing terms within the first two weeks.

**23.** So the ranking ends up Chinese, then Japanese, then English, then medicine. And it really comes down to two things: how many words are built from reusable pieces, and how predictable those pieces are.

## The add-on, and the close

**24.** So I packaged all of this into an Anki add-on called GuessWithAnki. It reorders your own deck's new cards this way, for Japanese, Chinese, English, or medical decks. It's free, and it's on GitHub. But if you take one thing from this video, don't let it be the speed-up. The thing that looked like black magic to me turned out to be a pattern. And patterns are something you can measure, play with, and actually learn. So, stay curious. And then go spend that time in the language.

---
24 paragraphs, 1731 words, about 9 minutes at your pace.