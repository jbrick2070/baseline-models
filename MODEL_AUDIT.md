# Installed Models & Baseline Coverage Audit

This document audits all generative model weights installed under `C:\ComfyUI-Models` and tracks their baseline workflow status, loader nodes, and VRAM budget against the target **NVIDIA RTX 5080 (16 GB VRAM ceiling, ~14.0–14.5 GB sustainable safe peak)**.

---

## 1. Video Generative Models

| Model | Installed File(s) on Disk | Size | Loader Node | RTX 5080 Fit (Est. VRAM) | Baseline Status | Notes / Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Wan2.2 TI2V-5B** | `diffusion_models/Wan2.2-TI2V-5B-Q5_K_M.gguf`<br>`diffusion_models/FastWan2.2-TI2V-5B-q6_k.gguf` | 3.55 GB<br>3.92 GB | `UnetLoaderGGUF` | ✅ Safe (~8.0 GB) | `baseline_wan2_2_ti2v_5b.json` | Stock Comfy-Org template adapted for GGUF. |
| **MiniMax H3 Turbo** | `diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors`<br>`vae/minimax_h3_video_vae_fp16.safetensors` | 19.53 GB<br>4.85 GB | `UNETLoader` / `ComfyUI-MiniMax-H3-Turbo` | ✅ Safe (~13.5 GB) | `baseline_minimax_h3_turbo.json` | High-fidelity video + audio generation via INT8 pruned weights and step600 EMA LoRA. |
| **Wan2.2 I2V-14B** | `diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors` | 13.31 GB | `UNETLoader` | ⚠️ Tight (~14.5 GB) | `baseline_wan2_2_14b_i2v.json` | Only low-noise expert installed. Full dual-expert graph is reference. |
| **HuMo 17B / Wan2.1 HuMo** | `diffusion_models/humo_17B_fp8_e4m3fn.safetensors`<br>`diffusion_models/HuMo-17b-Q3_K_M.gguf`<br>`diffusion_models/Wan2_1-HuMo-14B_fp8_e4m3fn_scaled_KJ.safetensors` | 15.89 GB<br>8.40 GB<br>16.66 GB | `UNETLoader`<br>`UnetLoaderGGUF` | ✅ Safe (~11–14 GB) | `baseline_humo_17b.json` | Production video backbone for OTR. GGUF and FP8 variants available. |
| **LTX-Video 2B (v0.9)** | `checkpoints/ltx-video-2b-v0.9.safetensors` | 8.73 GB | `CheckpointLoaderSimple` | ✅ Safe (~9.5 GB) | `baseline_ltx_2b_v0.9.json` | Official minimal T2V baseline from ComfyUI examples. |
| **LTX-2.3 22B Distilled-1.1** | `unet/distilled-1.1/ltx-2.3-22b-distilled-1.1-Q3_K_M.gguf`<br>`checkpoints/ltx-2.3-22b-dev.safetensors` (42.98 GB) | 9.90 GB<br>42.98 GB | `UnetLoaderGGUF`<br>`CheckpointLoaderSimple` | ✅ Safe (~11.5 GB GGUF)<br>❌ Exceeds (46 GB dev bf16) | `baseline_ltx2_3_distilled_1_1.json` | Full 42.98 GB dev bf16 exceeds 16GB; Q3_K_M GGUF runs smoothly. |
| **WanMove 480p** | `Wan21-WanMove_fp8_scaled_e4m3fn_KJ.safetensors` *(absent)* | N/A | `UNETLoader` | ⚠️ ~14.0 GB | `baseline_wanmove_480p.json` | Reference-only baseline. Model weights not installed on disk. |

---

## 2. 3D Generative & Reconstruction Models

| Model | Installed File(s) on Disk | Size | Loader Node | RTX 5080 Fit (Est. VRAM) | Baseline Status | Notes / Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Hunyuan3D-2 Multiview** | `checkpoints/hunyuan3d-dit-v2-mv.safetensors` | 4.59 GB | `ImageOnlyCheckpointLoader` | ✅ Safe (~11.0 GB) | `baseline_hunyuan3d_v2_mv.json` | Stock Comfy-Org template matching installed MV checkpoint. |
| **HunyuanWorld-Mirror** | `WorldMirror-V2/HY-WorldMirror-2.0/model.safetensors` | 4.71 GB | `LoadHunyuanWorldMirrorModel` | ✅ Safe (~4–12 GB depending on frames) | `baseline_hunyuanworldmirror.json` | Minimal feed-forward 3D reconstruction baseline using `ComfyUI-HunyuanWorld-Mirror`. |
| **Trellis2 MeshOnly** | *Weights absent on disk* | N/A | `Trellis2ModelLoader` | ❌ Exceeds (~18–24 GB) | `baseline_trellis2_meshonly.json` | Reference-only baseline. Exceeds single-GPU 16GB ceiling. |

