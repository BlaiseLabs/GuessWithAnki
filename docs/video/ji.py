"""Gaku: the kanji 学 ("study") with eyes, the video's narrator stand-in. Its moods change the eyes (and a small
mouth): neutral, happy, wow, think, doubt, confused, sad. Built from plain shapes so every mood can morph into
any other."""
import numpy as np
from manim import (DOWN, LEFT, RIGHT, UP, Arc, Circle, Ellipse, Line, VGroup, Text, Transform, Succession,
                   ApplyMethod, AnimationGroup, rate_functions)

JP = "Noto Sans CJK JP"
BODY = "#3987e5"
WHITE = "#f8f8f4"
PUPIL = "#101418"


class Ji(VGroup):
    def __init__(self, height=2.2, color=BODY, mood="neutral", glyph="学", **kw):
        super().__init__(**kw)
        self.body = Text(glyph, font=JP, weight="BOLD", color=color).set_height(height)
        self.add(self.body)
        self.mood = mood
        self.look = np.array([0.0, 0.0, 0.0])
        self.face = self._face(mood, self.look)
        self.add(self.face)

    @property
    def h(self):
        return self.body.height

    # the face sits on the open space under the roof (宀), above 子
    def _anchor(self):
        b = self.body
        return b.get_center() + UP * 0.12 * self.h

    def _face(self, mood, look):
        h = self.h
        c = self._anchor()
        ew, eh = 0.21 * h, 0.26 * h
        gap = 0.13 * h
        sq = {"neutral": 1.0, "happy": 0.55, "wow": 1.25, "think": 0.9, "doubt": 0.6, "confused": 1.0, "sad": 0.8}[mood]
        pupil_r = {"wow": 0.035, "happy": 0.05}.get(mood, 0.055) * h
        eyes = VGroup()
        for side, s in ((LEFT, -1), (RIGHT, 1)):
            this_sq = sq
            if mood == "doubt" and s > 0:
                this_sq = 1.1                          # one eye wide, one narrowed
            if mood == "confused":
                this_sq = 0.75 if s < 0 else 1.15
            e = Ellipse(width=ew, height=eh * this_sq, color=PUPIL, stroke_width=2.5, fill_color=WHITE, fill_opacity=1)
            e.move_to(c + side * gap)
            p = Circle(radius=pupil_r, fill_color=PUPIL, fill_opacity=1, stroke_width=0)
            off = np.array(look) * 0.045 * h
            if mood == "think":
                off = np.array([0.03, 0.06, 0]) * h       # looking up and away
            if mood == "confused":
                off = np.array([0.04 * s, 0.0, 0]) * h     # eyes drift apart
            p.move_to(e.get_center() + off)
            eyes.add(VGroup(e, p))
        # brows for doubt / sad / confused
        # always two brows (hidden in moods without them), so any mood morphs into any other: a mood with
        # fewer parts would make Transform collapse the extra ones to a point at the screen's centre
        brows = VGroup()
        shown = mood in ("doubt", "sad", "confused", "wow")
        for side, s in ((LEFT, -1), (RIGHT, 1)):
            y, tilt = eh * 0.75, 0.0
            if mood == "doubt":
                tilt = 0.25 if s > 0 else -0.05
                y = eh * (0.85 if s > 0 else 0.55)
            elif mood == "sad":
                tilt = 0.25 * s
            elif mood == "confused":
                tilt = -0.2 * s
            elif mood == "wow":
                y = eh * 0.95
            ln = Line(LEFT * ew * 0.45, RIGHT * ew * 0.45, color=PUPIL, stroke_width=5).rotate(tilt)
            ln.move_to(c + side * gap + UP * y)
            if not shown:
                ln.set_stroke(opacity=0)
            brows.add(ln)
        # a small mouth under the eyes, on the crossbar of 子
        m_c = c + DOWN * 0.22 * h
        if mood == "happy":
            mouth = Arc(radius=0.07 * h, start_angle=np.pi * 1.1, angle=np.pi * 0.8, color=PUPIL, stroke_width=5)
        elif mood == "wow":
            mouth = Ellipse(width=0.07 * h, height=0.1 * h, color=PUPIL, fill_color=PUPIL, fill_opacity=1)
        elif mood == "sad":
            mouth = Arc(radius=0.07 * h, start_angle=np.pi * 0.1, angle=np.pi * 0.8, color=PUPIL, stroke_width=5)
        else:
            mouth = Line(LEFT * 0.04 * h, RIGHT * 0.04 * h, color=PUPIL, stroke_width=5)
            if mood in ("doubt", "confused"):
                mouth.rotate(0.25)
        mouth.move_to(m_c)
        return VGroup(eyes, brows, mouth)

    def mood_to(self, mood, look=None, run_time=0.4):
        """an animation to a new mood"""
        self.mood = mood
        if look is not None:
            self.look = np.array(look, dtype=float)
        target = self._face(mood, self.look)
        return Transform(self.face, target, run_time=run_time)

    def look_at(self, direction, run_time=0.3):
        d = np.array(direction, dtype=float)
        n = np.linalg.norm(d)
        self.look = d / n if n else d
        return self.mood_to(self.mood, self.look, run_time)

    def blink(self):
        """a quick blink (squash the eyes and back)"""
        eyes = self.face[0]
        return Succession(ApplyMethod(eyes.stretch, 0.1, 1, run_time=0.08),
                          ApplyMethod(eyes.stretch, 10, 1, run_time=0.1))
