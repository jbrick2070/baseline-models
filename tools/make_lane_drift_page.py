"""Show the still-drift finding as pictures instead of a table.

The lane 5 numbers say both arms start AS the conditioning still (NCC ~0.999 at
frame 1) and fall to 0.11-0.36 against it by frame 97. That is the whole
finding, and it is far more legible as a filmstrip than as a column of decimals:
the leftmost image is what the model was handed, and everything to its right is
what came back.

Deliberately NOT blind. The operator's blind pass is done and recorded; this
page exists to explain a measurement, so the arms are labelled.

usage: make_lane_drift_page.py <lane_dir> [out_html]
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

COMFY_OUTPUT = Path(r"C:\Users\jeffr\Documents\ComfyUI\output")
INPUT_DIR = Path(r"C:\Users\jeffr\Documents\ComfyUI\input")
FRAMES = [1, 49, 97]
SEEDS = [42, 20260821]

CSS = """
:root{--bg:#f6f5f2;--panel:#fffdfa;--ink:#1c1a17;--muted:#6b6560;--line:#e0dbd3;
  --accent:#8a6a2f;--warn:#a8452b;--ok:#4a6b45;--chip:#fdf6e3}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#16151a;--panel:#1e1d23;--ink:#ece9e4;--muted:#a09a92;--line:#33313a;
  --accent:#d7b168;--warn:#e0866a;--ok:#9ec295;--chip:#2a2620}}
:root[data-theme="dark"]{--bg:#16151a;--panel:#1e1d23;--ink:#ece9e4;
  --muted:#a09a92;--line:#33313a;--accent:#d7b168;--warn:#e0866a;--ok:#9ec295;--chip:#2a2620}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.55 ui-serif,Georgia,'Iowan Old Style',serif}
.wrap{max-width:1400px;margin:0 auto;padding:26px 20px 70px}
h1{font-size:1.6rem;margin:0 0 4px}
.sub{color:var(--muted);margin:0 0 20px;font-size:.95rem}
.lead{background:var(--chip);border:1px solid var(--line);border-left:3px solid var(--accent);
  padding:14px 16px;border-radius:6px;margin:0 0 26px;font-size:.95rem}
h2{font-size:1.05rem;margin:30px 0 4px;letter-spacing:.01em}
.cellnote{color:var(--muted);font-size:.85rem;margin:0 0 10px}
.strip{display:grid;grid-template-columns:1.15fr 1fr 1fr 1fr;gap:10px;align-items:start}
.cardhead{font-size:.72rem;text-transform:uppercase;letter-spacing:.07em;
  color:var(--muted);margin-bottom:5px}
figure{margin:0}
img{width:100%;border-radius:5px;border:1px solid var(--line);display:block;background:#000}
figcaption{font-size:.78rem;color:var(--muted);margin-top:4px;font-variant-numeric:tabular-nums}
.still img{border-color:var(--accent);border-width:2px}
.armlabel{font-size:.9rem;font-weight:600;margin:16px 0 6px}
.n{font-variant-numeric:tabular-nums}
.bad{color:var(--warn);font-weight:600}
.good{color:var(--ok);font-weight:600}
.foot{margin-top:34px;padding:16px;background:var(--panel);border:1px solid var(--line);
  border-radius:8px;font-size:.92rem}
"""


def rel(target: Path, start: Path) -> str:
    import os
    return os.path.relpath(target, start).replace("\\", "/")


def klass(value: float) -> str:
    return "bad" if value < 0.5 else ("good" if value >= 0.9 else "")


def main(argv) -> int:
    if not argv:
        print(__doc__)
        return 2
    lane_dir = Path(argv[0])
    lane = json.loads(io.open(lane_dir / "LANE.json", encoding="utf-8").read())
    ncc = json.loads(io.open(lane_dir / "NCC.json", encoding="utf-8").read())
    base = COMFY_OUTPUT / "baseline_output" / lane["lane"]
    out = Path(argv[1]) if len(argv) > 1 else base / "drift.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    here = out.parent

    parts = ["<div class='wrap'>",
             "<h1>Where the conditioning still goes</h1>",
             "<p class='sub'>%s &middot; image-to-video &middot; "
             "the leftmost frame is what the model was handed</p>" % lane["lane"],
             "<div class='lead'><b>Both arms start AS the still and both walk away "
             "from it.</b> Frame 1 correlates with the input at about 0.999 &mdash; "
             "that is the image-conditioning wrapper doing its job. By frame 97 both "
             "arms sit at 0.11&ndash;0.36 against that same input. Some of that is "
             "correct: it is video, things move, and a static reference naturally "
             "correlates less as a scene evolves. The number to read is not whether "
             "it drops, but whether the two arms drop <i>differently</i>.</div>"]

    for fixture in sorted(lane["fixtures"]):
        arms = sorted(lane["arm_sha256"][fixture])
        candidate = next(a for a in arms if a != "ours")
        staging = json.loads(io.open(lane_dir / fixture / "STAGING.json",
                                     encoding="utf-8").read())
        still = INPUT_DIR / str(staging.get("image") or "")
        subdir = lane["fixtures"][fixture].get("output_subdir") or ""
        root = base / subdir if subdir else base

        for seed in SEEDS:
            cell_key = "%s/seed%d" % (fixture, seed)
            cell = ncc["cells"].get(cell_key)
            if not cell:
                continue
            rows = {r["frame"]: r for r in cell["rows"]}
            admitted = cell["admitted"]
            parts.append("<h2>%s &middot; seed %d</h2>" % (fixture, seed))
            parts.append(
                "<p class='cellnote'>arm-to-arm at the final frame "
                "<span class='n %s'>%.4f</span> &mdash; %s. %s</p>"
                % (klass(cell["final_frame_arm_ncc"]), cell["final_frame_arm_ncc"],
                   "admitted" if admitted else
                   "<b>below the 0.90 admission floor, so &ldquo;which is better&rdquo; "
                   "is the wrong question here</b>",
                   staging.get("role", "")))

            for arm in ("ours", candidate):
                label = "shipped 0.70 on our LoRA" if arm == "ours" \
                    else "official rank-111 at 0.50"
                parts.append("<div class='armlabel'>%s &mdash; <span class='n'>%s</span></div>"
                             % (arm, label))
                cards = []
                if still.is_file():
                    cards.append(
                        "<figure class='still'><div class='cardhead'>conditioning still"
                        "</div><img src='%s' alt='still'>"
                        "<figcaption>what the model was handed</figcaption></figure>"
                        % rel(still, here))
                for frame in FRAMES:
                    path = root / ("%s_seed%d" % (arm, seed)) / ("frame_%05d_.png" % frame)
                    if not path.is_file():
                        continue
                    key = "still_ncc_ours" if arm == "ours" else "still_ncc_candidate"
                    value = rows.get(frame, {}).get(key)
                    caption = ("f%03d &middot; vs still <span class='n %s'>%.4f</span>"
                               % (frame, klass(value), value)) if value is not None \
                        else "f%03d" % frame
                    cards.append("<figure><div class='cardhead'>frame %d</div>"
                                 "<img src='%s' alt='f%d'>"
                                 "<figcaption>%s</figcaption></figure>"
                                 % (frame, rel(path, here), frame, caption))
                parts.append("<div class='strip'>%s</div>" % "".join(cards))

    parts.append(
        "<div class='foot'><b>Why there is no verdict.</b> The admission gate was "
        "written into <code>LANE.json</code> before anything rendered: on an "
        "image-conditioned lane the arms share a still, so they should track each "
        "other, and arm-to-arm correlation under 0.90 at the final frame means the "
        "comparison is meaningless. It rejected all four cells. Judging anyway, or "
        "lowering the floor now that the numbers are visible, would be moving the "
        "goalposts after seeing the data &mdash; which is how lane 3 produced a 9&ndash;8 "
        "split that carried no signal.</div></div>")

    html = ("<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>Still drift</title><style>%s</style></head><body>%s</body></html>"
            % (CSS, "".join(parts)))
    io.open(out, "w", encoding="utf-8", newline="\n").write(html)
    print("[PAGE] %s" % out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
