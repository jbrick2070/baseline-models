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
`{lora.strength_model}` on the STAGED graphs; on the SUBMITTED graphs it is
that knob **plus the output destination** (`save.filename_prefix`), which
`render_arms.py` declares to the gate and which cannot reach the sampler.
Two receipts new to the method both held: the crop-overlay check ran BEFORE
the panel (`CROP_OVERLAY_RECEIPT.json`), and the A/A null was receipted at
creation -- **97/97 frames byte-identical**
(`march/render/AA_CONTROL.json`), so the pipeline is bit-exact and every arm
difference is the knob.

The sigma-injector ADAPT (local `_SigmasFromValues` -> registered
`ManualSigmas`, both arms, live contract check before queueing) worked first
try -- the census had flagged this wall a lane early, and Bible `12.122`'s
rule closed it without a failed leg.

**CORRECTION (completeness critic, verified by the driver):** the census
FLAG is real and reproducible -- `dynamic_input_census.py` raises
`UnsupportedGraphError: eng_ltx_video: node 'sigmas' resolves to local class
'_SigmasFromValues'` -- but it is **not in the cited receipt**.
`receipts/dynamic_input_census.json` holds only `engine_dict_inputs` and
`server_dynamic_classes`; the string `ltx_video` appears in it zero times.
The census prints `UNBUILDABLE:` to stdout and continues, so the flag was
never persisted. The claim stands on the reproduction, not on that file, and
the census needs an `unbuildable_engines` key before the next lane cites it.

## The panel

18 blinded seats (3 fixtures x 2 seeds x 3 seats), per-seat digest
permutations (the corrected `seat_plan`), prompt-anchored countable questions.

**CORRECTION (completeness critic, verified by the driver) -- the 18 seats are
not 18 independent views, and the permutation is still lopsided.**
`seat1_full` and `seat2_full` are **byte-identical image sets in all six
cells** (sha256-checked per file); only the labels differ. So the panel is 12
distinct views, not 18 -- and that accident is the most valuable thing in it,
because those duplicate pairs **disagreed in 3 of 6 cells**
(march/seed20260821 half-vs-ours, portrait/seed42 half-vs-ours,
radio/seed20260821 half-vs-TIE). Identical pixels, opposite verdicts: that is
the judge noise floor this lane never set out to measure, and a 9-8 split
across 18 votes sits inside it. The per-seat counts DO replicate across the
pair -- the disagreement is entirely in collapsing counts into one
`better_label`, so the countable-questions discipline is working and the
single summary field is not.
Read order also landed **14 candidate-first to 4 ours-first** (seat1 4/2,
seat2 5/1, seat3 5/1); two whole cells had all three seats reading the
candidate first. `seat_plan` flips an independent coin per seat
(`digest[0] & 1`) with no balance constraint, so lane 2's defect did not die,
it moved from seat1 to seats 2 and 3. Next lane deals a balanced 9/9
assignment instead of 18 coin flips.

| | half | ours | TIE |
| :--- | :---: | :---: | :---: |
| march (motion demanded) | 3 | 3 | 0 |
| portrait | 4 | 2 | 0 |
| radio | 2 | 3 | 1 |
| total | **9** | **8** | 1 |

A dead heat, and the margins prove less than they appear: **10** seats said
"clear" (7 marginal, 1 none -- the "9" first written here was the half-column
total pasted into the margin sentence; corrected against `rows[].margin`), but
clear calls point in OPPOSITE directions within the same cell
(march/seed42: two seats clear-for-half, one clear-for-ours). On a t2v lane
the two arms legitimately compose DIFFERENT scenes from the same seed, so a
seat's "clear" is substantially scene luck -- which aspects the arm's
composition happened to serve. That is lane 1's divergence-detector lesson
wearing t2v clothes, anticipated in the verdict matrix ("seats judge each arm
against the PROMPT", which is why the tally still means something: neither
composition population is countably better).

## What IS directional

