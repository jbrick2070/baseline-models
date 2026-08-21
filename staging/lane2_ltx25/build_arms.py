"""Stage lane 2: ltx25 I2V anchor strength -- ours (1.0) vs soft (0.7).

Both arms come from the shipping engine `eng_ltx25` via the differ's
`build_api_graph`, so topology, scheduler, sigmas, canvas and weights are
identical by construction. The contrast is ONE shipping knob that happens to be
TWO graph leaves: `LTX25_I2V_ANCHOR_STRENGTH` (`ltx25_recipe.py:223`) feeds
BOTH `i2v.strength` (`eng_ltx25.py:1042`) and `refine_i2v.strength` (`:1099`).
An `i2v`-only arm is not a shippable configuration -- reaching it would mean
splitting one constant into two, a code change nobody voted -- and holding the
refine anchor at 1.0 would replant the original still into the doubled latent
against a drifted stage-1 clip (the r1 panel's frame-0 discontinuity finding).

1.0 is the node default nobody chose; 0.7 is the sibling audio lane's
deliberate soft anchor (`eng_ltx_av.py:972`). The recipe's own note frames this
lane: "0.7 vs 1.0 has never been A/B'd on this model" -- and warns the hard pin
is what fights the live face-identity defect. Hence the pre-declared verdict
matrix below: identity is a GATE, not a score.

THE ONE DELIBERATE SHARED ADAPT, cited so no reader mistakes it for drift:
production swaps the text-encoder class at runtime
(`eng_ltx25.py:1188: classes["te"] = _cpu_pinned_clip_loader(classes["te"])`)
to pin the Gemma-4 12B encoder to CPU -- a GPU encode transiently needs ~15.6
GiB and OOM'd the 2026-08-19 canonical leg. That swap is invisible in graph
JSON, so an API arm submitted verbatim would silently run the stock loader.
The installed ComfyUI-GGUF pack registers `CLIPLoaderGGUFCPU`
(`ComfyUI-GGUF/nodes.py:253`, mapped at `:371`), which sets the identical
three-device placement with the identical fail-loud check. Both arms use it,
so the contrast is untouched and the bench runs production's memory path.
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
    "officer": {
        "image": "portrait_16_9.png",
        "role": "identity gate (primary)",
        "prompt": (
            "1950s black and white cinematic close-up of a military officer's "
            "face, facing the camera, holding his gaze steady, only subtle "
            "breathing and a slight head movement, " + STEADY_TAIL),
    },
    "crowd": {
        "image": "lane1_crowd.png",
        "role": "multi-face stress (secondary; cannot close the identity gate)",
        "prompt": (
            "A crowded 1950s tent hall at night, dozens of people shoulder to "
            "shoulder watching a large wooden valve radio with a chrome "
            "antenna and glowing vacuum tubes on a table in the foreground, "
            "warm lantern light overhead, a lit doorway beyond the crowd, "
            "only subtle breathing, small head turns in the crowd and a faint "
            "flicker in the tube filaments, " + STEADY_TAIL),
    },
    "testcard": {
        "image": "lane1_testcard.png",
        "role": "drift control (excluded from the identity gate)",
        "prompt": (
            "A 1950s broadcast test card held steady on screen: colour bars "
            "across the top, a grey step wedge, panels of geometric shapes and "
            "rows of block letters in decreasing sizes, fine line gratings, "
            "and a smooth grey gradient, perfectly flat and square to camera, "
            "only the faintest flicker and film grain, nothing moving, "
            + STEADY_TAIL),
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
                "lane": "lane2_ltx25", "fixture": key, "engine": ENGINE,
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
        json.dumps({"lane": "lane2_ltx25", "engine": ENGINE,
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
