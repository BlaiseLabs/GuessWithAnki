"""The narrated video: one scene per narration section (narration.py), each beat timed to its voice clip.

    python docs/video/build.py ...      (renders every scene, lays the voice on the recorded beat times, joins)

Each beat starts with self.beat(id), which records when it starts (build/starts_<Scene>.json) and returns when it
should end (its clip's length + a pause); self.hold(end) waits out the rest. Durations come from
build/durations.json (the trimmed voice clips); without it, an estimate from the word count."""
import json
import random
import sys
from pathlib import Path

import numpy as np
from manim import (DL, DOWN, DR, LEFT, ORIGIN, RIGHT, UL, UP, UR, Arc, Arrow, Circle, Create, Dot, FadeIn, FadeOut,
                   GrowFromCenter, GrowFromEdge, ImageMobject, Indicate, LaggedStart, Line, Polygon, Rectangle,
                   ReplacementTransform, RoundedRectangle, Scene, Square, Star, SurroundingRectangle, Text, Transform,
                   VGroup, VMobject, Write, config, rate_functions)

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from ji import Ji  # noqa: E402
from narration import segments  # noqa: E402

BG, INK, MUTE = "#14181c", "#eef0ec", "#9aa3ab"
BLUE, ORANGE, GREEN, YELLOW, RED, PURPLE = "#3987e5", "#e0723f", "#4cb27c", "#f2c14e", "#e05555", "#a77bd6"
CARD, CARD_INK, PANEL = "#f6f7f4", "#18212b", "#1d2630"
EN, JP, MONO = "Noto Sans", "Noto Sans CJK JP", "DejaVu Sans Mono"
GAP = 0.35
config.background_color = BG

SEG = {sid: (sec, text) for sec, sid, text, say in segments()}
_dur = HERE / "build" / "durations.json"
DUR = json.loads(_dur.read_text()) if _dur.exists() else {}
if DUR.get("_blocks"):
    GAP = 0.0                    # (block mode: each beat's length already holds its pause)


def dur(sid):
    return DUR.get(sid) or (0.5 + len(SEG[sid][1].split()) / 3.6)


# ---------------------------------------------------------------------------------------------------------- helpers
def T(s, size=36, color=INK, font=EN, weight="NORMAL", max_width=12.4):
    t = Text(s, font=font, font_size=size, color=color, weight=weight)
    if t.width > max_width:
        t.scale_to_fit_width(max_width)
    return t


def card(word, reading="", meaning="", scale=1.0, width=None):
    """a flashcard; with reading/meaning it is the card's back"""
    kanji = T(word, 110, CARD_INK, JP, "BOLD")
    w = width or max(3.2, kanji.width + 1.0)
    box = RoundedRectangle(corner_radius=0.28, width=w, height=3.6, fill_color=CARD, fill_opacity=1, stroke_width=0)
    kanji.move_to(box).shift(UP * (0.5 if reading or meaning else 0))
    g = VGroup(box, kanji)
    if reading or meaning:
        back = VGroup(T(reading or " ", 38, "#4a5560", JP), T(meaning or " ", 30, "#4a5560")).arrange(DOWN, buff=0.1)
        back.next_to(kanji, DOWN, buff=0.3)
        g.add(back)
    return g.scale(scale)


def small_card(word, color=CARD, ink=CARD_INK, w=1.7, h=1.1, size=44):
    box = RoundedRectangle(corner_radius=0.14, width=w, height=h, fill_color=color, fill_opacity=1, stroke_width=0)
    return VGroup(box, T(word, size, ink, JP, "BOLD").move_to(box))


def tile(ch, reading, meaning, color=BLUE):
    box = RoundedRectangle(corner_radius=0.18, width=3.6, height=1.5, fill_color="#1d2d42", fill_opacity=1,
                           stroke_color=color, stroke_width=4)
    k = T(ch, 72, INK, JP, "BOLD")
    r = VGroup(T(reading, 34, INK, JP), T(meaning, 26, MUTE)).arrange(DOWN, buff=0.08, aligned_edge=LEFT)
    inner = VGroup(k, r).arrange(RIGHT, buff=0.35)
    if inner.width + 0.6 > box.width:
        box.stretch_to_fit_width(inner.width + 0.6)
    return VGroup(box, inner.move_to(box))


def check(size=0.5, color=GREEN):
    m = VMobject(color=color, stroke_width=10)
    m.set_points_as_corners([LEFT * 0.5 + UP * 0.05, DOWN * 0.4 + LEFT * 0.1, UP * 0.55 + RIGHT * 0.6])
    return m.scale(size)


def cross(size=0.5, color=RED, width=12):
    return VGroup(Line(UL, DR, color=color, stroke_width=width), Line(UR, DL, color=color, stroke_width=width)).scale(size)


def bulb(size=1.0):
    glass = Circle(radius=0.45, fill_color=YELLOW, fill_opacity=1, stroke_width=0)
    base = Rectangle(width=0.36, height=0.28, fill_color="#9aa3ab", fill_opacity=1, stroke_width=0)
    base.next_to(glass, DOWN, buff=-0.06)
    rays = VGroup(*[Line(ORIGIN, UP * 0.25, color=YELLOW, stroke_width=5).shift(UP * 0.62).rotate(a, about_point=ORIGIN)
                    for a in np.linspace(-1.2, 1.2, 5)])
    return VGroup(rays, glass, base).scale(size)


def keep_in_frame(m, margin=0.25):
    """shift m back inside the frame"""
    fx, fy = config.frame_width / 2 - margin, config.frame_height / 2 - margin
    dx = max(0, -fx - m.get_left()[0]) - max(0, m.get_right()[0] - fx)
    dy = max(0, -fy - m.get_bottom()[1]) - max(0, m.get_top()[1] - fy)
    return m.shift(RIGHT * dx + UP * dy)


def bubble(content, color=PANEL, stroke=MUTE, pad=0.3):
    box = RoundedRectangle(corner_radius=0.2, width=content.width + 2 * pad, height=content.height + 2 * pad,
                           fill_color=color, fill_opacity=1, stroke_color=stroke, stroke_width=2)
    content.move_to(box)
    return VGroup(box, content)


def bar(value, vmax, width=7.0, height=0.45, color=BLUE):
    return Rectangle(width=max(0.02, width * value / vmax), height=height, fill_color=color, fill_opacity=1,
                     stroke_width=0)


def grid(n, cols, size=0.22, buff=0.06, color="#2a3540"):
    g = VGroup(*[Square(side_length=size, fill_color=color, fill_opacity=1, stroke_width=0) for _ in range(n)])
    return g.arrange_in_grid(cols=cols, buff=buff)


def lock(color=MUTE):
    body = RoundedRectangle(corner_radius=0.06, width=0.5, height=0.4, fill_color=color, fill_opacity=1, stroke_width=0)
    shackle = Arc(radius=0.17, start_angle=0, angle=np.pi, color=color, stroke_width=7).next_to(body, UP, buff=-0.02)
    return VGroup(body, shackle)


# ------------------------------------------------------------------------------------------------- layout checks
import os  # noqa: E402

CHECK = os.environ.get("GWA_CHECK") == "1"
FX, FY = config.frame_width / 2, config.frame_height / 2
BOXES = (Rectangle, RoundedRectangle, Square)


def _bbox(m):
    return (m.get_left()[0], m.get_right()[0], m.get_bottom()[1], m.get_top()[1])


def _visible(m):
    pts = [sm for sm in m.family_members_with_points()]
    if not pts:
        return False
    return max(max(sm.get_fill_opacity(), sm.get_stroke_opacity()) for sm in pts) > 0.15


def _inter(a, b, pad=0.03):
    w = min(a[1], b[1]) - max(a[0], b[0]) - pad
    h = min(a[3], b[3]) - max(a[2], b[2]) - pad
    return w * h if w > 0 and h > 0 else 0.0


def _inside(a, b, tol=0.03):
    return a[0] >= b[0] - tol and a[1] <= b[1] + tol and a[2] >= b[2] - tol and a[3] <= b[3] + tol


def _name(m):
    if isinstance(m, Text):
        return "text %r" % getattr(m, "original_text", getattr(m, "text", "?"))[:40]
    if isinstance(m, Ji):
        return "Gaku"
    if isinstance(m, ImageMobject):
        return "image"
    return "%s %.1fx%.1f at (%.1f, %.1f)" % (type(m).__name__, m.width, m.height, m.get_x(), m.get_y())


def layout_items(mobjects):
    """the visible texts, boxes (filled rectangles, images) and Gakus on screen"""
    texts, boxes, jis = [], [], []

    def walk(m):
        if isinstance(m, Ji):
            if _visible(m.body):
                jis.append(m)
            return
        if isinstance(m, Text):
            if _visible(m) and m.width > 0.01:
                texts.append(m)
            return
        if isinstance(m, ImageMobject):
            boxes.append(m)
            return
        if isinstance(m, BOXES) and m.get_fill_opacity() > 0.3 and m.width > 0.3 and m.height > 0.3:
            boxes.append(m)
        for sm in m.submobjects:
            walk(sm)
    for m in mobjects:
        walk(m)
    return texts, boxes, jis


def layout_problems(mobjects):
    texts, boxes, jis = layout_items(mobjects)
    out = []
    for m in texts + boxes + jis:
        b = _bbox(m)
        if b[0] < -FX + 0.05 or b[1] > FX - 0.05 or b[2] < -FY + 0.05 or b[3] > FY - 0.05:
            out.append(("off-frame", _name(m), ""))
    for i, a in enumerate(texts):
        for b in texts[i + 1:]:
            if _inter(_bbox(a), _bbox(b)) > 0.01:
                out.append(("text-on-text", _name(a), _name(b)))
        for bx in boxes:
            ia = _inter(_bbox(a), _bbox(bx))
            if ia > 0.01 and not _inside(_bbox(a), _bbox(bx)):
                out.append(("text-out-of-box", _name(a), _name(bx)))
        for j in jis:
            if _inter(_bbox(a), _bbox(j)) > 0.01:
                out.append(("text-on-Gaku", _name(a), ""))
    for j in jis:
        for bx in boxes:
            if _inter(_bbox(j), _bbox(bx)) > 0.01:
                out.append(("box-on-Gaku", _name(bx), ""))
        for k in jis:
            if k is not j and id(k) > id(j) and _inter(_bbox(j), _bbox(k)) > 0.01:
                out.append(("Gaku-on-Gaku", "", ""))
    return out


