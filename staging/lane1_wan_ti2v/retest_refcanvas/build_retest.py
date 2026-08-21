"""Stage the shift-transplant retest: the same contrast at the REFERENCE canvas.

Lane 1 tested shift 8 at 832x480 x 97 frames, an operating point it was never
authored for -- the official reference pairs it with 1280x704 x 121, and the
shipping engine's own comment says 5.0 is the 5B value. The verdict recorded
that as a bound on the null, and the completeness critic named the closer: run
the one cell that produced the only unanimous call (crowd, seed 20260821) at
the reference canvas, both arms.

The canvas move is a SHARED input change, applied identically to both arms, so
the declared contrast stays exactly the three sampler knobs. If the arms tie or
official falls behind here too, the transplant objection dies for good. If
official WINS here, that is a new finding about operating points, not a
reopened lane -- it goes to the operator, not into production.

Best-effort per the 2026-08-21 ruling: 2.26x the pixels and 121 frames on the
8GB-tier GGUF is exactly the kind of leg that may OOM, and an OOM is recorded
as a plain fault, not investigated.
"""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CROWD = HERE.parent / "crowd"

REF_CANVAS = {"width": 1280, "height": 704, "length": 121}
CONTRAST = {
    "ksampler.sampler_name": "uni_pc",
    "ksampler.steps": 20,
    "modelsampling.shift": 8.0,
}


def main() -> int:
    written = {}
    for arm in ("ours", "official"):
        graph = json.loads(io.open(CROWD / ("arm_%s.json" % arm),
                                   encoding="utf-8").read())
        for key, value in REF_CANVAS.items():
            graph["latent"]["inputs"][key] = value
        text = json.dumps(graph, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        path = HERE / ("arm_%s.json" % arm)
        io.open(path, "w", encoding="utf-8", newline="\n").write(text)
        written[arm] = hashlib.sha256(text.encode("utf-8")).hexdigest()
        print("[STAGED] %-18s sha256=%s  latent=%dx%dx%d"
              % (path.name, written[arm][:16], REF_CANVAS["width"],
                 REF_CANVAS["height"], REF_CANVAS["length"]))

    io.open(HERE / "ARMS.sha256", "w", encoding="utf-8", newline="\n").write(
        "".join("%s  arm_%s.json\n" % (written[a], a) for a in ("ours", "official")))
    io.open(HERE / "STAGING.json", "w", encoding="utf-8", newline="\n").write(
        json.dumps({
            "lane": "lane1_wan_ti2v", "cell": "retest_refcanvas",
            "fixture": "crowd", "seed": 20260821,
            "derived_from": "crowd arms, canvas override applied to BOTH arms",
            "canvas": REF_CANVAS,
            "declared_contrast": CONTRAST,
            "arm_sha256": written,
            "why": ("shift is resolution/length-dependent; this cell closes the "
                    "transplant objection recorded in the lane 1 verdict"),
        }, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print("[CONTRAST] unchanged: the three sampler knobs; canvas moved in BOTH arms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
