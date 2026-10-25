"""The explainer video, made to be watched without sound: why some Anki cards come free when new words arrive right
after their kanji. One idea per beat, a caption under it, and each caption held long enough to read.

    manim -qh docs/video/explainer.py Explainer          (1080p; -ql for a quick draft)

The chart uses the simulation behind the README table (JLPT N5-N1 deck, Anki's default FSRS, one sighting, 80% guess
rate): cards learned to reach 100 ... 1,000 words."""
from manim import (DOWN, LEFT, RIGHT, UP, Axes, Circumscribe, Create, DashedLine, Dot, FadeIn, FadeOut,
                   GrowFromCenter, Indicate, LaggedStart, ReplacementTransform, RoundedRectangle, Scene,
                   SurroundingRectangle, Text, VGroup, Write, config)

config.background_color = "#14181c"
JP, EN = "Noto Sans CJK JP", "Noto Sans"
INK, MUTE, CARD, CARD_INK = "#eef0ec", "#9aa3ab", "#f6f7f4", "#18212b"
BLUE, ORANGE, GOOD = "#3987e5", "#e0723f", "#4cb27c"
DECK = [100, 197, 294, 387, 478, 571, 664, 751, 838, 926]          # cards learned, deck's own order
PATH = [35, 72, 106, 141, 185, 226, 264, 304, 343, 385]             # cards learned, GuessWithAnki
CAPTION_Y = -3.05


def t(s, size=36, color=INK, font=EN, weight="NORMAL"):
    return Text(s, font=font, font_size=size, color=color, weight=weight)


def card(word, reading="", meaning="", scale=1.0):
    """a flashcard: the word, and under it (once revealed) its reading and meaning"""
    kanji = VGroup(*[t(ch, 120, CARD_INK, JP, "BOLD") for ch in word]).arrange(RIGHT, buff=0.08)
    w = max(3.4, kanji.width + 1.0)
    box = RoundedRectangle(corner_radius=0.3, width=w, height=3.9, fill_color=CARD, fill_opacity=1, stroke_width=0)
    kanji.move_to(box).shift(UP * 0.55)
    back = VGroup(t(reading or " ", 40, "#4a5560", JP), t(meaning or " ", 32, "#4a5560")).arrange(DOWN, buff=0.12)
    back.next_to(kanji, DOWN, buff=0.35)
    g = VGroup(box, kanji, back)
    g.scale(scale)
    return g


def tile(ch, reading, meaning):
    box = RoundedRectangle(corner_radius=0.18, width=3.6, height=1.5, fill_color="#1d2d42", fill_opacity=1,
                           stroke_color=BLUE, stroke_width=4)
    k = t(ch, 72, INK, JP, "BOLD")
    r = VGroup(t(reading, 34, INK, JP), t(meaning, 26, MUTE)).arrange(DOWN, buff=0.08, aligned_edge=LEFT)
    return VGroup(box, VGroup(k, r).arrange(RIGHT, buff=0.35).move_to(box))


def read_time(text):
    words = len(text.split())
    jp = sum(1 for c in text if "぀" <= c <= "鿿")
    return max(2.3, 0.9 + 0.3 * words + 0.25 * jp)