# -------------------------------------------------------------------------------------------------------- the base
class Beats(Scene):
    def setup(self):
        self.starts = {}
        self.problems = {}
        self.overruns = {}
        self.cur = "start"

    def play(self, *args, **kw):
        super().play(*args, **kw)
        if CHECK:
            for kind, a, b in layout_problems(self.mobjects):
                key = "%s | %s | %s" % (kind, a, b)
                if key not in self.problems:
                    self.problems[key] = {"beat": self.cur, "t": round(self.now(), 2)}

    def now(self):
        return self.renderer.time

    def beat(self, sid):
        self.cur = sid
        self.starts[sid] = round(self.now(), 3)
        return self.now() + dur(sid) + GAP

    def hold(self, end):
        rest = end - self.now()
        if rest > 0.02:
            self.wait(rest)
        elif rest < -0.04:
            self.overruns[self.cur] = round(-rest, 2)      # (its animation outlasts its voice: a gap opens)

    def tear_down(self):
        out = HERE / "build"
        out.mkdir(exist_ok=True)
        (out / ("starts_%s.json" % type(self).__name__)).write_text(
            json.dumps({"starts": self.starts, "end": round(self.now(), 3), "overruns": self.overruns}))
        if CHECK:
            (out / ("layout_%s.json" % type(self).__name__)).write_text(json.dumps(self.problems, indent=1, ensure_ascii=False))

    def clear_all(self, keep=(), run_time=0.5):
        mobs = [m for m in self.mobjects if m not in keep]
        if mobs:
            self.play(*[FadeOut(m) for m in mobs], run_time=run_time)

    def jiggle(self, ji, times=2):
        for d in (LEFT, RIGHT) * times:
            self.play(ji.look_at(d, run_time=0.25))
        self.play(ji.look_at(ORIGIN, run_time=0.2))


# ------------------------------------------------------------------------------------------------------------ scenes
class S01Intro(Beats):
    def construct(self):
        self.wait(0.3)
        ji = Ji(1.7).to_corner(DL).shift(UP * 0.1 + RIGHT * 0.2)
        e = self.beat("i01")
        front = card("電気").shift(UP * 0.4)
        self.play(FadeIn(front, shift=UP * 0.3), run_time=0.7)
        self.play(FadeIn(ji, shift=RIGHT * 0.3), run_time=0.5)
        self.play(ji.look_at(UR))
        guess = bubble(T("…でんき? electricity?", 34, INK, JP)).next_to(front, RIGHT, buff=0.4).shift(UP * 0.9)
        guess.scale_to_fit_width(min(guess.width, 4.4))
        keep_in_frame(guess)
        self.play(FadeIn(guess, shift=LEFT * 0.2), run_time=0.6)
        self.wait(max(0.1, dur("i01") * 0.25))
        back = card("電気", "でんき", "electricity").move_to(front)
        ok = check(0.6).next_to(back, RIGHT, buff=0.3).shift(DOWN * 0.6)
        self.play(Transform(front, back), run_time=0.7)
        self.play(Create(ok), ji.mood_to("wow"), run_time=0.5)
        self.hold(e)

        e = self.beat("i02")
        stars = VGroup(*[Star(n=5, outer_radius=0.16, color=PURPLE, fill_opacity=1).move_to(
            front.get_center() + np.array([np.cos(a) * 2.3, np.sin(a) * 2.1, 0])) for a in np.linspace(0, 2 * np.pi, 9)[:-1]])
        magic = T("black magic?", 44, PURPLE, weight="BOLD").next_to(front, UP, buff=0.35)
        self.play(LaggedStart(*[GrowFromCenter(s) for s in stars], lag_ratio=0.1), FadeOut(guess), run_time=0.9)
        self.play(Write(magic), ji.mood_to("confused"), run_time=0.8)
        self.wait(max(0.1, dur("i02") * 0.3))
        title = T("Guessing words you've never seen", 54, INK, weight="BOLD").shift(UP * 0.6)
        sub = T("a bit of computer science, and some Python", 32, MUTE).next_to(title, DOWN, buff=0.35)
        self.play(FadeOut(VGroup(front, ok, stars, magic)), run_time=0.5)
        self.play(Write(title), ji.mood_to("happy"), run_time=1.0)
        self.play(FadeIn(sub, shift=UP * 0.2), run_time=0.6)
        self.play(ji.blink())
        self.hold(e)


class S02Disclaimer(Beats):
    def construct(self):
        self.wait(0.3)
        ji = Ji(1.6).to_corner(DL).shift(UP * 0.1 + RIGHT * 0.2)
        self.add(ji)
        e = self.beat("d01")
        head = T("Quick disclaimer", 44, MUTE).to_edge(UP)
        self.play(FadeIn(head), run_time=0.5)
        two = T("2×", 150, ORANGE, weight="BOLD").shift(LEFT * 2 + UP * 0.2)
        six = T("6×", 190, ORANGE, weight="BOLD").shift(RIGHT * 2.2 + UP * 0.3)
        self.play(GrowFromCenter(two), ji.mood_to("wow"), run_time=0.7)
        self.wait(0.6)
        self.play(GrowFromCenter(six), run_time=0.7)
        self.hold(e)

        e = self.beat("d02")
        self.play(FadeOut(VGroup(two, six)), ji.mood_to("neutral"), run_time=0.5)
        lanes = VGroup(*[Line(LEFT * 5, RIGHT * 5, color="#3a4550", stroke_width=4).shift(UP * y) for y in (1.6, 0.5, -0.6)])
        finish = Line(UP * 1.9, DOWN * 0.9, color=INK, stroke_width=6).shift(RIGHT * 4.6)
        runners = VGroup(*[Dot(radius=0.16, color=c).move_to(LEFT * 4.6 + UP * y) for c, y in ((BLUE, 1.05), (ORANGE, -0.05))])
        self.play(Create(lanes), Create(finish), FadeIn(runners), run_time=0.8)
        self.play(runners[0].animate.shift(RIGHT * 6.5), runners[1].animate.shift(RIGHT * 5.2), run_time=1.3,
                  rate_func=rate_functions.linear)
        x = cross(1.3, RED, 16).move_to(UP * 0.5)
        self.play(Create(x), run_time=0.5)
        txt = T("This isn't a race.", 44, INK, weight="BOLD").shift(DOWN * 1.7)
        self.play(FadeIn(txt, shift=UP * 0.2), run_time=0.5)
        self.jiggle(ji, 1)
        self.hold(e)

        e = self.beat("d03")
        self.play(FadeOut(VGroup(lanes, finish, runners, x, txt)), run_time=0.5)
        q = T("?", 90, YELLOW, weight="BOLD").next_to(ji, UP, buff=0.2)
        self.play(FadeIn(q, shift=UP * 0.2), ji.mood_to("think"), run_time=0.6)
        b = bulb(1.2).next_to(ji, UP, buff=0.12)
        self.play(ReplacementTransform(q, b), ji.mood_to("happy"), run_time=0.7)
        words = VGroup(T("curious about something", 44, INK), T("↓", 44, MUTE), T("follow it", 44, INK),
                       T("↓", 44, MUTE), T("learning the language gets more fun", 44, GREEN)).arrange(DOWN, buff=0.18)
        words.shift(RIGHT * 1.3)
        self.play(LaggedStart(*[FadeIn(w, shift=UP * 0.15) for w in words], lag_ratio=0.45), run_time=2.2)
        self.hold(e)

        e = self.beat("d04")
        self.play(FadeOut(VGroup(words, b)), ji.mood_to("doubt"), run_time=0.5)
        label = T("your hours", 32, MUTE).shift(UP * 2.2)
        hours = VGroup(*[RoundedRectangle(corner_radius=0.08, width=0.8, height=0.8, fill_color=GREEN, fill_opacity=1,
                                          stroke_width=0) for _ in range(10)]).arrange(RIGHT, buff=0.12).shift(UP * 1.2)
        key = VGroup(VGroup(Square(0.3, fill_color=GREEN, fill_opacity=1, stroke_width=0), T("immersed in the language", 30)).arrange(RIGHT, buff=0.2),
                     VGroup(Square(0.3, fill_color="#5b6670", fill_opacity=1, stroke_width=0), T("optimizing your study system", 30)).arrange(RIGHT, buff=0.2)
                     ).arrange(DOWN, aligned_edge=LEFT, buff=0.25).shift(DOWN * 0.4 + RIGHT * 0.6)
        self.play(FadeIn(label), LaggedStart(*[GrowFromCenter(h) for h in hours], lag_ratio=0.06), run_time=1.0)
        self.play(FadeIn(key), run_time=0.5)
        self.play(LaggedStart(*[h.animate.set_fill("#5b6670") for h in hours[:6]], lag_ratio=0.25), run_time=2.0)
        trap = T("the over-optimization trap", 40, RED, weight="BOLD").shift(DOWN * 2.0 + RIGHT * 0.6)
        self.play(FadeIn(trap, shift=UP * 0.2), run_time=0.5)
        self.play(LaggedStart(*[h.animate.set_fill(GREEN) for h in hours[:6]], lag_ratio=0.15), ji.mood_to("happy"), run_time=1.2)
        self.hold(e)


