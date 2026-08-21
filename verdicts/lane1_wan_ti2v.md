# Lane 1 verdict -- `wan_ti2v`, official sampling recipe vs ours

**RESULT: NO WIN. The shipped recipe stands. Nothing is queued as an OTR item.**

Contrast under test, screened as a bundle:

| Knob | OURS (shipped) | OFFICIAL |
| :--- | :--- | :--- |
| `KSampler.sampler_name` | `euler` | `uni_pc` |
| `KSampler.steps` | 30 | 20 |
| `ModelSamplingSD3.shift` | 5.0 | 8.0 |

## What was run

Both arms generated from the shipping engine `eng_wan_ti2v` via
`diffomatic.build_api_graph`, so everything outside the table above is identical
by construction. Four fixtures x two arms x two seeds = 16 legs, all
`success`, 97 frames each, one resident server, sequential.

| Fixture | What it is | Why |
| :--- | :--- | :--- |
| `officer` | B&W close-up, flat background | easy control |
| `controlroom` | photoreal, 5 figures at depth, receding dials, haze | hard real content |
| `crowd` | illustrated, ~40 faces, glass tubes, meter scale | hard real content |
| `testcard` | authored acuity chart, gratings, bars, both polarities | the instrument |

The officer fixture was the whole lane at first. It is a poor discriminator --
the operator said so before any judging, and the panel then confirmed it: every
countable question tied on every seat. Had the lane shipped a verdict from that
fixture alone it would have measured the fixture, not the recipe.

Purity was proven twice per cell: on the staged arms (43 leaves, 3 changed) and
again on the graphs actually queued (46 leaves, 4 changed -- the three knobs
plus an inert `save.filename_prefix`). The gate was negative-tested against an
undeclared literal, a rewire, and a declared knob that failed to move.

## What the panels said

Blind 3-seat panels, countable questions only, no seat seeing another.

* **Seed 42** (4 fixtures, 12 seats): 10 TIE, 2 marginal-for-official. No
  fixture reached a 2-of-3 majority.
* **Seed 20260821** (3 fixtures, 9 seats): official 6, ours 2, TIE 1. `crowd`
  was unanimous 3/3 for official at *clear* margin.

That unanimous cell is what a win would have rested on.

## Why it was rejected

Three skeptics were run against the receipts. All three returned **refuted,
high confidence**. The two decisive findings were re-derived by the driver
against the real frames rather than taken on report:

**1. The apparent advantage is CONTRAST, not resolution.** In the judged crowd
face box at seed 20260821, raw Laplacian edge energy has official ahead of ours
by 22% at f097. After identical autocontrast is applied to both crops the ratio
is **0.980** -- official is fractionally *behind*. The edge advantage is
`shift 8` raising contrast, and higher contrast makes an edge easier to call
"coherent". Judges were told to ignore tone; they could not, because tone was
feeding the very counts they were asked for.

**2. The winning cell is the one where the arms stopped rendering the same
scene.** Arm-to-arm NCC at f097:

| cell | NCC | | cell | NCC |
| :--- | ---: | :-- | :--- | ---: |
| officer/42 | 0.9986 | | crowd/42 | 0.9483 |
| officer/20260821 | 0.9211 | | **crowd/20260821** | **0.6269** |
| controlroom/42 | 0.8962 | | testcard/42 | 0.9924 |
| controlroom/20260821 | 0.8883 | | testcard/20260821 | 0.9379 |

The claim rests entirely on the single outlier cell. A skeptic measured
Spearman(arm-arm NCC, count of non-TIE votes) = **-0.821** across the seven
judged cells: the panel ties when the two renders look alike and picks a winner
when they diverge. That is a divergence detector, not a quality judgement.

Supporting refutations, all verifiable in the receipts:

* **The seats were not independent, and that was my defect.** With two arms
  there are only two read orders, so three seats can never each have their own
  -- yet `make_judge_set.py` claimed they did and hard-coded one map in which
  seat2 and seat3 *both* read official first. All eight `KEY.json` files were
  byte-identical. "Unanimous 3/3" was at most two position conditions. Fixed:
  the odd seat and the leading arm are now derived per (fixture, seed), giving
  5 distinct configurations across the 8 cells instead of 1. **The panels in
  this lane ran under the flawed map and are reported as such.**
* **The instrument disagrees with itself on identical pixels.** On the same
  byte-identical f097 pair (confirmed by sha256), the three seats reported ours
  at 5-of-10, 8-of-9 and 1-of-3 coherent faces. Dense crowd-face counting is
  not a reliable readout.
* **Two of the three "unanimous" seats said in their own words the difference
  was not late-frame**, contradicting the claim's central word.
* **The seed-2 tally excluded `officer`.** Its judge set was built and never
  scored, so a 6-2-1 tally omitted the fixture most likely to tie. That framing
  was mine and it flattered the result.
* **The test card's tie is a saturated readout.** Row-and-pitch questions are
  quantized; measured continuously the card does not tie. The card is right to
  be countable, but its questions bottom out.
* **My own zoom-confound number was wrong.** I estimated ~1.10x vs ~1.12x
  differential push-in; measured properly it is ~1%, far too small to move a
  face count. The real geometric confound is translation: inside the fixed crowd
  crop box, official shifts +15.7px against ours at +1.1px, so a fixed box lands
  on ~7% different content.

## The A/A control, run after the refutation

The refutation's cheapest-settling-move was a null: render one arm twice and
judge it against itself. It was run.

