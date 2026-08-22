"""Arm-to-arm correlation, and drift from the conditioning still.

Lane 1 made this BINDING -- "admit a cell only if the arms still render the same
scene; arm-to-arm NCC at the final frame under ~0.90 means 'which is better' is
the wrong question" -- and then no lane ever computed it in the harness. Lane 3
declared it a flag and skipped it; its completeness critic had to compute the
numbers out-of-band afterwards (0.14-0.74, every cell under the line, which is
why that lane's 9-8 panel split carries no signal). This makes it a receipt.

TWO MEASUREMENTS, because on an image-conditioned lane they answer different
questions:

* ``arm_ncc`` -- ours vs official at the same frame. On an i2v lane the arms
  share a conditioning still, so they SHOULD track each other; a low value here
  is a real admission failure, not the legitimate scene divergence a t2v lane
  produces from one seed.
* ``still_ncc`` -- each arm against its own conditioning still. This is the half
  a t2v lane cannot have, and it separates "the arms disagree" from "both arms
  walked away from the input". Two arms can correlate perfectly with each other
  while both abandon the still.

usage: ncc_stats.py <lane_dir> [frame ...]
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

COMFY_OUTPUT = Path(r"C:\Users\jeffr\Documents\ComfyUI\output")
INPUT_DIR = Path(r"C:\Users\jeffr\Documents\ComfyUI\input")
SEEDS = [42, 20260821]
DEFAULT_FRAMES = [1, 49, 97]
ADMISSION_FLOOR = 0.90


def gray(path: Path, size=None) -> np.ndarray:
    image = Image.open(path).convert("L")
    if size and image.size != size:
        image = image.resize(size, Image.LANCZOS)
    return np.asarray(image, dtype=np.float64)


def ncc(a: np.ndarray, b: np.ndarray) -> float:
    a = a - a.mean()
    b = b - b.mean()
    denominator = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / denominator) if denominator else float("nan")


def main(argv) -> int:
    if not argv:
        print(__doc__)
        return 2
    lane_dir = Path(argv[0])
    frames = [int(x) for x in argv[1:]] or DEFAULT_FRAMES
    lane = json.loads(io.open(lane_dir / "LANE.json", encoding="utf-8").read())
    base = COMFY_OUTPUT / "baseline_output" / lane["lane"]

    report = {"lane": lane["lane"], "admission_floor": ADMISSION_FLOOR,
              "frames": frames, "cells": {}}
    print("%-30s %6s %9s %10s %10s" % ("cell", "frame", "arm_ncc", "still_ours", "still_cand"))

    for fixture in sorted(lane["fixtures"]):
        arms = sorted(lane["arm_sha256"][fixture])
        candidate = next(a for a in arms if a != "ours")
        subdir = lane["fixtures"][fixture].get("output_subdir") or ""
        root = base / subdir if subdir else base

        still = None
        staging_path = lane_dir / fixture / "STAGING.json"
        if staging_path.is_file():
            staging = json.loads(io.open(staging_path, encoding="utf-8").read())
            candidate_still = INPUT_DIR / str(staging.get("image") or "")
            if candidate_still.is_file():
                still = candidate_still

        for seed in SEEDS:
            dirs = {a: root / ("%s_seed%d" % (a, seed)) for a in (("ours", candidate))}
            if not all(d.is_dir() for d in dirs.values()):
                continue
            cell = "%s/seed%d" % (fixture, seed)
            rows = []
            for frame in frames:
                name = "frame_%05d_.png" % frame
                ours = gray(dirs["ours"] / name)
                cand = gray(dirs[candidate] / name)
                size = (ours.shape[1], ours.shape[0])
                row = {"frame": frame, "arm_ncc": round(ncc(ours, cand), 4)}
                if still is not None:
                    reference = gray(still, size=size)
                    row["still_ncc_ours"] = round(ncc(ours, reference), 4)
                    row["still_ncc_candidate"] = round(ncc(cand, reference), 4)
                rows.append(row)
                print("%-30s %6d %9.4f %10s %10s"
                      % (cell, frame, row["arm_ncc"],
                         ("%.4f" % row["still_ncc_ours"]) if still is not None else "-",
                         ("%.4f" % row["still_ncc_candidate"]) if still is not None else "-"))
            final = rows[-1]["arm_ncc"]
            report["cells"][cell] = {
                "rows": rows,
                "final_frame_arm_ncc": final,
                "admitted": bool(final >= ADMISSION_FLOOR),
                "conditioning_still": still.name if still is not None else None,
            }

    admitted = [c for c, v in report["cells"].items() if v["admitted"]]
    rejected = [c for c, v in report["cells"].items() if not v["admitted"]]
    report["admitted_cells"] = sorted(admitted)
    report["rejected_cells"] = sorted(rejected)
    out = lane_dir / "NCC.json"
    io.open(out, "w", encoding="utf-8", newline="\n").write(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n")

    print("\n[ADMISSION] %d of %d cells at or above %.2f"
          % (len(admitted), len(report["cells"]), ADMISSION_FLOOR))
    if rejected:
        print("[REJECTED]  %s" % ", ".join(sorted(rejected)))
        print("            'which is better' is the wrong question in these cells.")
    print("[RECEIPT]   %s" % out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
