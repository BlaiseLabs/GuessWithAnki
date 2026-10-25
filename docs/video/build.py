"""Build the narrated video: render every scene (in parallel), lay each voice clip on the time its beat started,
join the scenes, write captions.

    python docs/video/build.py [--quality h|l] [--scenes S01Intro ...] [--jobs 9]

Needs build/audio/<id>.wav (the trimmed voice clips) and build/durations.json; writes build/guesswithanki_video.mp4
and build/guesswithanki_video.srt. The voice is only levelled (one fixed gain to -16 LUFS), nothing else."""
import argparse
import json
import re
import subprocess
import sys
import wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
B = HERE / "build"
sys.path.insert(0, str(HERE))
from narration import segments  # noqa: E402
from video import SCENES  # noqa: E402

SR = 48000
MANIM = Path(sys.executable).parent / "manim"


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def render(scene, quality):
    media = B / ("media_%s" % scene)
    args = [str(MANIM), "--media_dir", str(media), "--disable_caching"]
    args += (["-r", "1920,1080", "--fps", "30"] if quality == "h" else ["-ql"])
    args += [str(HERE / "video.py"), scene]
    with open(B / ("render_%s.log" % scene), "w") as log:
        rc = subprocess.run(args, cwd=HERE, stdout=log, stderr=subprocess.STDOUT).returncode
    mp4 = sorted(media.glob("videos/video/*/%s.mp4" % scene), key=lambda p: p.stat().st_mtime)
    return scene, rc, (mp4[-1] if mp4 else None)


def duration(f):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)]).stdout)


def read_wav(f):
    w = wave.open(str(f))
    a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    if w.getnchannels() > 1:
        a = a.reshape(-1, w.getnchannels()).mean(1)
    assert w.getframerate() == SR, f
    return a


def write_wav(f, a):
    w = wave.open(str(f), "wb")
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())
    w.close()


def chunks(text, limit=84):
    """caption chunks of at most `limit` characters, broken at sentence ends, then commas, then spaces"""
    out = []
    for sent in re.split(r"(?<=[.?!])\s+", text.strip()):
        while len(sent) > limit:
            cut = max(sent.rfind(", ", 0, limit), sent.rfind(": ", 0, limit))
            cut = cut + 1 if cut > limit // 3 else sent.rfind(" ", 0, limit)
            out.append(sent[:cut].strip())
            sent = sent[cut:].strip()
        if sent:
            out.append(sent)
    return out


def stamp(t):
    ms = int(round(t * 1000))
    return "%02d:%02d:%02d,%03d" % (ms // 3600000, ms // 60000 % 60, ms // 1000 % 60, ms % 1000)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quality", default="h")
    ap.add_argument("--scenes", nargs="*", default=SCENES)
    ap.add_argument("--jobs", type=int, default=9)
    ap.add_argument("--no-render", action="store_true")
    a = ap.parse_args()
    B.mkdir(exist_ok=True)
    texts = {sid: text for sec, sid, text, say in segments()}
    videos = {}
    if not a.no_render and a.scenes:
        with ThreadPoolExecutor(a.jobs) as ex:
            for scene, rc, mp4 in ex.map(lambda s: render(s, a.quality), a.scenes):
                print(scene, "rendered" if rc == 0 else "FAILED (see build/render_%s.log)" % scene, flush=True)
                if rc != 0:
                    sys.exit(1)
                videos[scene] = mp4
    for s in SCENES:                                   # (scenes not rendered this time: the last render)
        if s not in videos:
            found = sorted((B / ("media_%s" % s)).glob("videos/video/*/%s.mp4" % s), key=lambda p: p.stat().st_mtime)
            videos[s] = found[-1]
    # one voice track per scene, each clip at its beat's recorded start
    parts, srt, offset, n = [], [], 0.0, 0
    for s in SCENES:
        v = videos[s]
        vd = duration(v)
        sj = json.loads((B / ("starts_%s.json" % s)).read_text())
        st = sj["starts"]
        if sj.get("overruns"):
            print("  %s: beats whose animation outlasts the voice (s): %s" % (s, sj["overruns"]))
        track = np.zeros(int(vd * SR) + SR, np.float32)
        for sid, t0 in st.items():
            clip = read_wav(B / "audio" / ("%s.wav" % sid))
            i = int(t0 * SR)
            track[i:i + len(clip)] += clip[:max(0, len(track) - i)]
            # captions: chunks timed by their share of the clip's characters
            cs = chunks(texts[sid])
            total = sum(len(c) for c in cs)
            t, cd = offset + t0, len(clip) / SR
            for c in cs:
                d = cd * len(c) / total
                n += 1
                srt.append("%d\n%s --> %s\n%s\n" % (n, stamp(t), stamp(t + d), c))
                t += d
        write_wav(B / ("voice_%s.wav" % s), track[:int(vd * SR)])
        parts.append((v, B / ("voice_%s.wav" % s)))
        offset += vd
    # level the whole voice once: a fixed gain to -16 LUFS
    allv = np.concatenate([read_wav(p[1]) for p in parts])
    write_wav(B / "voice_all.wav", allv)
    meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(B / "voice_all.wav"), "-af", "ebur128", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    lufs = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", meas)[-1])
    gain = -16.0 - lufs
    print("voice loudness %.1f LUFS, gain %+.1f dB" % (lufs, gain))
    # join the scene videos, then put the voice and captions on
    lst = B / "scenes.txt"
    lst.write_text("".join("file '%s'\n" % p[0] for p in parts))
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(B / "video_only.mp4")])
    (B / "guesswithanki_video.srt").write_text("\n".join(srt), encoding="utf-8")
    run(["ffmpeg", "-y", "-v", "error", "-i", str(B / "video_only.mp4"), "-i", str(B / "voice_all.wav"),
         "-i", str(B / "guesswithanki_video.srt"), "-map", "0:v", "-map", "1:a", "-map", "2:s",
         "-c:v", "copy", "-af", "volume=%.2fdB,alimiter=limit=0.95" % gain, "-c:a", "aac", "-b:a", "192k",
         "-c:s", "mov_text", "-metadata:s:s:0", "language=eng", "-shortest", str(B / "guesswithanki_video.mp4")])
    print("wrote", B / "guesswithanki_video.mp4", "%.1f s" % duration(B / "guesswithanki_video.mp4"))


if __name__ == "__main__":
    main()
