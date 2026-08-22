"""Still-canvas review: production's 1472x832 against a native 1920x1080 mint.

WHY THIS IS NOT A 2K UPGRADE. The operator declined the official 2K utility
("maybe for 2.5"). This is a different and cheaper question: the still spine is
already minted ABOVE every video canvas -- a sample of 80 recent production
stills is dominated by 1472x832, against video canvases of 1024x576 (ltx_video),
832x480 (wan_ti2v) and 1664x960 (ltx25). So supersampling already happens. The
question is only whether MORE of it is visible after the downscale.

WHY IT MATTERS MORE THAN A VIDEO KNOB. Lane 5 measured frame 1 of an i2v clip
at NCC ~0.999 against its conditioning still: frame one IS the still. Five video
lanes moved knobs downstream of the still and all five came back null. A knob at
the minting stage reaches every clip, every beat, every episode -- and the grid
defect already proved the direction of causation, having been minted by
z_image_turbo and merely preserved by the video lane.

THE CARD BECOMES A PROMPT, because Z-Image generates from text and there is
nothing to inject. So the countable targets are carried by the prompt itself:

  hands    fingers are ground truth -- five per hand, and the classic
           generative failure. The operator asked for hands specifically, and
           the orphan drum he found in lane 3 was a hands-and-objects failure.
  signage  known words on a sign: character-level legibility, the axis the
           lane 4 card measured (it rendered "TI2V" as "TIZV").
  radio    a declared count of glass tubes plus dial ticks: fine repeating
           structure, which is what extra pixels should buy if anything does.

Also folded in, from the lane 1 verdict's open follow-up 5: continuous readouts
alongside quantized ones. On a prompted card that becomes a smooth gradient
demanded beside the stepped elements, so a judge can see where continuous tone
breaks rather than only which discrete step survives.

ARMS: canvas only. Same prompt, same seed, same model, same steps/cfg/shift.
Bound: 1472x832 is 1.769:1 and 1920x1080 is 1.778:1, a 0.5% aspect difference
that is inherent to comparing production's real canvas against true 1080p. It
is recorded rather than hidden; squaring it would mean testing a canvas
production does not use.

usage: run_still_canvas.py [--render]
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
import diffomatic  # noqa: E402

SERVER = "http://127.0.0.1:8000"
# engine -> (params method, graph builder). Both image engines take the same
# (params, wire) shape; only the family-specific method names differ.
ENGINES = {
    "z_image_turbo": ("_zimage_params", "_build_zimage_graph"),
    "flux2_klein": ("_klein_params", "_build_klein_graph"),
}
ENGINE = "z_image_turbo"
OUT_PREFIX = "baseline_output/still_canvas_1080p"
SEEDS = [42, 20260821]
ARMS = {"ours": (1472, 832), "native1080": (1920, 1080)}

FIXTURES = {
    "hands": {
        "countable": "fingers per hand (5), thumbs (1), hands on the microphone (2)",
        "prompt": (
            "1950s radio studio close-up of an announcer's two bare hands "
            "resting on a chrome desk microphone, all ten fingers clearly "
            "visible and separated, fingernails distinct, one hand gripping "
            "the microphone stand and the other flat on the desk beside a "
            "paper script, warm tungsten key light falling across the "
            "knuckles into a smooth continuous shadow gradient on the desk, "
            "sharp focus on the hands"),
    },
    "signage": {
        "countable": "legible characters in ON AIR and in STUDIO B",
        "prompt": (
            "A 1950s radio station corridor, a glowing rectangular sign "
            "reading ON AIR mounted above a door, and a smaller enamel plate "
            "beside the door reading STUDIO B, both signs flat and square to "
            "camera and sharply lit, plain painted wall behind them shading "
            "from bright to dark in a smooth continuous gradient"),
    },
    "testcard": {
        "countable": ("colour bars (7), grey wedge steps (10), concentric "
                      "circles (3), eye-chart rows legible, top row C / "
                      "second row D H K / third row N O R S"),
        # The hardest thing you can ask an image model for: structured
        # graphics, exact quantities, geometry AND text, all at once. Every
        # element has a DECLARED count, so a judge answers by counting rather
        # than by taste. Circles are in here on the operator's own research
        # note -- the EIA-1956 chart tests geometry precisely because models
        # warp circles -- and the eye-chart rows are the axis lane 4 measured
        # when its card rendered "TI2V" as "TIZV".
        "prompt": (
            "A flat 1950s television test card photographed square to camera, "
            "filling the frame. Across the top, exactly seven vertical colour "
            "bars side by side. Below them a horizontal grey step wedge made "
            "of exactly ten distinct grey rectangles going from white on the "
            "left to black on the right. In the centre, three concentric "
            "black circles, perfectly round. On the left, an eye chart of "
            "block letters in rows decreasing in size, the top row reading C, "
            "the second row reading D H K, the third row reading N O R S. On "
            "the right, panels of fine parallel line gratings. Sharp, evenly "
            "lit, high contrast, no perspective distortion"),
    },
    "radio": {
        "countable": "glass tubes (6), dial tick marks, grille weave lines",
        "prompt": (
            "A wooden tabletop valve radio on a workbench with its back panel "
            "open, exactly six glass vacuum tubes standing in a row and "
            "glowing, a brass tuning dial with fine engraved tick marks, a "
            "woven cloth speaker grille with a visible weave, and a smooth "
            "continuous falloff of lamplight across the wooden cabinet from "
            "bright at the left to dark at the right, sharp macro focus"),
    },
}


def post_json(url, payload, timeout=60):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def get_json(url, timeout=90):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def build(engine, mapping, fixture, arm, seed):
    """One concrete API graph: logical classes resolved, canvas applied."""
    width, height = ARMS[arm]
    request = {
        "prompt": FIXTURES[fixture]["prompt"],
        "negative_prompt": "",
        "seed": seed,
        "width": width,
        "height": height,
    }
    params_name, builder_name = ENGINES[ENGINE]
    params = getattr(engine, params_name)(request)
    from nodes._otr_video_engines import wrapper_bridge as bridge  # noqa: E402
    raw = getattr(engine, builder_name)(params, bridge.Wire)

    api = {}
    for node_id, node in raw.items():
        logical = node.get("class")
        choices = mapping.get(logical)
        if not choices:
            raise SystemExit("[FAIL] logical class %r absent from _node_candidates"
                             % logical)
        api[str(node_id)] = {"class_type": choices[0],
                             "inputs": diffomatic._api_inputs(node.get("inputs") or {})
                             if hasattr(diffomatic, "_api_inputs")
                             else _plain(node.get("inputs") or {})}
    return api, params


def _plain(inputs):
    out = {}
    for key, value in inputs.items():
        if isinstance(value, tuple) and len(value) == 2:
            out[key] = [str(value[0]), int(value[1])]
        else:
            out[key] = value
    return out


def main(argv) -> int:
    global ENGINE, OUT_PREFIX
    for a in argv:
        if a.startswith("--engine="):
            ENGINE = a.split("=", 1)[1]
            if ENGINE not in ENGINES:
                raise SystemExit("[FAIL] unknown engine %r" % ENGINE)
            OUT_PREFIX = "baseline_output/still_canvas_1080p_%s" % ENGINE
    do_render = "--render" in argv
    # Render one fixture without re-minting the rest: a re-run of a
    # completed fixture would overwrite receipts that other numbers cite.
    only = [a for a in argv if not a.startswith("--")]
    wanted = [f for f in FIXTURES if not only or f in only]
    with diffomatic._isolated_otr_nodes(diffomatic.OTR_ROOT):
        import importlib
        registry = importlib.import_module("nodes._otr_image_engines.registry")
        engine = registry.get_engine(ENGINE)
        mapping = diffomatic._candidate_map(engine)

        staged = {}
        for fixture in sorted(wanted):
            for arm in sorted(ARMS):
                for seed in SEEDS:
                    api, params = build(engine, mapping, fixture, arm, seed)
                    terminal = [k for k, v in api.items()
                                if "SaveImage" in v["class_type"]]
                    if not terminal:
                        decode = [k for k, v in api.items()
                                  if "VAEDecode" in v["class_type"]]
                        if not decode:
                            raise SystemExit("[FAIL] no decoder to save from")
                        api["save"] = {"class_type": "SaveImage", "inputs": {
                            "images": [decode[0], 0],
                            "filename_prefix": "%s/%s/%s_seed%d/still"
                                               % (OUT_PREFIX, fixture, arm, seed)}}
                    key = "%s/%s/seed%d" % (fixture, arm, seed)
                    text = json.dumps(api, indent=2, sort_keys=True,
                                      ensure_ascii=False) + "\n"
                    staged[key] = {"graph": api,
                                   "sha256": hashlib.sha256(
                                       text.encode("utf-8")).hexdigest(),
                                   "canvas": list(ARMS[arm])}
                    actual = (api.get("latent", {}).get("inputs", {}).get("width"),
                              api.get("latent", {}).get("inputs", {}).get("height"))
                    # Engines may SNAP the requested canvas (flux2_klein rounds
                    # to multiples of 16, and 1080 is not one). Report what the
                    # graph actually carries, never what we asked for.
                    note = ""
                    if list(actual) != list(ARMS[arm]):
                        note = "  ASKED %dx%d" % ARMS[arm]
                    print("[STAGED] %-32s %sx%s nodes=%d sha=%s%s"
                          % (key, actual[0], actual[1], len(api),
                             staged[key]["sha256"][:12], note))

    # PURITY: within a fixture+seed, the two arms may differ ONLY by canvas
    # (and the destination). Anything else is a staging fault.
    for fixture in sorted(wanted):
        for seed in SEEDS:
            a = staged["%s/ours/seed%d" % (fixture, seed)]["graph"]
            b = staged["%s/native1080/seed%d" % (fixture, seed)]["graph"]
            diff = []
            for node_id in sorted(set(a) | set(b)):
                ai, bi = a.get(node_id, {}), b.get(node_id, {})
                for field in sorted(set(ai.get("inputs", {})) | set(bi.get("inputs", {}))):
                    av = ai.get("inputs", {}).get(field)
                    bv = bi.get("inputs", {}).get(field)
                    if av != bv:
                        diff.append("%s.%s" % (node_id, field))
            # The canvas is ONE declared knob, but engines carry it in
            # different numbers of nodes: FLUX.2 also feeds width/height
            # to Flux2Scheduler. Declaring those is not a loosening --
            # every leaf here is the canvas, and anything else still fails.
            allowed = {"latent.width", "latent.height",
                       "scheduler.width", "scheduler.height",
                       "save.filename_prefix"}
            unexpected = [d for d in diff if d not in allowed]
            status = "PURE" if not unexpected else "IMPURE %s" % unexpected
            print("[PURITY] %-22s seed %-9d changed=%s -> %s"
                  % (fixture, seed, diff, status))
            if unexpected:
                return 1

    io.open(HERE / "STAGED.json", "w", encoding="utf-8", newline="\n").write(
        json.dumps({"engine": ENGINE, "arms": {k: list(v) for k, v in ARMS.items()},
                    "seeds": SEEDS,
                    "fixtures": {k: FIXTURES[k]["countable"] for k in FIXTURES},
                    "sha256": {k: v["sha256"] for k, v in staged.items()}},
                   indent=2, sort_keys=True, ensure_ascii=False) + "\n")

    if not do_render:
        print("\n[DRY] staged only. Re-run with --render to mint.")
        return 0

    results = []
    for key in sorted(staged):
        graph = staged[key]["graph"]
        started = time.time()
        try:
            queued = post_json("%s/prompt" % SERVER, {"prompt": graph})
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:800]
            print("[FAULT] %s rejected: %s" % (key, detail))
            results.append({"leg": key, "status": "REJECTED", "detail": detail})
            continue
        prompt_id = queued.get("prompt_id")
        while True:
            time.sleep(2)
            history = get_json("%s/history/%s" % (SERVER, prompt_id))
            if prompt_id in history:
                break
            if time.time() - started > 900:
                print("[FAULT] %s timeout" % key)
                break
        elapsed = round(time.time() - started, 1)
        print("[MINT] %-32s %5.1fs" % (key, elapsed))
        results.append({"leg": key, "status": "success", "elapsed_s": elapsed,
                        "canvas": staged[key]["canvas"],
                        "sha256": staged[key]["sha256"]})

    io.open(HERE / "RENDER.json", "w", encoding="utf-8", newline="\n").write(
        json.dumps({"server": SERVER, "legs": results}, indent=2,
                   sort_keys=True, ensure_ascii=False) + "\n")
    print("\n[DONE] %d legs" % len(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