**The pipeline is bit-exact.** `official_seed20260821` re-submitted from its own
byte-identical graph produced 97 frames identical to the first run by sha256,
NCC 1.0000 and mean absolute difference 0.000 at every frame.

**The panel passed its null.** Three seats on those byte-identical frames
returned TIE, margin none, all three. One wrote that naming a winner "would
mean inventing a difference I cannot see."

Two consequences, and they pull in opposite directions:

* **The seed-noise framing was wrong, and it was mine to correct.** There is no
  run-to-run nondeterminism, so the crowd/seed20260821 divergence is not noise
  -- it is a real, reproducible consequence of the recipe change. The arms
  genuinely walk into different scenes by frame 97 on that cell.
* **The judges do not fabricate winners.** So the 3/3 clear call reflects a real
  pixel difference. What the refutation established is that the difference is
  contrast and trajectory divergence, not quality -- which is why the verdict
  still stands.

## What is actually true

* **No detail-resolution difference.** The instrument says so on both seeds, and
  contrast-normalized edge energy agrees.
* **`shift 8` renders darker and higher-contrast.** Real, repeatable, and not a
  quality improvement.
* **Official is measurably LESS temporally stable**, on the axis a sampling
  recipe is most likely to move and which this lane had not measured until the
  completeness critic said so. Mean absolute frame-to-frame luminance change
  across all 97 frames, official against ours: officer +31% / +60%,
  controlroom -5% / +18%, crowd +18% / +37%, testcard +11% / +20%. Official is
  worse in 7 of 8 cells, with consistently larger worst-case spikes. On the test
  card the prompt asks for *nothing moving*, so that excess is flicker by
  definition.
* **Official loses grey neutrality.** On the card's 16-step neutral wedge, mean
  channel spread at f097, seed 20260821: ours 2.42, official **11.50** -- both
  starting from 1.36 at f001. The higher-shift arm drifts the greyscale off
  neutral by roughly eight times as much.
* Official is ~27% faster (150s vs 205s per leg). Irrelevant: quality did not
  tie in official's favour, and render-recipe quality is never traded for speed
  on this project.

So the result is not merely "no win". Two independent measurements on a
known-ground-truth target put the official recipe *behind* the shipped one.

## What this lane did NOT screen

The fleet-diff receipt lists nine differences between the official reference and
ours. This lane screened the three sampler parameters and held the rest at ours
in **both** arms, which is correct for a sampling-recipe screen but must be
said plainly so nobody reads this verdict as "the official graph loses":

* fp16 `UNETLoader` vs our Q5_K_M `UnetLoaderGGUF`
* fp8-scaled `CLIPLoader` vs our Q5_K_M `CLIPLoaderGGUF`
* untiled `VAEDecode` vs our `VAEDecodeTiled`
* reference canvas 1280x704 x 121 frames @ 24fps vs our 832x480 x 97 @ 25fps
* the reference's own negative prompt
* `CreateVideo` / `SaveVideo` terminal vs our in-process decoder read

Each is its own candidate lane. Several are VRAM discipline and will not be
given up; the precision deltas are the interesting ones.

**A caveat on `shift` specifically.** The shipped engine documents its value at
[`eng_wan_ti2v.py:211`](../../ComfyUI-OldTimeRadio/nodes/_otr_video_engines/eng_wan_ti2v.py):
*"5.0 is the 5B value (the 14B uses 8.0)"*, and the official reference pairs
shift 8 with the 1280x704 x 121 configuration. Sigma shift interacts with
resolution and sequence length, so this lane tested it at an operating point it
was not authored for. That does not rescue it -- the measurements above put it
behind at OUR operating point, which is the one that ships -- but a null for
shift 8 here is not a null for shift 8 everywhere.

## Open follow-ups (do not reopen this lane for them)

1. ~~No A/A control~~ **CLOSED.** Pipeline is bit-exact; the panel returns TIE
   on identical pixels. `tools/run_aa_control.py`, and re-run it once per lane.
2. Admit a cell to judging only when arm-to-arm NCC at the final frame clears a
   threshold (~0.90); below that the arms are not rendering the same scene and
   "which is better" is the wrong question.
3. Contrast-match before judging, or ask a tonal question explicitly instead of
   pretending judges can ignore tone. They cannot: it feeds their counts.
4. Anchor crops to tracked content, not fixed pixel boxes (official translates
   +15.7px against ours at f097, so a fixed box lands on ~7% different content).
5. Give the test card continuous readouts alongside the quantized ones, and add
   crops for the grey wedge, colour bars and gradient -- authored but never
   judged in this lane.
6. Write mean and max frame-to-frame delta into `RENDER.json` per leg. One numpy
   pass, no re-render, and every future lane gets a temporal baseline.
7. Re-test one cell at the reference canvas (1280x704 x 121) to close the shift
   transplant objection for good.
8. Hands are the one anatomy gap across the fixture set.

## Provenance

* Workbench: `basline-models`, lane `staging/lane1_wan_ti2v/`.
* Frames: `ComfyUI/output/baseline_output/lane1_wan_ti2v/`, never `otr/obs`.
* Panels: `judge/PANEL_seed42.json`, `judge/PANEL_seed20260821.json`.
* Officer pass-1 receipts were lost in the per-fixture move and rebuilt from
  ComfyUI `/history`, each re-derived graph compared against the server's own
  record of what executed; digests match the original run log.
* Measurement only. No OTR production code was touched, no model downloaded.