class Explainer(Scene):
    caption = None

    def say(self, text, extra=0.0, color=INK):
        """swap the caption at the bottom and hold it long enough to read"""
        new = t(text, 40, color, JP)
        if new.width > config.frame_width - 1.2:
            new.scale_to_fit_width(config.frame_width - 1.2)
        new.move_to([0, CAPTION_Y, 0])
        if self.caption is None:
            self.play(FadeIn(new, shift=UP * 0.15), run_time=0.5)
        else:
            self.play(FadeOut(self.caption, shift=UP * 0.15), FadeIn(new, shift=UP * 0.15), run_time=0.5)
        self.caption = new
        self.wait(read_time(text) + extra)

    def clear(self, *mobs):
        mobs = [m for m in mobs if m is not None] + ([self.caption] if self.caption else [])
        self.play(*[FadeOut(m) for m in mobs], run_time=0.6)
        self.caption = None

    def construct(self):
        # 0. title
        title = t("Some of your Anki cards could be free", 60, INK, weight="BOLD")
        title.scale_to_fit_width(min(title.width, config.frame_width - 1.6))
        sub = t("if each new word arrives right after its kanji", 38, MUTE).next_to(title, DOWN, buff=0.45)
        self.play(Write(title), run_time=1.5)
        self.play(FadeIn(sub, shift=UP * 0.2), run_time=0.8)
        self.wait(2.6)
        self.play(FadeOut(title), FadeOut(sub), run_time=0.6)

        # 1. the deck's own order: 電気 comes before anything that teaches its kanji
        head = t("The deck's own order", 40, ORANGE, weight="BOLD").to_corner(UP + LEFT)
        words = ["会社", "電気", "今日", "天気", "電車"]
        row = VGroup(*[card(w, scale=0.5) for w in words]).arrange(RIGHT, buff=0.35).shift(UP * 0.6)
        for c in row:
            c[2].set_opacity(0)
        nums = VGroup(*[t("card %d" % (i + 1), 26, MUTE).next_to(c, DOWN, buff=0.2) for i, c in enumerate(row)])
        self.play(FadeIn(head), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(VGroup(c, n), shift=LEFT * 0.5) for c, n in zip(row, nums)], lag_ratio=0.35),
                  run_time=2.2)
        self.say("Normally, Anki shows new cards in the deck's own order.")
        self.play(Indicate(row[1], color=ORANGE, scale_factor=1.12), run_time=1.0)
        self.say("Card 2 is 電気. You haven't studied 天気 or 電車 yet.")
        big = card("電気", "でんき", "electricity", scale=1.0).move_to(LEFT * 2.4 + UP * 0.45)
        back = big[2]
        back.set_opacity(0)
        self.play(FadeOut(VGroup(*[row[i] for i in (0, 2, 3, 4)]), nums), ReplacementTransform(row[1], big),
                  run_time=1.0)
        marks = VGroup(*[t("?", 80, ORANGE, weight="BOLD").next_to(big[1][i], UP, buff=0.15) for i in range(2)])
        self.play(LaggedStart(*[GrowFromCenter(m) for m in marks], lag_ratio=0.6), run_time=1.2)
        self.say("Both of its kanji, 電 and 気, are new to you.")
        self.play(back.animate.set_opacity(1), run_time=0.8)
        label = t("learn from scratch", 36, "#1d0f08", weight="BOLD")
        stamp = VGroup(RoundedRectangle(corner_radius=0.3, width=label.width + 0.7, height=0.95, fill_color=ORANGE,
                                        fill_opacity=1, stroke_width=0), label)
        stamp[1].move_to(stamp[0])
        stamp.next_to(big, RIGHT, buff=0.6)
        self.play(GrowFromCenter(stamp), run_time=0.6)
        self.say("Nothing to guess from, so you have to learn this card.")
        self.clear(head, big, marks, stamp)

        # 2. the same cards, reordered
        head = t("GuessWithAnki order", 40, BLUE, weight="BOLD").to_corner(UP + LEFT)
        row = VGroup(*[card(w, scale=0.5) for w in words]).arrange(RIGHT, buff=0.35).shift(UP * 0.6)
        for c in row:
            c[2].set_opacity(0)
        self.play(FadeIn(head), FadeIn(row), run_time=0.8)
        self.say("GuessWithAnki reorders the same cards.")
        slots = [c.get_center() for c in row]
        new_order = [4, 3, 1, 0, 2]                         # 電車, 天気, 電気, 会社, 今日
        self.play(*[row[j].animate(path_arc=-1.2).move_to(slots[i]) for i, j in enumerate(new_order)], run_time=2.0)
        nums = VGroup(*[t("card %d" % (i + 1), 26, MUTE).next_to(row[j], DOWN, buff=0.2) for i, j in enumerate(new_order)])
        self.play(FadeIn(nums), run_time=0.5)
        self.say("Words that teach 電 and 気 now come before 電気.")
        self.clear(row, nums)

        # 3. step by step
        shelf_head = t("kanji you know", 30, MUTE).to_corner(UP + RIGHT).shift(LEFT * 0.4)
        self.play(FadeIn(shelf_head), run_time=0.4)
        c1 = card("電車", "でんしゃ", "train", scale=0.9).move_to(LEFT * 3.2 + UP * 0.45)
        self.play(FadeIn(c1, shift=LEFT * 0.5), run_time=0.7)
        self.say("Card 1: 電車, train. You learn it as usual.")
        box1 = SurroundingRectangle(c1[1][0], color=BLUE, buff=0.12, stroke_width=6)
        self.play(Create(box1), run_time=0.6)
        t1 = tile("電", "でん", "electric").next_to(shelf_head, DOWN, buff=0.35)
        self.play(ReplacementTransform(c1[1][0].copy(), t1), run_time=1.2)
        self.say("Along the way you meet 電: read でん, meaning electric.")
        c2 = card("天気", "てんき", "weather", scale=0.9).move_to(c1)
        self.play(FadeOut(VGroup(c1, box1), shift=LEFT * 0.5), FadeIn(c2, shift=LEFT * 0.5), run_time=0.8)
        self.say("Card 2: 天気, weather.")
        box2 = SurroundingRectangle(c2[1][1], color=BLUE, buff=0.12, stroke_width=6)
        self.play(Create(box2), run_time=0.6)
        t2 = tile("気", "き", "air, spirit").next_to(t1, DOWN, buff=0.3)
        self.play(ReplacementTransform(c2[1][1].copy(), t2), run_time=1.2)
        self.say("And here you meet 気: read き, meaning air or spirit.")
        c3 = card("電気", "でんき", "electricity", scale=1.0).move_to(LEFT * 4.3 + UP * 0.45)
        c3[2].set_opacity(0)
        self.play(FadeOut(VGroup(c2, box2), shift=LEFT * 0.5), FadeIn(c3, shift=LEFT * 0.5), run_time=0.8)
        self.say("Card 3: 電気. Before you flip it, can you guess it?", extra=1.5)
        self.play(Circumscribe(t1, color=BLUE, buff=0.05), Circumscribe(t2, color=BLUE, buff=0.05), run_time=1.2)
        hint = VGroup(t("でん + き", 54, INK, JP), t("electric + air", 36, MUTE)).arrange(DOWN, buff=0.15)
        hint.next_to(c3, RIGHT, buff=0.7).shift(UP * 0.3)
        self.play(FadeIn(hint, shift=RIGHT * 0.3), run_time=0.8)
        self.say("You know both kanji: でん plus き, electric plus air.")
        self.play(c3[2].animate.set_opacity(1), run_time=0.8)
        answer = t("= electricity", 50, GOOD, weight="BOLD").next_to(hint, DOWN, buff=0.4)
        self.play(Write(answer), run_time=0.8)
        badge = VGroup(RoundedRectangle(corner_radius=0.3, width=3.4, height=0.95, fill_color=GOOD, fill_opacity=1,
                                        stroke_width=0), t("free card", 38, "#0e1a14", weight="BOLD"))
        badge[1].move_to(badge[0])
        badge.next_to(answer, DOWN, buff=0.4)
        self.play(GrowFromCenter(badge), run_time=0.6)
        self.say("You guessed it right, so you never had to learn this card.", extra=0.8)
        self.clear(head, shelf_head, t1, t2, c3, hint, answer, badge)

        # 4. across a whole deck
        head = t("Across a whole deck", 40, INK, weight="BOLD").to_corner(UP + LEFT)
        ax = Axes(x_range=[0, 1000, 250], y_range=[0, 1000, 250], x_length=8.6, y_length=3.9, tips=False,
                  axis_config={"color": MUTE, "include_numbers": False}).shift(UP * 0.55 + LEFT * 1.3)
        ticks = VGroup(*[t(f"{v:,}", 24, MUTE).next_to(ax.c2p(v, 0), DOWN, buff=0.15) for v in (250, 500, 750, 1000)],
                       *[t(f"{v:,}", 24, MUTE).next_to(ax.c2p(0, v), LEFT, buff=0.15) for v in (250, 500, 750, 1000)])
        xl = t("words you know", 28, MUTE).next_to(ax.x_axis, DOWN, buff=0.55)
        yl = t("cards you learn", 28, MUTE).rotate(1.5708).next_to(ax.y_axis, LEFT, buff=1.05)
        note = t("simulated: JLPT N5–N1 vocabulary deck, Anki's default FSRS, 80% guess rate", 22, MUTE)
        note.next_to(head, DOWN, buff=0.15, aligned_edge=LEFT)
        self.play(FadeIn(head), Create(ax), FadeIn(ticks), FadeIn(xl), FadeIn(yl), FadeIn(note), run_time=1.2)
        self.say("Now do this across a whole deck of 7,700 words.")
        xs = [0] + [100 * (i + 1) for i in range(10)]
        deck = ax.plot_line_graph(xs, [0] + DECK, line_color=ORANGE, add_vertex_dots=False, stroke_width=6)
        dl = t("deck's own order", 28, ORANGE).next_to(ax.c2p(1000, DECK[-1]), RIGHT, buff=0.2)
        self.play(Create(deck), FadeIn(dl), run_time=1.6)
        self.say("In the deck's own order, nearly every word is a card to learn.")
        path = ax.plot_line_graph(xs, [0] + PATH, line_color=BLUE, add_vertex_dots=False, stroke_width=6)
        pl = t("GuessWithAnki", 28, BLUE).next_to(ax.c2p(1000, PATH[-1]), RIGHT, buff=0.2)
        self.play(Create(path), FadeIn(pl), run_time=1.6)
        self.say("With GuessWithAnki, many of them come free.")
        v = DashedLine(ax.c2p(500, 0), ax.c2p(500, DECK[4]), color=MUTE)
        d1, d2 = Dot(ax.c2p(500, DECK[4]), color=ORANGE, radius=0.11), Dot(ax.c2p(500, PATH[4]), color=BLUE, radius=0.11)
        lab1 = t("478 cards", 32, ORANGE, weight="BOLD").next_to(d1, LEFT, buff=0.2)
        lab2 = t("185 cards", 32, BLUE, weight="BOLD").next_to(d2, DOWN, buff=0.12).shift(RIGHT * 0.95)
        self.play(Create(v), FadeIn(d1), FadeIn(d2), run_time=0.8)
        self.play(FadeIn(lab1), FadeIn(lab2), run_time=0.6)
        self.say("To know 500 words: 478 cards to learn, or just 185.")
        big = t("2.6× faster", 48, INK, weight="BOLD").next_to(pl, DOWN, buff=0.7, aligned_edge=LEFT)
        if big.get_right()[0] > config.frame_width / 2 - 0.35:
            big.to_edge(RIGHT, buff=0.35)
        self.play(GrowFromCenter(big), run_time=0.7)
        self.say("That's 2.6 times faster.")
        self.say("Guess every word right, and your first 100 go up to 6 times faster.", extra=0.5)
        self.clear(head, ax, ticks, xl, yl, note, deck, dl, path, pl, v, d1, d2, lab1, lab2, big)

        # 5. call to action
        name = t("GuessWithAnki", 84, INK, weight="BOLD")
        sub = t("a free, open-source Anki add-on for Japanese decks", 38, MUTE).next_to(name, DOWN, buff=0.4)
        self.play(Write(name), run_time=1.2)
        self.play(FadeIn(sub), run_time=0.8)
        self.wait(5.0)
