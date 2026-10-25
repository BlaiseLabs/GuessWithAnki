"""Layout tests for the video: the checker finds what it should, Gaku keeps his shape through every mood, and no
scene has text over text, text sticking out of its box, anything over Gaku, or anything off the frame.

    ~/manim-venv/bin/python -m pytest -q docs/video/test_layout.py      (the scene test runs every scene, ~1 min)"""
import itertools
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from manim import DL, LEFT, RIGHT, UP, RoundedRectangle, Scene, Text

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from ji import Ji  # noqa: E402
from video import SCENES, layout_problems  # noqa: E402

MOODS = ["neutral", "happy", "wow", "think", "doubt", "confused", "sad"]


def kinds(mobs):
    return sorted({k for k, a, b in layout_problems(mobs)})


def test_the_checker_finds_overlaps_and_off_frame():
    a = Text("hello there")
    b = Text("overlapping").move_to(a.get_center() + RIGHT * 0.3)
    assert kinds([a, b]) == ["text-on-text"]
    box = RoundedRectangle(width=2, height=1, fill_opacity=1)
    long = Text("much too long for the box").move_to(box)
    assert kinds([box, long]) == ["text-out-of-box"]
    inside = Text("fits", font_size=24).move_to(box)
    assert kinds([box, inside]) == []
    assert kinds([Text("off the edge").shift(RIGHT * 7)]) == ["off-frame"]
    ji = Ji(1.5).shift(LEFT * 3)
    assert kinds([ji, Text("on Gaku").move_to(ji)]) == ["text-on-Gaku"]
    assert kinds([ji, Text("far away").shift(UP * 2)]) == []


@pytest.mark.parametrize("a,b", list(itertools.permutations(MOODS, 2)))
def test_gaku_keeps_his_shape_through_every_mood_change(a, b):
    """(a mood with fewer parts made Transform collapse the extra brows to a point at the screen's centre)"""
    class One(Scene):
        def construct(self):
            ji = Ji(1.6, mood=a).to_corner(DL)
            self.add(ji)
            before = (ji.get_left()[0], ji.get_right()[0], ji.get_bottom()[1], ji.get_top()[1])
            self.play(ji.mood_to(b, look=LEFT), run_time=0.1)
            after = (ji.get_left()[0], ji.get_right()[0], ji.get_bottom()[1], ji.get_top()[1])
            assert max(abs(x - y) for x, y in zip(before, after)) < 0.05, (a, b, before, after)
            assert len(ji.face[1]) == 2                     # (always two brows, hidden or not)
    from manim import tempconfig
    with tempconfig({"dry_run": True, "quality": "low_quality", "disable_caching": True}):
        One().render()


def test_no_scene_has_layout_problems():
    def run(scene):
        env = dict(os.environ, GWA_CHECK="1")
        r = subprocess.run([str(Path(sys.executable).parent / "manim"), "--dry_run", "--media_dir",
                            "/tmp/gwa_layout_%s" % scene, str(HERE / "video.py"), scene],
                           cwd=HERE, env=env, capture_output=True, text=True)
        assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
        return scene, json.loads((HERE / "build" / ("layout_%s.json" % scene)).read_text())
    with ThreadPoolExecutor(len(SCENES)) as ex:
        found = dict(ex.map(run, SCENES))
    bad = {s: list(p) for s, p in found.items() if p}
    assert not bad, json.dumps(bad, indent=1, ensure_ascii=False)
