"""Build ONE reel of every A/B pair in the programme, for the operator's eye.

The voted method's final judge seat is the operator's eye, and across four lanes
it has never been used. The blocker was never willingness -- it was friction:
twenty-odd mp4s in four directories, cryptic names, and a key file to cross-
reference. This collapses that into a single ~90-second video he can watch once.

TWO RULES THIS SCRIPT EXISTS TO ENFORCE:

1. IT STAYS BLIND. The pair clips already burn in LEFT / RIGHT and alternate
   which arm leads (``make_clips.left_arm_for``). This reel adds ONLY the lane,
   the fixture, the seed, and a NEUTRAL thing to count. It never names an arm
   and never states a prior finding -- a label that says "official drifted here"
   turns an independent read into a confirmation exercise, which is worth
   nothing as evidence.
2. IT ASKS FOR COUNTS, NOT TASTE. Same discipline as the blind panels: which
   features resolve, how many survive, does it hold still. Never "which is
   prettier" -- the arms can differ in content, and aesthetics flips on wardrobe
   (Bible 12.121 territory).

The answer key stays in each lane's own CLIPS.json, unchanged. Read it AFTER.

usage: make_operator_reel.py [out_dir]
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

COMFY_OUTPUT = Path(r"C:\Users\jeffr\Documents\ComfyUI\output")
BASE = COMFY_OUTPUT / "baseline_output"
DEFAULT_OUT = BASE / "_OPERATOR_EYE"
WIDTH, HEIGHT = 1920, 1080

# Neutral, countable prompts. NOTHING here reveals an arm or a prior result.
WHAT_TO_COUNT = {
    ("lane1_wan_ti2v", "testcard"): "how far down do the letter rows stay readable? is the grey strip neutral or tinted?",
    ("lane1_wan_ti2v", "crowd"): "how many faces stay intact? are the meter ticks separate lines?",
    ("lane1_wan_ti2v", "officer"): "does he stay the same man, start to end?",
    ("lane1_wan_ti2v", "controlroom"): "how far back can you still count separate dials?",
    ("lane2_ltx25", "officer"): "same man at the end as at the start?",
    ("lane2_ltx25", "crowd"): "how many faces hold together? does the framing wander?",
    ("lane2_ltx25", "testcard"): "does the card stay square and still?",
    ("lane3_ltx_video", "march"): "count the band members and their instruments. does the drum have someone carrying it?",
    ("lane3_ltx_video", "portrait"): "watch his face at the end. anything melt or change?",
    ("lane3_ltx_video", "radio"): "count the glass tubes. are the dial ticks separate?",
    ("lane4_wan_text_encoder", "crowd"): "does the camera hold still, or does the shot slide?",
    ("lane4_wan_text_encoder", "testcard_motion"): "does anything move at all?",
}
LANE_ORDER = ["lane1_wan_ti2v", "lane2_ltx25", "lane3_ltx_video",
              "lane4_wan_text_encoder"]


def run(args) -> bool:
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        tail = (result.stderr or "").strip().splitlines()[-2:]
        print("[FFMPEG FAIL] %s" % tail)
    return result.returncode == 0


def escape(text: str) -> str:
    """drawtext is filter-graph syntax: colons and quotes must not leak."""
    return (text.replace("\\", "\\\\").replace(":", "\\:")
            .replace("'", "").replace(",", "\\,").replace("[", "").replace("]", ""))


def normalize(source: Path, destination: Path, top: str, bottom: str) -> bool:
    """Letterbox to a common canvas and burn two neutral caption lines."""
    chain = (
        "scale=%d:%d:force_original_aspect_ratio=decrease,"
        "pad=%d:%d:(ow-iw)/2:(oh-ih)/2:color=black,"
        "drawtext=text='%s':x=(w-tw)/2:y=24:fontsize=40:fontcolor=white:"
        "box=1:boxcolor=black@0.75:boxborderw=12,"
        "drawtext=text='%s':x=(w-tw)/2:y=h-84:fontsize=32:fontcolor=yellow:"
        "box=1:boxcolor=black@0.75:boxborderw=12"
        % (WIDTH, HEIGHT, WIDTH, HEIGHT, escape(top), escape(bottom))
    )
    return run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(source),
                "-vf", chain, "-r", "25", "-c:v", "libx264", "-crf", "18",
                "-preset", "medium", "-pix_fmt", "yuv420p", str(destination)])


def main(argv) -> int:
    out_dir = Path(argv[0]) if argv else DEFAULT_OUT
    parts_dir = out_dir / "_parts"
    parts_dir.mkdir(parents=True, exist_ok=True)

    segments, missing = [], []
    for lane in LANE_ORDER:
        clips_json = BASE / lane / "_clips" / "CLIPS.json"
        if not clips_json.is_file():
            missing.append(lane)
            continue
        record = json.loads(io.open(clips_json, encoding="utf-8").read())
        for name in sorted(record.get("pairs", [])):
            source = BASE / lane / "_clips" / name
            if not source.is_file():
                continue
            stem = name[len("PAIR_"):-len(".mp4")]
            fixture, _, seed = stem.rpartition("_seed")
            hint = WHAT_TO_COUNT.get((lane, fixture), "what differs between them?")
            top = "%s   %s   seed %s" % (lane.split("_", 1)[0].upper(), fixture, seed)
            part = parts_dir / ("%02d_%s_%s.mp4" % (len(segments) + 1, lane, stem))
            if normalize(source, part, top, hint):
                segments.append(part)
                print("[SEGMENT] %2d  %-24s %s" % (len(segments), lane, stem))

    if not segments:
        print("[FAIL] no pair clips found under %s" % BASE)
        return 1

    listing = parts_dir / "concat.txt"
    io.open(listing, "w", encoding="utf-8", newline="\n").write(
        "".join("file '%s'\n" % p.as_posix() for p in segments))
    reel = out_dir / "OPERATOR_EYE_REEL.mp4"
    if not run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                "-i", str(listing), "-c", "copy", str(reel)]):
        return 1

    io.open(out_dir / "HOW_TO_WATCH.md", "w", encoding="utf-8", newline="\n").write(
        "# The reel -- about 90 seconds, watch it once\n\n"
        "Every A/B this programme rendered, side by side, one file:\n"
        "`OPERATOR_EYE_REEL.mp4`\n\n"
        "**It is blind on purpose.** LEFT and RIGHT swap between fixtures, and\n"
        "nothing on screen tells you which side is the shipped recipe. The\n"
        "yellow line is what to COUNT -- not what to prefer. The arms can differ\n"
        "in content and in wardrobe, so 'which is prettier' is the wrong\n"
        "question and would not survive as evidence.\n\n"
        "If a pair looks the same to you, that IS the answer. Three lanes have\n"
        "closed on exactly that and it is the most common honest result.\n\n"
        "## After you watch\n\n"
        "Say for each one: LEFT, RIGHT, or SAME. Rough is fine -- the ones you\n"
        "skip are recorded as skipped, not as ties.\n\n"
        "## The key\n\n"
        "Which side was which lives in each lane's own\n"
        "`baseline_output/<lane>/_clips/CLIPS.json`, under\n"
        "`left_right_mapping`. Read it AFTER, or ask and it is one line.\n\n"
        "%d segments, %d lanes.%s\n"
        % (len(segments), len(LANE_ORDER) - len(missing),
           ("  Not yet rendered: %s." % ", ".join(missing)) if missing else ""))

    print("\n[REEL] %s" % reel)
    print("[SEGMENTS] %d" % len(segments))
    if missing:
        print("[MISSING] no clips yet for: %s" % ", ".join(missing))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
