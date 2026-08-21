"""Stage lane 3: ltx_video distilled LoRA strength -- ours (0.7) vs half (0.5).

Both arms come from the shipping engine `eng_ltx_video` (distilled t2v mode)
via `diffomatic.build_api_graph`, so weights, sigmas, sampler, canvas and
topology are identical by construction. The contrast is ONE literal:
`lora.strength_model` -- `_LTX_DISTILLED_LORA_STRENGTH = 0.70` shipped, 0.5
the fleet-diff reference value. SAME LoRA FILE in both arms.

**Bound, stated up front:** the official template pairs 0.5 with a DIFFERENT
LoRA (the download-gated rank-111 dynamic file, not on disk). This lane tests
the strength knob on OUR installed file, so the candidate arm is named `half`,
not `official` -- a win or loss here says nothing about the official
file+strength combination. OTR's own HQ lane already runs its half-strength
LoRA at 0.5 (`_LTX_HQ_LORA_STRENGTH`), which is why 0.5 is a credible value
and not a random point.

TWO documented shared ADAPTs, identical in both arms:
1. `sigmas`: the engine injects a LOCAL `_SigmasFromValues` class
   (`eng_ltx_video.py:1621`) that cannot be submitted over the API (Bible
   12.122). Replaced with the registered `ManualSigmas` carrying the same nine
   `LTX_DISTILLED_SIGMAS` as a comma-joined string -- the exact form lane 2's
   `refine_sigmas` node already rendered successfully over the API.
2. Nothing else: `render_clip` has no other class swaps in distilled mode
   (grep receipt: `classes.setdefault` at 1621 only; 1745-1746 are HQ mode).
   The text encoder's device is a graph input here, not a runtime subclass.

THIS IS A TEXT-TO-VIDEO LANE -- prompts ARE the fixtures. The lane 2
completeness critic proved a motion claim cannot come from stillness prompts
judged as stills, so one fixture DEMANDS motion, and the verdict matrix says
what each outcome means before anything renders.
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
HALF = 0.5

FIXTURES = {
    "portrait": {
        "role": "coherence / facial detail (near-static subject)",
        "prompt": (
            "1950s cinematic close-up of a radio announcer at a chrome "
            "microphone, warm tungsten key light, tweed jacket and striped "
            "tie, he speaks calmly into the microphone with small natural "
            "head movements, shallow depth of field, single continuous shot"),
    },
    "march": {
        "role": "MOTION-demanding (the axis lane 2 could not test)",
        "prompt": (
            "A 1950s marching band parades left to right across the frame "
            "down a small-town main street, five brass players in red "
            "uniforms swinging their arms in step, a drum major twirling a "
            "baton out front, onlookers waving from the sidewalk, bright "
            "afternoon light, the camera holds position as the band crosses"),
    },
    "radio": {
        "role": "countable fine structure (tubes, dials, grille)",
        "prompt": (
            "A wooden tabletop valve radio glowing on a workbench, six glass "
            "vacuum tubes visible through the open back panel, a brass dial "
            "with fine tick marks, a woven speaker grille, a small flickering "
            "pilot lamp, gentle drifting dust motes in warm lamplight, slow "
            "subtle shimmer of the tube filaments, single continuous shot"),
    },
}

CONTRAST = {"lora.strength_model": HALF}

VERDICT_MATRIX = {
    "structural_regression": ("an arm with materially more structural defects "
                              "(melted faces, broken limbs, collapsed objects) "
                              "LOSES regardless of sharpness"),
    "coherence_hold_plus_material_gain": "candidate WIN -> refutation panel",
    "null_at_shipping_output": "LOSS for the candidate; shipped 0.7 stands",
    "motion_collapse": ("if either arm fails to produce the demanded march "
                        "motion, that is a countable finding on that arm, "
                        "judged by temporal receipts AND seats"),
    "notes": [
        "No conditioning still exists on a t2v lane, so 12.121's input-purity "
        "receipt reduces to: the prompt is the only shared input, identical "
        "in both arms, and each fixture's questions ask only about content "
        "the prompt itself demands.",
        "Expected knob axis: LoRA strength trades detail against overcooking. "
        "Questions count resolvable structure and defects, never 'prettier'.",
        "Arm-to-arm NCC is a divergence flag only; a t2v pair at different "
        "LoRA strengths may legitimately compose different scenes from the "
        "same seed -- if scenes diverge fully, seats judge each arm against "
        "the PROMPT's countable demands rather than against each other.",
    ],
}


def main() -> int:
    base, provenance = diffomatic.build_api_graph(
        ENGINE, allow_local=frozenset({"sigmas"}))

    for node_id in ("lora", "sigmas", "noise", "vaedecode", "pos", "latent"):
        if node_id not in base:
            raise SystemExit("[FAIL] expected node %r missing" % node_id)
    if base["lora"]["inputs"]["strength_model"] != 0.7:
        raise SystemExit("[FAIL] shipped strength is %r, expected 0.7"
                         % base["lora"]["inputs"]["strength_model"])
    if base["sigmas"]["class_type"] != "_SigmasFromValues":
        raise SystemExit("[FAIL] sigmas node is %r; ADAPT note is stale"
                         % base["sigmas"]["class_type"])

    # ADAPT 1: local sigma injector -> registered ManualSigmas, same values,
    # comma-joined string (the form lane 2 proved over the API).
    values = base["sigmas"]["inputs"].pop("values")
    if len(values) != 9:
        raise SystemExit("[FAIL] expected 9 distilled sigmas, got %d" % len(values))
    base["sigmas"] = {"class_type": "ManualSigmas",
                      "inputs": {"sigmas": ", ".join(repr(float(v)) for v in values)}}

    all_hashes = {}
    for key in sorted(FIXTURES):
        spec = FIXTURES[key]
        out_dir = HERE / key
        out_dir.mkdir(exist_ok=True)
        prepared = copy.deepcopy(base)
        prepared["pos"]["inputs"]["text"] = spec["prompt"]

        written = {}
        for arm in ("ours", "half"):
            graph = copy.deepcopy(prepared)
            if arm == "half":
                graph["lora"]["inputs"]["strength_model"] = HALF
            text = json.dumps(graph, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
            path = out_dir / ("arm_%s.json" % arm)
            io.open(path, "w", encoding="utf-8", newline="\n").write(text)
            written[arm] = hashlib.sha256(text.encode("utf-8")).hexdigest()
            print("[STAGED] %-9s %-16s sha256=%s nodes=%d"
                  % (key, path.name, written[arm][:16], len(graph)))
        all_hashes[key] = written

        io.open(out_dir / "ARMS.sha256", "w", encoding="utf-8", newline="\n").write(
            "".join("%s  arm_%s.json\n" % (written[a], a) for a in ("ours", "half")))
        io.open(out_dir / "STAGING.json", "w", encoding="utf-8", newline="\n").write(
            json.dumps({
                "lane": "lane3_ltx_video", "fixture": key, "engine": ENGINE,
                "role": spec["role"], "prompt": spec["prompt"],
                "declared_contrast": CONTRAST,
                "same_lora_file_both_arms": base["lora"]["inputs"]["lora_name"],
                "bound": ("official pairs 0.5 with the download-gated rank-111 "
                          "LoRA; this lane tests strength on OUR file only"),
                "shared_adapts": [{
                    "node": "sigmas",
                    "engine_authors": "_SigmasFromValues (local class, values list)",
                    "staged_as": "ManualSigmas (registered), comma-joined string",
                    "why": "Bible 12.122; the lane 2 refine_sigmas precedent",
                }],
                "arm_sha256": written,
            }, indent=2, sort_keys=True, ensure_ascii=False) + "\n")

    io.open(HERE / "LANE.json", "w", encoding="utf-8", newline="\n").write(
        json.dumps({"lane": "lane3_ltx_video", "engine": ENGINE,
                    "provenance": provenance,
                    "declared_contrast": CONTRAST,
                    "verdict_matrix": VERDICT_MATRIX,
                    "fixtures": {k: {"role": v["role"], "output_subdir": k}
                                 for k, v in FIXTURES.items()},
                    "arm_sha256": all_hashes},
                   indent=2, sort_keys=True, ensure_ascii=False) + "\n")

    print("[OURS] lora.strength_model 0.7 (shipped)")
    print("[HALF] lora.strength_model 0.5 (fleet-diff reference value, our file)")
    print("[ADAPT] sigmas -> ManualSigmas in BOTH arms (9 distilled sigmas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
