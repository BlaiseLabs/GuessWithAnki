**search**. Which notes to plan, as an Anki search (for example `deck:Japanese`). Empty means every note whose type has a word field.

**profile**. What kind of deck it is, `japanese`, `chinese`, `english`, `medical`, or `auto`. The default, `auto`, tells it from the fields' text, and a medical deck is told by its terms (`-itis`, `cardi`, `hyper-` and so on). Set it when a deck mixes kinds, or when a medical deck reads as everyday English.

**fields**. The field names to use for `word`, `reading` and `meaning` when the automatic guess (Expression, Reading, Meaning, Simplified, Pinyin, Term, Definition and common variants) picks the wrong ones. A word field written with furigana (`漢字[かんじ]`) needs no reading field, and English and medical decks need none either.

**guessable**. The levels (0 to 1) a word's reading and meaning must reach to count as guessable.

**sources**. How much each kind of label weighs when they disagree. `crowd` is your votes and imported files, `deck` is labels the deck carries from its author, `llm` is a model, and `heuristic` is computed. Set a weight to 0 to leave that kind out, so `{"crowd": 1, "deck": 1, "llm": 0, "heuristic": 0}` uses people's votes only.

**path**. `window` is how many new cards back a piece (kanji+reading, character+pinyin, word part) still counts as fresh. `ahead` is how many new cards to plan (the rest keep the deck's order). `setup` is the pull of a word that opens up later guessable words. `deck_every` makes every n-th new card the deck's own next one, which keeps part of a frequency order (0 turns it off). `mature_counts` means pieces in mature cards always count as known. `spacing` is "SRS for patterns", so once a piece has been met in `after` words, it's shown again only after growing gaps (`window` × `growth`^n, at most `max_gap`).

**heuristic**. `reading_from` is `dictionary`, `deck` or `both` (where a piece's usual reading comes from). `reading_full` is the share of a kanji's words that makes a reading fully guessable. `meaning` is `embeddings`, `words` or `off`. With `embeddings` and no embedding server running, it falls back to `words` by itself. `meaning_lo` and `meaning_hi` are the cosine range mapped to 0..1.

**embeddings**, **llm**. Optional. Each takes any server with an OpenAI-style API, an address (`base_url`), a `model` and an `api_key` if the server needs one. The defaults point at [Ollama](https://ollama.com) on your own computer (`http://127.0.0.1:11434/v1`), but LM Studio, llama.cpp's server, vLLM or a cloud API such as OpenAI's work too. Without a server the add-on still works, with meanings judged by word overlap and no model labels. `per_day` caps the words the model labels per day, and `batch` is the words per call. `reasoning_effort` ("none" by default) keeps thinking models such as Gemma 4 from spending the whole answer on hidden reasoning, so empty it for servers that reject the field. Some reasoning models refuse a temperature, so set `temperature` to `false` in the `llm` block for those.

**free**. How the dashboard counts free cards. `seen` is the sightings (each within `path.window` cards of the last) before a piece counts as learned, and `rate` is how often you guess a guessable word right. Virtual cards are the cards studied plus `rate` × the words you could guess now.

**auto_reorder**. Plan again when you open the profile and after each review session.

**crowd_name**. The name saved with your own labels (shared files carry it).

**sentry_dsn**. Optional. It sends each labelling job to Sentry as an AI agent trace.
