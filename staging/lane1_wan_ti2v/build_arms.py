"""Stage lane 1: wan_ti2v -- the official sampling recipe against ours.

Both arms are generated FROM THE SHIPPING ENGINE (``eng_wan_ti2v`` via the
differ's own engine resolver), so weights, tiling, encoder, canvas, length and
topology are identical BY CONSTRUCTION rather than by careful copying. Arm
OFFICIAL then applies exactly the three knobs the fleet diff surfaced --
sampler ``uni_pc``, 20 steps, shift 8. Arm OURS applies nothing.

The contrast is the SAMPLING RECIPE AS A BUNDLE: a screen, not a forensic
decomposition. If the bundle wins, the knobs get separated afterwards;
decomposing a bundle that loses buys three renders of nothing.

FOUR FIXTURES, because one subject cannot answer the question. The officer
close-up is an easy control -- black and white, flat background, little fine
detail -- and a recipe difference could be genuinely invisible on it. Reporting
"no difference" from that alone would measure the fixture, not the recipe. So
the lane also carries two hard real stills and one authored instrument:

  officer      easy control, already rendered in pass 1
  controlroom  photoreal, five figures at depth, receding dials, hazy gradient
  crowd        illustrated, ~40 faces, glass tubes, a meter scale with ticks
  testcard     the instrument: acuity chart, gratings, bars, both polarities

Every prompt describes its own still, because 12.121's second instance was an
A/B whose prompt contradicted its conditioning and so scored both arms on
obedience to the prompt rather than on the knob under test.

Why the graph comes from ``build_api_graph`` and not from a ``LoadedGraph``:
the differ's node params are a COMPARISON form -- nested dicts flattened to
dotted keys, empty containers dropped, wires lifted into ``edges``. Rebuilt
into an arm they would carry quietly altered literals, which is precisely the
uncontrolled second variable 12.121 was promoted for.
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

STEADY_TAIL = ("static locked-off camera, single continuous shot, no cut, "
               "no scene change, no camera move.")

FIXTURES = {
    "officer": {
        "image": "portrait_16_9.png",
        "output_subdir": "",  # pass 1 rendered before the lane gained subdirs
        "prompt": (
            "1950s black and white cinematic close-up of a military officer's "
            "face, facing the camera, holding his gaze steady, only subtle "
            "breathing and a slight head movement, " + STEADY_TAIL),
    },
    "controlroom": {
        "image": "lane1_controlroom.png",
        "output_subdir": "controlroom",
        "prompt": (
            "A dim 1950s underground control room in warm amber haze, two "
            "shirt-sleeved operators seated at long banks of round dials "
            "working their controls, a man in a suit standing still in the "
            "centre aisle, pendant lamps overhead, deep perspective receding "
            "to a bright glare at the far end, only subtle breathing, small "
            "hand movements at the consoles and a faint drift of haze, "
            + STEADY_TAIL),
    },
    "crowd": {
        "image": "lane1_crowd.png",
        "output_subdir": "crowd",
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
        "output_subdir": "testcard",
        "prompt": (
            "A 1950s broadcast test card held steady on screen: colour bars "
            "across the top, a grey step wedge, panels of geometric shapes and "
            "rows of block letters in decreasing sizes, fine line gratings, "
            "and a smooth grey gradient, perfectly flat and square to camera, "
            "only the faintest flicker and film grain, nothing moving, "
            + STEADY_TAIL),
    },
}

# The declared contrast set, in the exact form the purity gate asserts against.
CONTRAST = {
    "ksampler.sampler_name": "uni_pc",
    "ksampler.steps": 20,
    "modelsampling.shift": 8.0,
}


def sole(api, class_type):
    """The one node of a class -- ambiguity is a staging fault, not a default."""
    hits = sorted(k for k, v in api.items() if v["class_type"] == class_type)
    if len(hits) != 1:
        raise SystemExit("[FAIL] expected exactly one %s, found %s" % (class_type, hits))
    return hits[0]


def stage_fixture(key, spec, base, ksampler, model_sampling, ours_recipe):
    out_dir = HERE / key
    out_dir.mkdir(exist_ok=True)

    prepared = copy.deepcopy(base)
    prepared[sole(prepared, "LoadImage")]["inputs"]["image"] = spec["image"]
    positive = prepared[ksampler]["inputs"]["positive"][0]
    prepared[positive]["inputs"]["text"] = spec["prompt"]

    written = {}
    for arm in ("ours", "official"):
        graph = copy.deepcopy(prepared)
        if arm == "official":
            graph[ksampler]["inputs"]["sampler_name"] = CONTRAST["ksampler.sampler_name"]
            graph[ksampler]["inputs"]["steps"] = CONTRAST["ksampler.steps"]
            graph[model_sampling]["inputs"]["shift"] = CONTRAST["modelsampling.shift"]
        text = json.dumps(graph, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        path = out_dir / ("arm_%s.json" % arm)
        io.open(path, "w", encoding="utf-8", newline="\n").write(text)
        written[arm] = hashlib.sha256(text.encode("utf-8")).hexdigest()
        print("[STAGED] %-12s %-18s sha256=%s nodes=%d"
              % (key, path.name, written[arm][:16], len(graph)))

    io.open(out_dir / "ARMS.sha256", "w", encoding="utf-8", newline="\n").write(
        "".join("%s  arm_%s.json\n" % (written[arm], arm) for arm in ("ours", "official")))

    receipt = {
        "lane": "lane1_wan_ti2v",
        "fixture": key,
        "engine": ENGINE,
        "image": spec["image"],
        "output_subdir": spec["output_subdir"],
        "prompt": spec["prompt"],
        "declared_contrast": CONTRAST,
        "ours_recipe": ours_recipe,
        "arm_sha256": written,
        "note": ("Seeds are applied identically to BOTH arms at render time; "
                 "the staged arms carry the engine's own fixture seed."),
    }
    io.open(out_dir / "STAGING.json", "w", encoding="utf-8", newline="\n").write(
        json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    return written


def main():
    base, provenance = diffomatic.build_api_graph(ENGINE)
    ksampler = sole(base, "KSampler")
    model_sampling = sole(base, "ModelSamplingSD3")
    if ksampler != "ksampler" or model_sampling != "modelsampling":
        raise SystemExit(
            "[FAIL] node ids moved: KSampler=%r ModelSamplingSD3=%r; CONTRAST keys "
            "are stale" % (ksampler, model_sampling))

    ours_recipe = {
        "ksampler.sampler_name": base[ksampler]["inputs"]["sampler_name"],
        "ksampler.steps": base[ksampler]["inputs"]["steps"],
        "modelsampling.shift": base[model_sampling]["inputs"]["shift"],
    }
    for key, official in CONTRAST.items():
        if ours_recipe[key] == official:
            raise SystemExit(
                "[FAIL] %s is already %r in the shipping engine; that knob is not "
                "a contrast and the lane must be re-declared" % (key, official))

    all_hashes = {}
    for key in sorted(FIXTURES):
        all_hashes[key] = stage_fixture(
            key, FIXTURES[key], base, ksampler, model_sampling, ours_recipe)

    io.open(HERE / "LANE.json", "w", encoding="utf-8", newline="\n").write(
        json.dumps({"lane": "lane1_wan_ti2v", "engine": ENGINE,
                    "provenance": provenance, "declared_contrast": CONTRAST,
                    "ours_recipe": ours_recipe,
                    "fixtures": {k: {"image": v["image"],
                                     "output_subdir": v["output_subdir"]}
                                 for k, v in FIXTURES.items()},
                    "arm_sha256": all_hashes},
                   indent=2, sort_keys=True, ensure_ascii=False) + "\n")

    print("[OURS]     %s" % ours_recipe)
    print("[OFFICIAL] %s" % CONTRAST)
    print("[CONTRAST] official-vs-ours = "
          "{KSampler.sampler_name, KSampler.steps, ModelSamplingSD3.shift} ONLY")


if __name__ == "__main__":
    main()
