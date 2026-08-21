"""Per-leg temporal stability: mean and max |frame(t) - frame(t-1)| luminance.

Lane 1 closed having never measured the axis a sampling recipe moves most --
the clips existed, nobody cited them, and when the completeness critic finally
measured it the official arm was worse in 7 of 8 cells. This makes the number a
standard receipt field so no future lane can skip it: one numpy pass over
frames already on disk, no re-render.

Import surface: ``leg_stats(frames_dir)`` returns the dict render harnesses
embed per leg. CLI surface: point it at RENDER.json files to backfill legs that
predate the field.

usage: temporal_stats.py <RENDER.json> [...]
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

COMFY_OUTPUT = Path(r"C:\Users\jeffr\Documents\ComfyUI\output")


def leg_stats(frames_dir: Path) -> dict:
    """Mean/max absolute frame-to-frame luminance delta over every frame pair."""
    frames = sorted(frames_dir.glob("frame_*_.png"))
    if len(frames) < 2:
        return {"error": "fewer than 2 frames in %s" % frames_dir}
    previous = None
    deltas = []
    for path in frames:
        current = np.asarray(Image.open(path).convert("L"), dtype=np.float32)
        if previous is not None:
            deltas.append(float(np.abs(current - previous).mean()))
        previous = current
    return {
        "frame_pairs": len(deltas),
        "mean_abs_delta": round(float(np.mean(deltas)), 4),
        "max_abs_delta": round(float(np.max(deltas)), 4),
        "argmax_pair": int(np.argmax(deltas)) + 1,
    }


def backfill(render_json: Path) -> int:
    doc = json.loads(io.open(render_json, encoding="utf-8").read())
    changed = 0
    for leg in doc.get("legs", []):
        if leg.get("status") != "success" or "temporal" in leg:
            continue
        subfolder = leg.get("subfolder")
        if not subfolder:
            continue
        frames_dir = COMFY_OUTPUT / subfolder
        if not frames_dir.is_dir():
            print("[SKIP] %s: no dir %s" % (leg["leg"], frames_dir))
            continue
        leg["temporal"] = leg_stats(frames_dir)
        changed += 1
        print("[TEMPORAL] %-34s mean=%.3f max=%.3f (pair %d)"
              % (leg["leg"], leg["temporal"]["mean_abs_delta"],
                 leg["temporal"]["max_abs_delta"], leg["temporal"]["argmax_pair"]))
    if changed:
        io.open(render_json, "w", encoding="utf-8", newline="\n").write(
            json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        print("[WROTE] %s (%d leg(s))" % (render_json, changed))
    return changed


def main(argv) -> int:
    if not argv:
        print(__doc__)
        return 2
    total = 0
    for arg in argv:
        total += backfill(Path(arg).resolve())
    print("[DONE] %d leg(s) backfilled" % total)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
