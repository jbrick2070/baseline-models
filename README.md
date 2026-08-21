# baseline-models

A dedicated ComfyUI repository and toolkit focused on fetching, adapting, and validating stock/baseline workflow graphs (`.json`) and custom node dependencies for generative models.

## Scope & Purpose

- **Workflow Graphs & Node Dependencies**: Focuses on curating minimal, official baseline workflow graphs and managing node dependencies to benchmark generative models against their stock pipelines.
- **Zero Model Downloads**: This repository is **not** for downloading LLMs or raw model weights. All workflows are configured to run against existing installed weights under `C:\ComfyUI-Models` within an RTX 5080 (16 GB VRAM) budget.
- **Strict Boundary**: All writes and scripts are confined to this repository folder (`c:\Users\jeffr\Documents\ComfyUI\custom_nodes\basline-models`).

---

## Directory Structure

```
📂 baseline-models/
├── 📂 baselines/
│   ├── 📂 source_original/      # Pristine upstream workflow JSONs from official repos
│   ├── 📂 adapted/              # Workflows adapted for local on-disk models with 0 dangling links
│   ├── 📂 metadata/             # Structured JSON metadata (VRAM, loader, status)
│   ├── FETCH_SUMMARY.json       # Manifest of fetched templates
│   └── VALIDATION_REPORT.json   # Full validation and link integrity report
├── 📂 scripts/
│   ├── audit_models.py          # Scans C:\ComfyUI-Models and categorizes installed weights
│   ├── fetch_and_build_baselines.py  # Fetches and adapts official baseline graphs
│   └── validate_baselines.py    # Validates syntax, links, custom nodes, and model presence
├── AGENTS.md                    # Operational policy & compatibility rules
├── MODEL_AUDIT.md               # Complete audit of installed models vs. VRAM ceilings
├── COMPATIBILITY_LOG.md         # 7-field records of all compatibility patches/adapters
└── README.md
```

---

## Baselined Models Summary

| Baseline Key | Model / Architecture | Modality | Loader Node | RTX 5080 VRAM | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `baseline_wan2_2_ti2v_5b` | Wan2.2 TI2V-5B (GGUF) | Video | `UnetLoaderGGUF` | ~8.0 GB | ✅ RUNNABLE |
| `baseline_minimax_h3_turbo` | MiniMax H3 Turbo (INT8) | Video | `UNETLoader` | ~13.5 GB | ✅ RUNNABLE |
| `baseline_humo_17b` | HuMo 17B (FP8 / GGUF) | Video | `UNETLoader` | ~15.0 GB | ✅ RUNNABLE |
| `baseline_ltx_2b_v0.9` | LTX-Video 2B v0.9 | Video | `CheckpointLoaderSimple` | ~9.5 GB | ✅ RUNNABLE |
| `baseline_ltx2_3_distilled_1_1` | LTX-2.3 22B Distilled-1.1 | Video | `UnetLoaderGGUF` | ~11.5 GB | ✅ RUNNABLE |
| `baseline_flux_dev_checkpoint` | FLUX.1 [dev] FP8 All-In-One | Image | `CheckpointLoaderSimple` | ~12.5 GB | ✅ RUNNABLE |
| `baseline_lumina2_bf16` | Lumina-Image 2.0 (BF16) | Image | `UNETLoader` | ~9.5 GB | ✅ RUNNABLE |
| `baseline_hunyuan3d_v2_mv` | Hunyuan3D-2 Multiview | 3D | `ImageOnlyCheckpointLoader` | ~11.0 GB | ✅ RUNNABLE |
| `baseline_hunyuanworldmirror` | HunyuanWorld-Mirror 2.0 | 3D | `LoadHunyuanWorldMirrorModel` | ~4–12 GB | ✅ RUNNABLE |
| `baseline_stable_audio_3_music` | Stable Audio 3 Small Music | Music | `CheckpointLoaderSimple` | ~3.0 GB | ✅ RUNNABLE |
| `baseline_dmm_music_enhancer` | DMM MusicGen Enhancer | Music | `DMM_MusicEnhancer` | ~1.5 GB | ✅ RUNNABLE |
| `baseline_stable_audio_open` | Stable Audio Open 1.0 | Audio | `CheckpointLoaderSimple` | ~5.0 GB | ✅ RUNNABLE |
| `baseline_kokorotts` | Kokoro-82M Voice Synthesis | TTS | `KokoroTTS` | ~1.5 GB | ✅ RUNNABLE |
| `baseline_ltx_spatial_upscaler_x2` | LTX 2.3 Spatial Upscaler x2 | Upscalers | `LatentUpscaleModelLoader` | ~4.0 GB | ✅ RUNNABLE |
| `baseline_wan2_2_14b_i2v` | Wan2.2 I2V-14B (Low Noise) | Video | `UNETLoader` | ~14.5 GB | ⚠️ Partial Expert |
| `baseline_wanmove_480p` | WanMove 480p | Video | `UNETLoader` | ~14.0 GB | ℹ️ Reference |
| `baseline_trellis2_meshonly` | Trellis2 MeshOnly | 3D | `Trellis2ModelLoader` | ~18–24 GB | ℹ️ Reference |

---

## Usage

### 1. Audit Installed Models
```powershell
python scripts/audit_models.py
```

### 2. Fetch & Build Baselines
```powershell
python scripts/fetch_and_build_baselines.py
```

### 3. Validate Baseline Graphs
```powershell
python scripts/validate_baselines.py
```
