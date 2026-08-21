# Driver anchor -- lane 4, round r2 (coding plan / implementability)

Written by the driver (Claude, Cowork) BEFORE any fan-out, from the real
Windows files, in the r2 output format. Every claim is labelled CONFIRMED /
MISREAD / UNVERIFIABLE against files actually read.

VERDICT: yes-with-fixes. The arms stage, the gate change is narrower than it
looks, and 2 of 8 legs have already rendered without OOM. The build risk is not
the code; it is that the INSTRUMENT may be mismatched to the KNOB, and that the
lane inherits five unfixed method debts from lane 3.

## Grounding log (what I actually read, and what it says)

CONFIRMED -- `receipts/2026-08-21-grounded/wan_ti2v__video_wan2_2_5B_ti2v.json`
has exactly 6 entries in `differences`; 3 are `cfg 5/5.0`, `denoise 1/1.0` and
`seed`, i.e. noise. The remaining 3 are lane 1's screened sampler knobs. The
plan's "zero unscreened parameter deltas" is correct, and the plan's own table
is the honest form of the GO_FORWARD line that says "nine differences".

CONFIRMED -- both encoder files exist:
`C:\ComfyUI-Models\text_encoders\umt5_xxl_fp8_e4m3fn_scaled.safetensors`
(6,735,906,897 bytes) and `umt5-xxl-encoder-Q5_K_M.gguf` (4,145,878,880 bytes).
No download needed. `wan2.2_ti2v_5B_fp16.safetensors` is NOT present anywhere
under `C:\ComfyUI-Models\`, so the UNET lane is correctly out of scope.

CONFIRMED -- live `/object_info/CLIPLoader` lists 14 `clip_name` options
including `umt5_xxl_fp8_e4m3fn_scaled.safetensors`, and `type` includes `wan`.
The official arm names a real, currently-loadable interface.

CONFIRMED -- the shipping graph from `diffomatic.build_api_graph("eng_wan_ti2v")`
is 10 nodes; `clip` is `CLIPLoaderGGUF` and feeds exactly `pos` and `neg`;
terminal is `vaedecode` (`VAEDecodeTiled`); seed lives at `ksampler.seed`;
canvas 832x480, length 97.

CONFIRMED -- `tools/purity_gate.py` records `{node}.__class__` as a `CLASS`
leaf and, before the change, appended a failure for ANY changed CLASS leaf
without consulting the declaration. The wiring check is a separate branch that
fires first and is still unconditional.

CONFIRMED -- all five gate regression cases behave as the plan states; I ran
them. Lane 3's existing invocation still passes with 1 knob, and the staged
lane 4 pair reports 43 leaves per side with exactly 2 changed.

CONFIRMED -- lane 3's `seat1_full` and `seat2_full` are byte-identical image
sets in all six cells (sha256 per file), and those duplicate pairs disagreed in
3 of 6 cells. Lane 3 read-order landed 14 candidate-first / 4 ours-first.
`lane3/judge/` has no `PANEL_META.json` and no `PANEL_PROMPTS.js`, though
`lane2/judge/` has both.

CONFIRMED -- arm-to-arm NCC at f097 for lane 3 is 0.1448 / 0.2587 / 0.3887 /
0.7398 / 0.5711 / 0.6486, all below lane 1's ~0.90 admission line. Nothing in
`tools/` computes NCC; I computed it out-of-band with numpy.

UNVERIFIABLE until the legs land -- whether the fp8 encoder changes anything
VISIBLE at 832x480 on an image-conditioned lane. This is the whole question and
no file can answer it.

## MUST-FIX BEFORE BUILD

1. **[Fixtures / instrument-knob match] The lane may be structurally incapable
   of showing the effect it is looking for.** `wan_ti2v` is image-conditioned:
   `latent` is `Wan22ImageToVideoLatent` with `start_image` wired from
   `loadimage`. The conditioning still therefore dominates composition, and the
   text encoder's contribution is the residual. If both arms simply reproduce
   the still, the lane returns a null that measures the FIXTURE, not the
   encoder -- lane 1's officer-close-up lesson wearing new clothes. Fix: before
   judging, compute arm-to-arm NCC per cell (item 4 below) AND record how much
   each arm departs from the conditioning still; if both arms sit at high NCC
   to each other and to the still, report "encoder effect below the resolution
   of this fixture" rather than "no difference".

2. **[testcard_motion] The motion demand may floor the acuity instrument.** The
   card's value is that element sizes are KNOWN; a prompted camera drift can
   smear every fine element in BOTH arms, which is a 12.121 floor effect and
   teaches nothing. Fix: judge the card at f001 (pre-drift) as well as f049/f097,
   so the ladder has a legible baseline; if f001 is already smeared, the fixture
   failed and must be reported as failed rather than as a null.

3. **[Method debt] The judge-seat duplication must be fixed before this panel
   runs, not after.** Lane 3's seat1/seat2 saw byte-identical pixels. Repeating
   that here spends 2 of 3 seats on the same view and inflates the apparent
   sample. Fix: seat2 must differ materially from seat1 -- different frames, a
   contact strip, or the rendered PAIR clip -- or the panel is 2 seats, not 3,
   and must say so.

4. **[Method debt] NCC is an admission rule with no implementation.** Lane 1
   made it binding; no lane has ever computed it in-harness. Fix: add it to
   `tools/temporal_stats.py` or a sibling and write it into `RENDER.json` as a
   standard field, so it is a receipt rather than an out-of-band numpy run.

## SHOULD-FIX

5. **[Receipts] Archive `PANEL_META.json` and `PANEL_PROMPTS` at panel time.**
   Lane 2 did; lane 3 did not, and lane 3's judge model and questions are now
   permanently unrecorded. This is a one-line discipline that keeps a verdict
   re-derivable.

6. **[Read order] Deal a balanced assignment.** `seat_plan` flips an independent
   coin per seat (`digest[0] & 1`); with 3 seats x 6 cells that is free to land
   14/4, and did. Fix: constrain to a balanced split rather than 18 coin flips.

7. **[VRAM honesty] Record peak VRAM per arm even though there is no ceremony.**
   The operator banned OOM forensics, not observation. The fp8 arm is ~2.6 GB
   larger and a WIN that only fits at 14.5 GB is a tier, not a default -- the
   number is what makes that argument.

8. **[Verdict wording] Pre-commit the tier language.** `LANE.json` already says
   a win becomes a QUALITY TIER proposal, never a silent swap. Keep that exact
   wording in the verdict so a future window cannot read a win as authority to
   change the 16 GB default.

## OPTIONAL

- Judge the six existing lane 3 PAIR clips with one seat, since they are already
  on disk and no seat has ever seen a moving frame in this programme.

## CUT THESE

- **Any UNET fp16 arm in this lane.** The file is not on disk, it is
  download-gated, and bundling it would make a clean 8-leg lane into a blocked
  one. Safe to cut: it is its own lane and loses nothing by waiting.
- **A refutation panel.** It runs only on a believed WIN. Standing it up now is
  pre-spending on an outcome that has not happened.
- **Decomposing the swap into class-vs-file.** `CLIPLoaderGGUF` cannot load a
  `.safetensors` and `CLIPLoader` cannot load a `.gguf`, so class and file are
  not separable knobs. Attempting it is incoherent, not thorough.
