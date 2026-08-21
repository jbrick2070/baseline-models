# Lane 3 verdict -- `ltx_video` distilled LoRA strength, ours (0.7) vs half (0.5)

**RESULT: NO WIN. The shipped `_LTX_DISTILLED_LORA_STRENGTH = 0.70` stands.
Nothing is queued as an OTR item.** Decided by the matrix pre-declared in
`LANE.json` before any render: no structural-regression dominance either way,
no material gain for the candidate = null at the shipping output.

## The knob and its bound

ONE literal: `lora.strength_model` on `LoraLoaderModelOnly`, 0.7 shipped vs
0.5, SAME LoRA file both arms (`ltx-2.3-22b-distilled-lora-384-1.1`). The
official template pairs 0.5 with the download-gated rank-111 dynamic LoRA that
is not on disk, so the candidate arm is named `half`, never `official` -- this
lane says nothing about the official file+strength combination.

## What was run

Three t2v prompt-fixtures (portrait / march / radio -- prompts ARE the
fixtures on a text-to-video lane) x 2 arms x 2 seeds = 12 legs, all success,
97 frames at 1024x576, 100-120s per leg. Purity: changed set exactly
`{lora.strength_model}` on staged AND submitted graphs. Two receipts new to
the method both held: the crop-overlay check ran BEFORE the panel
(`CROP_OVERLAY_RECEIPT.json`), and the A/A null was receipted at creation --
**97/97 frames byte-identical** (`march/render/AA_CONTROL.json`), so the
pipeline is bit-exact and every arm difference is the knob.

The sigma-injector ADAPT (local `_SigmasFromValues` -> registered
`ManualSigmas`, both arms, live contract check before queueing) worked first
try -- the census had flagged this wall a lane early, and Bible `12.122`'s
rule closed it without a failed leg.

## The panel

18 blinded seats (3 fixtures x 2 seeds x 3 seats), per-seat digest
permutations (the corrected `seat_plan`), prompt-anchored countable questions.

| | half | ours | TIE |
| :--- | :---: | :---: | :---: |
| march (motion demanded) | 3 | 3 | 0 |
| portrait | 4 | 2 | 0 |
| radio | 2 | 3 | 1 |
| total | **9** | **8** | 1 |

A dead heat, and the margins prove less than they appear: 9 seats said
"clear", but clear calls point in OPPOSITE directions within the same cell
(march/seed42: two seats clear-for-half, one clear-for-ours). On a t2v lane
the two arms legitimately compose DIFFERENT scenes from the same seed, so a
seat's "clear" is substantially scene luck -- which aspects the arm's
composition happened to serve. That is lane 1's divergence-detector lesson
wearing t2v clothes, anticipated in the verdict matrix ("seats judge each arm
against the PROMPT", which is why the tally still means something: neither
composition population is countably better).

## What IS directional

* **The half arm moves less on every cell** (temporal receipts): march 13.4
  vs 21.6 mean frame-delta at seed 42 (-38%), 22.5 vs 24.0 at the other seed;
  portrait and radio lower by 25-30% throughout. On the march -- where
  traversal is the prompt's explicit demand -- less motion is worse prompt
  compliance, and the driver's strip read agrees: ours plays its instruments
  (trumpets raised, snare carried), half mostly carries horns at its sides
  and admits an unprompted half-dressed figure at f97.
* Both arms are structurally clean on faces (portrait: zero defects, every
  seat, every frame, both arms -- consistent with lane 2's identity result).

So if anything, the evidence leans toward the shipped 0.7 on the axis the
knob was expected to move. 0.5 buys nothing measurable and costs motion.

## Bounds

* Same-file-only: the rank-111 dynamic LoRA remains download-gated and
  untested; a future lane on that file is a NEW question.
* t2v scene divergence caps seat-margin meaning, as recorded above.
* The completeness critic has NOT yet run on this lane (the window closed at
  the operator's request); it is the next window's first act, and this verdict
  may gain a corrections section from it, as lane 2's did.

## Provenance

Workbench `basline-models`, lane `staging/lane3_ltx_video/`; frames under
`ComfyUI/output/baseline_output/lane3_ltx_video/`, never `otr/obs`. Panel
`judge/PANEL.json` (run `wf_cc532009-7af`, 18/18 seats, 0 errors -- resumed
across an app crash from the 17-seat journal, last seat run live). Measurement
only: no OTR production code, no model download, shipped recipes untouched.