---

## 3. Image Generative Models

| Model | Installed File(s) on Disk | Size | Loader Node | RTX 5080 Fit (Est. VRAM) | Baseline Status | Notes / Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **FLUX.1 [dev] FP8** | `checkpoints/flux1-dev-fp8.safetensors` | 16.06 GB | `CheckpointLoaderSimple` | ✅ Safe (~12.5 GB) | `baseline_flux_dev_checkpoint.json` | Minimal stock baseline using single all-in-one checkpoint. |
| **Lumina-Image 2.0** | `diffusion_models/lumina_2_model_bf16.safetensors`<br>`vae/lumina2_ae.safetensors` | 4.86 GB<br>0.31 GB | `UNETLoader` + `VAELoader` | ✅ Safe (~9.5 GB) | `baseline_lumina2_bf16.json` | Text-to-image pipeline using Gemma 4 text encoder and Lumina VAE. |
| **FLUX.1 [dev] Split** | *Separate unet/clip/t5 files* | N/A | `UNETLoader` + `DualCLIPLoader` | ✅ Safe (~13.0 GB) | `baseline_flux_dev.json` | Comfy-Org template using subgraphs / split loaders. |

---

## 4. Audio & TTS Models

| Model | Installed File(s) on Disk | Size | Loader Node | RTX 5080 Fit | Baseline Status | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Kokoro-82M TTS** | `huggingface/models--hexgrad--Kokoro-82M/snapshots/.../kokoro-v1_0.pth` | 0.30 GB | `KokoroTTS` | ✅ Safe (~1.5 GB) | `baseline_kokorotts.json` | High-speed local voice synthesis with multi-voice support. |
| **Stable Audio Open 1.0** | `checkpoints/stable-audio-open-1.0.safetensors` | 4.52 GB | `CheckpointLoaderSimple` | ✅ Safe (~5.0 GB) | `baseline_stable_audio_open.json` | Long-form atmospheric soundscapes and sound effects. |
| **Stable Audio 3 Small** | `checkpoints/stable_audio_3_small_music.safetensors` | 2.11 GB | `CheckpointLoaderSimple` | ✅ Safe (~3.0 GB) | Ready for integration | Fast music synthesis. |
| **ResembleAI Chatterbox** | `huggingface/models--ResembleAI--chatterbox/snapshots/.../s3gen.safetensors` | 2.97 GB | Python / Custom | ✅ Safe (~3.5 GB) | Installed on disk | High quality expressive conversational audio. |

---

## 5. Spatial & Video Upscalers

| Model | Installed File(s) on Disk | Size | Loader Node | RTX 5080 Fit | Baseline Status | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **LTX 2.3 Latent Spatial Upscaler x2** | `latent_upscale_models/ltx-2.3-spatial-upscaler-x2-1.1.safetensors` | 0.93 GB | `LatentUpscaleModelLoader` | ✅ Safe (~4.0 GB) | `baseline_ltx_spatial_upscaler_x2.json` | Native latent-space 2x upscaler for video and stills. |
| **LTX 2.5 Latent Upscaler** | `latent_upscale_models/ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors` | 0.93 GB | `LatentUpscaleModelLoader` | ✅ Safe (~4.0 GB) | Installed on disk | Next-gen latent upscaler model. |
| **SeedVR2 Video Upscaler** | `ComfyUI-SeedVR2_VideoUpscaler` extension | Custom | `SeedVR2Extension` | ✅ Safe (~6–10 GB) | Installed in custom_nodes | High quality temporal video enhancement. |

---

## 6. Local LLMs & Prompt Engineers

| Model | Installed File(s) on Disk | Size | Loader Format | RTX 5080 Fit | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Unsloth Gemma 4 12B IT** | `unsloth/gemma-4-12b-it-GGUF/gemma-4-12b-it-Q4_K_M.gguf` | 6.63 GB | GGUF / llama-cpp | ✅ Safe (~7.5 GB) | Ideal for fast local prompt expansion and scene scripting. |
| **Mistral Nemo Instruct 2407** | `huggingface/hub/models--mistralai--Mistral-Nemo-Instruct-2407` | 22.81 GB | Safetensors / GGUF | ⚠️ ~15 GB (quantized) | 12B parameter model with 128k context for deep story reasoning. |
| **Qwen 3 4B** | `text_encoders/qwen_3_4b.safetensors` / `fp8_mixed` | 7.49 GB | Safetensors | ✅ Safe (~4.5 GB) | Lightweight multilingual text reasoning and clip encoding. |
