"""Rebuild a fixture's render receipts and PROVE them against server history.

A receipt that is merely re-derived is an assertion. ComfyUI keeps the exact
graph it executed in ``/history``, so a re-derived submission can be compared
against the server's own record of what ran -- which turns the reconstruction
into evidence.

This exists because lane 1's pass-1 receipts were deleted during the move to
per-fixture directories while the rendered frames survived. Re-rendering would
have produced new receipts for new runs; this proves the ORIGINAL ones.

usage:
    rebuild_receipts.py <lane_dir> <fixture> <arm>_seed<seed>=<prompt_id> ...
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
import urllib.request
from pathlib import Path

SERVER = "http://127.0.0.1:8000"


def get_json(url, timeout=90):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def normalise(graph):
    """Compare semantically: history round-trips numbers and key order."""
    return json.loads(json.dumps(graph, sort_keys=True))


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    lane_dir = Path(argv[0]).resolve()
    fixture = argv[1]
    pairs = []
    for item in argv[2:]:
        label, _, prompt_id = item.partition("=")
        pairs.append((label, prompt_id))

    sys.path.insert(0, str(lane_dir))
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import render_arms  # noqa: E402
    import purity_gate  # noqa: E402

    lane = json.loads(io.open(lane_dir / "LANE.json", encoding="utf-8").read())
    subdir = lane["fixtures"][fixture]["output_subdir"]
    receipts = lane_dir / fixture / "render"
    receipts.mkdir(parents=True, exist_ok=True)

    legs, manifest, faults = [], {}, []
    for label, prompt_id in pairs:
        arm, _, seed_text = label.partition("_seed")
        seed = int(seed_text)
        expected = render_arms.build_submission(fixture, subdir, arm, seed)
        text = json.dumps(expected, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()

        entry = get_json("%s/history/%s" % (SERVER, prompt_id)).get(prompt_id)
        if not entry:
            faults.append("%s: prompt_id %s is not in server history" % (label, prompt_id))
            continue

        executed = entry.get("prompt", [None, None, {}])[2]
        if normalise(executed) != normalise(expected):
            faults.append("%s: the graph the server executed differs from the "
                          "re-derived submission" % label)
        else:
            print("[PROVEN] %-24s executed graph == re-derived submission" % label)

        path = receipts / ("submitted_%s_seed%d.json" % (arm, seed))
        io.open(path, "w", encoding="utf-8", newline="\n").write(text)
        manifest[path.name] = digest

        status = entry.get("status") or {}
        images = []
        for output in (entry.get("outputs") or {}).values():
            for image in output.get("images") or []:
                images.append(image)
        legs.append({
            "leg": "%s/%s" % (fixture, label), "fixture": fixture, "arm": arm,
            "seed": seed, "sha256": digest, "prompt_id": prompt_id,
            "status": status.get("status_str", "unknown"),
            "frame_count": len(images),
            "subfolder": images[0]["subfolder"] if images else None,
            "first_frame": images[0]["filename"] if images else None,
            "last_frame": images[-1]["filename"] if images else None,
            "receipt_origin": "rebuilt from server history",
        })
        print("  %-24s status=%s frames=%d sha256=%s"
              % (label, legs[-1]["status"], len(images), digest[:16]))

    io.open(receipts / "ARMS.sha256", "w", encoding="utf-8", newline="\n").write(
        "".join("%s  %s\n" % (manifest[n], n) for n in sorted(manifest)))
    io.open(receipts / "RENDER.json", "w", encoding="utf-8", newline="\n").write(
        json.dumps({"server": SERVER, "fixture": fixture,
                    "seeds": sorted({leg["seed"] for leg in legs}),
                    "arms": sorted({leg["arm"] for leg in legs}),
                    "output_prefix": render_arms.OUT_PREFIX, "fps": 25,
                    "legs": legs,
                    "note": ("Receipts rebuilt from ComfyUI /history after the "
                             "pass-1 files were lost in the per-fixture move. "
                             "Each executed graph was compared against the "
                             "re-derived submission.")},
                   indent=2, sort_keys=True, ensure_ascii=False) + "\n")

    for seed in sorted({leg["seed"] for leg in legs}):
        argv_gate = [str(receipts / ("submitted_ours_seed%d.json" % seed)),
                     str(receipts / ("submitted_official_seed%d.json" % seed)),
                     "--expect", 'ksampler.sampler_name="uni_pc"',
                     "--expect", "ksampler.steps=20",
                     "--expect", "modelsampling.shift=8.0",
                     "--expect", 'save.filename_prefix="%s"'
                     % render_arms.leg_prefix(fixture, subdir, "official", seed)]
        if purity_gate.main(argv_gate) != 0:
            faults.append("seed %d: rebuilt submissions are not pure" % seed)

    if faults:
        print("")
        for fault in faults:
            print("[FAIL] %s" % fault)
        return 1
    print("\n[REBUILD] %d leg(s) proven against server history." % len(legs))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
