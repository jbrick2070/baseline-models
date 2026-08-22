"""Lane 6 analysis: does tiled decode leave a seam the untiled arm does not?

Three instruments, all countable, all declared before the numbers were read.

1. ARM-TO-ARM NCC -- the admission gate. Below ~0.90 at the final frame the arms
   stopped rendering the same scene and "which is better" is the wrong question
   (lane 1 precedent, lane 5 gate). A DECODER swap should score very high: the
   latents are identical by construction and only the decode differs, so unlike
   lanes 1-5 this lane expects admissible cells.

2. THE TILE-LATTICE METRIC -- the specific defect this lane exists to find.
   A tiled decoder's failure mode is a seam on a predictable grid: 256px tiles
   with 64px overlap. So take the per-pixel difference between arms, collapse it
   to a per-COLUMN energy profile, and compare the energy ON the lattice
   (tile boundaries and their overlap edges) against everything else.

   The point of the ratio is that it is SPECIFIC. A large arm-to-arm difference
   spread evenly is ordinary decoder variance and says nothing about tiling; a
   difference concentrated on the 256px lattice is a seam. Ratio ~1.0 means no
   concentration. A real seam prints well above 1.0.

   The same profile is computed for ROWS, because the tiling is 2-D and a
   horizontal seam would hide in a column-only view.

3. WITHIN-ARM TEMPORAL MEAN -- reused from the shipped receipt field
   (tools/temporal_stats.py, wired into every lane since lane 1's tail). A
   decoder that stabilises or destabilises frame-to-frame motion would show here.

Usage: analyse.py            (every rendered cell)
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = Path("C:/Users/jeffr/Documents/ComfyUI/output/baseline_output/"
            "lane6_wan_tiled_decode")
SEEDS = (42, 20260821)
ARMS = ("ours", "candidate")
FRAMES = (1, 49, 97)
TILE = 256
OVERLAP = 64
#: Declared BEFORE reading any number: at or above this the cell is judged.
ADMISSION_NCC = 0.90
#: Declared BEFORE reading any number: a lattice concentration at or above this
#: is called a seam. 1.15 is deliberately generous to the candidate -- it only
#: has to beat "no concentration at all" by 15%.
SEAM_RATIO = 1.15


def load(cell: Path, n: int) -> np.ndarray | None:
    p = cell / f"frame_{n:05d}_.png"
    if not p.exists():
        return None
    return np.asarray(Image.open(p).convert("RGB")).astype(np.float64)


def ncc(a: np.ndarray, b: np.ndarray) -> float:
    a = a.ravel() - a.mean()
    b = b.ravel() - b.mean()
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d else 0.0


def lattice_mask(length: int) -> np.ndarray:
    """Columns (or rows) where a tile boundary can actually fall, +/-2px.

    CORRECTED: an earlier version stepped by TILE, which is not where tiles
    land. Overlapping tiles advance by the STRIDE -- ``TILE - OVERLAP`` -- so a
    256px tile with 64px overlap starts at 0, 192, 384, 576, ... and its
    trailing edge sits 256 later. Stepping by 256 marked columns no tile edge
    passes through and missed real ones (384 among them), which would have
    diluted the very signal this metric exists to find.

    Both the leading and trailing edge of every tile are marked, since either
    can print a discontinuity.
    """
    stride = TILE - OVERLAP
    m = np.zeros(length, dtype=bool)
    start = 0
    while start < length:
        for x in (start, start + TILE):
            if 0 <= x < length:
                m[max(0, x - 2):min(length, x + 3)] = True
        start += stride
    return m


def seam_ratio(diff2d: np.ndarray, axis: int) -> float:
    """Energy ON the tile lattice / energy off it, along one axis."""
    prof = diff2d.mean(axis=1 - axis)
    m = lattice_mask(prof.shape[0])
    on = prof[m].mean() if m.any() else 0.0
    off = prof[~m].mean() if (~m).any() else 0.0
    return float(on / off) if off else float("nan")


def temporal_mean(cell: Path) -> float:
    """Mean absolute frame-to-frame change across the clip (sampled)."""
    frames = sorted(cell.glob("frame_*.png"))
    if len(frames) < 3:
        return float("nan")
    step = max(1, len(frames) // 24)
    picked = frames[::step]
    prev, total, n = None, 0.0, 0
    for p in picked:
        cur = np.asarray(Image.open(p).convert("RGB")).astype(np.float64)
        if prev is not None:
            total += float(np.abs(cur - prev).mean())
            n += 1
        prev = cur
    return total / n if n else float("nan")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    report: dict = {"lane": "lane6_wan_tiled_decode",
                    "admission_ncc": ADMISSION_NCC,
                    "seam_ratio_threshold": SEAM_RATIO,
                    "tile": TILE, "overlap": OVERLAP, "cells": {}}

    fixtures = sorted(p.name for p in ROOT.iterdir() if p.is_dir())
    for fixture in fixtures:
        for seed in SEEDS:
            cells = {a: ROOT / fixture / f"{a}_seed{seed}" for a in ARMS}
            if not all(c.exists() for c in cells.values()):
                continue
            key = f"{fixture}/seed{seed}"
            entry: dict = {"frames": {}}
            print(f"\n=== {key} ===")
            print(f"{'frame':>6} {'NCC':>9} {'meanAbsDiff':>12} "
                  f"{'seamCol':>9} {'seamRow':>9} {'admit':>7}")
            for n in FRAMES:
                a, b = load(cells["ours"], n), load(cells["candidate"], n)
                if a is None or b is None:
                    continue
                diff = np.abs(a - b).mean(axis=2)
                r = {
                    "ncc": round(ncc(a, b), 6),
                    "mean_abs_diff": round(float(diff.mean()), 4),
                    "max_abs_diff": round(float(diff.max()), 2),
                    "seam_ratio_col": round(seam_ratio(diff, 0), 4),
                    "seam_ratio_row": round(seam_ratio(diff, 1), 4),
                }
                r["admitted"] = bool(r["ncc"] >= ADMISSION_NCC)
                r["seam_detected"] = bool(
                    max(r["seam_ratio_col"], r["seam_ratio_row"]) >= SEAM_RATIO)
                entry["frames"][str(n)] = r
                print(f"{n:>6} {r['ncc']:>9.4f} {r['mean_abs_diff']:>12.3f} "
                      f"{r['seam_ratio_col']:>9.3f} {r['seam_ratio_row']:>9.3f} "
                      f"{'yes' if r['admitted'] else 'NO':>7}")
            entry["temporal_mean"] = {
                a: round(temporal_mean(cells[a]), 4) for a in ARMS}
            print(f"  temporal mean  ours={entry['temporal_mean']['ours']}  "
                  f"candidate={entry['temporal_mean']['candidate']}")
            report["cells"][key] = entry

    admitted = [f for c in report["cells"].values()
                for f in c["frames"].values() if f["admitted"]]
    seams = [f for c in report["cells"].values()
             for f in c["frames"].values() if f["seam_detected"]]
    report["summary"] = {
        "cells": len(report["cells"]),
        "frames_scored": sum(len(c["frames"]) for c in report["cells"].values()),
        "frames_admitted": len(admitted),
        "frames_with_seam": len(seams),
        "max_mean_abs_diff": max((f["mean_abs_diff"] for c in
                                  report["cells"].values()
                                  for f in c["frames"].values()), default=None),
    }
    io.open(HERE / "ANALYSIS.json", "w", encoding="utf-8", newline="\n").write(
        json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("\n=== SUMMARY ===")
    print(json.dumps(report["summary"], indent=2))
    print(f"\nwrote {HERE / 'ANALYSIS.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
