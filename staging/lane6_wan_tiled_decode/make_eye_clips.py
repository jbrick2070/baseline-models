"""Build the operator-eye comparison for lane 6: does the shimmer SHOW?

The lane measured that tiled decode churns 4-5x more between frames on a card
whose prompt demands stillness. That is a pixel statistic, not a judgment, and
the operator asked the right question: is this better quality, or just a number?

So this makes the thing his eye can answer, from frames ALREADY on disk -- no new
GPU time. Two shapes, because they answer different questions:

  SIDE-BY-SIDE   the two arms hard-cut together, left and right, same frame at
                 the same instant. Best for spotting a difference at all.
  SOLO PAIRS     each arm alone, full width, one after the other. Best for
                 judging whether the difference is objectionable rather than
                 merely present -- a defect you only see when it is pointed at
                 is a different thing from one that spoils a shot.

BLIND BY CONSTRUCTION. Which arm is on the left alternates per cell and no arm
is named on screen. The key is written to a JSON beside the clips and is not
needed until after the calls are in. This is lane 1's protocol
(``make_clips.left_arm_for``) and it exists because the driver's own strip reads
have been wrong twice, at both seeds, and were caught by blinded seats.

The test card is the fixture where the effect is largest (4-5x); crowd is where
it nearly vanishes (1.2-1.4x). BOTH are built, deliberately: if he can see it on
the card and not on the crowd, that is the honest shape of the finding and it
should be what he sees too, rather than only the flattering fixture.
"""
from __future__ import annotations

import hashlib
import io
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FRAMES = Path("C:/Users/jeffr/Documents/ComfyUI/output/baseline_output/"
              "lane6_wan_tiled_decode")
OUT = FRAMES / "_eye"
FPS = 24
CELLS = [("testcard", 42), ("testcard", 20260821),
         ("crowd", 42), ("crowd", 20260821)]


def left_arm_for(fixture: str, seed: int) -> str:
    """Deterministic but unguessable-at-a-glance side assignment."""
    h = hashlib.sha256(f"lane6|{fixture}|{seed}".encode()).hexdigest()
    return "ours" if int(h[:8], 16) % 2 == 0 else "candidate"


def run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("ffmpeg failed:\n" + (r.stderr or "")[-1500:])


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    OUT.mkdir(parents=True, exist_ok=True)
    key = {}

    for fixture, seed in CELLS:
        left = left_arm_for(fixture, seed)
        right = "candidate" if left == "ours" else "ours"
        lpat = str(FRAMES / fixture / f"{left}_seed{seed}" / "frame_%05d_.png")
        rpat = str(FRAMES / fixture / f"{right}_seed{seed}" / "frame_%05d_.png")
        stem = f"{fixture}_seed{seed}"

        sbs = OUT / f"SIDEBYSIDE_{stem}.mp4"
        run(["ffmpeg", "-y", "-loglevel", "error",
             "-framerate", str(FPS), "-start_number", "1", "-i", lpat,
             "-framerate", str(FPS), "-start_number", "1", "-i", rpat,
             "-filter_complex",
             "[0:v]pad=iw+6:ih:0:0:color=black[l];[l][1:v]hstack=inputs=2,"
             "scale=1600:-2:flags=lanczos",
             "-c:v", "libx264", "-crf", "16", "-preset", "slow",
             "-pix_fmt", "yuv420p", str(sbs)])

        solo = OUT / f"SOLO_{stem}.mp4"
        run(["ffmpeg", "-y", "-loglevel", "error",
             "-framerate", str(FPS), "-start_number", "1", "-i", lpat,
             "-framerate", str(FPS), "-start_number", "1", "-i", rpat,
             "-filter_complex",
             "[0:v]scale=1280:-2:flags=lanczos[a];"
             "[1:v]scale=1280:-2:flags=lanczos[b];[a][b]concat=n=2:v=1:a=0",
             "-c:v", "libx264", "-crf", "16", "-preset", "slow",
             "-pix_fmt", "yuv420p", str(solo)])

        key[stem] = {"left_or_first": left, "right_or_second": right}
        print(f"[BUILT] {stem:<24} left/first={left}")

    io.open(OUT / "KEY.json", "w", encoding="utf-8", newline="\n").write(
        json.dumps({
            "lane": "lane6_wan_tiled_decode",
            "question": ("On the SIDE-BY-SIDE: does either half sit stiller? "
                         "On the SOLO pairs: is the restless one objectionable, "
                         "or only different?"),
            "note": ("ours = tiled = what ships today. candidate = untiled = "
                     "the proposed change. Do not read this file before calling "
                     "it."),
            "cells": key,
            "expected_effect": {
                "testcard": "large -- 4.3x and 4.9x more churn in the TILED arm",
                "crowd": "small -- 1.2-1.4x; may be invisible",
            },
        }, indent=2, sort_keys=True) + "\n")
    print(f"\nclips + KEY.json -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
