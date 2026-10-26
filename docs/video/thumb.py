"""The YouTube thumbnail and the article's cover, in the video's look.

    manim -s -r 1280,720 docs/video/thumb.py Thumbnail      (YouTube)
    manim -s -r 2000,840 docs/video/thumb.py Cover          (DEV cover, shown at 1000x420)"""
import sys
from pathlib import Path

from manim import DOWN, LEFT, RIGHT, UP, Scene, VGroup, config

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ji import Ji  # noqa: E402
from video import BG, GREEN, INK, MUTE, YELLOW, T, card, check  # noqa: E402

config.background_color = BG


def pieces():
    head = VGroup(T("GUESS WORDS", 92, YELLOW, weight="BOLD", max_width=20),
                  T("YOU'VE NEVER SEEN", 92, INK, weight="BOLD", max_width=20)).arrange(DOWN, buff=0.15, aligned_edge=LEFT)
    gaku = Ji(4.6, mood="wow")
    c = card("電気", "でんき", "electricity")
    ok = check(0.7).next_to(c, RIGHT, buff=0.25)
    return head, gaku, VGroup(c, ok)


class Thumbnail(Scene):
    def construct(self):
        head, gaku, c = pieces()
        head.scale_to_fit_width(config.frame_width * 0.62).to_corner(UP + RIGHT, buff=0.5)
        gaku.scale(0.95).to_corner(DOWN + LEFT, buff=0.45)
        c.scale(0.85).to_corner(DOWN + RIGHT, buff=0.5).shift(LEFT * 0.4)
        sub = T("with a bit of computer science", 34, MUTE).next_to(head, DOWN, buff=0.3).align_to(head, LEFT)
        self.add(head, gaku, c, sub)


class Cover(Scene):
    """(at 2000x840 Manim keeps the frame 14.2 wide and makes it about 6 high)"""
    def construct(self):
        head, gaku, c = pieces()
        gaku.scale(0.72).move_to(LEFT * 5.3)
        head.scale_to_fit_width(6.2).move_to(LEFT * 0.1 + UP * 0.45)
        sub = T("Japanese · Chinese · English · Medicine", 36, GREEN).scale_to_fit_width(5.6)
        sub.next_to(head, DOWN, buff=0.4)
        c.scale(0.62).move_to(RIGHT * 5.0)
        self.add(head, gaku, c, sub)
