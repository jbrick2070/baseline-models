"""Lane 7 analysis -- the MOTION gate first, then the anchor question.

THE GATE COMES FIRST AND IT CAN END THE LANE. Lane 4 proved a prompt demanding
movement does not produce it: its `testcard_motion` fixture returned 0.0 px
translation in both arms at both seeds. So before any arm is compared to any
other, each clip has to prove it actually moved. If it did not, the fixture
failed and the correct verdict is "the fixture failed", not "soft ties on
motion" -- which would be lane 2's bound restated, not closed.

The gate uses two numbers per clip, neither of which needs a judge:

  excursion   mean |f097 - f001|. How far the clip travelled overall.
  churn       mean consecutive-frame difference. How much it moved per frame.

A clip that demands traversal and returns lane-2-like stillness numbers has not
tested the motion axis. Lane 2's stillness-prompted fixtures are the reference:
its prompts asked for "only subtle breathing and a slight head movement".

THEN THE ANCHOR QUESTION, which is the mechanism this lane exists to expose.
The anchor binds each clip to its conditioning still. A SOFT anchor should let
the clip depart further from that still -- invisible on a fixture that demands
stillness, which is exactly why lane 2's null is bounded. So the decisive
per-arm number is NCC against the conditioning still at the final frame
(lane 5's instrument): if soft does not depart further under a motion demand,
the anchor is not doing what the lane assumed and a null means something
different.
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
            "lane7_ltx25_motion")
SEEDS = (42, 20260821)
ARMS = ("ours", "soft")
#: Declared BEFORE reading any number. Below this excursion a clip has not
#: meaningfully traversed and the cell fails the motion gate. Calibrated on
#: lane 6's crowd fixture, which moved without being asked to and scored ~9-12.
MOTION_MIN_EXCURSION = 6.0
#: Arm-to-arm admission, the lane 1 / lane 5 line.
ADMISSION_NCC = 0.90


def frame(cell: Path, n: int):
    p = cell / f"frame_{n:05d}_.png"
    if not p.exists():
        return None
    return np.asarray(Image.open(p).convert("RGB")).astype(np.float64)


def ncc(a, b) -> float:
    a, b = a.ravel() - a.mean(), b.ravel() - b.mean()
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d else 0.0


def churn(cell: Path) -> float:
    fr = sorted(cell.glob("frame_*.png"))
    step = max(1, len(fr) // 24)
    prev, tot, n = None, 0.0, 0
    for p in fr[::step]:
        cur = np.asarray(Image.open(p).convert("RGB")).astype(np.float64)
        if prev is not None:
            tot += float(np.abs(cur - prev).mean())
            n += 1
        prev = cur
    return tot / n if n else float("nan")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    report = {"lane": "lane7_ltx25_motion",
              "motion_min_excursion": MOTION_MIN_EXCURSION,
              "admission_ncc": ADMISSION_NCC, "cells": {}}

    print("=== MOTION GATE (per clip) ===")
    print(f"{'clip':<34}{'excursion':>10}{'churn':>9}{'moved':>7}")
    gate = {}
    for fixture in sorted(p.name for p in ROOT.iterdir() if p.is_dir()):
        for seed in SEEDS:
            for arm in ARMS:
                cell = ROOT / f"{fixture}/{arm}_seed{seed}"
                if not cell.exists():
                    continue
                a, z = frame(cell, 1), frame(cell, 97)
                exc = float(np.abs(z - a).mean())
                ch = churn(cell)
                ok = exc >= MOTION_MIN_EXCURSION
                gate[f"{fixture}/{arm}/{seed}"] = {
                    "excursion": round(exc, 3), "churn": round(ch, 3),
                    "moved": bool(ok)}
                print(f"{fixture+'/'+arm+'/'+str(seed):<34}{exc:>10.3f}"
                      f"{ch:>9.3f}{'yes' if ok else 'NO':>7}")
    report["motion_gate"] = gate

    print("\n=== ANCHOR: departure from the conditioning still (f001) ===")
    print(f"{'cell':<26}{'ours f97 vs f1':>15}{'soft f97 vs f1':>15}"
          f"{'soft departs more':>19}")
    for fixture in sorted(p.name for p in ROOT.iterdir() if p.is_dir()):
        for seed in SEEDS:
            cells = {a: ROOT / f"{fixture}/{a}_seed{seed}" for a in ARMS}
            if not all(c.exists() for c in cells.values()):
                continue
            vals = {}
            for a in ARMS:
                f1, f97 = frame(cells[a], 1), frame(cells[a], 97)
                vals[a] = ncc(f1, f97)
            more = vals["soft"] < vals["ours"]
            key = f"{fixture}/seed{seed}"
            report["cells"].setdefault(key, {})["anchor_ncc_f1_f97"] = {
                a: round(vals[a], 4) for a in ARMS}
            report["cells"][key]["soft_departs_more"] = bool(more)
            print(f"{key:<26}{vals['ours']:>15.4f}{vals['soft']:>15.4f}"
                  f"{('YES' if more else 'no'):>19}")

    print("\n=== ARM-TO-ARM (admission) ===")
    print(f"{'cell':<26}{'f001':>9}{'f049':>9}{'f097':>9}{'admit f097':>12}")
    for fixture in sorted(p.name for p in ROOT.iterdir() if p.is_dir()):
        for seed in SEEDS:
            cells = {a: ROOT / f"{fixture}/{a}_seed{seed}" for a in ARMS}
            if not all(c.exists() for c in cells.values()):
                continue
            key = f"{fixture}/seed{seed}"
            row = {}
            for n in (1, 49, 97):
                o, s = frame(cells["ours"], n), frame(cells["soft"], n)
                row[str(n)] = round(ncc(o, s), 4) if o is not None else None
            adm = row["97"] is not None and row["97"] >= ADMISSION_NCC
            report["cells"][key]["arm_to_arm_ncc"] = row
            report["cells"][key]["admitted"] = bool(adm)
            print(f"{key:<26}{row['1']:>9.4f}{row['49']:>9.4f}"
                  f"{row['97']:>9.4f}{('yes' if adm else 'NO'):>12}")

    moved = sum(1 for v in gate.values() if v["moved"])
    report["summary"] = {
        "clips": len(gate), "clips_that_moved": moved,
        "cells": len(report["cells"]),
        "cells_admitted": sum(1 for c in report["cells"].values()
                              if c.get("admitted")),
        "cells_where_soft_departs_more": sum(
            1 for c in report["cells"].values() if c.get("soft_departs_more")),
    }
    io.open(HERE / "ANALYSIS.json", "w", encoding="utf-8", newline="\n").write(
        json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("\n=== SUMMARY ===")
    print(json.dumps(report["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
