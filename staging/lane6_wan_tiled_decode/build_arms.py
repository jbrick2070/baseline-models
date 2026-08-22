"""Stage lane 6: wan_ti2v VAE DECODE -- ours (tiled) vs candidate (untiled).

Both arms are generated FROM THE SHIPPING ENGINE (``eng_wan_ti2v``) via
``diffomatic.build_api_graph``, so weights, encoder, sampler, canvas, length and
topology are identical by construction. The contrast is ONE node: the decoder.

  ours       VAEDecodeTiled   tile 256, overlap 64, temporal 16, t-overlap 8
  candidate  VAEDecode        no tiling at all

WHY THIS LANE EXISTS. It is a lane-4-shaped lane, not a lane-1-shaped one: this
is a COMPROMISE, not a quality choice, and nobody has measured what it costs.
The engine says so itself (``eng_wan_ti2v.py:221-226``):

    "Tiled decode is ON for this tier: the video-VAE decode is a top VRAM-peak
     driver at 8GB. (The ltx tier measured the same direction on 2026-07-27 --
     tiled holds the peak FLAT across clip length where untiled climbs with it.
     That is ltx's measurement, not this adapter's, so it is context for a
     future WAN sweep and not a claim about these numbers.)"

So the field was frozen ON for VRAM at the 8 GB tier, on another engine's
evidence, and its QUALITY cost on this engine has never been measured. That is
exactly the "biggest untested compromise" class the plan flagged after five
knob-lanes returned null.

A CLASS SWAP, NOT A LITERAL, AND THE SHIPPED RECIPE IS NOT TOUCHED.
``tiled_vae`` is a FROZEN recipe field whose env knob only binds under the
prequalification consent act. This lane does not open that act and does not
edit the recipe: it stages the shipped engine's own graph and swaps ONE NODE in
the staged API JSON, exactly as lane 4 swapped the encoder loader. The shipped
recipe stays byte-identical and the operator's "recipes are not on the table"
directive is respected -- a WIN here would be a PROPOSAL to him, not a change.

FIXTURES. A tiled decoder's failure mode is SPATIAL -- seams at tile
boundaries, discontinuities across the 256px grid, softening near edges -- so
both fixtures are chosen to make a seam countable rather than impressionistic:

  crowd     hard content, many faces and held objects across the full frame,
            so a boundary that falls through a face is visible.
  testcard  the authored acuity card held STILL. Lane 1 proved a card held
            still is countable and lane 4 proved this same card FAILS as a
            motion fixture (0.0 px translation at both seeds, measured by
            tools/drift_stats.py), so it is used here only as what it is: a
            static acuity instrument with known element sizes. A tile seam
            crossing a grating or a letter row is the most legible evidence
            this defect class can produce.
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

ENGINE = "eng_wan_ti2v"
LANE = "lane6_wan_tiled_decode"

STEADY_TAIL = ("static locked-off camera, single continuous shot, no cut, "
               "no scene change, no camera move.")

# The engine's frozen negative suppresses "text", which is correct for ordinary
# content and FATAL for an acuity card whose positive prompt asks for letter
# rows. Lane 4 established this override; it is applied to BOTH arms, so it is
# not part of the contrast.
TESTCARD_NEGATIVE = ("blurry, low quality, distorted, warped, rippling, "
                     "melting, morphing, scene change, cut")

FIXTURES = {
    "crowd": {
        "image": "lane1_crowd.png",
        "role": "hard content -- faces and held objects across the whole frame",
        "negative": None,
        "prompt": (
            "A crowded 1940s radio studio control room, a dozen technicians at "
            "consoles, rows of glass valve tubes glowing along the back wall, a "
            "large VU meter with a clearly ruled scale on the near panel, faces "
            "lit from below by the console lamps. " + STEADY_TAIL),
    },
    "testcard": {
        "image": "lane1_testcard.png",
        "role": "authored acuity instrument, STATIC -- known element sizes",
        "negative": TESTCARD_NEGATIVE,
        "prompt": (
            "A 1950s broadcast test card filling the frame: colour bars across "
            "the top, a grey step wedge, panels of geometric shapes and rows of "
            "block letters in decreasing sizes, fine line gratings, and a "
            "smooth grey gradient. The card is flat, square and rigid, every "
            "printed element holding its exact shape, straight edges and "
            "sharpness. " + STEADY_TAIL),
    },
}


def sole(api, class_type):
    """The one node of a class -- ambiguity is a staging fault, not a default."""
    hits = sorted(k for k, v in api.items() if v["class_type"] == class_type)
    if len(hits) != 1:
        raise SystemExit("[FAIL] expected exactly one %s, found %s"
                         % (class_type, hits))
    return hits[0]


def main() -> int:
    base, provenance = diffomatic.build_api_graph(ENGINE)

    decode = sole(base, "VAEDecodeTiled")
    loadimage = sole(base, "LoadImage")
    ksampler = sole(base, "KSampler")
    ours_decode = copy.deepcopy(base[decode])

    # The untiled arm keeps ONLY the wires; every tiling literal is dropped
    # because VAEDecode has no such inputs. Carrying one over would not be a
    # smaller contrast, it would be an invalid graph.
    keep = {k: v for k, v in ours_decode["inputs"].items()
            if k in ("samples", "vae")}
    if set(keep) != {"samples", "vae"}:
        raise SystemExit("[FAIL] tiled decoder does not expose samples+vae as "
                         "expected: %s" % sorted(ours_decode["inputs"]))
    candidate_decode = {"class_type": "VAEDecode", "inputs": keep}

    dropped = sorted(set(ours_decode["inputs"]) - set(keep))
    print("[CONTRAST] node %r  VAEDecodeTiled -> VAEDecode" % decode)
    print("[CONTRAST] tiling literals dropped in the candidate arm: %s"
          % ", ".join("%s=%r" % (k, ours_decode["inputs"][k]) for k in dropped))

    # Whatever consumes the decoded IMAGE must survive the swap untouched.
    consumers = sorted(k for k, v in base.items()
                       if any(isinstance(x, list) and len(x) == 2
                              and x[0] == decode for x in v["inputs"].values()))
    print("[WIRING] decoder %r feeds %s -- unchanged in both arms"
          % (decode, consumers))

    all_hashes = {}
    for key in sorted(FIXTURES):
        spec = FIXTURES[key]
        out_dir = HERE / key
        out_dir.mkdir(parents=True, exist_ok=True)

        prepared = copy.deepcopy(base)
        prepared[loadimage]["inputs"]["image"] = spec["image"]
        positive = prepared[ksampler]["inputs"]["positive"][0]
        prepared[positive]["inputs"]["text"] = spec["prompt"]
        if spec.get("negative"):
            negative = prepared[ksampler]["inputs"]["negative"][0]
            if negative == positive:
                raise SystemExit("[FAIL] positive and negative resolve to the "
                                 "same node; a per-fixture negative would "
                                 "overwrite the prompt")
            prepared[negative]["inputs"]["text"] = spec["negative"]
            print("[NEGATIVE] %-10s fixture-specific (BOTH arms): %s"
                  % (key, spec["negative"]))

        written = {}
        for arm in ("ours", "candidate"):
            graph = copy.deepcopy(prepared)
            if arm == "candidate":
                graph[decode] = copy.deepcopy(candidate_decode)
            text = json.dumps(graph, indent=2, sort_keys=True,
                              ensure_ascii=False) + "\n"
            path = out_dir / ("arm_%s.json" % arm)
            io.open(path, "w", encoding="utf-8", newline="\n").write(text)
            written[arm] = hashlib.sha256(text.encode("utf-8")).hexdigest()
            print("[STAGED] %-10s %-20s sha256=%s nodes=%d"
                  % (key, path.name, written[arm][:16], len(graph)))

        io.open(out_dir / "ARMS.sha256", "w", encoding="utf-8",
                newline="\n").write(
            "".join("%s  arm_%s.json\n" % (written[a], a)
                    for a in ("ours", "candidate")))
        io.open(out_dir / "STAGING.json", "w", encoding="utf-8",
                newline="\n").write(json.dumps({
            "lane": LANE,
            "fixture": key,
            "engine": ENGINE,
            "image": spec["image"],
            "role": spec["role"],
            "prompt": spec["prompt"],
            "negative": (prepared[prepared[ksampler]["inputs"]["negative"][0]]
                         ["inputs"]["text"]),
            "negative_is_fixture_specific": bool(spec.get("negative")),
            "declared_contrast": {
                "kind": "node class swap",
                "node": decode,
                "ours": {"class_type": ours_decode["class_type"],
                         "inputs": ours_decode["inputs"]},
                "candidate": candidate_decode,
                "tiling_literals_dropped": dropped,
            },
            "wiring_note": ("decoder feeds %s in BOTH arms; any wiring delta "
                            "is a staging fault" % consumers),
            "arm_sha256": written,
        }, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        all_hashes[key] = written

    io.open(HERE / "LANE.json", "w", encoding="utf-8", newline="\n").write(
        json.dumps({
            "lane": LANE,
            "engine": ENGINE,
            "arm_sha256": all_hashes,
            "declared_contrast": {
                "node": decode,
                "kind": "node class swap",
                "ours_class": "VAEDecodeTiled",
                "candidate_class": "VAEDecode",
                "tiling_literals_dropped": dropped,
            },
            "fixtures": {k: {"output_subdir": k, "role": FIXTURES[k]["role"]}
                         for k in FIXTURES},
            "provenance": provenance,
            "recipe_note": ("tiled_vae is a FROZEN recipe field whose env knob "
                            "only binds under the prequalification consent act. "
                            "This lane does not open that act and does not edit "
                            "the recipe -- it swaps one node in the STAGED API "
                            "graph. The shipped recipe stays byte-identical."),
            "verdict_matrix": {
                "seam_regression": ("a visible tile seam, boundary "
                    "discontinuity or 256-grid artifact in the TILED arm that "
                    "is absent from the untiled arm is the candidate's win "
                    "condition and the only one that matters"),
                "detail_gain": ("untiled resolving more of the card's known "
                    "elements -- read down to which grating, which letter row"),
                "null_at_shipping_output": ("LOSS for the candidate; tiled "
                    "decode stands and its VRAM saving is free"),
                "admission": ("arm-to-arm NCC below ~0.90 at the final frame "
                    "means the arms stopped rendering the same scene and the "
                    "cell is not judged (lane 1 precedent, lane 5 gate)"),
            },
        }, indent=2, sort_keys=True, ensure_ascii=False) + "\n")

    print("[LANE] wrote %s" % (HERE / "LANE.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
