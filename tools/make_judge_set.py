"""Build the blinded judge sets for one A/B: matched frames and native crops.

Three seats per comparison, and none of them can see which arm is which:

  seat1  full frames, labelled A/B, read A then B
  seat2  the SAME frames, relabelled and permuted, read X then Y
  seat3  native-pixel crops only, labelled P/Q

Each seat gets its own independent label permutation, so a seat that leans on
label position rather than on pixels disagrees with the others instead of
quietly agreeing with them. The arm behind every label lives in KEY.json, which
is the driver's file and is never handed to a seat.

Crops are cut, never resampled: a judge asked "how many pins resolve" must be
looking at the model's own pixels, not at an interpolation of them.
"""
from __future__ import annotations

import io
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

FRAMES = [1, 49, 97]
CROP_FRAMES = [49, 97]
# (name, left, top, width, height) on the 832x480 render canvas.
CROP_REGIONS = [
    ("face", 216, 16, 320, 320),
    ("uniform", 60, 340, 256, 128),
]
# seat -> (label for arm ours, label for arm official, read order)
SEATS = {
    "seat1_full_A_then_B": {"ours": "A", "official": "B", "order": ["A", "B"]},
    "seat2_full_X_then_Y": {"ours": "Y", "official": "X", "order": ["X", "Y"]},
    "seat3_crops_P_then_Q": {"ours": "Q", "official": "P", "order": ["P", "Q"]},
}


def frame_path(base: Path, leg: str, index: int) -> Path:
    return base / leg / ("frame_%05d_.png" % index)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 3:
        print(__doc__)
        print("usage: make_judge_set.py <render_output_base> <seed> <judge_out_dir>")
        return 2
    base, seed, out_root = Path(argv[0]), int(argv[1]), Path(argv[2])
    out_dir = out_root / ("seed%d" % seed)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    legs = {"ours": "ours_seed%d" % seed, "official": "official_seed%d" % seed}
    for arm, leg in legs.items():
        missing = [i for i in set(FRAMES + CROP_FRAMES) if not frame_path(base, leg, i).exists()]
        if missing:
            print("[FAIL] %s is missing frame(s) %s" % (leg, sorted(missing)))
            return 1

    key = {"seed": seed, "legs": legs, "seats": {}, "files": {}}
    manifest = {"seed": seed, "seats": {}}

    for seat, spec in SEATS.items():
        seat_dir = out_dir / seat
        seat_dir.mkdir()
        shown = []
        crops_only = seat.startswith("seat3")
        for arm, leg in legs.items():
            label = spec[arm]
            if crops_only:
                for index in CROP_FRAMES:
                    with Image.open(frame_path(base, leg, index)) as image:
                        for name, left, top, width, height in CROP_REGIONS:
                            box = (left, top, left + width, top + height)
                            if box[2] > image.width or box[3] > image.height:
                                print("[FAIL] crop %s exceeds canvas %s" % (name, image.size))
                                return 1
                            crop = image.crop(box)
                            filename = "%s_f%03d_%s.png" % (label, index, name)
                            crop.save(seat_dir / filename)
                            shown.append(filename)
                            key["files"][filename] = {"arm": arm, "leg": leg,
                                                      "frame": index, "region": name,
                                                      "box": list(box)}
            else:
                for index in FRAMES:
                    filename = "%s_f%03d.png" % (label, index)
                    shutil.copyfile(frame_path(base, leg, index), seat_dir / filename)
                    shown.append(filename)
                    key["files"][filename] = {"arm": arm, "leg": leg, "frame": index}
        key["seats"][seat] = {"ours": spec["ours"], "official": spec["official"]}
        manifest["seats"][seat] = {
            "dir": str(seat_dir),
            "read_order": spec["order"],
            "files": sorted(shown),
            "kind": "native-pixel crops" if crops_only else "full matched frames",
        }
        print("[SEAT] %-22s %2d image(s)  order=%s"
              % (seat, len(shown), "->".join(spec["order"])))

    io.open(out_dir / "KEY.json", "w", encoding="utf-8", newline="\n").write(
        json.dumps(key, indent=2, sort_keys=True) + "\n")
    io.open(out_dir / "MANIFEST.json", "w", encoding="utf-8", newline="\n").write(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print("[JUDGE SET] %s" % out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
