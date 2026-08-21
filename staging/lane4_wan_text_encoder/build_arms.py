"""Stage lane 4: wan_ti2v TEXT ENCODER precision -- ours (Q5_K_M GGUF) vs official (fp8-scaled).

Both arms are generated FROM THE SHIPPING ENGINE (``eng_wan_ti2v``) via
``diffomatic.build_api_graph``, so weights, sampler, tiling, canvas, length and
topology are identical by construction. The contrast is ONE node: the text
encoder loader.

  ours      CLIPLoaderGGUF   umt5-xxl-encoder-Q5_K_M.gguf           4.1 GB
  official  CLIPLoader       umt5_xxl_fp8_e4m3fn_scaled.safetensors 6.7 GB

WHY THIS LANE EXISTS AND WHY IT IS DIFFERENT FROM LANES 1-3. Lanes 1-3 screened
knobs where somebody had made a deliberate QUALITY choice. This delta is not
that: the GGUF encoder is a COMPROMISE taken for a 16 GB ceiling, and nobody has
ever measured what it costs. That makes it the highest-probability source of a
real quality gap between the shipped graphs and the official template -- the
exact exposure for an engine meant to be read, copied and re-used by people who
may have far more VRAM than this box.

A CLASS SWAP, NOT A LITERAL. The declared contrast is the loader node itself.
Wiring is untouched: both loaders emit CLIP into the same ``pos``/``neg``
encoders, so any wiring difference at all is a staging fault and the purity gate
must still fail it.

FIXTURES. A text encoder drives PROMPT ADHERENCE, so both fixtures carry
countable prompt demands, and one of them MOVES:

  crowd            hard content -- dozens of faces, glass tubes, a meter scale
                   with ticks; the prompt names what must be there.
  testcard_motion  the authored acuity card as the conditioning still, with a
                   prompt that DEMANDS a slow lateral move. Lane 1 proved a card
                   held still is countable; lane 2's critic proved a motion
                   claim cannot come from a stillness prompt. This fixture is
                   both at once -- known element sizes, in motion.
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
LANE = "lane4_wan_text_encoder"

OFFICIAL_CLIP = {
    "class_type": "CLIPLoader",
    "inputs": {"clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "type": "wan"},
}

STEADY_TAIL = ("static locked-off camera, single continuous shot, no cut, "
               "no scene change, no camera move.")

# The engine's frozen negative suppresses "text". That is correct for every
# ordinary fixture and FATAL for an acuity card whose positive prompt asks for
# rows of block letters -- the fixture would suppress the thing it measures.
# A fixture may therefore declare its own negative; it is applied to BOTH arms,
# so purity is untouched and the gate still sees one changed node.
TESTCARD_NEGATIVE = "low quality, worst quality, blurry, distorted, static"

FIXTURES = {
    "crowd": {
        "image": "lane1_crowd.png",
        # NOT "meter ticks": the crowd prompt never names a meter. A role string
        # that promises a countable the prompt does not demand invites the panel
        # to score an object neither arm was asked for (caught in review).
        "role": "hard content, countable prompt demands (faces, tubes, doorway)",
        "prompt": (
            "A crowded 1950s tent hall at night, dozens of people shoulder to "
            "shoulder watching a large wooden valve radio with a chrome antenna "
            "and glowing vacuum tubes on a table in the foreground, warm lantern "
            "light overhead, a lit doorway beyond the crowd, only subtle "
            "breathing, small head turns in the crowd and a faint flicker in the "
            "tube filaments, " + STEADY_TAIL),
    },
    "testcard_motion": {
        "image": "lane1_testcard.png",
        "role": "authored acuity instrument IN MOTION -- known element sizes, moving",
        "negative": TESTCARD_NEGATIVE,
        "prompt": (
            "A 1950s broadcast test card filling the frame: colour bars across "
            "the top, a grey step wedge, panels of geometric shapes and rows of "
            "block letters in decreasing sizes, fine line gratings, and a smooth "
            "grey gradient. The camera drifts slowly and steadily to the left "
            "across the card at a constant rate, the card itself stays flat, "
            "square and rigid, every printed element holding its shape and "
            "sharpness as it moves, single continuous shot, no cut, no scene "
            "change, nothing warping or rippling."),
    },
}


def sole(api, class_type):
    """The one node of a class -- ambiguity is a staging fault, not a default."""
    hits = sorted(k for k, v in api.items() if v["class_type"] == class_type)
    if len(hits) != 1:
        raise SystemExit("[FAIL] expected exactly one %s, found %s" % (class_type, hits))
    return hits[0]


def main() -> int:
    base, provenance = diffomatic.build_api_graph(ENGINE)
    clip = sole(base, "CLIPLoaderGGUF")
    loadimage = sole(base, "LoadImage")
    ksampler = sole(base, "KSampler")
    ours_clip = copy.deepcopy(base[clip])

    if ours_clip["inputs"].get("clip_name") == OFFICIAL_CLIP["inputs"]["clip_name"]:
        raise SystemExit("[FAIL] the shipping engine already loads the official "
                         "encoder; this lane is not a contrast")

    # Every consumer of the encoder must survive the swap untouched.
    consumers = sorted(k for k, v in base.items()
                       if any(isinstance(x, list) and len(x) == 2 and x[0] == clip
                              for x in v["inputs"].values()))
    print("[WIRING] encoder %r feeds %s -- unchanged in both arms" % (clip, consumers))

    all_hashes = {}
    for key in sorted(FIXTURES):
        spec = FIXTURES[key]
        out_dir = HERE / key
        out_dir.mkdir(exist_ok=True)

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
            print("[NEGATIVE] %-16s fixture-specific (both arms): %s"
                  % (key, spec["negative"]))

        written = {}
        for arm in ("ours", "official"):
            graph = copy.deepcopy(prepared)
            if arm == "official":
                graph[clip] = {"class_type": OFFICIAL_CLIP["class_type"],
                               "inputs": dict(OFFICIAL_CLIP["inputs"])}
            text = json.dumps(graph, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
            path = out_dir / ("arm_%s.json" % arm)
            io.open(path, "w", encoding="utf-8", newline="\n").write(text)
            written[arm] = hashlib.sha256(text.encode("utf-8")).hexdigest()
            print("[STAGED] %-16s %-18s sha256=%s nodes=%d"
                  % (key, path.name, written[arm][:16], len(graph)))

        io.open(out_dir / "ARMS.sha256", "w", encoding="utf-8", newline="\n").write(
            "".join("%s  arm_%s.json\n" % (written[a], a) for a in ("ours", "official")))
        io.open(out_dir / "STAGING.json", "w", encoding="utf-8", newline="\n").write(
            json.dumps({
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
                    "node": clip,
                    "ours": {"class_type": ours_clip["class_type"],
                             "inputs": ours_clip["inputs"]},
                    "official": OFFICIAL_CLIP,
                },
                "wiring_note": ("encoder feeds %s in BOTH arms; any wiring delta "
                                "is a staging fault" % consumers),
                "arm_sha256": written,
            }, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        all_hashes[key] = written

    io.open(HERE / "LANE.json", "w", encoding="utf-8", newline="\n").write(
        json.dumps({
            "lane": LANE,
            "engine": ENGINE,
            "arm_sha256": all_hashes,
            "declared_contrast": {"node": clip, "kind": "node class swap",
                                  "ours_class": ours_clip["class_type"],
                                  "official_class": OFFICIAL_CLIP["class_type"]},
            "fixtures": {k: {"output_subdir": k, "role": FIXTURES[k]["role"]}
                         for k in FIXTURES},
            "provenance": provenance,
            "verdict_matrix": {
                "structural_regression": ("an arm with materially more structural "
                    "defects loses regardless of sharpness"),
                "adherence_gain": ("the encoder's own axis: does an arm deliver "
                    "MORE of what the prompt names (countable objects, held "
                    "geometry) -- counted per arm against the PROMPT"),
                "null_at_shipping_output": ("LOSS for the candidate; the shipped "
                    "GGUF encoder stands and the VRAM saving is free"),
                "candidate_win": ("official WINS -> refutation panel, then this "
                    "becomes a QUALITY TIER proposal for boxes with headroom, "
                    "never a silent swap on a 16 GB default"),
            },
        }, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print("[LANE] %s staged: %d fixtures x 2 arms" % (LANE, len(FIXTURES)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