* **The half arm moves less on every cell** (temporal receipts): march 13.4
  vs 21.6 mean frame-delta at seed 42 (-38%), 22.5 vs 24.0 at the other seed
  (**only -6.4%** -- the spread across the six cells is -6.4% to -37.9%,
  median -26.3%); portrait and radio lower by 25-30% throughout. The
  DIRECTION is 6 of 6 cells (sign test p ~ 0.031); the MAGNITUDE is not
  separated from seed variance, because the within-arm seed-to-seed swing is
  as large as the arm-to-arm gap (half march 13.42 -> 22.45, +67%).
* **CORRECTION (completeness critic, verified by the driver) -- the driver's
  strip read was wrong on its main clause and is withdrawn.** It claimed
  "ours plays its instruments (trumpets raised, snare carried), half mostly
  carries horns at its sides". On march/seed42 TWO of three seats record the
  opposite: seat1 -- half "delivers exactly 5 red brass players with
  well-formed horns", ours "only 4 red players of whom just 3 are brass,
  decaying to 3-plus-a-partial by f097 with trombone-length trumpet
  deformations, a warped drum, a fused stick-hand"; seat2 records the same
  counts. What IS corroborated is the tail of the sentence: seat3 finds half
  carrying "a shirtless, non-red band drummer" at f097 and ~5 melted onlookers
  against ours' ~1. The strip read also named no seed and cited no frame.
* **A further caution on reading the march temporal numbers as compliance.**
  The prompt ends "the camera holds position as the band crosses", and the
  seats independently report BOTH arms violate it ("both are tracking shots").
  `temporal_stats.leg_stats` is a whole-frame mean absolute frame difference,
  so it cannot separate camera drift from subject motion -- on this fixture a
  HIGHER delta may be worse compliance, not better. The motion claim is
  therefore weaker than first written.
