# Lane 4 -- wan_ti2v TEXT ENCODER precision, and the purity-gate change it required

Measurement-only work in the `basline-models` workbench. No OTR production
code, no model download, nothing published to `otr/obs`. Shipped recipes are
untouchable; only a WIN becomes an OTR item, and only through the normal gate.

## Why this lane exists

The 2026-08-21 grounded fleet diff compared the shipping `wan_ti2v` engine
against the official Comfy template `video_wan2_2_5B_ti2v.json` (package
`0.1.50`). Its receipt is
`receipts/2026-08-21-grounded/wan_ti2v__video_wan2_2_5B_ti2v.json`.

Read literally, that receipt lists **six** parameter differences:

| # | node.param | reference | ours | status |
| :-- | :-- | :-- | :-- | :-- |
| 1 | `KSampler.cfg` | `5` | `5.0` | serialization noise |
| 2 | `KSampler.denoise` | `1` | `1.0` | serialization noise |
| 3 | `KSampler.seed` | 898471028164125 | 42 | per-render, not a recipe delta |
| 4 | `KSampler.sampler_name` | `uni_pc` | `euler` | SCREENED, lane 1 |
| 5 | `KSampler.steps` | `20` | `30` | SCREENED, lane 1 |
| 6 | `ModelSamplingSD3.shift` | `8` | `5.0` | SCREENED, lane 1, and documented |

**So there are zero unscreened PARAMETER deltas left on `wan_ti2v`.** What
remains is structural, in `only_in_reference` / `only_in_ours`:

* `UNETLoader` (`wan2.2_ti2v_5B_fp16.safetensors`) vs `UnetLoaderGGUF`
  (`Wan2.2-TI2V-5B-Q5_K_M.gguf`)
* `CLIPLoader` (`umt5_xxl_fp8_e4m3fn_scaled.safetensors`) vs `CLIPLoaderGGUF`
  (`umt5-xxl-encoder-Q5_K_M.gguf`)
* `VAEDecode` vs `VAEDecodeTiled` (tile 256 / overlap 64 / temporal 16 / 8)
* `CreateVideo` + `SaveVideo` vs our frame saves, and `LoadImage` only in ours
  (harness and t2v-vs-ti2v mode, not quality deltas)

Lanes 1-3 all screened knobs where somebody had made a deliberate QUALITY
choice, and all three returned NO WIN. **These structural deltas are a
different category: they are COMPROMISES taken for a 16 GB ceiling, and their
cost has never been measured.** That makes them the highest-probability source
of a real quality gap between the shipped graphs and the official template.

The operator's stated stake is not his own box: he intends the engine to be
read, copied and re-used by other people, some of whom have far more VRAM. A
graph quantized for a 16 GB laptop, shipped as the only graph, does those users
a disservice whether or not it is optimal here.