class S03Python(Beats):
    def construct(self):
        self.wait(0.3)
        ji = Ji(1.6).to_corner(DL).shift(UP * 0.1 + RIGHT * 0.2)
        self.add(ji)
        e = self.beat("p01")
        code = VGroup(*[T(s, 26, c, MONO) for s, c in (
            ("def next_card(cards_left, seen):", BLUE),
            ("    best = max(cards_left,", INK),
            ("               key=lambda c: score(c, seen))", INK),
            ("    return best", INK))]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        cw = T("m", 26, INK, MONO).width * 1.08                  # (Text drops leading spaces: indent by hand)
        for line, src in zip(code, ("def", "    best", "               key", "    return")):
            line.shift(RIGHT * cw * (len(src) - len(src.lstrip(" "))))
        win = bubble(code, PANEL, "#3a4550", 0.4).shift(UP * 0.9 + RIGHT * 0.8)
        self.play(FadeIn(win, shift=UP * 0.2), run_time=0.7)
        langs = VGroup(*[T(s, 34, MUTE, MONO) for s in ("C++", "Rust", "JavaScript", "Go", "Julia", "Java")])
        langs.arrange(RIGHT, buff=0.5).next_to(win, DOWN, buff=0.7)
        self.play(LaggedStart(*[FadeIn(l, shift=UP * 0.15) for l in langs], lag_ratio=0.2), run_time=1.5)
        self.hold(e)

        e = self.beat("p02")
        self.play(FadeOut(VGroup(win, langs)), run_time=0.4)
        podium = Rectangle(width=2.6, height=1.6, fill_color=YELLOW, fill_opacity=1, stroke_width=0).shift(DOWN * 0.9 + LEFT * 2.6)
        one = T("1", 80, CARD_INK, weight="BOLD").move_to(podium)
        py = T("Python", 48, INK, MONO).next_to(podium, UP, buff=0.2)
        self.play(GrowFromEdge(podium, DOWN), FadeIn(one), run_time=0.6)
        self.play(FadeIn(py, shift=DOWN * 0.2), run_time=0.4)
        claims = VGroup()
        for s in ("objectively the best", "the fastest", "the most consistently designed", "multithreading: famously easy"):
            c = VGroup(T(s, 34, INK), T("(citation needed)", 22, MUTE)).arrange(DOWN, aligned_edge=LEFT, buff=0.05)
            claims.add(c)
        claims.arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to(RIGHT * 2.9 + UP * 0.3)
        per = max(0.6, (dur("p02") - 2.0) / 4)
        for i, c in enumerate(claims):
            self.play(FadeIn(c, shift=LEFT * 0.2), ji.mood_to("doubt" if i % 2 == 0 else "neutral", look=RIGHT), run_time=0.5)
            self.wait(max(0.05, per - 0.5))
        self.hold(e)

        e = self.beat("p03")
        self.play(ji.mood_to("happy", look=LEFT), run_time=0.3)
        self.play(FadeOut(VGroup(podium, one, py, claims), shift=RIGHT * 0.5), run_time=0.7)
        self.hold(e)


class S04Story(Beats):
    def construct(self):
        self.wait(0.3)
        me = Ji(1.7).shift(LEFT * 4.6 + DOWN * 1.4)
        me_lab = T("me: beginner", 28, MUTE).next_to(me, DOWN, buff=0.15)
        sensei = Ji(2.3, color=ORANGE, glyph="先").shift(RIGHT * 3.6 + DOWN * 1.0)
        s_lab = T("N2 · N1", 28, MUTE).next_to(sensei, DOWN, buff=0.15)
        e = self.beat("s01")
        self.play(FadeIn(me, shift=UP * 0.2), FadeIn(me_lab), run_time=0.6)
        self.play(FadeIn(sensei, shift=UP * 0.2), FadeIn(s_lab), me.look_at(RIGHT), run_time=0.6)
        words = ["銀行", "改札", "締切", "検討", "訪問"]
        cards = VGroup(*[small_card(w, w=2.0, h=1.3, size=50) for w in words]).arrange(RIGHT, buff=0.3)
        cards.move_to(UP * 2.4)
        self.play(LaggedStart(*[FadeIn(c, shift=LEFT * 0.4) for c in cards], lag_ratio=0.2), run_time=1.2)
        self.hold(e)

        e = self.beat("s02")
        top = cards[-1]
        reads = ["ぎんこう bank", "かいさつ ticket gate", "しめきり deadline"]
        shown = None
        for i, r in enumerate(reads):
            c = small_card(words[i], w=2.0, h=1.3, size=50).move_to(UP * 1.8 + LEFT * 0.2)
            lab = T(r, 30, INK, JP).next_to(c, DOWN, buff=0.15)
            ok = check(0.4).next_to(c, RIGHT, buff=0.2)
            grp = VGroup(c, lab, ok)
            if shown is None:
                self.play(FadeOut(cards), FadeIn(c), run_time=0.4)
                self.play(FadeIn(lab), Create(ok), sensei.mood_to("happy"), run_time=0.5)
            else:
                self.play(ReplacementTransform(shown, grp), run_time=0.6)
            shown = grp
            self.wait(0.5)
        others = VGroup(Ji(1.3, color=ORANGE, glyph="師", mood="happy"), Ji(1.3, color=ORANGE, glyph="達", mood="happy"))
        others.arrange(RIGHT, buff=0.4).next_to(sensei, LEFT, buff=0.4).shift(DOWN * 0.4)
        self.play(LaggedStart(*[FadeIn(o, shift=UP * 0.2) for o in others], lag_ratio=0.3), me.mood_to("wow"), run_time=0.8)
        self.hold(e)

        e = self.beat("s03")
        self.play(FadeOut(VGroup(shown, others)), run_time=0.4)
        para = T("既存の顧客との関係を維持しつつ、\n新規開拓にも注力する必要がある。", 40, INK, JP).shift(UP * 2.3 + RIGHT * 0.3)
        self.play(FadeIn(para), me.mood_to("confused"), run_time=0.6)
        random.seed(3)
        glyphs = VGroup()
        for ch in para:
            kind = random.choice(["circle", "tri", "wave", "eye"])
            c = ch.get_center()
            if kind == "circle":
                g = Circle(radius=0.16, color=YELLOW, stroke_width=4).move_to(c)
            elif kind == "tri":
                g = Polygon(UP * 0.2, DL * 0.18, DR * 0.18, color=YELLOW, stroke_width=4).move_to(c)
            elif kind == "wave":
                g = VMobject(color=YELLOW, stroke_width=4).set_points_smoothly(
                    [c + LEFT * 0.18, c + UP * 0.1 + LEFT * 0.06, c + DOWN * 0.1 + RIGHT * 0.06, c + RIGHT * 0.18])
            else:
                g = VGroup(Arc(radius=0.18, start_angle=0.3, angle=2.5, color=YELLOW, stroke_width=4),
                           Dot(radius=0.05, color=YELLOW)).move_to(c)
            glyphs.add(g)
        self.wait(0.6)
        self.play(ReplacementTransform(para, glyphs), run_time=1.0)
        hiero = T("basically hieroglyphics", 34, YELLOW).next_to(glyphs, DOWN, buff=0.4)
        self.play(FadeIn(hiero), run_time=0.4)
        self.hold(e)

        e = self.beat("s04")
        self.play(FadeOut(VGroup(glyphs, hiero, sensei, s_lab, me_lab)), me.animate.move_to(LEFT * 3.8 + DOWN * 0.6), run_time=0.7)
        self.play(me.mood_to("neutral"), run_time=0.3)
        front = card("天気").shift(RIGHT * 1.8 + UP * 0.3)
        self.play(FadeIn(front, shift=UP * 0.3), me.look_at(RIGHT), run_time=0.6)
        think = bubble(T("weather?", 36, INK)).next_to(me, UP, buff=0.3).shift(RIGHT * 0.6)
        self.play(me.mood_to("think"), FadeIn(think, shift=UP * 0.15), run_time=0.6)
        self.wait(max(0.2, dur("s04") * 0.3))
        back = card("天気", "てんき", "weather").move_to(front)
        ok = check(0.6).next_to(back, RIGHT, buff=0.3)
        self.play(Transform(front, back), run_time=0.6)
        self.play(Create(ok), me.mood_to("happy", look=RIGHT), run_time=0.5)
        self.hold(e)

        e = self.beat("s05")
        self.play(FadeOut(VGroup(front, ok, think)), me.animate.move_to(LEFT * 4.4 + DOWN * 1.2), run_time=0.6)
        self.play(me.mood_to("wow"), run_time=0.3)
        b = bulb(1.1).next_to(me, UP, buff=0.25)
        self.play(GrowFromCenter(b), run_time=0.5)
        q1 = T("How often does this actually happen?", 40, INK, weight="BOLD", max_width=9.0).move_to(RIGHT * 1.4 + UP * 1.0)
        q2 = VGroup(T("a fluke?", 38, MUTE), T("or something you can count on?", 38, GREEN)).arrange(DOWN, buff=0.3)
        q2.next_to(q1, DOWN, buff=0.6)
        keep_in_frame(q2)
        self.wait(max(0.1, dur("s05") * 0.25))
        self.play(Write(q1), me.mood_to("think"), run_time=1.0)
        self.wait(0.6)
        self.play(FadeIn(q2[0], shift=UP * 0.15), run_time=0.4)
        self.play(FadeIn(q2[1], shift=UP * 0.15), run_time=0.4)
        self.hold(e)


class S05Measure(Beats):
    def construct(self):
        self.wait(0.3)
        ji = Ji(1.4).to_corner(DL).shift(UP * 0.05 + RIGHT * 0.1)
        self.add(ji)
        e = self.beat("m01")
        uniq = VGroup(*[small_card(w, "#2a3540", MUTE) for w in ("猫", "山", "本", "犬", "雨", "鳥")]).arrange_in_grid(rows=2, buff=0.35)
        uniq.shift(UP * 0.6 + RIGHT * 0.6)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.15) for c in uniq], lag_ratio=0.1), run_time=1.0)
        note = T("every word with its own kanji: nothing to guess", 32, MUTE).next_to(uniq, DOWN, buff=0.5)
        self.play(FadeIn(note), ji.mood_to("sad"), run_time=0.5)
        self.hold(e)

        e = self.beat("m02")
        self.play(FadeOut(VGroup(uniq, note)), run_time=0.4)
        a = small_card("電車", w=2.4, h=1.3, size=56).shift(LEFT * 3.2 + UP * 1.5)
        b = small_card("天気", w=2.4, h=1.3, size=56).shift(RIGHT * 3.4 + UP * 1.5)
        c = small_card("電気", w=2.4, h=1.3, size=56).shift(RIGHT * 0.1 + DOWN * 0.8)
        self.play(FadeIn(a), FadeIn(b), run_time=0.5)
        self.play(FadeIn(c, shift=UP * 0.2), run_time=0.5)
        l1 = Line(a[1][0].get_bottom(), c[1][0].get_top(), color=BLUE, stroke_width=6)
        l2 = Line(b[1][1].get_bottom(), c[1][1].get_top(), color=ORANGE, stroke_width=6)
        self.play(a[1][0].animate.set_color(BLUE), c[1][0].animate.set_color(BLUE), Create(l1), run_time=0.6)
        self.play(b[1][1].animate.set_color(ORANGE), c[1][1].animate.set_color(ORANGE), Create(l2), run_time=0.6)
        self.play(Indicate(c, color=GREEN, scale_factor=1.08), ji.mood_to("happy", look=UR), run_time=0.8)
        self.hold(e)

        e = self.beat("m03")
        self.play(FadeOut(VGroup(a, b, l1, l2)), c.animate.move_to(UP * 1.9), run_time=0.6)
        t1 = tile("電", "でん", "electric", BLUE).shift(LEFT * 2.2 + DOWN * 0.2)
        t2 = tile("気", "き", "spirit, energy", ORANGE).shift(RIGHT * 2.2 + DOWN * 0.2)
        self.play(FadeIn(t1, shift=DOWN * 0.3), FadeIn(t2, shift=DOWN * 0.3), run_time=0.7)
        defn = T("a piece = a kanji + the reading it has in this word", 32, MUTE).shift(DOWN * 1.8 + RIGHT * 0.6)
        self.play(FadeIn(defn), run_time=0.5)
        self.play(Indicate(t1, color=BLUE), run_time=0.8)
        self.hold(e)

        e = self.beat("m04")
        self.play(FadeOut(defn), run_time=0.3)
        r1 = VGroup(check(0.35), T("reading: follows from the pieces' usual readings", 30)).arrange(RIGHT, buff=0.3)
        r2 = VGroup(check(0.35), T("meaning: follows from what the pieces mean", 30)).arrange(RIGHT, buff=0.3)
        rules = VGroup(r1, r2).arrange(DOWN, aligned_edge=LEFT, buff=0.3).shift(DOWN * 2.1 + RIGHT * 0.8)
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.5)
        self.wait(max(0.2, dur("m04") * 0.3))
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.5)
        self.hold(e)

        e = self.beat("m05")
        self.play(FadeOut(VGroup(c, t1, t2, rules)), run_time=0.5)
        books = VGroup()
        for name, sub, col in (("KANJIDIC2", "every kanji's readings", BLUE), ("JMdict", "tens of thousands of words", ORANGE)):
            cover = RoundedRectangle(corner_radius=0.1, width=3.4, height=4.0, fill_color=col, fill_opacity=0.9, stroke_width=0)
            spine = Rectangle(width=0.25, height=4.0, fill_color="#0d1014", fill_opacity=0.35, stroke_width=0).align_to(cover, LEFT)
            nm = T(name, 40, INK, weight="BOLD").move_to(cover).shift(UP * 0.8)
            sb = T(sub, 24, INK).next_to(nm, DOWN, buff=0.3)
            if sb.width > 3.0:
                sb.scale_to_fit_width(3.0)
            books.add(VGroup(cover, spine, nm, sb))
        books.arrange(RIGHT, buff=0.9).shift(RIGHT * 0.8 + UP * 0.2)
        free = T("free · open data", 28, GREEN).next_to(books, DOWN, buff=0.35)
        self.play(LaggedStart(*[FadeIn(bk, shift=UP * 0.3) for bk in books], lag_ratio=0.3), ji.mood_to("happy"), run_time=1.0)
        self.play(FadeIn(free), run_time=0.4)
        self.hold(e)

        e = self.beat("m06")
        self.play(FadeOut(VGroup(books, free)), run_time=0.4)
        word = T("電気", 120, INK, JP, "BOLD").shift(UP * 1.8 + LEFT * 3.0)
        kana = T("でんき", 60, MUTE, JP).next_to(word, DOWN, buff=0.25)
        self.play(FadeIn(word), FadeIn(kana), run_time=0.5)
        cut = Line(word.get_top() + UP * 0.1, kana.get_bottom() + DOWN * 0.1, color=YELLOW, stroke_width=5)
        cut.move_to([word[0].get_right()[0] + 0.05, (word.get_top()[1] + kana.get_bottom()[1]) / 2, 0])
        self.play(Create(cut), kana[:2].animate.set_color(BLUE), kana[2:].animate.set_color(ORANGE),
                  word[0].animate.set_color(BLUE), word[1].animate.set_color(ORANGE), run_time=0.8)
        title = T("気 in the dictionary's words", 32, INK, JP).shift(RIGHT * 2.4 + UP * 2.2)
        b1 = bar(130, 144, 4.5, 0.55, ORANGE)
        b2 = bar(14, 144, 4.5, 0.55, "#5b6670")
        rows = VGroup(VGroup(T("き", 36, INK, JP), b1, T("130 words", 26, MUTE)).arrange(RIGHT, buff=0.25),
                      VGroup(T("け", 36, INK, JP), b2, T("14", 26, MUTE)).arrange(RIGHT, buff=0.25))
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.3).next_to(title, DOWN, buff=0.4).align_to(title, LEFT)
        self.play(FadeIn(title), run_time=0.4)
        self.play(GrowFromEdge(b1, LEFT), FadeIn(rows[0][0]), FadeIn(rows[0][2]), run_time=0.7)
        self.play(GrowFromEdge(b2, LEFT), FadeIn(rows[1][0]), FadeIn(rows[1][2]), run_time=0.5)
        usual = VGroup(check(0.35), T("き is the usual reading → guessable", 30, GREEN, JP)).arrange(RIGHT, buff=0.25)
        usual.next_to(rows, DOWN, buff=0.5).align_to(rows, LEFT)
        self.play(FadeIn(usual, shift=UP * 0.1), run_time=0.5)
        self.hold(e)

        e = self.beat("m07")
        self.play(FadeOut(VGroup(word, kana, cut, title, rows, usual)), run_time=0.4)
        pts = {"electric": (-1.0, 1.2, BLUE), "spirit, energy": (0.7, 1.5, ORANGE), "electricity": (-0.1, 0.6, GREEN),
               "weather": (3.4, -1.2, MUTE), "train": (-3.6, -0.9, MUTE), "bank": (2.6, 2.4, MUTE), "cat": (4.4, 0.6, MUTE)}
        dots = VGroup()
        for name, (x, y, col) in pts.items():
            d = Dot(radius=0.11, color=col).move_to([x + 0.8, y, 0])
            lab = T(name, 26, col).next_to(d, UP, buff=0.1)
            dots.add(VGroup(d, lab))
        frame = RoundedRectangle(corner_radius=0.2, width=10.5, height=5.6, stroke_color="#2f3a45", stroke_width=2).move_to(RIGHT * 0.8 + UP * 0.5)
        cap = T("meanings as points: similar ones land close", 26, MUTE).next_to(frame, DOWN, buff=0.15)
        self.play(Create(frame), FadeIn(cap), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(dd, scale=0.5) for dd in dots], lag_ratio=0.15), ji.mood_to("think"), run_time=1.6)
        self.hold(e)

        e = self.beat("m08")
        el, en, ey = dots[0][0], dots[1][0], dots[2][0]
        l1 = Line(ey.get_center(), el.get_center(), color=GREEN, stroke_width=5)
        l2 = Line(ey.get_center(), en.get_center(), color=GREEN, stroke_width=5)
        close = T("close → probably guessable", 30, GREEN).move_to(RIGHT * 0.8 + DOWN * 1.6)
        self.play(Create(l1), Create(l2), FadeIn(close), run_time=0.8)
        self.wait(max(0.2, dur("m08") * 0.3))
        self.play(FadeOut(VGroup(frame, cap, dots, l1, l2, close)), run_time=0.4)
        ask = bubble(T("Could a learner who knows 電 (electric) and 気 (spirit)\nguess 電気 (electricity)?", 28, INK, JP))
        ans = bubble(T('{"meaning": "yes", "reading": "yes"}', 30, GREEN, MONO), "#16241c", GREEN)
        VGroup(ask, ans).arrange(DOWN, buff=0.5).shift(RIGHT * 0.8 + UP * 0.3)
        ask.shift(LEFT * 0.6)
        ans.shift(RIGHT * 0.6)
        self.play(FadeIn(ask, shift=UP * 0.2), run_time=0.5)
        self.play(FadeIn(ans, shift=UP * 0.2), ji.mood_to("happy"), run_time=0.5)
        self.hold(e)

        e = self.beat("m09")
        self.play(FadeOut(VGroup(ask, ans)), run_time=0.4)
        mine = T("my deck", 40, MUTE).shift(UP * 1.6 + RIGHT * 0.6)
        n = T("2,038", 120, INK, weight="BOLD").next_to(mine, DOWN, buff=0.3)
        w = T("words with kanji", 36, MUTE).next_to(n, DOWN, buff=0.2)
        self.play(FadeIn(mine), Write(n), FadeIn(w), run_time=1.0)
        self.hold(e)

        e = self.beat("m10")
        self.play(FadeOut(VGroup(mine, n, w)), run_time=0.4)
        rows = VGroup()
        spec = (("reading guessable", 96, GREEN), ("meaning: clearly", 69, BLUE), ("meaning: at least a hint", 95, "#7fb3f0"),
                ("no clue at all", 5, RED))
        for name, v, col in spec:
            lab = T(name, 30, INK).set_width(4.0) if T(name, 30).width > 4.0 else T(name, 30, INK)
            br = bar(v, 100, 6.0, 0.5, col)
            pc = T("%d%%" % v, 32, col, weight="BOLD")
            rows.add(VGroup(lab, br, pc))
        for r in rows:
            r[0].move_to([-3.2, 0, 0], aligned_edge=RIGHT)
            r[1].move_to([-2.9, 0, 0], aligned_edge=LEFT)
        for i, r in enumerate(rows):
            r.shift(UP * (1.9 - i * 1.0))
            r[2].next_to(r[1], RIGHT, buff=0.25)
        VGroup(*rows).shift(RIGHT * 1.6)
        per = max(0.5, (dur("m10") - 1.0) / 4)
        for i, r in enumerate(rows):
            self.play(FadeIn(r[0]), GrowFromEdge(r[1], LEFT), FadeIn(r[2]),
                      *( [ji.mood_to("wow")] if i == 0 else []), run_time=0.6)
            self.wait(max(0.05, per - 0.6))
        self.hold(e)

        e = self.beat("m11")
        self.play(FadeOut(rows), run_time=0.4)
        both = T("reading and meaning: 67%", 54, GREEN, weight="BOLD").shift(UP * 1.6 + RIGHT * 0.6)
        three = VGroup(*[small_card(wd, w=2.2, h=1.4, size=52) for wd in ("入口", "電車", "大丈夫")]).arrange(RIGHT, buff=0.5)
        three.next_to(both, DOWN, buff=0.7)
        self.play(Write(both), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(cd, shift=UP * 0.2) for cd in three], lag_ratio=0.2), run_time=0.8)
        glow = VGroup(*[SurroundingRectangle(cd, color=GREEN, buff=0.1, corner_radius=0.15, stroke_width=6) for cd in three[:2]])
        two3 = T("2 out of 3, guessable on first sight", 32, INK).next_to(three, DOWN, buff=0.45)
        self.play(Create(glow), FadeIn(two3), ji.mood_to("wow"), run_time=0.8)
        self.hold(e)

        e = self.beat("m12")
        self.play(FadeOut(VGroup(both, three, glow, two3)), ji.animate.move_to(LEFT * 5.0 + DOWN * 0.5).scale(1.4),
                  run_time=0.6)
        self.play(ji.mood_to("think"), run_time=0.4)
        q = T("How do I take advantage of that?", 44, INK, weight="BOLD", max_width=9.2).move_to(RIGHT * 1.2 + UP * 0.6)
        self.play(Write(q), run_time=1.0)
        self.hold(e)


