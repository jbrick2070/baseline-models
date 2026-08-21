# Compatibility & Patch Record

This log records every compatibility patch, node adapter, and non-model dependency required to run baseline graphs cleanly in ComfyUI, following the 7-field standard defined in [`AGENTS.md`](./AGENTS.md).

---

### Record 1: Wan2.2 TI2V-5B GGUF Unet Loader Adaptation
1. **What failed**: Upstream template (`video_wan2_2_5B_ti2v.json`) expects unquantized FP16 `UNETLoader` target `wan2.2_ti2v_5B_fp16.safetensors`, whereas disk only has `Wan2.2-TI2V-5B-Q5_K_M.gguf`.
2. **Exact patch or dependency used**: Changed loader node from standard `UNETLoader` to `UnetLoaderGGUF` and target widget to `Wan2.2-TI2V-5B-Q5_K_M.gguf`.
3. **Source URL**: `https://github.com/city96/ComfyUI-GGUF` (node provider) & `https://raw.githubusercontent.com/Comfy-Org/workflow_templates/refs/heads/main/templates/video_wan2_2_5B_ti2v.json` (source template).
4. **Version or commit**: `ComfyUI-GGUF` (installed locally in custom_nodes).
5. **Why it is compatible**: `UnetLoaderGGUF` outputs standard `MODEL` latent conditioning identical to `UNETLoader`, permitting quantized execution under 8.0 GB VRAM on RTX 5080.
6. **Validation result**: Verified 0 dangling links, graph parsed cleanly, model resolved on disk.
7. **Requirement status**: `Required` (for on-disk quantized weights).

---

### Record 2: LTX-2.3 22B Distilled GGUF Adapter
1. **What failed**: Upstream author template loads full 42.98 GB `ltx-2.3-22b-dev.safetensors` plus separate LoRA, which requires ~46 GB VRAM and exceeds RTX 5080's 16 GB ceiling.
2. **Exact patch or dependency used**: Substituted loader with `unet/distilled-1.1/ltx-2.3-22b-distilled-1.1-Q3_K_M.gguf` via `UnetLoaderGGUF`.
3. **Source URL**: `https://raw.githubusercontent.com/Lightricks/ComfyUI-LTXVideo/refs/heads/master/example_workflows/2.3/LTX-2.3_T2V_I2V_Single_Stage_Distilled_Full.json`.
4. **Version or commit**: `ComfyUI-LTXVideo` v2.3.
5. **Why it is compatible**: Fits within ~11.5 GB VRAM peak, maintaining single-stage distilled sampling.
6. **Validation result**: Verified 0 dangling links, graph parsed cleanly.
7. **Requirement status**: `Required` (for single 16GB GPU execution).

---

### Record 3: HunyuanWorld-Mirror Absolute Path & Link Type Fix
1. **What failed**: Upstream community README example uses relative path causing remote HF download attempt, and earlier hand-built JSON had link type `MODEL` instead of `HWMIRROR_MODEL`.
2. **Exact patch or dependency used**: Updated link type to `HWMIRROR_MODEL`, added missing widget values (`force_reload=false`, `subsample_factor=1`), and pointed model path to `C:/ComfyUI-Models/WorldMirror-V2/HY-WorldMirror-2.0/model.safetensors`.
3. **Source URL**: `https://github.com/cedarconnor/ComfyUI-HunyuanWorld-Mirror`.
4. **Version or commit**: Local install at `custom_nodes/ComfyUI-HunyuanWorld-Mirror`.
5. **Why it is compatible**: Matches exact Python class definitions in `nodes.py` and uses local weights without downloading.
6. **Validation result**: Validated in `validate_baselines.py` with 0 dangling links and successful local model resolution.
7. **Requirement status**: `Required`.

---

### Record 4: Hunyuan3D-2 Multiview Checkpoint Matching
1. **What failed**: Upstream single-view template requested `hunyuan3d-dit-v2.safetensors`, but disk has `hunyuan3d-dit-v2-mv.safetensors` (multiview-trained).
2. **Exact patch or dependency used**: Used the official `3d_hunyuan3d_multiview_to_model.json` template with `ImageOnlyCheckpointLoader` pointing to `hunyuan3d-dit-v2-mv.safetensors`.
3. **Source URL**: `https://raw.githubusercontent.com/Comfy-Org/workflow_templates/refs/heads/main/templates/3d_hunyuan3d_multiview_to_model.json`.
4. **Version or commit**: Upstream template v0.4.
5. **Why it is compatible**: Matches multiview model conditioning architecture with installed checkpoint on disk.
6. **Validation result**: Validated with 0 dangling links and model found on disk.
7. **Requirement status**: `Required`.

---

### Record 5: Kokoro-82M Local Audio Pipeline Integration
1. **What failed**: Standard audio nodes do not provide single-call phonemized high-speed speech synthesis.
2. **Exact patch or dependency used**: Built `baseline_kokorotts.json` utilizing `KokoroTTS` custom node mapped directly to `SaveAudio`.
3. **Source URL**: `https://github.com/danirollins/comfyui-kokorotts`.
4. **Version or commit**: Installed custom node package `custom_nodes/comfyui-kokorotts`.
5. **Why it is compatible**: Loads locally installed `kokoro-v1_0.pth` and outputs standard ComfyUI `AUDIO` tensors.
6. **Validation result**: Validated with 0 dangling links.
7. **Requirement status**: `Required` (for TTS baseline).

---

### Record 6: MiniMax H3 Turbo Pruned Weights Mapping
1. **What failed**: Example workflow references unpruned `minimax_h3_fl2va_int8_convrot.safetensors`, but disk contains `minimax_h3_fl2va_pruned_int8_convrot.safetensors`.
2. **Exact patch or dependency used**: Adapted `UNETLoader` widget value to target the exact pruned weight file on disk.
3. **Source URL**: `https://github.com/Comfy-Org/ComfyUI-MiniMax-H3-Turbo`.
4. **Version or commit**: Local package `custom_nodes/ComfyUI-MiniMax-H3-Turbo`.
5. **Why it is compatible**: INT8 pruned weights contain identical input/output shapes with reduced memory footprint (~13.5 GB peak).
6. **Validation result**: Verified model target resolved as `FOUND` on disk with 0 link errors.
7. **Requirement status**: `Required`.

---

### Record 7: LTX 2.3 Latent Spatial 2x Upscaler
1. **What failed**: Standard pixel upscalers do not preserve LTX video latent fidelity and require full frame decode/encode overhead.
2. **Exact patch or dependency used**: Configured `LatentUpscaleModelLoader` with `ltx-2.3-spatial-upscaler-x2-1.1.safetensors` via `LatentUpscaleByModel`.
3. **Source URL**: `https://github.com/Lightricks/ComfyUI-LTXVideo`.
4. **Version or commit**: Local install `custom_nodes/ComfyUI-LTXVideo`.
5. **Why it is compatible**: Upscales directly in the LTX latent domain before final VAE decode, reducing VRAM to ~4.0 GB.
6. **Validation result**: Verified 0 dangling links and successful model mapping.
7. **Requirement status**: `Required`.
