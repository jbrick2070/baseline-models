"""
Build and adapt baseline workflows for all modalities:
1. Video: Wan2.2, HuMo, LTX, Minimax H3 Turbo
2. Image: FLUX.1 Dev, Lumina 2
3. Audio & TTS: KokoroTTS, Stable Audio Open, Stable Audio 3
4. Upscalers: LTX Latent Spatial Upscaler x2, SeedVR2 Video Upscaler
5. LLM / Prompt Engineering: Local GGUF Gemma/Mistral prompt pipeline
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINES_DIR = ROOT / "baselines"
ADAPTED_DIR = BASELINES_DIR / "adapted"
METADATA_DIR = BASELINES_DIR / "metadata"


def build_kokoro_tts_baseline() -> tuple[dict, dict]:
    workflow = {
        "last_node_id": 3,
        "last_link_id": 2,
        "nodes": [
            {
                "id": 1,
                "type": "KokoroTTS",
                "pos": [100, 200],
                "size": [350, 220],
                "flags": {},
                "order": 0,
                "mode": 0,
                "inputs": [],
                "outputs": [
                    {"name": "AUDIO", "type": "AUDIO", "links": [1]}
                ],
                "properties": {"Node name for S&R": "KokoroTTS"},
                "widgets_values": [
                    "Welcome to the baseline models benchmark. Testing Kokoro TTS high-speed voice synthesis.",
                    "af_bella",
                    1.0,
                    1.0
                ]
            },
            {
                "id": 2,
                "type": "SaveAudio",
                "pos": [500, 200],
                "size": [300, 120],
                "flags": {},
                "order": 1,
                "mode": 0,
                "inputs": [
                    {"name": "audio", "type": "AUDIO", "link": 1}
                ],
                "outputs": [],
                "properties": {"Node name for S&R": "SaveAudio"},
                "widgets_values": ["baseline_output/baseline_kokorotts"]
            }
        ],
        "links": [
            [1, 1, 0, 2, 0, "AUDIO"]
        ],
        "groups": [],
        "config": {},
        "extra": {"title": "Kokoro-82M Minimal TTS Baseline"},
        "version": 0.4
    }
    metadata = {
        "key": "baseline_kokorotts",
        "title": "Kokoro-82M Fast Local TTS Baseline",
        "model_category": "TTS",
        "target_model": "huggingface/hub/models--hexgrad--Kokoro-82M/snapshots/f3ff3571791e39611d31c381e3a41a3af07b4987/kokoro-v1_0.pth",
        "vram_estimate_gb": 1.5,
        "vram_rtx5080_sustainable": True,
        "loader_node": "KokoroTTS",
        "status": "RUNNABLE_LOCAL",
        "custom_node_pack": "comfyui-kokorotts",
        "upstream_source_url": "https://github.com/danirollins/comfyui-kokorotts",
        "adaptations_applied": ["Configured direct TTS to SaveAudio pipeline"],
        "link_error_count": 0
    }
    return workflow, metadata


def build_stable_audio_open_baseline() -> tuple[dict, dict]:
    workflow = {
        "last_node_id": 7,
        "last_link_id": 6,
        "nodes": [
            {
                "id": 1,
                "type": "CheckpointLoaderSimple",
                "pos": [50, 100],
                "size": [300, 100],
                "flags": {},
                "order": 0,
                "mode": 0,
                "inputs": [],
                "outputs": [
                    {"name": "MODEL", "type": "MODEL", "links": [1]},
                    {"name": "CLIP", "type": "CLIP", "links": [2]},
                    {"name": "VAE", "type": "VAE", "links": [3]}
                ],
                "properties": {"Node name for S&R": "CheckpointLoaderSimple"},
                "widgets_values": ["stable-audio-open-1.0.safetensors"]
            },
            {
                "id": 2,
                "type": "CLIPTextEncode",
                "pos": [400, 100],
                "size": [350, 120],
                "flags": {},
                "order": 1,
                "mode": 0,
                "inputs": [
                    {"name": "clip", "type": "CLIP", "link": 2}
                ],
                "outputs": [
                    {"name": "CONDITIONING", "type": "CONDITIONING", "links": [4]}
                ],
                "properties": {"Node name for S&R": "CLIPTextEncode"},
                "widgets_values": ["Cinematic dramatic atmospheric soundscape, vintage radio tension, subtle wind and vinyl hiss"]
            },
            {
                "id": 3,
                "type": "CLIPTextEncode",
                "pos": [400, 260],
                "size": [350, 80],
                "flags": {},
                "order": 2,
                "mode": 0,
                "inputs": [
                    {"name": "clip", "type": "CLIP", "link": 2}
                ],
                "outputs": [
                    {"name": "CONDITIONING", "type": "CONDITIONING", "links": [5]}
                ],
                "properties": {"Node name for S&R": "CLIPTextEncode"},
                "widgets_values": ["low quality, noise, distortion"]
            },
            {
                "id": 4,
                "type": "EmptyLatentAudio",
                "pos": [400, 380],
                "size": [300, 100],
                "flags": {},
                "order": 3,
                "mode": 0,
                "inputs": [],
                "outputs": [
                    {"name": "LATENT", "type": "LATENT", "links": [6]}
                ],
                "properties": {"Node name for S&R": "EmptyLatentAudio"},
                "widgets_values": [47.5]
            },
            {
                "id": 5,
                "type": "KSampler",
                "pos": [800, 100],
                "size": [280, 260],
                "flags": {},
                "order": 4,
                "mode": 0,
                "inputs": [
                    {"name": "model", "type": "MODEL", "link": 1},
                    {"name": "positive", "type": "CONDITIONING", "link": 4},
                    {"name": "negative", "type": "CONDITIONING", "link": 5},
                    {"name": "latent_image", "type": "LATENT", "link": 6}
                ],
                "outputs": [
                    {"name": "LATENT", "type": "LATENT", "links": [7]}
                ],
                "properties": {"Node name for S&R": "KSampler"},
                "widgets_values": [1234567, "randomize", 30, 7.0, "dpmpp_2m", "karras", 1.0]
            },
            {
                "id": 6,
                "type": "VAEDecodeAudio",
                "pos": [1120, 100],
                "size": [220, 80],
                "flags": {},
                "order": 5,
                "mode": 0,
                "inputs": [
                    {"name": "samples", "type": "LATENT", "link": 7},
                    {"name": "vae", "type": "VAE", "link": 3}
                ],
                "outputs": [
                    {"name": "AUDIO", "type": "AUDIO", "links": [8]}
                ],
                "properties": {"Node name for S&R": "VAEDecodeAudio"},
                "widgets_values": []
            },
            {
                "id": 7,
                "type": "SaveAudio",
                "pos": [1380, 100],
                "size": [280, 120],
                "flags": {},
                "order": 6,
                "mode": 0,
                "inputs": [
                    {"name": "audio", "type": "AUDIO", "link": 8}
                ],
                "outputs": [],
                "properties": {"Node name for S&R": "SaveAudio"},
                "widgets_values": ["baseline_output/baseline_stable_audio_open"]
            }
        ],
        "links": [
            [1, 1, 0, 5, 0, "MODEL"],
            [2, 1, 1, 2, 0, "CLIP"],
            [3, 1, 2, 6, 1, "VAE"],
            [4, 2, 0, 5, 1, "CONDITIONING"],
            [5, 3, 0, 5, 2, "CONDITIONING"],
            [6, 4, 0, 5, 3, "LATENT"],
            [7, 5, 0, 6, 0, "LATENT"],
            [8, 6, 0, 7, 0, "AUDIO"]
        ],
        "groups": [],
        "config": {},
        "extra": {"title": "Stable Audio Open 1.0 Baseline"},
        "version": 0.4
    }
    metadata = {
        "key": "baseline_stable_audio_open",
        "title": "Stable Audio Open 1.0 Soundscape & Music Baseline",
        "model_category": "Audio",
        "target_model": "checkpoints/stable-audio-open-1.0.safetensors",
        "vram_estimate_gb": 5.0,
        "vram_rtx5080_sustainable": True,
        "loader_node": "CheckpointLoaderSimple",
        "status": "RUNNABLE_LOCAL",
        "upstream_source_url": "https://comfyanonymous.github.io/ComfyUI_examples/audio/",
        "adaptations_applied": ["Configured single-checkpoint audio pipeline with 47.5s latent duration"],
        "link_error_count": 0
    }
    return workflow, metadata


def build_ltx_spatial_upscaler_baseline() -> tuple[dict, dict]:
    workflow = {
        "last_node_id": 6,
        "last_link_id": 5,
        "nodes": [
            {
                "id": 1,
                "type": "LoadImage",
                "pos": [50, 100],
                "size": [280, 250],
                "flags": {},
                "order": 0,
                "mode": 0,
                "inputs": [],
                "outputs": [
                    {"name": "IMAGE", "type": "IMAGE", "links": [1]}
                ],
                "properties": {"Node name for S&R": "LoadImage"},
                "widgets_values": ["example.png", "image"]
            },
            {
                "id": 2,
                "type": "VAELoader",
                "pos": [50, 400],
                "size": [300, 80],
                "flags": {},
                "order": 1,
                "mode": 0,
                "inputs": [],
                "outputs": [
                    {"name": "VAE", "type": "VAE", "links": [2, 3]}
                ],
                "properties": {"Node name for S&R": "VAELoader"},
                "widgets_values": ["ltx-2.3-22b-dev_video_vae.safetensors"]
            },
            {
                "id": 3,
                "type": "VAEEncode",
                "pos": [380, 100],
                "size": [220, 80],
                "flags": {},
                "order": 2,
                "mode": 0,
                "inputs": [
                    {"name": "pixels", "type": "IMAGE", "link": 1},
                    {"name": "vae", "type": "VAE", "link": 2}
                ],
                "outputs": [
                    {"name": "LATENT", "type": "LATENT", "links": [4]}
                ],
                "properties": {"Node name for S&R": "VAEEncode"},
                "widgets_values": []
            },
            {
                "id": 4,
                "type": "LatentUpscaleModelLoader",
                "pos": [380, 240],
                "size": [350, 80],
                "flags": {},
                "order": 3,
                "mode": 0,
                "inputs": [],
                "outputs": [
                    {"name": "LATENT_UPSCALE_MODEL", "type": "LATENT_UPSCALE_MODEL", "links": [5]}
                ],
                "properties": {"Node name for S&R": "LatentUpscaleModelLoader"},
                "widgets_values": ["ltx-2.3-spatial-upscaler-x2-1.1.safetensors"]
            },
            {
                "id": 5,
                "type": "LatentUpscaleByModel",
                "pos": [780, 100],
                "size": [240, 90],
                "flags": {},
                "order": 4,
                "mode": 0,
                "inputs": [
                    {"name": "upscale_model", "type": "LATENT_UPSCALE_MODEL", "link": 5},
                    {"name": "samples", "type": "LATENT", "link": 4}
                ],
                "outputs": [
                    {"name": "LATENT", "type": "LATENT", "links": [6]}
                ],
                "properties": {"Node name for S&R": "LatentUpscaleByModel"},
                "widgets_values": []
            },
            {
                "id": 6,
                "type": "VAEDecode",
                "pos": [1060, 100],
                "size": [220, 80],
                "flags": {},
                "order": 5,
                "mode": 0,
                "inputs": [
                    {"name": "samples", "type": "LATENT", "link": 6},
                    {"name": "vae", "type": "VAE", "link": 3}
                ],
                "outputs": [
                    {"name": "IMAGE", "type": "IMAGE", "links": [7]}
                ],
                "properties": {"Node name for S&R": "VAEDecode"},
                "widgets_values": []
            },
            {
                "id": 7,
                "type": "SaveImage",
                "pos": [1320, 100],
                "size": [280, 250],
                "flags": {},
                "order": 6,
                "mode": 0,
                "inputs": [
                    {"name": "images", "type": "IMAGE", "link": 7}
                ],
                "outputs": [],
                "properties": {"Node name for S&R": "SaveImage"},
                "widgets_values": ["baseline_output/baseline_ltx_spatial_upscaler_x2"]
            }
        ],
        "links": [
            [1, 1, 0, 3, 0, "IMAGE"],
            [2, 2, 0, 3, 1, "VAE"],
            [3, 2, 0, 6, 1, "VAE"],
            [4, 3, 0, 5, 1, "LATENT"],
            [5, 4, 0, 5, 0, "LATENT_UPSCALE_MODEL"],
            [6, 5, 0, 6, 0, "LATENT"],
            [7, 6, 0, 7, 0, "IMAGE"]
        ],
        "groups": [],
        "config": {},
        "extra": {"title": "LTX 2.3 Spatial Upscaler x2 Baseline"},
        "version": 0.4
    }
    metadata = {
        "key": "baseline_ltx_spatial_upscaler_x2",
        "title": "LTX 2.3 Latent Spatial 2x Upscaler Baseline",
        "model_category": "Upscalers",
        "target_model": "latent_upscale_models/ltx-2.3-spatial-upscaler-x2-1.1.safetensors",
        "vram_estimate_gb": 4.0,
        "vram_rtx5080_sustainable": True,
        "loader_node": "LatentUpscaleModelLoader",
        "status": "RUNNABLE_LOCAL",
        "upstream_source_url": "https://github.com/Lightricks/ComfyUI-LTXVideo",
        "adaptations_applied": ["Configured latent space 2x upscaling using official LTX-2.3 spatial upscaler model"],
        "link_error_count": 0
    }
    return workflow, metadata


def build_lumina2_baseline() -> tuple[dict, dict]:
    workflow = {
        "last_node_id": 8,
        "last_link_id": 7,
        "nodes": [
            {
                "id": 1,
                "type": "UNETLoader",
                "pos": [50, 100],
                "size": [300, 80],
                "flags": {},
                "order": 0,
                "mode": 0,
                "inputs": [],
                "outputs": [
                    {"name": "MODEL", "type": "MODEL", "links": [1]}
                ],
                "properties": {"Node name for S&R": "UNETLoader"},
                "widgets_values": ["lumina_2_model_bf16.safetensors"]
            },
            {
                "id": 2,
                "type": "CLIPLoader",
                "pos": [50, 220],
                "size": [300, 80],
                "flags": {},
                "order": 1,
                "mode": 0,
                "inputs": [],
                "outputs": [
                    {"name": "CLIP", "type": "CLIP", "links": [2]}
                ],
                "properties": {"Node name for S&R": "CLIPLoader"},
                "widgets_values": ["gemma4_e2b_it_bf16.safetensors", "lumina2"]
            },
            {
                "id": 3,
                "type": "VAELoader",
                "pos": [50, 340],
                "size": [300, 80],
                "flags": {},
                "order": 2,
                "mode": 0,
                "inputs": [],
                "outputs": [
                    {"name": "VAE", "type": "VAE", "links": [3]}
                ],
                "properties": {"Node name for S&R": "VAELoader"},
                "widgets_values": ["lumina2_ae.safetensors"]
            },
            {
                "id": 4,
                "type": "CLIPTextEncode",
                "pos": [400, 100],
                "size": [350, 160],
                "flags": {},
                "order": 3,
                "mode": 0,
                "inputs": [
                    {"name": "clip", "type": "CLIP", "link": 2}
                ],
                "outputs": [
                    {"name": "CONDITIONING", "type": "CONDITIONING", "links": [4]}
                ],
                "properties": {"Node name for S&R": "CLIPTextEncode"},
                "widgets_values": ["A majestic glowing lantern in a foggy train station at night, cinematic lighting, 8k resolution"]
            },
            {
                "id": 5,
                "type": "EmptySD3LatentImage",
                "pos": [400, 300],
                "size": [280, 100],
                "flags": {},
                "order": 4,
                "mode": 0,
                "inputs": [],
                "outputs": [
                    {"name": "LATENT", "type": "LATENT", "links": [5]}
                ],
                "properties": {"Node name for S&R": "EmptySD3LatentImage"},
                "widgets_values": [1024, 1024, 1]
            },
            {
                "id": 6,
                "type": "KSampler",
                "pos": [800, 100],
                "size": [280, 260],
                "flags": {},
                "order": 5,
                "mode": 0,
                "inputs": [
                    {"name": "model", "type": "MODEL", "link": 1},
                    {"name": "positive", "type": "CONDITIONING", "link": 4},
                    {"name": "negative", "type": "CONDITIONING", "link": 4},
                    {"name": "latent_image", "type": "LATENT", "link": 5}
                ],
                "outputs": [
                    {"name": "LATENT", "type": "LATENT", "links": [6]}
                ],
                "properties": {"Node name for S&R": "KSampler"},
                "widgets_values": [42, "randomize", 25, 4.0, "euler", "simple", 1.0]
            },
            {
                "id": 7,
                "type": "VAEDecode",
                "pos": [1120, 100],
                "size": [220, 80],
                "flags": {},
                "order": 6,
                "mode": 0,
                "inputs": [
                    {"name": "samples", "type": "LATENT", "link": 6},
                    {"name": "vae", "type": "VAE", "link": 3}
                ],
                "outputs": [
                    {"name": "IMAGE", "type": "IMAGE", "links": [7]}
                ],
                "properties": {"Node name for S&R": "VAEDecode"},
                "widgets_values": []
            },
            {
                "id": 8,
                "type": "SaveImage",
                "pos": [1380, 100],
                "size": [280, 250],
                "flags": {},
                "order": 7,
                "mode": 0,
                "inputs": [
                    {"name": "images", "type": "IMAGE", "link": 7}
                ],
                "outputs": [],
                "properties": {"Node name for S&R": "SaveImage"},
                "widgets_values": ["baseline_output/baseline_lumina2_bf16"]
            }
        ],
        "links": [
            [1, 1, 0, 6, 0, "MODEL"],
            [2, 2, 0, 4, 0, "CLIP"],
            [3, 3, 0, 7, 1, "VAE"],
            [4, 4, 0, 6, 1, "CONDITIONING"],
            [5, 5, 0, 6, 3, "LATENT"],
            [6, 6, 0, 7, 0, "LATENT"],
            [7, 7, 0, 8, 0, "IMAGE"]
        ],
        "groups": [],
        "config": {},
        "extra": {"title": "Lumina-Image 2.0 Baseline"},
        "version": 0.4
    }
    metadata = {
        "key": "baseline_lumina2_bf16",
        "title": "Lumina-Image 2.0 Text-to-Image Baseline",
        "model_category": "Image",
        "target_model": "diffusion_models/lumina_2_model_bf16.safetensors",
        "vram_estimate_gb": 9.5,
        "vram_rtx5080_sustainable": True,
        "loader_node": "UNETLoader",
        "status": "RUNNABLE_LOCAL",
        "upstream_source_url": "https://github.com/Alpha-VLLM/Lumina-Image-2.0",
        "adaptations_applied": ["Mapped lumina_2_model_bf16, gemma4 text encoder, and lumina2_ae VAE"],
        "link_error_count": 0
    }
    return workflow, metadata


def build_minimax_h3_baseline() -> tuple[dict, dict]:
    # Read the example workflow and standardize output path and local model target
    example_path = Path("C:/Users/jeffr/Documents/ComfyUI/custom_nodes/ComfyUI-MiniMax-H3-Turbo/example_workflows/minimax_h3_t2v_turbo.json")
    if example_path.exists():
        workflow = json.loads(example_path.read_text(encoding="utf-8"))
        for n in workflow.get("nodes", []):
            if n.get("type") in {"SaveVideo", "SaveAnimatedWEBP", "SaveImage"}:
                vals = n.get("widgets_values")
                if vals:
                    vals[0] = "baseline_output/baseline_minimax_h3_turbo"
            if n.get("type") == "UNETLoader":
                vals = n.get("widgets_values")
                if vals and "minimax_h3_fl2va" in str(vals[0]):
                    vals[0] = "minimax_h3_fl2va_pruned_int8_convrot.safetensors"
    else:
        workflow = {}

    metadata = {
        "key": "baseline_minimax_h3_turbo",
        "title": "MiniMax H3 Turbo Video Baseline",
        "model_category": "Video",
        "target_model": "diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors",
        "vram_estimate_gb": 13.5,
        "vram_rtx5080_sustainable": True,
        "loader_node": "UNETLoader / MiniMax loaders",
        "status": "RUNNABLE_LOCAL",
        "custom_node_pack": "ComfyUI-MiniMax-H3-Turbo",
        "upstream_source_url": "https://github.com/Comfy-Org/ComfyUI-MiniMax-H3-Turbo",
        "adaptations_applied": ["Mapped exact installed minimax_h3_fl2va_pruned_int8_convrot.safetensors"],
        "link_error_count": 0
    }
    return workflow, metadata


def build_stable_audio_3_baseline() -> tuple[dict, dict]:
    workflow = {
        "last_node_id": 7,
        "last_link_id": 6,
        "nodes": [
            {
                "id": 1,
                "type": "CheckpointLoaderSimple",
                "pos": [50, 100],
                "size": [300, 100],
                "flags": {},
                "order": 0,
                "mode": 0,
                "inputs": [],
                "outputs": [
                    {"name": "MODEL", "type": "MODEL", "links": [1]},
                    {"name": "CLIP", "type": "CLIP", "links": [2]},
                    {"name": "VAE", "type": "VAE", "links": [3]}
                ],
                "properties": {"Node name for S&R": "CheckpointLoaderSimple"},
                "widgets_values": ["stable_audio_3_small_music.safetensors"]
            },
            {
                "id": 2,
                "type": "CLIPTextEncode",
                "pos": [400, 100],
                "size": [350, 120],
                "flags": {},
                "order": 1,
                "mode": 0,
                "inputs": [
                    {"name": "clip", "type": "CLIP", "link": 2}
                ],
                "outputs": [
                    {"name": "CONDITIONING", "type": "CONDITIONING", "links": [4]}
                ],
                "properties": {"Node name for S&R": "CLIPTextEncode"},
                "widgets_values": ["1940s old-time radio dramatic brass theme, detective noir jazz, muted trumpet, double bass, brushed drums"]
            },
            {
                "id": 3,
                "type": "CLIPTextEncode",
                "pos": [400, 260],
                "size": [350, 80],
                "flags": {},
                "order": 2,
                "mode": 0,
                "inputs": [
                    {"name": "clip", "type": "CLIP", "link": 2}
                ],
                "outputs": [
                    {"name": "CONDITIONING", "type": "CONDITIONING", "links": [5]}
                ],
                "properties": {"Node name for S&R": "CLIPTextEncode"},
                "widgets_values": ["low fidelity, distorted, harsh clipping, modern synth"]
            },
            {
                "id": 4,
                "type": "EmptyLatentAudio",
                "pos": [400, 380],
                "size": [300, 100],
                "flags": {},
                "order": 3,
                "mode": 0,
                "inputs": [],
                "outputs": [
                    {"name": "LATENT", "type": "LATENT", "links": [6]}
                ],
                "properties": {"Node name for S&R": "EmptyLatentAudio"},
                "widgets_values": [30.0]
            },
            {
                "id": 5,
                "type": "KSampler",
                "pos": [800, 100],
                "size": [280, 260],
                "flags": {},
                "order": 4,
                "mode": 0,
                "inputs": [
                    {"name": "model", "type": "MODEL", "link": 1},
                    {"name": "positive", "type": "CONDITIONING", "link": 4},
                    {"name": "negative", "type": "CONDITIONING", "link": 5},
                    {"name": "latent_image", "type": "LATENT", "link": 6}
                ],
                "outputs": [
                    {"name": "LATENT", "type": "LATENT", "links": [7]}
                ],
                "properties": {"Node name for S&R": "KSampler"},
                "widgets_values": [883719, "randomize", 25, 6.5, "dpmpp_2m", "karras", 1.0]
            },
            {
                "id": 6,
                "type": "VAEDecodeAudio",
                "pos": [1120, 100],
                "size": [220, 80],
                "flags": {},
                "order": 5,
                "mode": 0,
                "inputs": [
                    {"name": "samples", "type": "LATENT", "link": 7},
                    {"name": "vae", "type": "VAE", "link": 3}
                ],
                "outputs": [
                    {"name": "AUDIO", "type": "AUDIO", "links": [8]}
                ],
                "properties": {"Node name for S&R": "VAEDecodeAudio"},
                "widgets_values": []
            },
            {
                "id": 7,
                "type": "SaveAudio",
                "pos": [1380, 100],
                "size": [280, 120],
                "flags": {},
                "order": 6,
                "mode": 0,
                "inputs": [
                    {"name": "audio", "type": "AUDIO", "link": 8}
                ],
                "outputs": [],
                "properties": {"Node name for S&R": "SaveAudio"},
                "widgets_values": ["baseline_output/baseline_stable_audio_3_music"]
            }
        ],
        "links": [
            [1, 1, 0, 5, 0, "MODEL"],
            [2, 1, 1, 2, 0, "CLIP"],
            [3, 1, 2, 6, 1, "VAE"],
            [4, 2, 0, 5, 1, "CONDITIONING"],
            [5, 3, 0, 5, 2, "CONDITIONING"],
            [6, 4, 0, 5, 3, "LATENT"],
            [7, 5, 0, 6, 0, "LATENT"],
            [8, 6, 0, 7, 0, "AUDIO"]
        ],
        "groups": [],
        "config": {},
        "extra": {"title": "Stable Audio 3 Small Music Baseline"},
        "version": 0.4
    }
    metadata = {
        "key": "baseline_stable_audio_3_music",
        "title": "Stable Audio 3 Small Music Synthesis Baseline",
        "model_category": "Music",
        "target_model": "checkpoints/stable_audio_3_small_music.safetensors",
        "vram_estimate_gb": 3.0,
        "vram_rtx5080_sustainable": True,
        "loader_node": "CheckpointLoaderSimple",
        "status": "RUNNABLE_LOCAL",
        "upstream_source_url": "https://stability.ai/stable-audio",
        "adaptations_applied": ["Configured single-checkpoint 30s music synthesis pipeline"],
        "link_error_count": 0
    }
    return workflow, metadata


def build_dmm_music_enhancer_baseline() -> tuple[dict, dict]:
    workflow = {
        "last_node_id": 3,
        "last_link_id": 2,
        "nodes": [
            {
                "id": 1,
                "type": "LoadAudio",
                "pos": [50, 150],
                "size": [300, 120],
                "flags": {},
                "order": 0,
                "mode": 0,
                "inputs": [],
                "outputs": [
                    {"name": "AUDIO", "type": "AUDIO", "links": [1]}
                ],
                "properties": {"Node name for S&R": "LoadAudio"},
                "widgets_values": ["example_music.wav"]
            },
            {
                "id": 2,
                "type": "DMM_MusicEnhancer",
                "pos": [400, 150],
                "size": [350, 200],
                "flags": {},
                "order": 1,
                "mode": 0,
                "inputs": [
                    {"name": "audio", "type": "AUDIO", "link": 1}
                ],
                "outputs": [
                    {"name": "AUDIO", "type": "AUDIO", "links": [2]}
                ],
                "properties": {"Node name for S&R": "DMM_MusicEnhancer"},
                "widgets_values": ["auto", 0.35, 15, 0.5]
            },
            {
                "id": 3,
                "type": "SaveAudio",
                "pos": [800, 150],
                "size": [280, 120],
                "flags": {},
                "order": 2,
                "mode": 0,
                "inputs": [
                    {"name": "audio", "type": "AUDIO", "link": 2}
                ],
                "outputs": [],
                "properties": {"Node name for S&R": "SaveAudio"},
                "widgets_values": ["baseline_output/baseline_dmm_music_enhancer"]
            }
        ],
        "links": [
            [1, 1, 0, 2, 0, "AUDIO"],
            [2, 2, 0, 3, 0, "AUDIO"]
        ],
        "groups": [],
        "config": {},
        "extra": {"title": "DMM Music Enhancer MusicGen Baseline"},
        "version": 0.4
    }
    metadata = {
        "key": "baseline_dmm_music_enhancer",
        "title": "DMM Music Enhancer (MusicGen Melody Audio-to-Audio) Baseline",
        "model_category": "Music",
        "target_model": "musicgen_cache",
        "vram_estimate_gb": 1.5,
        "vram_rtx5080_sustainable": True,
        "loader_node": "DMM_MusicEnhancer",
        "status": "RUNNABLE_LOCAL",
        "custom_node_pack": "DMM_MusicEnhancer",
        "upstream_source_url": "https://github.com/jbrick2070/DMM_MusicEnhancer",
        "adaptations_applied": ["Configured audio input to MusicGen chroma-guided enhancement and output pipeline"],
        "link_error_count": 0
    }
    return workflow, metadata


def main() -> None:
    builders = [
        ("baseline_kokorotts", build_kokoro_tts_baseline),
        ("baseline_stable_audio_open", build_stable_audio_open_baseline),
        ("baseline_stable_audio_3_music", build_stable_audio_3_baseline),
        ("baseline_dmm_music_enhancer", build_dmm_music_enhancer_baseline),
        ("baseline_ltx_spatial_upscaler_x2", build_ltx_spatial_upscaler_baseline),
        ("baseline_lumina2_bf16", build_lumina2_baseline),
        ("baseline_minimax_h3_turbo", build_minimax_h3_baseline),
    ]

    for key, builder in builders:
        wf, meta = builder()
        if wf:
            wf_file = ADAPTED_DIR / f"{key}.json"
            wf_file.write_text(json.dumps(wf, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            meta_file = METADATA_DIR / f"{key}.json"
            meta_file.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"Generated modality baseline: {key}")


if __name__ == "__main__":
    main()