class S06Greedy(Beats):
    def construct(self):
        self.wait(0.3)
        ji = Ji(1.4).to_corner(DL).shift(UP * 0.05 + RIGHT * 0.1)
        self.add(ji)
        e = self.beat("g01")
        target = small_card("電気", w=2.6, h=1.5, size=64).shift(RIGHT * 2.5 + UP * 0.6)
        lk = lock().scale(1.4).next_to(target, UP, buff=0.2)
        self.play(FadeIn(target), FadeIn(lk), ji.mood_to("sad", look=RIGHT), run_time=0.6)
        self.wait(max(0.2, dur("g01") * 0.25))
        key = small_card("電車", w=2.6, h=1.5, size=64).shift(LEFT * 1.8 + UP * 0.6)
        self.play(FadeIn(key, shift=RIGHT * 0.3), run_time=0.5)
        self.play(key[1][0].animate.set_color(BLUE), target[1][0].animate.set_color(BLUE), run_time=0.5)
        self.play(lk[1].animate.shift(UP * 0.25 + RIGHT * 0.12).rotate(0.6), run_time=0.4)
        self.play(FadeOut(lk), target[0].animate.set_fill(GREEN), ji.mood_to("happy"), run_time=0.5)
        order = T("the order matters", 40, INK, weight="BOLD").shift(DOWN * 1.6 + RIGHT * 0.6)
        self.play(FadeIn(order, shift=UP * 0.2), run_time=0.5)
        self.hold(e)

        e = self.beat("g02")
        self.play(FadeOut(VGroup(target, key, order)), run_time=0.4)
        mn = VGroup(T("minimize", 44, ORANGE, weight="BOLD"), T("cards learned the hard way", 36)).arrange(RIGHT, buff=0.4)
        mx = VGroup(T("maximize", 44, GREEN, weight="BOLD"), T("words you can guess", 36)).arrange(RIGHT, buff=0.4)
        VGroup(mx, mn).arrange(DOWN, aligned_edge=LEFT, buff=0.6).shift(RIGHT * 0.8 + UP * 0.6)
        self.play(FadeIn(mx, shift=UP * 0.2), ji.mood_to("think"), run_time=0.6)
        self.play(FadeIn(mn, shift=UP * 0.2), run_time=0.6)
        self.hold(e)

        e = self.beat("g03")
        self.play(FadeOut(VGroup(mx, mn)), run_time=0.4)
        fact = T("2000!", 120, INK, weight="BOLD").shift(UP * 1.2 + RIGHT * 0.6)
        self.play(Write(fact), run_time=0.7)
        random.seed(7)
        lines = VGroup(*[T("".join(random.choice("0123456789") for _ in range(46)), 26, MUTE, MONO) for _ in range(9)])
        lines.arrange(DOWN, buff=0.08).next_to(fact, DOWN, buff=0.4)
        self.play(LaggedStart(*[FadeIn(l) for l in lines], lag_ratio=0.12), ji.mood_to("wow"), run_time=1.4)
        digits = T("…a number with 5,736 digits", 36, ORANGE).next_to(lines, DOWN, buff=0.3)
        self.play(FadeIn(digits), run_time=0.5)
        self.hold(e)

        e = self.beat("g04")
        self.play(FadeOut(VGroup(fact, lines, digits)), run_time=0.4)
        g = T("a greedy algorithm", 64, YELLOW, weight="BOLD").shift(UP * 0.4 + RIGHT * 0.6)
        self.play(Write(g), ji.mood_to("happy"), run_time=1.0)
        self.hold(e)

        e = self.beat("g05")
        self.play(g.animate.scale(0.55).to_edge(UP), run_time=0.5)
        random.seed(11)
        root = Dot(radius=0.14, color=INK).move_to(LEFT * 3.2 + UP * 0.2)
        self.play(FadeIn(root), run_time=0.3)
        cur = root
        per = max(1.0, (dur("g05") - 1.5) / 3)
        for level in range(3):
            vals = random.sample(range(1, 10), 3)
            kids = VGroup()
            for k, v in enumerate(vals):
                p = cur.get_center() + RIGHT * 2.3 + UP * (1.3 - k * 1.3)
                d = Dot(radius=0.12, color=MUTE).move_to(p)
                lab = T(str(v), 30, INK).next_to(d, UP, buff=0.08)
                ln = Line(cur.get_center(), d.get_center(), color="#3a4550", stroke_width=4)
                kids.add(VGroup(ln, d, lab))
            self.play(LaggedStart(*[Create(kd[0]) for kd in kids], lag_ratio=0.1), *[FadeIn(kd[1:]) for kd in kids], run_time=0.5)
            best = max(range(3), key=lambda i: vals[i])
            others = [kids[i] for i in range(3) if i != best]
            self.play(kids[best][0].animate.set_color(YELLOW), kids[best][1].animate.set_color(YELLOW),
                      *[o.animate.set_opacity(0.25) for o in others], ji.look_at(RIGHT), run_time=0.5)
            cur = kids[best][1]
            self.wait(max(0.05, per - 1.0))
        rule = T("take what looks best now · never go back", 30, MUTE).to_edge(DOWN).shift(RIGHT * 0.8)
        self.play(FadeIn(rule), run_time=0.4)
        self.hold(e)

        e = self.beat("g06")
        self.clear_all(keep=[ji, g], run_time=0.4)
        q = T("which card comes next?", 36, INK).shift(UP * 2.2 + RIGHT * 0.6)
        left = [("銀行", 0.2), ("天気", 1.0), ("会社", 0.4), ("電話", 0.7)]
        cards_ = VGroup()
        for w_, s in left:
            sc = small_card(w_, w=1.9, h=1.2, size=48)
            br = bar(s, 1.0, 1.9, 0.18, GREEN if s == 1.0 else MUTE).next_to(sc, DOWN, buff=0.12)
            cards_.add(VGroup(sc, br))
        cards_.arrange(RIGHT, buff=0.45).shift(RIGHT * 0.8 + UP * 0.6)
        self.play(FadeIn(q), LaggedStart(*[FadeIn(c) for c in cards_], lag_ratio=0.15), run_time=0.9)
        best = cards_[1]
        why = T("guessable right now: you just met 天 and 気", 30, GREEN, JP).next_to(cards_, DOWN, buff=0.6)
        self.wait(max(0.2, dur("g06") * 0.35))
        self.play(best.animate.shift(DOWN * 0.2).scale(1.12), Indicate(best[0], color=GREEN), FadeIn(why), ji.mood_to("happy"), run_time=0.8)
        self.hold(e)

        e = self.beat("g07")
        self.clear_all(keep=[ji, g], run_time=0.4)
        specs = [("取る", "とる · take"), ("戻る", "もどる · return"), ("取り戻す", "とりもどす · take back")]
        row = VGroup()
        for w_, gl in specs:
            sc = small_card(w_, w=3.0, h=1.4, size=54)
            lab = T(gl, 26, MUTE, JP).next_to(sc, DOWN, buff=0.15)
            row.add(VGroup(sc, lab))
        row.arrange(RIGHT, buff=0.6).shift(RIGHT * 0.8 + UP * 0.6)
        per = max(1.2, (dur("g07") - 1.5) / 3)
        tags = ["opener: new 取", "opener: new 戻", "already guessable"]
        for i, item in enumerate(row):
            self.play(FadeIn(item, shift=UP * 0.2), run_time=0.5)
            tg = T(tags[i], 24, GREEN if i == 2 else YELLOW, JP).next_to(item, DOWN, buff=0.2)
            if i == 2:
                self.play(item[0][0].animate.set_fill(GREEN), FadeIn(tg), ji.mood_to("wow"), run_time=0.6)
            else:
                self.play(FadeIn(tg), run_time=0.4)
            self.wait(max(0.05, per - 1.0))
        self.hold(e)

        e = self.beat("g08")
        self.clear_all(keep=[ji, g], run_time=0.4)
        lab1 = T("deck order", 30, MUTE)
        lab2 = T("guessable path", 30, GREEN)
        g1 = grid(500, 25, 0.16, 0.04)
        g2 = grid(500, 25, 0.16, 0.04)
        b1 = VGroup(lab1, g1).arrange(DOWN, buff=0.2)
        b2 = VGroup(lab2, g2).arrange(DOWN, buff=0.2)
        VGroup(b1, b2).arrange(RIGHT, buff=1.0).shift(RIGHT * 0.9 + DOWN * 0.15)
        self.play(FadeIn(b1), FadeIn(b2), run_time=0.5)
        random.seed(5)
        on1 = random.sample(range(500), 66)
        on2 = random.sample(range(500), 307)
        n1 = T("66", 44, INK, weight="BOLD").next_to(g1, DOWN, buff=0.15)
        n2 = T("307", 44, GREEN, weight="BOLD").next_to(g2, DOWN, buff=0.15)
        self.play(*[g1[i].animate.set_fill(GREEN) for i in on1], FadeIn(n1), run_time=0.8)
        self.play(*[g2[i].animate.set_fill(GREEN) for i in on2], FadeIn(n2), ji.mood_to("happy"), run_time=1.2)
        self.hold(e)


