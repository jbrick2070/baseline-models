"""Build the blinded judge sets for one fixture/seed: matched frames and crops.

Three seats per comparison, and none of them can see which arm is which:

  seat1  full frames, labelled A/B
  seat2  the SAME frames, relabelled X/Y
  seat3  native-pixel crops only, labelled P/Q

WITH TWO ARMS THERE ARE ONLY TWO READ ORDERS, so three seats can never each
have their own. An earlier version of this file claimed they did and hard-coded
a single map in which seat2 and seat3 both read official first -- two position
conditions wearing three seats, with every fixture and seed sharing the same
map. A refutation pass caught it. The honest design is stated here instead:
the 2-1 split is unavoidable, so what varies is WHICH seat draws the minority
order and WHICH arm reads first, derived per (fixture, seed) from a digest.
That is deterministic and reproducible, but no longer aligned with seat
identity across cells, so a position-leaning seat cannot agree with itself
cell after cell and look like corroboration.

The arm behind every label lives in KEY.json, which is the driver's file and is
never handed to a seat.

Crops are cut, never resampled: a judge asked "which eye-chart row still reads"
must be looking at the model's own pixels, not at an interpolation of them.
Crop regions are per fixture, aimed at whatever that fixture makes countable.

usage: make_judge_set.py <lane_dir> <fixture> <seed> <judge_out_root>
"""
from __future__ import annotations

import hashlib
import io
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

COMFY_OUTPUT = Path(r"C:\Users\jeffr\Documents\ComfyUI\output")
FRAMES = [1, 49, 97]
CROP_FRAMES = [49, 97]

# Per fixture, the regions that carry this fixture's countable evidence.
REGIONS = {
    "officer": [("face", 216, 16, 320, 320), ("uniform", 60, 340, 256, 128)],
    "controlroom": [("dials", 512, 176, 320, 160), ("figure", 320, 140, 208, 232)],
    "crowd": [("meter", 330, 404, 260, 76), ("faces", 500, 60, 224, 168)],
    "testcard": [("eye_light", 8, 258, 400, 160), ("eye_dark", 424, 258, 400, 160),
                 ("gratings_light", 8, 208, 400, 46),
                 ("gratings_dark", 424, 208, 400, 46)],
}
SEAT_LABELS = {
    "seat1_full": ("A", "B"),
    "seat2_full": ("X", "Y"),
    "seat3_crops": ("P", "Q"),
}


def seat_plan(fixture: str, seed: int) -> dict:
    """Assign each seat a read order, varied per cell rather than fixed.

    Two arms admit only two orders, so one order is always used twice. The
    digest decides which seat is the odd one out and which arm leads, so the
    repeat does not land on the same seats in every cell.
    """
    digest = hashlib.sha256(("%s|%d" % (fixture, seed)).encode("utf-8")).digest()
    odd_seat = digest[0] % 3
    ours_leads = bool(digest[1] & 1)
    plan = {}
    for index, (seat, (first, second)) in enumerate(sorted(SEAT_LABELS.items())):
        leads = not ours_leads if index == odd_seat else ours_leads
        ours_label, official_label = (first, second) if leads else (second, first)
        plan[seat] = {"ours": ours_label, "official": official_label,
                      "order": [first, second],
                      "reads_first": "ours" if leads else "official"}
    return plan


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 4:
        print(__doc__)
        return 2
    lane_dir, fixture, seed, out_root = Path(argv[0]), argv[1], int(argv[2]), Path(argv[3])

    lane = json.loads(io.open(lane_dir / "LANE.json", encoding="utf-8").read())
    if fixture not in lane["fixtures"]:
        print("[FAIL] unknown fixture %r" % fixture)
        return 1
    subdir = lane["fixtures"][fixture]["output_subdir"]
    base = COMFY_OUTPUT / "baseline_output" / "lane1_wan_ti2v"
    if subdir:
        base = base / subdir

    out_dir = out_root / fixture / ("seed%d" % seed)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    legs = {"ours": "ours_seed%d" % seed, "official": "official_seed%d" % seed}
    for arm, leg in legs.items():
        for index in sorted(set(FRAMES + CROP_FRAMES)):
            path = base / leg / ("frame_%05d_.png" % index)
            if not path.exists():
                print("[FAIL] missing %s" % path)
                return 1

    regions = REGIONS[fixture]
    key = {"fixture": fixture, "seed": seed, "legs": legs, "seats": {}, "files": {}}
    manifest = {"fixture": fixture, "seed": seed, "seats": {}}

    for seat, spec in seat_plan(fixture, seed).items():
        seat_dir = out_dir / seat
        seat_dir.mkdir()
        shown = []
        crops_only = seat.startswith("seat3")
        for arm, leg in legs.items():
            label = spec[arm]
            if crops_only:
                for index in CROP_FRAMES:
                    with Image.open(base / leg / ("frame_%05d_.png" % index)) as image:
                        for name, left, top, width, height in regions:
                            box = (left, top, left + width, top + height)
                            if box[2] > image.width or box[3] > image.height:
                                print("[FAIL] crop %s exceeds canvas %s"
                                      % (name, image.size))
                                return 1
                            filename = "%s_f%03d_%s.png" % (label, index, name)
                            image.crop(box).save(seat_dir / filename)
                            shown.append(filename)
                            key["files"][filename] = {
                                "arm": arm, "leg": leg, "frame": index,
                                "region": name, "box": list(box)}
            else:
                for index in FRAMES:
                    filename = "%s_f%03d.png" % (label, index)
                    shutil.copyfile(base / leg / ("frame_%05d_.png" % index),
                                    seat_dir / filename)
                    shown.append(filename)
                    key["files"][filename] = {"arm": arm, "leg": leg, "frame": index}
        key["seats"][seat] = {"ours": spec["ours"], "official": spec["official"],
                              "reads_first": spec["reads_first"]}
        manifest["seats"][seat] = {
            "dir": str(seat_dir), "read_order": spec["order"],
            "files": sorted(shown),
            "kind": "native-pixel crops" if crops_only else "full matched frames",
        }
        print("[SEAT] %-22s %-12s %2d image(s)  order=%s"
              % (seat, fixture, len(shown), "->".join(spec["order"])))

    io.open(out_dir / "KEY.json", "w", encoding="utf-8", newline="\n").write(
        json.dumps(key, indent=2, sort_keys=True) + "\n")
    io.open(out_dir / "MANIFEST.json", "w", encoding="utf-8", newline="\n").write(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print("[JUDGE SET] %s" % out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
