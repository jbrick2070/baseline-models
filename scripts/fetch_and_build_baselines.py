"""
Fetch official upstream baseline workflows, adapt them for on-disk models,
and output structured baseline JSONs and metadata.
"""
from __future__ import annotations

import json
import urllib.request
from copy import deepcopy
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINES_DIR = ROOT / "baselines"
SOURCE_ORIGINAL_DIR = BASELINES_DIR / "source_original"
ADAPTED_DIR = BASELINES_DIR / "adapted"
METADATA_DIR = BASELINES_DIR / "metadata"

SOURCES = {
    "baseline_flux_dev": {
        "url": "https://raw.githubusercontent.com/Comfy-Org/workflow_templates/refs/heads/main/templates/flux_dev_checkpoint_example.json",
        "title": "FLUX.1 [dev] Minimal Checkpoint Baseline",
        "model_category": "Image",
        "target_model": "checkpoints/flux1-dev-fp8.safetensors",
        "vram_estimate_gb": 12.5,
        "loader_node": "CheckpointLoaderSimple",
        "status": "RUNNABLE_LOCAL",
    },
    "baseline_ltx_2b_v0.9": {
        "url": "https://comfyanonymous.github.io/ComfyUI_examples/ltxv/ltxv_text_to_video_0.9.5.json",
        "title": "LTX-Video 2B v0.9 Text-to-Video Baseline",
        "model_category": "Video",
        "target_model": "checkpoints/ltx-video-2b-v0.9.safetensors",
        "vram_estimate_gb": 9.5,
        "loader_node": "CheckpointLoaderSimple",
        "status": "RUNNABLE_LOCAL",
    },
    "baseline_hunyuan3d_v2_mv": {
        "url": "https://raw.githubusercontent.com/Comfy-Org/workflow_templates/refs/heads/main/templates/3d_hunyuan3d_multiview_to_model.json",
        "title": "Hunyuan3D-2 Multiview-to-3D Baseline",
        "model_category": "3D",
        "target_model": "checkpoints/hunyuan3d-dit-v2-mv.safetensors",
        "vram_estimate_gb": 11.0,
        "loader_node": "ImageOnlyCheckpointLoader",
        "status": "RUNNABLE_LOCAL",
    },
    "baseline_wan2_2_ti2v_5b": {
        "url": "https://raw.githubusercontent.com/Comfy-Org/workflow_templates/refs/heads/main/templates/video_wan2_2_5B_ti2v.json",
        "title": "Wan2.2 TI2V-5B Text+Image-to-Video GGUF Baseline",
        "model_category": "Video",
        "target_model": "diffusion_models/Wan2.2-TI2V-5B-Q5_K_M.gguf",
        "vram_estimate_gb": 8.0,
        "loader_node": "UnetLoaderGGUF",
        "status": "RUNNABLE_LOCAL",
    },
    "baseline_wan2_2_14b_i2v": {
        "url": "https://raw.githubusercontent.com/Comfy-Org/workflow_templates/refs/heads/main/templates/video_wan2_2_14B_i2v.json",
        "title": "Wan2.2 I2V-14B Image-to-Video (Low Noise Expert) Baseline",
        "model_category": "Video",
        "target_model": "diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors",
        "vram_estimate_gb": 14.5,
        "loader_node": "UNETLoader",
        "status": "PARTIAL_EXPERT_PRESENT",
    },
    "baseline_humo_17b": {
        "url": "https://raw.githubusercontent.com/Comfy-Org/workflow_templates/refs/heads/main/templates/video_humo.json",
        "title": "HuMo 17B Video Baseline",
        "model_category": "Video",
        "target_model": "diffusion_models/humo_17B_fp8_e4m3fn.safetensors",
        "vram_estimate_gb": 15.0,
        "loader_node": "UNETLoader",
        "status": "RUNNABLE_LOCAL",
    },
    "baseline_ltx2_3_distilled_1_1": {
        "url": "https://raw.githubusercontent.com/Lightricks/ComfyUI-LTXVideo/refs/heads/master/example_workflows/2.3/LTX-2.3_T2V_I2V_Single_Stage_Distilled_Full.json",
        "title": "LTX-2.3 22B Distilled-1.1 GGUF Baseline",
        "model_category": "Video",
        "target_model": "unet/distilled-1.1/ltx-2.3-22b-distilled-1.1-Q3_K_M.gguf",
        "vram_estimate_gb": 11.5,
        "loader_node": "UnetLoaderGGUF",
        "status": "RUNNABLE_LOCAL",
    },
    "baseline_ltx2_3_dev_t2v": {
        "url": "https://raw.githubusercontent.com/Comfy-Org/workflow_templates/refs/heads/main/templates/video_ltx2_3_t2v.json",
        "title": "LTX-2.3 22B Dev Text-to-Video (Reference Source)",
        "model_category": "Video",
        "target_model": "unet/ltx-2.3-22b-dev-Q3_K_M.gguf",
        "vram_estimate_gb": 12.0,
        "loader_node": "UnetLoaderGGUF",
        "status": "ADAPTED_FOR_GGUF",
    },
    "baseline_wanmove_480p": {
        "url": "https://raw.githubusercontent.com/Comfy-Org/workflow_templates/refs/heads/main/templates/video_wanmove_480p.json",
        "title": "WanMove 480p Baseline (Reference)",
        "model_category": "Video",
        "target_model": "Wan21-WanMove_fp8_scaled_e4m3fn_KJ.safetensors",
        "vram_estimate_gb": 14.0,
        "loader_node": "UNETLoader",
        "status": "REFERENCE_ONLY_WEIGHTS_NOT_INSTALLED",
    },
    "baseline_trellis2_meshonly": {
        "url": "https://raw.githubusercontent.com/visualbruno/ComfyUI-Trellis2/main/example_workflows/MeshOnly.json",
        "title": "Trellis2 MeshOnly 3D Baseline (Reference)",
        "model_category": "3D",
        "target_model": "trellis2 weights",
        "vram_estimate_gb": 18.0,
        "loader_node": "Trellis2ModelLoader",
        "status": "REFERENCE_ONLY_EXCEEDS_VRAM",
    },
}