**Scope of THIS lane:** the text encoder only. On disk we already have BOTH
files -- `umt5_xxl_fp8_e4m3fn_scaled.safetensors` (6.7 GB, the exact file the
template names) and `umt5-xxl-encoder-Q5_K_M.gguf` (4.1 GB, ours), under
`C:\ComfyUI-Models\text_encoders\`. **No download is required or authorized.**
The fp16 UNET (`wan2.2_ti2v_5B_fp16.safetensors`) is NOT on disk, so the UNET
precision lane remains download-gated and is out of scope.

## The contrast

ONE node, `clip`, swapped class and file:

```
ours      CLIPLoaderGGUF   umt5-xxl-encoder-Q5_K_M.gguf            4.1 GB
official  CLIPLoader       umt5_xxl_fp8_e4m3fn_scaled.safetensors  6.7 GB
```

Both arms are generated FROM THE SHIPPING ENGINE via
`diffomatic.build_api_graph("eng_wan_ti2v")`, so weights, sampler, tiling,
canvas (832x480), length (97) and topology are identical by construction rather
than by careful copying. The encoder feeds `pos` and `neg` in both arms and the
wiring is untouched.

## The purity-gate change this forced, and why it is the risky part

`tools/purity_gate.py` flattens both graphs structurally and records
`{node}.__class__` as a `CLASS` leaf. Before this change, **any** class
difference was an unconditional abort, consulted against nothing -- deliberately,
because an undeclared class change is exactly the uncontrolled second variable
Bible `12.121` was promoted for.

A loader lane cannot run under that rule. The change adds an **opt-in,
node-specific** declaration:

```
--expect-class NODE=ClassName      e.g.  --expect-class clip=CLIPLoader
```

Design intent, stated so it can be attacked:

1. The strict default is unchanged -- an UNdeclared class change still aborts.
2. The permission is per-node and per-target-class; a swap to a different class
   than declared still aborts.
3. Wiring/topology differences still abort unconditionally, ahead of any class
   handling.
4. A declared swap that did not actually occur aborts (no phantom declarations).
5. Leaf-level deltas are still checked separately: the swap does not license
   the new node's inputs to differ freely.

Regression evidence already run (all five behaved as specified):

| Test | Expected | Result |
| :-- | :-- | :-- |
| Lane 3's existing declaration, unchanged | PASS | PASS, 1 knob |
| Lane 4 arms, swap NOT declared | FAIL | FAIL |
| Lane 4 arms, swap declared correctly | PASS | PASS, 2 changed leaves |
| Lane 4 arms, WRONG class declared | FAIL | FAIL |
| Swap declared that never happened | FAIL | FAIL |

On the staged pair the gate reports 43 leaves per side, exactly 2 changed:
`clip.__class__` and `clip.clip_name`, both declared.

## Fixtures, and why these two

A text encoder drives PROMPT ADHERENCE more than it drives fine spatial detail,
which mostly comes from the conditioning image, the UNET and the VAE. So both
fixtures carry countable prompt demands, and one MOVES:

* **`crowd`** (`lane1_crowd.png`) -- hard content. Dozens of faces, glass tubes,
  a meter scale with ticks; the prompt names what must be present.
* **`testcard_motion`** (`lane1_testcard.png`) -- the authored acuity card as
  the conditioning still, with a prompt DEMANDING a slow constant lateral
  camera drift. Lane 1 proved a card held still is countable; lane 2's
  completeness critic proved a motion claim cannot come from a stillness
  prompt. This fixture is both at once: known element sizes, in motion.

`wan_ti2v` is image-to-video, so unlike lane 3's pure t2v the card can be
injected as a real ground-truth input rather than prompted into existence.

2 fixtures x 2 arms x 2 seeds (42, 20260821) = 8 legs, sequential, one server.

## Verdict matrix, declared BEFORE judging

* **structural_regression** -- an arm with materially more structural defects
  loses regardless of sharpness.
* **adherence_gain** -- the encoder's own axis: does an arm deliver MORE of
  what the prompt names (countable objects, held geometry), counted per arm
  against the PROMPT.
* **null_at_shipping_output** -- LOSS for the candidate; the shipped GGUF
  encoder stands and its VRAM saving is free.
* **candidate_win** -- official WINS -> refutation panel, and then it becomes a
  **QUALITY TIER** proposal for boxes with headroom, never a silent swap of the
  16 GB default.

That last cell is the point of the lane. A win here does not mean "change the
shipped graph"; it means "the shipped graph is a 16 GB tier and the project
should say so and offer the other one."

## Known open method debts carried in from lane 3's completeness critic

These are verified against the files and are NOT fixed by this lane:

1. `seat1_full` and `seat2_full` are byte-identical image sets; the panel is 12
   distinct views, not 18. Those duplicate pairs disagreed in 3 of 6 cells --
   the judge noise floor.
2. Read-order permutation is an independent coin per seat with no balance
   constraint; lane 3 landed 14 candidate-first vs 4 ours-first.
3. `PANEL_META.json` / `PANEL_PROMPTS.js` were not archived for lane 3, so its
   judge model and questions are unrecorded.
4. Arm-to-arm NCC is computed nowhere in the harness, though lane 1 made it an
   admission rule (~0.90 at the final frame).
5. Seats see 3 of 97 frames; rendered PAIR clips exist and are never judged.

## What this plan is asking the panel

1. Is the `--expect-class` extension actually as narrow as claimed, or does it
   open a path for a second uncontrolled difference to ride along?
2. Is a text-encoder swap judgeable AT ALL on these two fixtures, or is the
   instrument mismatched to the knob (the honest worry: encoder precision may
   be invisible on an image-conditioned lane where the still dominates)?
3. Does `testcard_motion` measure acuity-under-motion, or does prompted camera
   drift simply destroy the card and floor both arms (a 12.121 floor effect)?
4. What in the harness would make a WIN here unshippable or unsafe to act on?
5. Which of the five carried-in method debts must be fixed BEFORE this lane's
   panel runs, rather than after?
