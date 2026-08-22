"""Stage lane 7: ltx25 I2V anchor strength on MOTION -- ours (1.0) vs soft (0.7).

THE SAME CONTRAST AS LANE 2, ON THE AXIS LANE 2 COULD NOT TEST. Lane 2 closed
NO WIN and wrote the bound itself:

    "the MOTION axis was structurally untested (every prompt demanded
     stillness, seats judged stills) -- if soft is ever re-argued it takes one
     motion-demanding fixture, 4 legs on the existing harness."

This is that fixture and those four legs. Nothing else about the contrast moves:
ONE constant `LTX25_I2V_ANCHOR_STRENGTH` feeds BOTH `i2v.strength` and
`refine_i2v.strength`, so both leaves move together exactly as they do in
production. An i2v-only arm is not a shippable configuration and is not staged.

WHY IT MATTERS THAT THE FIXTURE MOVES. A soft anchor lets the clip depart
further from its conditioning still. On a fixture that demands stillness that is
invisible by construction -- which is precisely why lane 2's null is bounded.
On a fixture that demands the subject cross the frame, a weaker anchor should
show up as either more willing motion (the candidate's case) or as identity and
structure falling apart (ours' case).

THE MOTION GATE, DECLARED BEFORE RENDERING. Lane 4 established that a prompt
demanding a camera move does not guarantee one: its `testcard_motion` fixture
produced 0.0 px translation in both arms at both seeds. So this lane fails
CLOSED on its own premise -- if neither arm actually moves, the fixture did not
test the motion axis and the cell is NOT judged. That verdict would be "the
fixture failed", not "soft ties on motion".
"""
from __future__ import annotations

import copy
import hashlib
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
import diffomatic  # noqa: E402

ENGINE = "eng_ltx25"
SOFT = 0.7

STEADY_TAIL = ("static locked-off camera, single continuous shot, no cut, "
               "no scene change, no camera move.")

FIXTURES = {
    "crossing": {
        "image": "lane1_crowd.png",
        "role": ("MOTION-demanding, crowd -- the axis lane 2 left untested; "
                 "people must traverse the frame, not merely breathe"),
        "prompt": (
            "A crowded 1950s tent hall at night. The people walk steadily "
            "across the hall from left to right, passing in front of the "
            "camera and out of frame, arms swinging as they go, heads turning "
            "to follow something off to the right, a large wooden valve radio "
            "with glowing tubes on a table in the foreground, warm lantern "
            "light overhead. The camera holds position while the crowd moves "
            "through, single continuous shot, no cut, no scene change."),
    },
    "turning": {
        "image": "portrait_16_9.png",
        "role": ("MOTION-demanding, identity under movement -- the harder case: "
                 "does a soft anchor keep the FACE while the head moves"),
        "prompt": (
            "1950s black and white cinematic shot of a military officer. He "
            "turns his head fully from his left shoulder around to his right, "
            "then lifts his chin and leans forward toward the camera, his "
            "shoulders rotating with him, a deliberate continuous movement "
            "throughout. The camera holds position, single continuous shot, "
            "no cut, no scene change."),
    },
}

# Two graph leaves, ONE shipping knob. The purity gate declares both.
CONTRAST = {"i2v.strength": SOFT, "refine_i2v.strength": SOFT}

VERDICT_MATRIX = {
    "identity_regression": "LOSS, regardless of any motion or stability gain",
    "identity_hold_plus_material_gain": "candidate WIN -> refutation panel",
    "null_at_shipping_output": "LOSS (the shipped default stands)",
    "semantic_scene_failure": "invalid cell -> fix the fixture, never a vote",
    "notes": [
        "Identity is judged on RAW native-pixel face crops against the "
        "conditioning still at early/middle/final frames; contrast-normalized "
        "copies serve only secondary motion/detail questions.",
        "Arm-to-arm NCC is a divergence FLAG on this lane, not an admission "
        "gate: the soft arm is designed to drift, so lane 1's 0.90 rule would "
        "reject the effect under test.",
        "The expected freer-motion benefit of 0.7 is an ASSUMPTION carried "
        "from an audio-driven sibling lane; it is what the A/B tests, not a "
        "premise.",
    ],
}


def sole(api, class_type):
    hits = sorted(k for k, v in api.items() if v["class_type"] == class_type)
    if len(hits) != 1:
        raise SystemExit("[FAIL] expected exactly one %s, found %s" % (class_type, hits))
    return hits[0]


