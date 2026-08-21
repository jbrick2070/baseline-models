# Operational Policy & Compatibility Rules

## Scope & Folder Boundary
- All writes, modifications, tests, and scripts must strictly remain within this repository:
  `c:\Users\jeffr\Documents\ComfyUI\custom_nodes\basline-models`
- **Zero modification to OTR**: Never modify `otr_canonical.json` or any file in `ComfyUI-OldTimeRadio` or other external repositories.

## Zero Model Downloads Policy
- **Strictly Prohibited**: Downloading or installing model content of any kind, including:
  - Checkpoints
  - Diffusion weights
  - Video weights
  - TTS weights
  - LLM weights
  - VAEs
  - LoRAs
  - ControlNets
  - Embeddings
  - Upscalers

## Permitted Compatibility Materials (Exception)
If a selected graph cannot load or validate due to missing custom nodes, version mismatches, Python dependencies, frontend extensions, format differences, or small bugs, the following non-model materials may be obtained:
- Custom-node source packages
- Pinned compatible node versions
- Python/package dependencies
- Frontend extensions required by the graph
- Workflow conversion tools
- Graph-format patches or adapter nodes
- Corrected or patched workflow JSONs
- Compatibility metadata and configuration files

## Validation & Staging Requirements
- Before accepting anything, test in a staging/non-production ComfyUI context and verify that the graph loads without missing-node or schema errors.

## Patch Documentation Record
Whenever a compatibility patch or non-model dependency is introduced, record:
1. **What failed**
2. **Exact patch or dependency used**
3. **Source URL**
4. **Version or commit**
5. **Why it is compatible**
6. **Validation result**
7. **Requirement status** (`Required` / `Optional`)
