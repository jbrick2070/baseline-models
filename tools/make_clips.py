"""Encode each rendered leg to an mp4, and one side-by-side pair per fixture.

The judging is done on the PNG frames, which are lossless. These clips exist so
a human can watch the result move -- a still cannot show temporal flicker, and
flicker is the thing a sampling recipe is most likely to change on a video lane.

The paired clips are labelled LEFT and RIGHT rather than by arm, so the eye
gets a look before the label does. The mapping is written to CLIPS.json.
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

COMFY_OUTPUT = Path(r"C:\Users\jeffr\Documents\ComfyUI\output")
FPS = 25


def lane_base(lane) -> Path:
    """Output root for THIS lane, not lane 1's.

    The old module-level BASE pinned every lane's clips at lane1_wan_ti2v, and
    the LEFT_ARM table only named lane 1's fixtures -- so any other lane either
    wrote to the wrong tree or died on KeyError.
    """
    return COMFY_OUTPUT / "baseline_output" / lane["lane"]


def arms_for(lane, fixture):
    """(ours, candidate) -- the candidate is whatever the lane called its arm."""
    arms = sorted(lane["arm_sha256"][fixture])
    if "ours" not in arms or len(arms) != 2:
        raise SystemExit("[FAIL] %s: expected 'ours' plus one candidate, got %s"
                         % (fixture, arms))
    return "ours", next(a for a in arms if a != "ours")


def left_arm_for(lane, fixture) -> str:
    """Alternate LEFT/RIGHT across fixtures so a viewer cannot settle into
    'the left one is always ours'. Deterministic from the sorted fixture order,
    so the mapping is reproducible and is written into CLIPS.json as the key."""
    ours, candidate = arms_for(lane, fixture)
    index = sorted(lane["fixtures"]).index(fixture)
    return ours if index % 2 == 0 else candidate


def run(args):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        print("[FFMPEG FAIL] %s" % result.stderr.strip().splitlines()[-1:])
    return result.returncode == 0


def encode_leg(frames_dir: Path, destination: Path) -> bool:
    return run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
                "-i", str(frames_dir / "frame_%05d_.png"),
                "-c:v", "libx264", "-crf", "16", "-preset", "medium",
                "-pix_fmt", "yuv420p", str(destination)])


def encode_pair(left: Path, right: Path, destination: Path) -> bool:
    label = ("[0:v]drawtext=text='LEFT':x=12:y=12:fontsize=22:fontcolor=white:"
             "box=1:boxcolor=black@0.6:boxborderw=6[l];"
             "[1:v]drawtext=text='RIGHT':x=12:y=12:fontsize=22:fontcolor=white:"
             "box=1:boxcolor=black@0.6:boxborderw=6[r];[l][r]hstack=inputs=2")
    return run(["ffmpeg", "-y", "-loglevel", "error",
                "-framerate", str(FPS), "-i", str(left / "frame_%05d_.png"),
                "-framerate", str(FPS), "-i", str(right / "frame_%05d_.png"),
                "-filter_complex", label,
                "-c:v", "libx264", "-crf", "16", "-preset", "medium",
                "-pix_fmt", "yuv420p", str(destination)])


def main(argv) -> int:
    lane_dir = Path(argv[0]) if argv else None
    lane = json.loads(io.open(lane_dir / "LANE.json", encoding="utf-8").read())
    seeds = [42, 20260821]
    base_root = lane_base(lane)
    clips_dir = base_root / "_clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    record = {"fps": FPS, "lane": lane["lane"],
              "left_right_mapping": {}, "singles": [], "pairs": []}
    for fixture in sorted(lane["fixtures"]):
        subdir = lane["fixtures"][fixture]["output_subdir"]
        base = base_root / subdir if subdir else base_root
        ours, candidate = arms_for(lane, fixture)
        left_arm = left_arm_for(lane, fixture)
        right_arm = candidate if left_arm == ours else ours
        record["left_right_mapping"][fixture] = {"LEFT": left_arm, "RIGHT": right_arm}
        for seed in seeds:
            dirs = {arm: base / ("%s_seed%d" % (arm, seed))
                    for arm in (ours, candidate)}
            if not all(d.exists() for d in dirs.values()):
                print("[SKIP] %s seed%d: frames missing" % (fixture, seed))
                continue
            for arm, frames in dirs.items():
                single = clips_dir / ("%s_%s_seed%d.mp4" % (fixture, arm, seed))
                if encode_leg(frames, single):
                    record["singles"].append(single.name)
            pair = clips_dir / ("PAIR_%s_seed%d.mp4" % (fixture, seed))
            if encode_pair(dirs[left_arm], dirs[right_arm], pair):
                record["pairs"].append(pair.name)
                print("[PAIR] %-12s seed%-9d LEFT=%-8s RIGHT=%s"
                      % (fixture, seed, left_arm, right_arm))

    io.open(clips_dir / "CLIPS.json", "w", encoding="utf-8", newline="\n").write(
        json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("[CLIPS] %d single(s), %d pair(s) -> %s"
          % (len(record["singles"]), len(record["pairs"]), clips_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
