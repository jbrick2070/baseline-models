"""Stage lane 1: wan_ti2v -- the official sampling recipe against ours.

Both arms are generated FROM THE SHIPPING ENGINE (``eng_wan_ti2v`` via the
differ's own engine resolver), so weights, tiling, encoder, canvas, length and
topology are identical BY CONSTRUCTION rather than by careful copying. Arm
OFFICIAL then applies exactly the three knobs the fleet diff surfaced --
sampler ``uni_pc``, 20 steps, shift 8. Arm OURS applies nothing.

The contrast is the SAMPLING RECIPE AS A BUNDLE: it is a screen, not a
forensic decomposition. If the bundle wins, the knobs get separated afterwards;
decomposing a bundle that loses buys three renders of nothing.

Why the graph comes from ``build_api_graph`` and not from a ``LoadedGraph``:
the differ's node params are a COMPARISON form -- nested dicts flattened to
dotted keys, empty containers dropped, wires lifted out into ``edges``. Rebuilt
into an arm they would carry quietly altered literals, which is precisely the
uncontrolled second variable Bible 12.121 was promoted for.

The prompt DESCRIBES the conditioning still (an officer close-up against
``portrait_16_9.png``), because 12.121's second instance was an A/B whose
prompt contradicted its own still and so scored both arms on obedience to the
prompt instead of on the knob under test.
"""
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
FIXTURE = "portrait_16_9.png"
FIXTURE_SHA256 = "4fd6479da40a215ffda4867373ad330d6d45ab4bd34ffe3ad4c0db4fce40e375"
PROMPT = ("1950s black and white cinematic close-up of a military officer's "
          "face, facing the camera, holding his gaze steady, only subtle "
          "breathing and a slight head movement, static locked-off camera, "
          "single continuous shot, no cut, no scene change, no camera move.")

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
        raise SystemExit(f"[FAIL] expected exactly one {class_type}, found {hits}")
    return hits[0]


def main():
    base, provenance = diffomatic.build_api_graph(ENGINE)

    # Shared inputs: identical in both arms, and both aligned with the question.
    load_image = sole(base, "LoadImage")
    base[load_image]["inputs"]["image"] = FIXTURE
    ksampler = sole(base, "KSampler")
    model_sampling = sole(base, "ModelSamplingSD3")
    # The positive encoder is whichever node KSampler.positive is wired to --
    # there are two CLIPTextEncode nodes and only the wire says which is which.
    positive = base[ksampler]["inputs"]["positive"][0]
    base[positive]["inputs"]["text"] = PROMPT

    if ksampler != "ksampler" or model_sampling != "modelsampling":
        raise SystemExit(
            f"[FAIL] node ids moved: KSampler={ksampler!r} "
            f"ModelSamplingSD3={model_sampling!r}; CONTRAST keys are stale"
        )

    ours_recipe = {
        "ksampler.sampler_name": base[ksampler]["inputs"]["sampler_name"],
        "ksampler.steps": base[ksampler]["inputs"]["steps"],
        "modelsampling.shift": base[model_sampling]["inputs"]["shift"],
    }
    for key, official in CONTRAST.items():
        if ours_recipe[key] == official:
            raise SystemExit(
                f"[FAIL] {key} is already {official!r} in the shipping engine; "
                "that knob is not a contrast and the lane must be re-declared"
            )

    written = {}
    for arm in ("ours", "official"):
        graph = copy.deepcopy(base)
        if arm == "official":
            graph[ksampler]["inputs"]["sampler_name"] = CONTRAST["ksampler.sampler_name"]
            graph[ksampler]["inputs"]["steps"] = CONTRAST["ksampler.steps"]
            graph[model_sampling]["inputs"]["shift"] = CONTRAST["modelsampling.shift"]
        text = json.dumps(graph, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        path = HERE / f"arm_{arm}.json"
        io.open(path, "w", encoding="utf-8", newline="\n").write(text)
        written[arm] = hashlib.sha256(text.encode("utf-8")).hexdigest()
        print(f"[STAGED] {path.name}  sha256={written[arm][:16]}  nodes={len(graph)}")

    io.open(HERE / "ARMS.sha256", "w", encoding="utf-8", newline="\n").write(
        "".join(f"{written[arm]}  arm_{arm}.json\n" for arm in ("ours", "official")))

    receipt = {
        "lane": "lane1_wan_ti2v",
        "engine": ENGINE,
        "provenance": provenance,
        "fixture": {"image": FIXTURE, "sha256": FIXTURE_SHA256},
        "prompt": PROMPT,
        "declared_contrast": CONTRAST,
        "ours_recipe": ours_recipe,
        "arm_sha256": written,
        "note": ("Seeds are applied identically to BOTH arms at render time; "
                 "the staged arms carry the engine's own fixture seed."),
    }
    io.open(HERE / "STAGING.json", "w", encoding="utf-8", newline="\n").write(
        json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n")

    print(f"[OURS]     {ours_recipe}")
    print(f"[OFFICIAL] {CONTRAST}")
    print("[CONTRAST] official-vs-ours = "
          "{KSampler.sampler_name, KSampler.steps, ModelSamplingSD3.shift} ONLY")


if __name__ == "__main__":
    main()