LOCAL_SUBSTITUTIONS = {
    "baseline_ltx_2b_v0.9": {
        "CheckpointLoaderSimple": {"ltx-video-2b-v0.9.5.safetensors": "ltx-video-2b-v0.9.safetensors"},
    },
    "baseline_hunyuan3d_v2_mv": {
        "ImageOnlyCheckpointLoader": {"hunyuan3d-dit-v2-mv_fp16.safetensors": "hunyuan3d-dit-v2-mv.safetensors"},
    },
    "baseline_wan2_2_ti2v_5b": {
        "UNETLoader": {"wan2.2_ti2v_5B_fp16.safetensors": "Wan2.2-TI2V-5B-Q5_K_M.gguf"},
    },
}


def fetch_url(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "baseline-models/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def iter_nodes(data: dict):
    for n in data.get("nodes", []) or []:
        yield n
    subgraphs = (data.get("definitions") or {}).get("subgraphs", []) or []
    for sg in subgraphs:
        for n in sg.get("nodes", []) or []:
            yield n


def adapt_graph(key: str, data: dict) -> list[str]:
    changes = []
    subs = LOCAL_SUBSTITUTIONS.get(key, {})
    for node in iter_nodes(data):
        ntype = node.get("type")
        vals = node.get("widgets_values")
        if not vals:
            continue

        if ntype in subs:
            old_val = str(vals[0])
            new_val = subs[ntype].get(old_val)
            if new_val:
                vals[0] = new_val
                changes.append(f"{ntype}: {old_val} -> {new_val}")
                if key == "baseline_wan2_2_ti2v_5b" and ntype == "UNETLoader":
                    node["type"] = "UnetLoaderGGUF"
                    node.setdefault("properties", {})["Node name for S&R"] = "UnetLoaderGGUF"
                    node["widgets_values"] = [new_val]
                    changes.append("Changed UNETLoader to UnetLoaderGGUF")

        # Standardize save paths to baseline-models/output
        if ntype in {"SaveVideo", "SaveAnimatedWEBP", "SaveWEBM", "SaveImage", "SaveGLB", "SaveAudio"}:
            vals[0] = f"baseline_output/{key}"
            changes.append(f"{ntype} output path set to baseline_output/{key}")

    return changes


def validate_top_level_links(data: dict) -> list[str]:
    nodes = data.get("nodes", []) or []
    links = data.get("links", []) or []
    link_ids = {l[0] for l in links if isinstance(l, list) and l}
    errors = []
    for n in nodes:
        nid = n.get("id")
        for inp in n.get("inputs", []) or []:
            lid = inp.get("link")
            if lid is not None and lid not in link_ids:
                errors.append(f"Node {nid} ({n.get('type')}) input '{inp.get('name')}' dangling link {lid}")
        for out in n.get("outputs", []) or []:
            for lid in out.get("links") or []:
                if lid not in link_ids:
                    errors.append(f"Node {nid} ({n.get('type')}) output '{out.get('name')}' dangling link {lid}")
    return errors


def main() -> int:
    SOURCE_ORIGINAL_DIR.mkdir(parents=True, exist_ok=True)
    ADAPTED_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    summary = {
        "generated_date": date.today().isoformat(),
        "total_sources": len(SOURCES),
        "successful_fetches": 0,
        "adapted_graphs": 0,
        "link_errors": {},
    }

    print(f"Starting fetch and build for {len(SOURCES)} baseline graphs...")

    for key, spec in SOURCES.items():
        print(f"\nProcessing [{key}]...")
        try:
            raw_data = fetch_url(spec["url"])
            source_file = SOURCE_ORIGINAL_DIR / f"{key}.json"
            source_file.write_text(json.dumps(raw_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            summary["successful_fetches"] += 1
            print(f"  Saved pristine source: {source_file.name}")

            adapted = deepcopy(raw_data)
            changes = adapt_graph(key, adapted)
            adapted_file = ADAPTED_DIR / f"{key}.json"
            adapted_file.write_text(json.dumps(adapted, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            summary["adapted_graphs"] += 1
            print(f"  Saved adapted graph: {adapted_file.name} ({len(changes)} adaptations)")

            errors = validate_top_level_links(adapted)
            if errors:
                summary["link_errors"][key] = errors
                print(f"  WARNING: {len(errors)} dangling link errors found!")
            else:
                print("  Link integrity: OK (0 dangling links)")

            meta = {
                "key": key,
                "title": spec["title"],
                "model_category": spec["model_category"],
                "target_model": spec["target_model"],
                "vram_estimate_gb": spec["vram_estimate_gb"],
                "vram_rtx5080_sustainable": spec["vram_estimate_gb"] <= 14.5,
                "loader_node": spec["loader_node"],
                "status": spec["status"],
                "upstream_source_url": spec["url"],
                "adaptations_applied": changes,
                "link_error_count": len(errors),
            }
            meta_file = METADATA_DIR / f"{key}.json"
            meta_file.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        except Exception as e:
            print(f"  ERROR processing {key}: {e}")

    summary_file = BASELINES_DIR / "FETCH_SUMMARY.json"
    summary_file.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nCompleted baseline fetch & build. Summary written to {summary_file}")
    return 0


if __name__ == "__main__":
    main()
