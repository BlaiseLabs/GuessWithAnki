**search**: which notes to plan (an Anki search, e.g. `deck:Japanese`); empty = every note whose type has a word field.

**fields**: field names to use for `word`, `reading`, `meaning` when the automatic guess (Expression / Reading / Meaning and common variants) picks the wrong ones. A word field written with furigana (`漢字[かんじ]`) needs no reading field.

**guessable**: the levels (0 to 1) a word's reading and meaning must reach to count as guessable.

**sources**: how much each kind of label weighs when they disagree: `crowd` (your votes and imported files), `deck` (labels the deck carries from its author), `llm` (a model), `heuristic` (computed). Set a weight to 0 to leave that kind out: `{"crowd": 1, "deck": 1, "llm": 0, "heuristic": 0}` uses people's votes only.

**path**: `window` = how many new cards back a kanji+reading still counts as fresh; `ahead` = how many new cards to plan (the rest keep the deck's order); `setup` = the pull of a word that opens up later guessable words; `deck_every` = every n-th new card is the deck's own next one (keeps part of a frequency order; 0 = off); `mature_counts` = kanji+readings in mature cards always count as known; `spacing` = "SRS for patterns": once a kanji+reading has been met in `after` words, show it again only after growing gaps (`window` × `growth`^n, at most `max_gap`).

**heuristic**: `reading_from` = `dictionary`, `deck` or `both` (how a kanji is usually read); `reading_full` = the share of a kanji's words that makes a reading fully guessable; `meaning` = `embeddings`, `words` or `off`; `meaning_lo` / `meaning_hi` = the cosine range mapped to 0..1.

**embeddings**, **llm**: any server with the OpenAI API (Ollama: `http://127.0.0.1:11434/v1`). `per_day` caps the words the model labels per day; `batch` = words per call; `reasoning_effort` ("none" by default) keeps thinking models such as Gemma 4 from spending the whole answer on hidden reasoning: empty it for servers that reject the field.

**free**: how the dashboard counts free cards: `seen` = sightings (each within `path.window` cards of the last) before a kanji reading counts as learned; `rate` = how often you guess a guessable word right. Virtual cards = cards studied + `rate` × words you could guess now.

**auto_reorder**: plan again when you open the profile and after each review session.

**crowd_name**: the name saved with your own labels (shared files carry it).

**sentry_dsn**: optional, sends each labelling job to Sentry as an AI agent trace.
