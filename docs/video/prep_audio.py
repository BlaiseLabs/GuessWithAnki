"""The voice clips for the build, from segments cut out of block takes (narration.BLOCKS): the first segment of a
block loses its leading silence, the last its trailing silence plus a pause between blocks; inner cuts keep the
natural pause they were cut in. Writes build/audio/<id>.wav (48 kHz mono) and build/durations.json (each beat's
length: its clip, plus the pause after a block's end).

    python3 docs/video/prep_audio.py SEGS_DIR [--block-gap 0.45]"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from narration import BLOCKS  # noqa: E402

LEAD = "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.04"
TAIL = "areverse,silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.12,areverse"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("segs")
    ap.add_argument("--block-gap", type=float, default=0.45)
    a = ap.parse_args()
    out = HERE / "build" / "audio"
    out.mkdir(parents=True, exist_ok=True)
    durs = {"_blocks": True}
    for blk in BLOCKS:
        for k, sid in enumerate(blk):
            f = [LEAD] if k == 0 else []
            if k == len(blk) - 1:
                f.append(TAIL)
            dst = out / ("%s.wav" % sid)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(Path(a.segs) / ("%s.wav" % sid))]
                           + (["-af", ",".join(f)] if f else []) + ["-ac", "1", "-ar", "48000", str(dst)], check=True)
            d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                      str(dst)], capture_output=True, text=True).stdout)
            durs[sid] = round(d + (a.block_gap if k == len(blk) - 1 else 0.0), 3)
    (HERE / "build" / "durations.json").write_text(json.dumps(durs, indent=1))
    print(len(durs) - 1, "clips, %.1f s" % sum(v for k, v in durs.items() if k != "_blocks"))


if __name__ == "__main__":
    main()