* Both arms are structurally clean on faces (portrait: zero defects, every
  seat, every frame, both arms -- consistent with lane 2's identity result).

**So the honest reading is flatter than the first draft.** 0.5 buys nothing
measurable; the claim that it visibly "costs motion" does not survive the
seats or the metric's limits. NO WIN stands on the burden of proof -- the
candidate showed no material gain -- rather than on ours being better.

## Bounds

* Same-file-only: the rank-111 dynamic LoRA remains download-gated and
  untested; a future lane on that file is a NEW question.
* **THE BIG ONE, and it was not known when this verdict was first written:
  the knob was screened on the TEXT-ONLY path, while production defaults to
  IMAGE-CONDITIONED.** `eng_ltx_video.py:931` is
  `_i2v_enabled() -> os.environ.get("OTR_ENABLE_LTX_I2V", "1") == "1"` --
  default ON -- and with an init image `render_clip` builds the
  `LTXVImgToVideoConditionOnly` wrapper. Lane 3 staged through
  `diffomatic._invoke_graph_builder` -> `engine._build_graph(...)`, which
  never reaches that branch: the staged graphs are `EmptyLTXVLatentVideo` plus
  two `CLIPTextEncode`, with no image node at all. **This null is bounded to
  t2v; the shipped 0.70 is unchallenged on the path production actually
  uses.** It does not overturn NO WIN -- the burden was the candidate's, and
  the candidate did not clear it on the path tested -- but the i2v question is
  genuinely open and is a NEW lane (re-stage through the wrapper, 12 legs,
  ~25 min, plus a panel).
* **Arm-to-arm NCC was declared a flag and then never computed. Now measured,
  and every cell is far under lane 1's ~0.90 admission line.** At f097:
  march 0.1448 / 0.2587, portrait 0.3887 / 0.7398, radio 0.5711 / 0.6486;
  march/seed42 is essentially uncorrelated across all three sampled frames
  (0.09-0.14). Lane 1's binding finding was that the panel decides a winner
  exactly when renders diverge (Spearman -0.821), so all 18 seats sat at
  maximum divergence -- the regime lane 1 said yields a coin-flip tally. This
  CONFIRMS the scene-luck reasoning with numbers instead of prose, and it is
  why the 9-8 split carries no signal.
* **Tone was never contrast-matched** (lane 1: "tone feeds the counts"), and
  no receipt records the lesson being applied. Measured after the fact: the
  largest arm-to-arm mean-luminance gap is 26.5 levels (march/seed42 f097,
  ours 96.97 vs half 70.43; contrast std 77.53 vs 66.18). The good news is
  that the sign FLIPS between cells and half's std is higher in 6 of 12 frame
  samples and lower in 6, so there is no systematic knob-driven tone bias --
  and the biggest gap sits in the cell where half is the DARKER, lower-contrast
  arm and still took two clear calls, the opposite of lane 1's mechanism.
* **The A/A null was run only half-way.** `AA_CONTROL.json` proves render
  determinism (97/97 byte-identical), but lane 1 also seated three JUDGES on
  those byte-identical frames and recorded TIE from all three. Lane 3 has no
  `_aa_control` judge directory and no A/A rows in `PANEL.json`. The
  seat1/seat2 duplicate-pixel disagreement above is a stronger substitute and
  it was free, but the literal check was skipped.
* **Panel prompts, questions, judge model and the resume journal were not
  archived.** Lane 2 has `judge/PANEL_PROMPTS.js` and `judge/PANEL_META.json`;
  lane 3 has neither, anywhere in the workbench. So "prompt-anchored countable
  questions" is unverifiable from the receipts, the tally cannot be
  re-derived, and which model sat the 18 seats is permanently unrecorded. The
  "resumed across an app crash from the 17-seat journal" line is likewise
  unverifiable -- no journal survives. This is lane 2's own rule, dropped one
  lane later, and it must be enforced in the harness rather than by intent.
* **Seats saw 3 of 97 frames** (f001/f049/f097 for seats 1-2; 2 frames x 2
  regions for seat 3), so per-frame flicker and any mid-clip collapse or
  recovery are invisible to the panel. Six side-by-side PAIR clips WERE
  rendered (`output/baseline_output/lane3_ltx_video/_clips/PAIR_*.mp4`) and no
  seat was ever given one. Lane 2's lesson was that a motion claim cannot come
  from stillness prompts; lane 3 fixed the stillness half and not the
  judged-from-stills half.
* **The operator's eye -- the final seat in the voted method -- was never
  exercised**, on this lane or on lanes 1 and 2. It cost nothing because all
  three closed NO WIN and a loss costs nothing downstream; it would have
  mattered on a WIN. The six PAIR clips on disk are exactly what an eye pass
  wants.
* Frame length was 97 against the engine's documented 169 ceiling
  (`_LTX_MAX_FRAMES_DEFAULT`), so a strength effect on drift or overcooking had
  43% less clip to accumulate in. Legal and ordinary, low materiality, recorded
  for completeness.

## Corrections and completeness -- provenance

The completeness critic ran at lane close (one agent, per the ultracode
routing) and its findings above were each re-verified by the driver against
the real Windows files before being folded in: the margin recount, the
submitted-graph purity wording, the census citation, the withdrawn strip read,
the i2v-default bound, the byte-identical judge seats, the read-order tally,
and the missing panel receipts. The NCC and tone numbers were computed
independently by the driver from the frames on disk. **Nothing here reopens the
lane** -- two of these findings make the NO WIN stronger by showing the panel
could not have detected a win at this divergence, and one (the i2v default)
bounds what the null is allowed to claim.

## Provenance

Workbench `basline-models`, lane `staging/lane3_ltx_video/`; frames under
`ComfyUI/output/baseline_output/lane3_ltx_video/`, never `otr/obs`. Panel
`judge/PANEL.json` (run `wf_cc532009-7af`, 18/18 seats, 0 errors -- resumed
across an app crash from the 17-seat journal, last seat run live). Measurement
only: no OTR production code, no model download, shipped recipes untouched.