class S07Sim(Beats):
    def construct(self):
        self.wait(0.3)
        e = self.beat("x01")
        a = Ji(1.5, mood="neutral").shift(LEFT * 3.4 + DOWN * 0.6)
        b = Ji(1.5, mood="neutral").shift(RIGHT * 3.0 + DOWN * 0.6)
        la = T("deck order", 30, MUTE).next_to(a, DOWN, buff=0.15)
        lb = T("guessable order", 30, GREEN).next_to(b, DOWN, buff=0.15)
        cal = VGroup()
        for who in (a, b):
            box = RoundedRectangle(corner_radius=0.12, width=1.6, height=1.3, fill_color=CARD, fill_opacity=1, stroke_width=0)
            top = Rectangle(width=1.6, height=0.35, fill_color=RED, fill_opacity=1, stroke_width=0).align_to(box, UP)
            cal.add(VGroup(box, top).next_to(who, RIGHT, buff=0.35).shift(UP * 0.5))
        info = T("20 new cards a day · reviews by FSRS (what Anki uses)", 30, INK).to_edge(UP).shift(DOWN * 0.3)
        self.play(FadeIn(a), FadeIn(b), FadeIn(la), FadeIn(lb), FadeIn(cal), FadeIn(info), run_time=0.8)
        days = [T("day %d" % d, 26, CARD_INK, weight="BOLD") for d in (1, 2, 3, 5, 8, 13, 21, 30)]
        nums = VGroup(days[0].copy().move_to(cal[0][0]).shift(DOWN * 0.15), days[0].copy().move_to(cal[1][0]).shift(DOWN * 0.15))
        self.play(FadeIn(nums), run_time=0.3)
        for dd in days[1:]:
            new = VGroup(dd.copy().move_to(cal[0][0]).shift(DOWN * 0.15), dd.copy().move_to(cal[1][0]).shift(DOWN * 0.15))
            self.remove(nums)
            self.add(new)
            nums = new
            self.wait(0.35)
        self.hold(e)

        e = self.beat("x02")
        self.clear_all(run_time=0.4)
        ax_x = Line(LEFT * 5.5, RIGHT * 5.5, color=MUTE).shift(DOWN * 1.8)
        ax_y = Line(DOWN * 1.8, UP * 1.9, color=MUTE).shift(LEFT * 5.5)
        ylab = T("memory of 電:でん", 26, MUTE, JP).next_to(ax_y, UP, buff=0.1).shift(RIGHT * 1.0)
        xlab = T("days", 26, MUTE).next_to(ax_x, DOWN, buff=0.1).align_to(ax_x, RIGHT)
        self.play(Create(ax_x), Create(ax_y), FadeIn(ylab), FadeIn(xlab), run_time=0.6)
        sights = [0.0, 2.2, 5.0, 8.6]
        pts = []
        for i, s0 in enumerate(sights):
            s1 = sights[i + 1] if i + 1 < len(sights) else 11.0
            stab = 1.2 * (1.8 ** i)
            for x in np.linspace(s0, s1, 30):
                pts.append([x - 5.5, -1.8 + 3.4 * np.exp(-(x - s0) / stab), 0])
        curve = VMobject(color=BLUE, stroke_width=6).set_points_as_corners(pts)
        marks = VGroup(*[VGroup(Line(UP * 0.0, UP * 0.3, color=ORANGE, stroke_width=5), T(w_, 22, ORANGE, JP).shift(UP * 0.5))
                         .move_to([s - 5.5, -1.55, 0]) for s, w_ in zip(sights, ["電話", "電車", "電気", "発電"])])
        self.play(Create(curve), LaggedStart(*[FadeIn(m) for m in marks], lag_ratio=0.4), run_time=3.0, rate_func=rate_functions.linear)
        note = T("every word with 電 refreshes it", 28, INK, JP).shift(UP * 2.4 + RIGHT * 1.5)
        self.play(FadeIn(note), run_time=0.4)
        self.hold(e)

        e = self.beat("x03")
        self.clear_all(run_time=0.4)
        binbox = VGroup(Line(LEFT * 1.6 + UP * 0.6, LEFT * 1.6 + DOWN * 0.9, color=GREEN, stroke_width=6),
                        Line(LEFT * 1.6 + DOWN * 0.9, RIGHT * 1.6 + DOWN * 0.9, color=GREEN, stroke_width=6),
                        Line(RIGHT * 1.6 + DOWN * 0.9, RIGHT * 1.6 + UP * 0.6, color=GREEN, stroke_width=6)).shift(DOWN * 1.2)
        lab = T("free cards", 40, GREEN, weight="BOLD").next_to(binbox, DOWN, buff=0.2)
        cd = small_card("電気", w=2.0, h=1.2, size=48).shift(UP * 2.2)
        self.play(Create(binbox), FadeIn(lab), FadeIn(cd), run_time=0.6)
        self.play(cd.animate.move_to(binbox.get_center() + DOWN * 0.15).scale(0.8), run_time=0.8, rate_func=rate_functions.ease_in_quad)
        self.hold(e)

        e = self.beat("x04")
        self.clear_all(run_time=0.4)
        ji = Ji(1.4).to_corner(DL).shift(UP * 0.05 + RIGHT * 0.1)
        hdr = T("JLPT deck · perfect guessing · first 100 words", 30, MUTE).to_edge(UP).shift(DOWN * 0.2)
        g100 = grid(100, 10, 0.42, 0.08).shift(LEFT * 0.8 + DOWN * 0.3)
        self.play(FadeIn(hdr), FadeIn(g100), FadeIn(ji), run_time=0.6)
        self.play(LaggedStart(*[g100[i].animate.set_fill(BLUE) for i in range(16)], lag_ratio=0.05), run_time=1.0)
        self.play(LaggedStart(*[g100[i].animate.set_fill(GREEN) for i in range(16, 100)], lag_ratio=0.01), run_time=1.4)
        leg = VGroup(VGroup(Square(0.3, fill_color=BLUE, fill_opacity=1, stroke_width=0), T("16 learned", 32)).arrange(RIGHT, buff=0.2),
                     VGroup(Square(0.3, fill_color=GREEN, fill_opacity=1, stroke_width=0), T("84 guessed", 32)).arrange(RIGHT, buff=0.2)
                     ).arrange(DOWN, aligned_edge=LEFT, buff=0.3).next_to(g100, RIGHT, buff=0.7)
        big = T("6.2×", 80, ORANGE, weight="BOLD").next_to(leg, DOWN, buff=0.5).align_to(leg, LEFT)
        self.play(FadeIn(leg), run_time=0.4)
        self.play(GrowFromCenter(big), ji.mood_to("wow"), run_time=0.6)
        self.hold(e)

        e = self.beat("x05")
        self.play(FadeOut(VGroup(hdr, g100, leg, big)), run_time=0.4)
        arc_bg = Arc(radius=2.0, start_angle=np.pi, angle=-np.pi, color="#2a3540", stroke_width=26).shift(DOWN * 0.3 + RIGHT * 0.6)
        arc = Arc(radius=2.0, start_angle=np.pi, angle=-np.pi * 0.73, color=GREEN, stroke_width=26).shift(DOWN * 0.3 + RIGHT * 0.6)
        pct = T("73%", 72, GREEN, weight="BOLD").move_to(arc_bg.get_center() + DOWN * 0.2)
        sub = T("my real first guesses (guessable, kanji seen recently)", 28, MUTE).next_to(arc_bg, DOWN, buff=0.5)
        self.play(Create(arc_bg), run_time=0.4)
        self.play(Create(arc), FadeIn(pct), FadeIn(sub), ji.mood_to("happy"), run_time=1.0)
        self.hold(e)

        e = self.beat("x06")
        self.play(FadeOut(VGroup(arc_bg, arc, pct, sub)), run_time=0.4)
        hdr = T("at 80% guessing · first 100 words", 30, MUTE).to_edge(UP).shift(DOWN * 0.2)
        g100 = grid(100, 10, 0.42, 0.08).shift(LEFT * 0.8 + DOWN * 0.3)
        self.play(FadeIn(hdr), FadeIn(g100), run_time=0.4)
        self.play(LaggedStart(*[g100[i].animate.set_fill(BLUE) for i in range(35)], lag_ratio=0.03), run_time=1.0)
        self.play(LaggedStart(*[g100[i].animate.set_fill(GREEN) for i in range(35, 100)], lag_ratio=0.01), run_time=1.0)
        leg = VGroup(VGroup(Square(0.3, fill_color=BLUE, fill_opacity=1, stroke_width=0), T("35 learned", 32)).arrange(RIGHT, buff=0.2),
                     VGroup(Square(0.3, fill_color=GREEN, fill_opacity=1, stroke_width=0), T("65 guessed", 32)).arrange(RIGHT, buff=0.2)
                     ).arrange(DOWN, aligned_edge=LEFT, buff=0.3).next_to(g100, RIGHT, buff=0.7)
        big = T("2.9×", 80, ORANGE, weight="BOLD").next_to(leg, DOWN, buff=0.5).align_to(leg, LEFT)
        self.play(FadeIn(leg), GrowFromCenter(big), run_time=0.6)
        self.hold(e)

        e = self.beat("x07")
        self.play(FadeOut(VGroup(hdr, g100, leg, big)), run_time=0.4)
        # speed-up at 80% guessing: Core 2k and Kaishi 1.5k (docs/results.md)
        xs = [100, 250, 500, 1000]
        series = (("Core 2k", [2.3, 2.0, 1.8, 1.4], BLUE), ("Kaishi 1.5k", [2.4, 2.0, 1.7, 1.2], ORANGE))
        X = lambda i: -4.0 + i * 2.6
        Y = lambda v: -1.9 + (v - 1.0) * 2.4
        axes = VGroup(Line([-4.6, -1.9, 0], [4.4, -1.9, 0], color=MUTE), Line([-4.6, -1.9, 0], [-4.6, 2.0, 0], color=MUTE))
        ticks = VGroup(*[T("%s words" % format(x, ","), 22, MUTE).move_to([X(i), -2.25, 0]) for i, x in enumerate(xs)])
        yt = VGroup(*[T("%.1f×" % v, 22, MUTE).move_to([-5.1, Y(v), 0]) for v in (1.0, 1.5, 2.0, 2.5)])
        self.play(Create(axes), FadeIn(ticks), FadeIn(yt), run_time=0.6)
        for name, vals, col in series:
            pl = VMobject(color=col, stroke_width=6).set_points_as_corners([[X(i), Y(v), 0] for i, v in enumerate(vals)])
            lab = T(name, 26, col).next_to([X(3), Y(vals[3]), 0], RIGHT, buff=0.15)
            self.play(Create(pl), FadeIn(lab), run_time=1.0)
        fade = T("biggest early, fades by ~1,000 words", 30, INK).shift(UP * 2.5)
        self.play(FadeIn(fade), ji.mood_to("think"), run_time=0.5)
        self.hold(e)

        e = self.beat("x08")
        self.clear_all(keep=[ji], run_time=0.4)
        t = T("forgotten reviews by day 30 (Core 2k, 80% guessing)", 30, MUTE).shift(UP * 2.3 + RIGHT * 0.6)
        r1 = VGroup(T("deck order", 32, INK), bar(189, 189, 6.0, 0.6, RED), T("189", 32, RED)).arrange(RIGHT, buff=0.3)
        r2 = VGroup(T("guessable order", 32, INK), bar(72, 189, 6.0, 0.6, GREEN), T("72", 32, GREEN)).arrange(RIGHT, buff=0.3)
        for r in (r1, r2):
            r[0].set_width(min(r[0].width, 3.2))
        VGroup(r1, r2).arrange(DOWN, aligned_edge=LEFT, buff=0.5).shift(RIGHT * 0.6 + UP * 0.6)
        self.play(FadeIn(t), FadeIn(r1[0]), GrowFromEdge(r1[1], LEFT), FadeIn(r1[2]), run_time=0.7)
        self.play(FadeIn(r2[0]), GrowFromEdge(r2[1], LEFT), FadeIn(r2[2]), ji.mood_to("wow"), run_time=0.7)
        pat = T("you're practicing the pattern", 40, YELLOW, weight="BOLD").shift(DOWN * 1.6 + RIGHT * 0.6)
        self.wait(max(0.2, dur("x08") * 0.35))
        self.play(Write(pat), ji.mood_to("happy"), run_time=0.9)
        self.hold(e)


