"""Stage this lane's conditioning stills into ComfyUI/input and hash them.

The lane owns copies under its own names so nothing upstream can change the
inputs under a rendered arm; every digest recorded here is what the renders are
citable against.

The control-room still ships with 45/47 rows of letterbox. Those bars are not
free: they would occupy roughly a ninth of an already small 832x480 canvas with
flat black, which is a ninth less surface on which a sampler difference could
show. They are cut once, here, and the result is trimmed to the render aspect
so the node's own centre crop has almost nothing left to remove. Both arms
consume the identical prepared file.
"""
from __future__ import annotations

import hashlib
import io
import json
import shutil
from pathlib import Path

from PIL import Image

INPUT = Path(r"C:\Users\jeffr\Documents\ComfyUI\input")
HERE = Path(__file__).resolve().parent
CANVAS_W, CANVAS_H = 832, 480
TARGET_ASPECT = CANVAS_W / CANVAS_H


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_fixture(source: Path, name: str) -> Path:
    destination = INPUT / name
    shutil.copyfile(source, destination)
    return destination


def debar_and_fit(source: Path, name: str, top: int, bottom: int) -> Path:
    """Cut the letterbox, then trim to the render aspect about the centre."""
    with Image.open(source) as image:
        width, height = image.size
        cropped = image.crop((0, top, width, height - bottom))
        new_width, new_height = cropped.size
        fitted_width = int(round(new_height * TARGET_ASPECT))
        if fitted_width > new_width:
            fitted_height = int(round(new_width / TARGET_ASPECT))
            offset = (new_height - fitted_height) // 2
            cropped = cropped.crop((0, offset, new_width, offset + fitted_height))
        else:
            offset = (new_width - fitted_width) // 2
            cropped = cropped.crop((offset, 0, offset + fitted_width, new_height))
        destination = INPUT / name
        cropped.save(destination)
        print("   %s -> %s  %s -> %s" % (source.name, name, (width, height), cropped.size))
    return destination


def main() -> int:
    records = {}

    officer = INPUT / "portrait_16_9.png"
    if not officer.exists():
        print("[FAIL] officer fixture missing at %s" % officer)
        return 1
    records["officer"] = {
        "image": officer.name,
        "sha256": sha256(officer),
        "note": "already rendered in pass 1; left exactly as staged",
    }

    control = debar_and_fit(
        INPUT / "otr_wan_init_shot_b005_s1794688454_1472x832.png",
        "lane1_controlroom.png", top=45, bottom=47)
    records["controlroom"] = {
        "image": control.name,
        "sha256": sha256(control),
        "source": "otr_wan_init_shot_b005_s1794688454_1472x832.png",
        "note": "letterbox cut (45/47 rows), trimmed to the 832x480 aspect",
    }

    crowd = copy_fixture(INPUT / "still_b013_58fcc78202cf.png", "lane1_crowd.png")
    records["crowd"] = {
        "image": crowd.name,
        "sha256": sha256(crowd),
        "source": "still_b013_58fcc78202cf.png",
        "note": "1920x1080, no letterbox; copied unmodified",
    }

    io.open(HERE / "FIXTURES.json", "w", encoding="utf-8", newline="\n").write(
        json.dumps(records, indent=2, sort_keys=True) + "\n")
    for key in sorted(records):
        print("[FIXTURE] %-12s %-28s %s"
              % (key, records[key]["image"], records[key]["sha256"][:16]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
