"""Measure the lane 4 knob DIRECTLY: the conditioning tensors the two encoders emit.

The video lane observes 97-frame renders through a judge panel whose noise floor
lane 3 measured at ~50% of cells. This script observes the thing actually being
varied. No render, no GPU: both encoders load on CPU.

If the two encoders emit near-identical conditioning for these prompts, a null in
the video lane is GUARANTEED and MEANINGFUL -- "output-equivalent at this canvas"
is a quotable finding. If they diverge materially, the panel has a reason to run.

Writes a JSON receipt; prints a table.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

COMFY_ROOT = Path(r"C:\Users\jeffr\ComfyUI-Installs\ComfyUI\ComfyUI")
OUT = Path(r"C:\Users\jeffr\Documents\ComfyUI\custom_nodes\basline-models"
           r"\staging\lane4_wan_text_encoder\ENCODER_DELTA.json")

OURS = ("CLIPLoaderGGUFCPU", "umt5-xxl-encoder-Q5_K_M.gguf")
OFFICIAL = ("CLIPLoader", "umt5_xxl_fp8_e4m3fn_scaled.safetensors")

STAGING = Path(r"C:\Users\jeffr\Documents\ComfyUI\custom_nodes\basline-models"
               r"\staging\lane4_wan_text_encoder")

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "")
sys.path.insert(0, str(COMFY_ROOT))
os.chdir(COMFY_ROOT)

import torch  # noqa: E402
import folder_paths  # noqa: E402
import nodes  # noqa: E402

# The live server is launched with --user-directory, so it scans the packs under
# Documents\ComfyUI\custom_nodes (ComfyUI-GGUF among them). An in-process import
# sees ONLY the install root's custom_nodes and therefore has no GGUF loader at
# all -- verified: 891 mappings, none of them GGUF. Register the user tree before
# init so this script sees the same node set the render legs ran against.
USER_CUSTOM_NODES = Path(r"C:\Users\jeffr\Documents\ComfyUI\custom_nodes")

# Same story for MODEL paths: the render legs ran under the server's
# --extra-model-paths-config, so the weights live at C:\ComfyUI-Models. Without
# it, get_full_path returns None and the GGUF loader dies on NoneType.endswith.
# Load the SERVER'S OWN yaml rather than hand-registering directories, so this
# measurement resolves the identical files the legs did.
MODEL_PATHS_YAML = Path(r"C:\Users\jeffr\Documents\ComfyUI\custom_nodes"
                        r"\ComfyUI-OldTimeRadio\scripts"
                        r"\_otr_headless_model_paths.yaml")


def init_model_paths():
    if not MODEL_PATHS_YAML.is_file():
        raise SystemExit("[FAIL] model paths yaml missing: %s" % MODEL_PATHS_YAML)
    loader = None
    try:
        from utils.extra_config import load_extra_path_config as loader
    except ImportError:
        try:
            from main import load_extra_path_config as loader  # older layouts
        except ImportError:
            loader = None
    if loader is None:
        raise SystemExit("[FAIL] could not import load_extra_path_config")
    loader(str(MODEL_PATHS_YAML))
    print("[PATH] loaded model paths from %s" % MODEL_PATHS_YAML.name)


def init_custom_nodes():
    """Register custom nodes; the initializer went async in newer ComfyUI."""
    known = [Path(p).resolve()
             for p in folder_paths.get_folder_paths("custom_nodes")]
    if USER_CUSTOM_NODES.resolve() not in known:
        folder_paths.add_model_folder_path("custom_nodes",
                                           str(USER_CUSTOM_NODES))
        print("[PATH] registered %s" % USER_CUSTOM_NODES)
    init = getattr(nodes, "init_extra_nodes", None)
    if init is None:
        return
    result = init()
    if hasattr(result, "__await__"):
        import asyncio
        asyncio.run(result)
    print("[NODES] %d mappings registered" % len(nodes.NODE_CLASS_MAPPINGS))
    for name, _ in (OURS, OFFICIAL):
        if name not in nodes.NODE_CLASS_MAPPINGS:
            raise SystemExit(
                "[FAIL] %r is not registered in-process. The render legs used "
                "the live server's node set; measuring against a different one "
                "would not be the same experiment." % name)


def load_clip(class_name, clip_name):
    cls = nodes.NODE_CLASS_MAPPINGS[class_name]
    fn = getattr(cls(), cls.FUNCTION)
    required = cls.INPUT_TYPES().get("required", {})
    kwargs = {"clip_name": clip_name, "type": "wan"}
    if "device" in (cls.INPUT_TYPES().get("optional") or {}):
        kwargs["device"] = "cpu"
    kwargs = {k: v for k, v in kwargs.items() if k in required or k == "device"}
    print("[LOAD] %-20s %s  kwargs=%s" % (class_name, clip_name, sorted(kwargs)))
    return fn(**kwargs)[0]


def encode(clip, text):
    cls = nodes.NODE_CLASS_MAPPINGS["CLIPTextEncode"]
    out = getattr(cls(), cls.FUNCTION)(clip=clip, text=text)[0]
    tensor = out[0][0]
    return tensor.detach().to(torch.float32).cpu()


def compare(a, b):
    if a.shape != b.shape:
        return {"shape_a": list(a.shape), "shape_b": list(b.shape),
                "comparable": False}
    flat_a, flat_b = a.flatten(), b.flatten()
    diff = (flat_a - flat_b)
    cos = torch.nn.functional.cosine_similarity(flat_a, flat_b, dim=0).item()
    denom = flat_a.abs().mean().item() or 1.0
    return {
        "shape": list(a.shape),
        "comparable": True,
        "cosine_similarity": round(cos, 6),
        "max_abs_diff": round(diff.abs().max().item(), 6),
        "rms_diff": round(diff.pow(2).mean().sqrt().item(), 6),
        "mean_abs_ours": round(flat_a.abs().mean().item(), 6),
        "relative_rms": round(diff.pow(2).mean().sqrt().item() / denom, 6),
    }


def main():
    init_model_paths()
    init_custom_nodes()
    for label, (_, filename) in (("ours", OURS), ("official", OFFICIAL)):
        for key in ("text_encoders", "clip"):
            resolved = folder_paths.get_full_path(key, filename)
            if resolved:
                print("[RESOLVED] %-9s %s -> %s" % (label, key, resolved))
                break
        else:
            raise SystemExit("[FAIL] %s (%s) does not resolve in folder_paths; "
                             "measuring a file the legs did not use would be a "
                             "different experiment" % (label, filename))
    prompts = {}
    for fixture in ("crowd", "testcard_motion"):
        staging = json.loads((STAGING / fixture / "STAGING.json")
                             .read_text(encoding="utf-8"))
        prompts[fixture + "/positive"] = staging["prompt"]
        neg = staging.get("negative")
        if neg:
            prompts[fixture + "/negative"] = neg
    if not any(k.endswith("/negative") for k in prompts):
        prompts["shared/negative"] = ("low quality, worst quality, blurry, "
                                      "distorted, watermark, text, static")

    print("[PROMPTS] %d" % len(prompts))
    results = {}

    clip_ours = load_clip(*OURS)
    enc_ours = {k: encode(clip_ours, v) for k, v in prompts.items()}
    del clip_ours

    clip_off = load_clip(*OFFICIAL)
    enc_off = {k: encode(clip_off, v) for k, v in prompts.items()}
    del clip_off

    print()
    print("%-28s %10s %12s %10s %10s" % ("prompt", "cosine", "rel_rms", "max_abs", "rms"))
    for key in prompts:
        stats = compare(enc_ours[key], enc_off[key])
        results[key] = stats
        if stats.get("comparable"):
            print("%-28s %10.6f %12.6f %10.4f %10.4f"
                  % (key, stats["cosine_similarity"], stats["relative_rms"],
                     stats["max_abs_diff"], stats["rms_diff"]))
        else:
            print("%-28s SHAPE MISMATCH %s vs %s"
                  % (key, stats["shape_a"], stats["shape_b"]))

    receipt = {
        "measurement": "conditioning-tensor delta between the two lane 4 encoders",
        "why": ("the video panel observes renders; this observes the thing the "
                "knob actually varies. A near-identical result makes a video "
                "null meaningful rather than ambiguous."),
        "ours": {"class": OURS[0], "file": OURS[1]},
        "official": {"class": OFFICIAL[0], "file": OFFICIAL[1]},
        "device": "cpu (both arms)",
        "prompts": prompts,
        "results": results,
    }
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True,
                              ensure_ascii=False) + "\n", encoding="utf-8")
    print("\n[RECEIPT] %s" % OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
