"""Stage lane 5: ltx_video, the OFFICIAL pairing vs the SHIPPED one, on the i2v path.

This lane exists because lane 3 closed with two bounds written into its own
verdict, and this closes BOTH at once.

  BOUND 1 -- THE PATH. Lane 3 staged through ``_build_graph``, which is
  text-only. Production defaults to IMAGE-CONDITIONED: ``_i2v_enabled()``
  reads ``OTR_ENABLE_LTX_I2V`` with a default of ``"1"``
  (``eng_ltx_video.py:931``) and ``render_clip`` then builds the
  ``LTXVImgToVideoConditionOnly`` wrapper. So lane 3's null is proven on a path
  the show does not use. This lane stages through ``_build_graph_i2v``, named
  explicitly at the call site (``diffomatic.build_api_graph(builder_name=...)``).

  BOUND 2 -- THE FILE. Lane 3 tested 0.7 against 0.5 on OUR file, and said in
  writing that it "says nothing about the official file+strength combination".
  The official ComfyUI template pairs strength 0.5 with a DIFFERENT LoRA --
  ``ltx_2.3_22b_distilled_1.1_lora_dynamic_fro09_avg_rank_111_bf16``, 2.74 GB,
  which was download-gated until the operator authorized it. It is now on disk
  and visible to the server.

A BUNDLED SCREEN, AND THE PRICE IS STATED UP FRONT. The arms differ by TWO
things at once -- the LoRA file and its strength -- because that pair IS the
official configuration; splitting them would test a combination nobody ships.
This is lane 1's precedent (three sampler knobs bundled, "decompose only on a
win"). **A win here cannot be attributed to file or strength alone without a
follow-up lane, and the verdict must say so rather than discovering it later.**

  ours      ltx-2.3-22b-distilled-lora-384-1.1.safetensors        @ 0.70
  official  ltx_2.3_22b_distilled_1.1_lora_dynamic_..._rank_111  @ 0.50

FIXTURES -- both conditioning stills, because i2v needs one:

  portrait  portrait_16_9.png, EXACTLY 1024x576 -- the engine's own render
            canvas, so the latent resize is a no-op and the model sees the
            pixels as authored. Identity and face, which is production's real
            concern on this engine.
  crowd     lane1_crowd.png, 1920x1080 -- same 16:9 aspect, so the downscale
            is clean and identical in both arms. A busy scene with many people
            and objects: this is the ORPHAN-OBJECT hunt.

THE TEST CARD IS DELIBERATELY ABSENT. It is authored at 832x480 and its whole
value is that element sizes are KNOWN at the render canvas -- ``make_testcard``
says so in its own docstring. At 1024x576 it would be judged through a
resampler, which destroys the acuity ladder. Re-authoring it at this canvas is
a follow-up, not a thing to fake here.

A THIRD SCORING AXIS, DEFINED BY THE OPERATOR. On 2026-08-21 he watched the
reel and pointed at lane 3 march/seed20260821: "drum is by itself, no person
playing it." Verified at native pixels -- the shipped arm had an orphan snare
with no carrier while the candidate had it carried. That defect class is now a
declared, counted axis here: STRUCTURAL DEFECTS, and specifically orphan
objects. It is the class most likely to embarrass a published episode, and
nobody has ever hunted it on the path production actually renders.
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

ENGINE = "eng_ltx_video"
LANE = "lane5_ltx_i2v_official"
BUILDER = "_build_graph_i2v"

OURS_LORA = "ltxv\\ltx2\\ltx-2.3-22b-distilled-lora-384-1.1.safetensors"
OFFICIAL_LORA = ("ltxv\\ltx2\\"
                 "ltx_2.3_22b_distilled_1.1_lora_dynamic_fro09_avg_rank_111_bf16"
                 ".safetensors")
CONTRAST = {
    "lora.lora_name": OFFICIAL_LORA,
    "lora.strength_model": 0.5,
}

FIXTURES = {
    "portrait": {
        "image": "portrait_16_9.png",
        "role": "identity / face, conditioning still at EXACTLY the render canvas",
        "prompt": (
            "1950s cinematic close-up of a radio announcer at a chrome "
            "microphone, warm tungsten key light, tweed jacket and striped "
            "tie, he speaks calmly with small natural head movements, "
            "shallow depth of field, single continuous shot"),
    },
    "crowd": {
        "image": "lane1_crowd.png",
        "role": "ORPHAN-OBJECT hunt -- busy scene, many people and held objects",
        "prompt": (
            "A crowded 1950s tent hall at night, dozens of people shoulder to "
            "shoulder watching a large wooden valve radio with a chrome "
            "antenna and glowing vacuum tubes on a table in the foreground, "
            "warm lantern light overhead, only subtle breathing, small head "
            "turns in the crowd and a faint flicker in the tube filaments, "
            "static locked-off camera, single continuous shot, no cut, "
            "no scene change, no camera move."),
    },
}


def main() -> int:
    base, provenance = diffomatic.build_api_graph(
        ENGINE, allow_local=frozenset({"sigmas"}), builder_name=BUILDER)

    # The i2v graph must actually BE the i2v graph -- this is the whole point
    # of the lane, and a silent fallback to the text-only builder is exactly
    # the failure lane 3 shipped.
    for node_id in ("lora", "sigmas", "noise", "vaedecode", "pos", "latent",
                    "img2vid", "loadimage"):
        if node_id not in base:
            raise SystemExit("[FAIL] expected node %r missing -- is this the "
                             "i2v graph?" % node_id)
    if "ImgToVideo" not in base["img2vid"]["class_type"]:
        raise SystemExit("[FAIL] img2vid is %r, not an image-conditioning "
                         "wrapper" % base["img2vid"]["class_type"])
    if base["lora"]["inputs"]["strength_model"] != 0.7:
        raise SystemExit("[FAIL] shipped strength is %r, expected 0.7"
                         % base["lora"]["inputs"]["strength_model"])
    if base["lora"]["inputs"]["lora_name"] != OURS_LORA:
        raise SystemExit("[FAIL] shipped LoRA is %r, expected %r"
                         % (base["lora"]["inputs"]["lora_name"], OURS_LORA))
    if base["sigmas"]["class_type"] != "_SigmasFromValues":
        raise SystemExit("[FAIL] sigmas node is %r; ADAPT note is stale"
                         % base["sigmas"]["class_type"])

    # ADAPT: local sigma injector -> registered ManualSigmas, same values,
    # comma-joined string. Identical in BOTH arms; Bible 12.122.
    values = base["sigmas"]["inputs"].pop("values")
    if len(values) != 9:
        raise SystemExit("[FAIL] expected 9 distilled sigmas, got %d" % len(values))
    base["sigmas"] = {"class_type": "ManualSigmas",
                      "inputs": {"sigmas": ", ".join(repr(float(v)) for v in values)}}
    print("[ADAPT] sigmas -> ManualSigmas in BOTH arms (9 distilled sigmas)")
    print("[I2V]   %d nodes, wrapper=%s, still=%s"
          % (len(base), base["img2vid"]["class_type"],
             base["loadimage"]["inputs"].get("image")))

    all_hashes = {}
    for key in sorted(FIXTURES):
        spec = FIXTURES[key]
        out_dir = HERE / key
        out_dir.mkdir(exist_ok=True)

        prepared = copy.deepcopy(base)
        prepared["loadimage"]["inputs"]["image"] = spec["image"]
        prepared["pos"]["inputs"]["text"] = spec["prompt"]

        written = {}
        for arm in ("ours", "official"):
            graph = copy.deepcopy(prepared)
            if arm == "official":
                graph["lora"]["inputs"]["lora_name"] = OFFICIAL_LORA
                graph["lora"]["inputs"]["strength_model"] = CONTRAST["lora.strength_model"]
            text = json.dumps(graph, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
            path = out_dir / ("arm_%s.json" % arm)
            io.open(path, "w", encoding="utf-8", newline="\n").write(text)
            written[arm] = hashlib.sha256(text.encode("utf-8")).hexdigest()
            print("[STAGED] %-9s %-18s sha256=%s nodes=%d"
                  % (key, path.name, written[arm][:16], len(graph)))

        io.open(out_dir / "ARMS.sha256", "w", encoding="utf-8", newline="\n").write(
            "".join("%s  arm_%s.json\n" % (written[a], a) for a in ("ours", "official")))
        io.open(out_dir / "STAGING.json", "w", encoding="utf-8", newline="\n").write(
            json.dumps({
                "lane": LANE,
                "fixture": key,
                "engine": ENGINE,
                "builder": BUILDER,
                "image": spec["image"],
                "role": spec["role"],
                "prompt": spec["prompt"],
                "declared_contrast": CONTRAST,
                "bundled_screen": ("file AND strength move together because that "
                                   "pair IS the official configuration; a win "
                                   "cannot be attributed to either alone"),
                "shared_adapts": [{"node": "sigmas",
                                   "engine_authors": "_SigmasFromValues (local)",
                                   "staged_as": "ManualSigmas (registered)",
                                   "why": "Bible 12.122; lane 2/3 precedent"}],
                "arm_sha256": written,
            }, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        all_hashes[key] = written

    io.open(HERE / "LANE.json", "w", encoding="utf-8", newline="\n").write(
        json.dumps({
            "lane": LANE,
            "engine": ENGINE,
            "builder": BUILDER,
            "arm_sha256": all_hashes,
            "declared_contrast": CONTRAST,
            "fixtures": {k: {"output_subdir": k, "role": FIXTURES[k]["role"]}
                         for k in FIXTURES},
            "provenance": provenance,
            "closes_bounds": [
                "lane 3 path bound: screened text-only while OTR_ENABLE_LTX_I2V "
                "defaults to 1 (eng_ltx_video.py:931)",
                "lane 3 file bound: tested 0.7 vs 0.5 on OUR file only; the "
                "official 0.5 pairs with the rank-111 dynamic LoRA",
            ],
            "verdict_matrix": {
                "structural_regression": ("an arm with materially more structural "
                    "defects LOSES regardless of sharpness. ORPHAN OBJECTS are a "
                    "named, counted sub-class here -- the operator found one in "
                    "the shipped arm on lane 3 march/seed20260821 and it is the "
                    "defect most likely to embarrass a published episode"),
                "identity_hold": ("i2v conditions on a still, so likeness to that "
                    "still is a GATE, not a score: an arm that loses the man "
                    "loses outright"),
                "null_at_shipping_output": ("LOSS for the candidate; the shipped "
                    "0.70 on our file stands, now proven on the path production "
                    "actually uses"),
                "candidate_win": ("official pairing WINS -> refutation panel, then "
                    "a decomposition lane to separate file from strength before "
                    "anything reaches otr_canonical.json"),
                "notes": [
                    "i2v arms share a conditioning still, so unlike lane 3's t2v "
                    "the arms should render the SAME scene; arm-to-arm NCC is "
                    "therefore a real admission gate here, not merely a flag.",
                    "A bundled screen: file and strength move together.",
                ],
            },
        }, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print("[LANE] %s staged: %d fixtures x 2 arms" % (LANE, len(FIXTURES)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