def main() -> int:
    base, provenance = diffomatic.build_api_graph(ENGINE)

    for node_id in ("i2v", "refine_i2v", "loadimage", "noise", "decode", "te", "pos"):
        if node_id not in base:
            raise SystemExit("[FAIL] expected node %r missing from %s" % (node_id, ENGINE))
    for node_id in ("i2v", "refine_i2v"):
        if base[node_id]["inputs"].get("strength") != 1.0:
            raise SystemExit("[FAIL] %s.strength is %r, expected the shipped 1.0"
                             % (node_id, base[node_id]["inputs"].get("strength")))
    if base["te"]["class_type"] != "CLIPLoaderGGUF":
        raise SystemExit("[FAIL] te resolved to %r; the ADAPT note is stale"
                         % base["te"]["class_type"])

    # The one deliberate shared ADAPT (see module docstring).
    base["te"]["class_type"] = "CLIPLoaderGGUFCPU"

    all_hashes = {}
    for key in sorted(FIXTURES):
        spec = FIXTURES[key]
        out_dir = HERE / key
        out_dir.mkdir(exist_ok=True)

        prepared = copy.deepcopy(base)
        prepared[sole(prepared, "LoadImage")]["inputs"]["image"] = spec["image"]
        # The positive encoder is set by node id (asserted present above)
        # rather than traced through wires: ltx25's guider takes conditioning
        # through LTXVConditioning, so there is no direct positive wire to walk.
        prepared["pos"]["inputs"]["text"] = spec["prompt"]

        written = {}
        for arm in ("ours", "soft"):
            graph = copy.deepcopy(prepared)
            if arm == "soft":
                graph["i2v"]["inputs"]["strength"] = SOFT
                graph["refine_i2v"]["inputs"]["strength"] = SOFT
            text = json.dumps(graph, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
            path = out_dir / ("arm_%s.json" % arm)
            io.open(path, "w", encoding="utf-8", newline="\n").write(text)
            written[arm] = hashlib.sha256(text.encode("utf-8")).hexdigest()
            print("[STAGED] %-9s %-16s sha256=%s nodes=%d"
                  % (key, path.name, written[arm][:16], len(graph)))
        all_hashes[key] = written

        io.open(out_dir / "ARMS.sha256", "w", encoding="utf-8", newline="\n").write(
            "".join("%s  arm_%s.json\n" % (written[a], a) for a in ("ours", "soft")))
        io.open(out_dir / "STAGING.json", "w", encoding="utf-8", newline="\n").write(
            json.dumps({
                "lane": "lane7_ltx25_motion", "fixture": key, "engine": ENGINE,
                "image": spec["image"], "role": spec["role"],
                "prompt": spec["prompt"],
                "declared_contrast": CONTRAST,
                "contrast_note": ("two graph leaves, ONE shipping knob: both "
                                  "read LTX25_I2V_ANCHOR_STRENGTH "
                                  "(ltx25_recipe.py:223)"),
                "shared_adapt": {
                    "node": "te",
                    "engine_emits": "CLIPLoaderGGUF",
                    "staged_as": "CLIPLoaderGGUFCPU",
                    "why": ("matches production's runtime CPU pin at "
                            "eng_ltx25.py:1188; identical three-device "
                            "placement, both arms, contrast untouched"),
                },
                "arm_sha256": written,
            }, indent=2, sort_keys=True, ensure_ascii=False) + "\n")

    io.open(HERE / "LANE.json", "w", encoding="utf-8", newline="\n").write(
        json.dumps({"lane": "lane7_ltx25_motion", "engine": ENGINE,
                    "provenance": provenance,
                    "declared_contrast": CONTRAST,
                    "verdict_matrix": VERDICT_MATRIX,
                    "fixtures": {k: {"image": v["image"], "role": v["role"],
                                     "output_subdir": k}
                                 for k, v in FIXTURES.items()},
                    "arm_sha256": all_hashes},
                   indent=2, sort_keys=True, ensure_ascii=False) + "\n")

    print("[OURS] anchor 1.0 (both nodes, the shipped default nobody chose)")
    print("[SOFT] anchor %s (both nodes, the sibling lane's deliberate value)" % SOFT)
    print("[ADAPT] te -> CLIPLoaderGGUFCPU in BOTH arms (production memory path)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