class S08Languages(Beats):
    def construct(self):
        self.wait(0.3)
        ji = Ji(1.4).to_corner(DL).shift(UP * 0.05 + RIGHT * 0.1)
        self.add(ji)
        e = self.beat("l01")
        q = T("does this only work for Japanese?", 44, INK, weight="BOLD").to_edge(UP).shift(DOWN * 0.3)
        self.play(Write(q), ji.mood_to("think"), run_time=0.9)
        langs = VGroup()
        for big_, small_, col in (("日本語", "Japanese", BLUE), ("中文", "Chinese", RED), ("Aa", "English learners", GREEN), ("Rx", "medical students", PURPLE)):
            box = RoundedRectangle(corner_radius=0.2, width=2.5, height=2.2, fill_color=PANEL, fill_opacity=1, stroke_color=col, stroke_width=4)
            b_ = T(big_, 54, col, JP, "BOLD").move_to(box).shift(UP * 0.25)
            s_ = T(small_, 22, INK, max_width=2.2).next_to(b_, DOWN, buff=0.2)
            langs.add(VGroup(box, b_, s_))
        langs.arrange(RIGHT, buff=0.35).shift(RIGHT * 0.7 + DOWN * 0.1)
        self.play(LaggedStart(*[FadeIn(l, shift=UP * 0.2) for l in langs], lag_ratio=0.3), run_time=1.6)
        self.hold(e)

        e = self.beat("l02")
        self.play(FadeOut(q), langs.animate.scale(0.6).to_edge(UP).shift(RIGHT * 0.6), run_time=0.6)
        random.seed(2)
        threads = VGroup(*[RoundedRectangle(corner_radius=0.05, width=random.uniform(1.2, 2.6), height=0.22, fill_color=ORANGE,
                                            fill_opacity=random.uniform(0.35, 0.9), stroke_width=0) for _ in range(60)])
        threads.arrange_in_grid(rows=12, buff=0.12).shift(RIGHT * 0.6 + DOWN * 0.6)
        cnt = T("~1,600 Reddit threads", 40, ORANGE, weight="BOLD").next_to(threads, DOWN, buff=0.3)
        self.play(LaggedStart(*[FadeIn(t_, shift=DOWN * 0.3) for t_ in threads], lag_ratio=0.02), run_time=1.6)
        self.play(FadeIn(cnt), ji.mood_to("happy"), run_time=0.4)
        self.hold(e)

        e = self.beat("l03")
        self.play(FadeOut(VGroup(threads, cnt)), run_time=0.4)
        what = T("what counts as a piece?", 46, YELLOW, weight="BOLD").shift(RIGHT * 0.6)
        self.play(Write(what), run_time=0.8)
        self.hold(e)

        e = self.beat("l04")
        self.play(FadeOut(what), langs.animate.set_opacity(0.3), run_time=0.4)
        self.play(langs[1].animate.set_opacity(1), run_time=0.3)
        word = T("开学", 110, INK, JP, "BOLD").shift(UP * 0.9 + RIGHT * 0.6)
        p1 = tile("开", "kāi", "open", RED).shift(LEFT * 1.6 + DOWN * 1.3)
        p2 = tile("学", "xué", "study", RED).shift(RIGHT * 2.8 + DOWN * 1.3)
        self.play(FadeIn(word), run_time=0.4)
        self.play(FadeIn(p1, shift=DOWN * 0.2), FadeIn(p2, shift=DOWN * 0.2), run_time=0.6)
        mean = T("= the start of term", 34, GREEN).next_to(word, RIGHT, buff=0.4)
        self.play(FadeIn(mean), ji.mood_to("wow"), run_time=0.5)
        self.hold(e)

        e = self.beat("l05")
        self.play(FadeOut(VGroup(word, p1, p2, mean)), run_time=0.4)
        s1 = VGroup(T("96%", 90, RED, weight="BOLD"), T("of words: the pinyin follows\nfrom the characters", 28, INK)).arrange(DOWN, buff=0.2)
        s2 = VGroup(T("90%", 90, RED, weight="BOLD"), T("of HSK words share all their\ncharacters with other words", 28, INK)).arrange(DOWN, buff=0.2)
        VGroup(s1, s2).arrange(RIGHT, buff=1.4).shift(RIGHT * 0.6 + DOWN * 0.3)
        self.play(FadeIn(s1, shift=UP * 0.2), run_time=0.6)
        self.wait(max(0.3, dur("l05") * 0.4))
        self.play(FadeIn(s2, shift=UP * 0.2), run_time=0.6)
        self.hold(e)

        e = self.beat("l06")
        self.play(FadeOut(VGroup(s1, s2)), run_time=0.4)
        t = T("cards to reach 500 words, at 80% guessing (HSK 3.0)", 28, MUTE).shift(UP * 2.0 + RIGHT * 0.6)
        r1 = VGroup(T("deck order", 30), bar(392, 392, 6.0, 0.55, "#5b6670"), T("392", 30, MUTE)).arrange(RIGHT, buff=0.3)
        r2 = VGroup(T("guessable", 30, RED), bar(200, 392, 6.0, 0.55, RED), T("200", 30, RED)).arrange(RIGHT, buff=0.3)
        rows = VGroup(r1, r2).arrange(DOWN, aligned_edge=LEFT, buff=0.45).shift(RIGHT * 0.6 + UP * 0.2)
        self.play(FadeIn(t), FadeIn(r1[0]), GrowFromEdge(r1[1], LEFT), FadeIn(r1[2]), run_time=0.6)
        self.play(FadeIn(r2[0]), GrowFromEdge(r2[1], LEFT), FadeIn(r2[2]), run_time=0.6)
        two = T("about 2×, still 1.6–1.8× past 1,000 words", 32, INK).next_to(rows, DOWN, buff=0.6)
        self.play(FadeIn(two), ji.mood_to("happy"), run_time=0.5)
        self.hold(e)

        e = self.beat("l07")
        self.play(FadeOut(VGroup(t, rows, two)), langs.animate.set_opacity(0.3), run_time=0.4)
        self.play(langs[2].animate.set_opacity(1), run_time=0.3)
        parts = VGroup(*[bubble(T(s, 44, INK), "#173022", GREEN, 0.2) for s in ("un-", "employ", "-ed")]).arrange(RIGHT, buff=0.25)
        parts.shift(UP * 0.8 + RIGHT * 0.6)
        eq = T("= unemployed", 40, GREEN).next_to(parts, DOWN, buff=0.35)
        self.play(LaggedStart(*[FadeIn(p, shift=UP * 0.15) for p in parts], lag_ratio=0.2), run_time=0.8)
        self.play(FadeIn(eq), run_time=0.4)
        self.wait(max(0.3, dur("l07") * 0.35))
        nope = VGroup(T("beach", 44, INK), T("rock", 44, INK)).arrange(RIGHT, buff=1.2).shift(DOWN * 1.6 + RIGHT * 0.6)
        qm = VGroup(*[T("?", 44, RED, weight="BOLD").next_to(n_, RIGHT, buff=0.15) for n_ in nope])
        self.play(FadeIn(nope), FadeIn(qm), ji.mood_to("confused"), run_time=0.6)
        self.hold(e)

        e = self.beat("l08")
        self.play(FadeOut(VGroup(parts, eq, nope, qm)), run_time=0.4)
        root = bubble(T("employ", 44, INK), "#173022", GREEN, 0.2).shift(UP * 1.3 + RIGHT * 0.6)
        kids = VGroup(*[bubble(T(s, 36, INK), PANEL, MUTE, 0.18) for s in ("employer", "employment", "unemployed")]).arrange(RIGHT, buff=0.5)
        kids.shift(DOWN * 0.4 + RIGHT * 0.6)
        links = VGroup(*[Line(root.get_bottom(), k.get_top(), color=GREEN, stroke_width=4) for k in kids])
        self.play(FadeIn(root), run_time=0.4)
        self.play(Create(links), LaggedStart(*[FadeIn(k, shift=DOWN * 0.2) for k in kids], lag_ratio=0.2), run_time=0.9)
        self.play(*[k[0].animate.set_stroke(GREEN) for k in kids], ji.mood_to("happy"), run_time=0.4)
        st = T("a fifth to a quarter guessable · about 1.5× at 500 words", 30, INK).shift(DOWN * 2.0 + RIGHT * 0.6)
        self.play(FadeIn(st), run_time=0.5)
        self.hold(e)

        e = self.beat("l09")
        self.play(FadeOut(VGroup(root, kids, links, st)), langs.animate.set_opacity(0.3), run_time=0.4)
        self.play(langs[3].animate.set_opacity(1), run_time=0.3)
        med = VGroup(bubble(T("hepat", 44, INK), "#261c33", PURPLE, 0.2), T("+", 44, MUTE),
                     bubble(T("-itis", 44, INK), "#261c33", PURPLE, 0.2)).arrange(RIGHT, buff=0.3).shift(UP * 0.8 + RIGHT * 0.6)
        gl = VGroup(T("liver", 28, MUTE).next_to(med[0], DOWN, buff=0.15), T("inflammation", 28, MUTE).next_to(med[2], DOWN, buff=0.15))
        res = T("= hepatitis", 40, PURPLE).next_to(med, RIGHT, buff=0.4)
        self.play(FadeIn(med), FadeIn(gl), run_time=0.6)
        self.play(FadeIn(res), ji.mood_to("wow"), run_time=0.4)
        self.wait(max(0.3, dur("l09") * 0.4))
        meh = T("the terminology deck alone: about 1.0×", 32, INK).shift(DOWN * 1.7 + RIGHT * 0.6)
        self.play(FadeIn(meh), ji.mood_to("sad"), run_time=0.5)
        self.hold(e)

        e = self.beat("l10")
        self.play(FadeOut(VGroup(med, gl, res, meh)), run_time=0.4)
        mixed = VGroup(*[small_card(w_, w=2.5, h=1.0, size=34) for w_ in ("RCA", "infliximab", "braces", "Rx", "colpotomy", "MTB")])
        mixed.arrange_in_grid(rows=2, buff=0.35).shift(RIGHT * 0.6 + UP * 0.4)
        self.play(LaggedStart(*[FadeIn(m, shift=UP * 0.15) for m in mixed], lag_ratio=0.12), run_time=1.0)
        rare = T("its roots rarely come back in a second term", 30, MUTE).next_to(mixed, DOWN, buff=0.5)
        self.play(FadeIn(rare), ji.mood_to("doubt"), run_time=0.5)
        self.hold(e)

        e = self.beat("l11")
        self.play(FadeOut(VGroup(mixed, rare)), run_time=0.4)
        lab = T("roots first", 32, INK).move_to([-4.6, 1.2, 0])
        roots = Rectangle(width=5.8, height=0.6, fill_color=PURPLE, fill_opacity=0.8, stroke_width=0)
        terms = Rectangle(width=2.6, height=0.6, fill_color=GREEN, fill_opacity=0.8, stroke_width=0)
        tl = VGroup(roots, terms).arrange(RIGHT, buff=0).move_to([1.7, 1.2, 0])
        rl = T("982 root cards", 24, INK).move_to(roots)
        tlab = T("terms", 24, CARD_INK).move_to(terms)
        mark = VGroup(Line(UP * 0.5, DOWN * 0.5, color=YELLOW, stroke_width=5), T("first term: day 50", 24, YELLOW).shift(DOWN * 0.75))
        mark.move_to(terms.get_left() + DOWN * 0.15)
        self.play(FadeIn(lab), GrowFromEdge(roots, LEFT), FadeIn(rl), run_time=1.0)
        self.play(GrowFromEdge(terms, LEFT), FadeIn(tlab), FadeIn(mark), run_time=0.7)
        self.hold(e)

        e = self.beat("l12")
        lab2 = T("guessable order", 32, GREEN).move_to([-4.6, -1.0, 0])
        blocks = VGroup()
        for i in range(28):
            col = PURPLE if i % 3 != 2 else GREEN
            blocks.add(Rectangle(width=0.3, height=0.6, fill_color=col, fill_opacity=0.85, stroke_width=0))
        blocks.arrange(RIGHT, buff=0.0).move_to([0.9, -1.0, 0]).align_to(roots, LEFT)
        self.play(FadeIn(lab2), LaggedStart(*[FadeIn(b_) for b_ in blocks], lag_ratio=0.03), run_time=1.2)
        wk = T("68 free terms by day 14", 30, GREEN, weight="BOLD").next_to(blocks, DOWN, buff=0.35).align_to(blocks, LEFT)
        self.play(FadeIn(wk), ji.mood_to("happy"), run_time=0.5)
        self.hold(e)

        e = self.beat("l13")
        self.clear_all(keep=[ji], run_time=0.4)
        t = T("speed-up at 500 words, 80% guessing", 30, MUTE).shift(UP * 2.4 + RIGHT * 0.6)
        data = (("Chinese", 1.9, RED), ("Japanese", 1.75, BLUE), ("English", 1.5, GREEN), ("Medical", 1.07, PURPLE))
        rows = VGroup()
        for i, (nm, v, col) in enumerate(data):
            y = 1.5 - i * 0.85
            lab = T(nm, 32, INK)
            lab.move_to([-1.6, y, 0], aligned_edge=RIGHT)
            br = bar(v - 0.9, 1.1, 6.0, 0.55, col).move_to([-1.3, y, 0], aligned_edge=LEFT)
            val = T("%.2g×" % v if v < 1.1 else "%.1f×" % v, 32, col).next_to(br, RIGHT, buff=0.25)
            rows.add(VGroup(lab, br, val))
        self.play(FadeIn(t), run_time=0.3)
        for r in rows:
            self.play(FadeIn(r[0]), GrowFromEdge(r[1], LEFT), FadeIn(r[2]), run_time=0.45)
        why = VGroup(T("1. how many words are built from reusable pieces", 30, INK),
                     T("2. how predictable those pieces are", 30, INK)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        why.next_to(rows, DOWN, buff=0.5).align_to(rows, LEFT)
        self.play(FadeIn(why, shift=UP * 0.15), ji.mood_to("think"), run_time=0.6)
        self.hold(e)


class S09Outro(Beats):
    def construct(self):
        self.wait(0.3)
        ji = Ji(1.5).to_corner(DL).shift(UP * 0.05 + RIGHT * 0.1)
        self.add(ji)
        e = self.beat("o01")
        img = ImageMobject(str(HERE / "assets" / "dashboard_zh.png")).set_height(5.2).shift(RIGHT * 1.6 + UP * 0.3)
        frame = SurroundingRectangle(img, color="#3a4550", buff=0.05, stroke_width=3)
        name = T("GuessWithAnki", 46, INK, weight="BOLD").next_to(img, UP, buff=0.2)
        self.play(FadeIn(img), Create(frame), FadeIn(name), ji.mood_to("happy", look=RIGHT), run_time=0.8)
        tags = T("free · open source · on GitHub", 28, GREEN).next_to(img, DOWN, buff=0.2)
        self.wait(max(0.3, dur("o01") * 0.5))
        self.play(FadeIn(tags), run_time=0.4)
        self.hold(e)

        e = self.beat("o02")
        self.play(FadeOut(VGroup(frame, name, tags)), FadeOut(img), run_time=0.5)
        magic = T("black magic", 60, PURPLE, weight="BOLD").shift(UP * 1.0 + RIGHT * 0.6)
        self.play(FadeIn(magic), ji.mood_to("neutral"), run_time=0.5)
        self.wait(max(0.3, dur("o02") * 0.3))
        strike = Line(magic.get_left(), magic.get_right(), color=RED, stroke_width=8)
        pattern = T("a pattern", 60, GREEN, weight="BOLD").next_to(magic, DOWN, buff=0.6)
        self.play(Create(strike), run_time=0.4)
        self.play(FadeIn(pattern, shift=UP * 0.2), ji.mood_to("happy"), run_time=0.6)
        verbs = T("measure it · play with it · learn it", 32, INK).next_to(pattern, DOWN, buff=0.5)
        self.play(FadeIn(verbs), run_time=0.5)
        self.hold(e)

        e = self.beat("o03")
        self.play(FadeOut(VGroup(magic, strike, pattern, verbs)), ji.animate.move_to(ORIGIN + DOWN * 0.3).scale(1.6), run_time=0.8)
        stay = T("stay curious", 52, INK, weight="BOLD").next_to(ji, UP, buff=0.4)
        self.play(FadeIn(stay, shift=DOWN * 0.2), run_time=0.5)
        self.play(ji.blink(), run_time=0.3)
        self.hold(e)
        self.play(FadeOut(stay), ji.mood_to("happy"), run_time=0.6)
        self.wait(1.2)
        self.play(FadeOut(ji), run_time=0.8)


SCENES = ["S01Intro", "S02Disclaimer", "S03Python", "S04Story", "S05Measure", "S06Greedy", "S07Sim", "S08Languages",
          "S09Outro"]
