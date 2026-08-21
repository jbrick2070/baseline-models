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

## What is actually true

* No detail-resolution difference between the recipes. The instrument says so
  on both seeds, and contrast-normalized edge energy agrees.
* `shift 8` renders darker and higher-contrast. That is a real, repeatable
  tonal difference and it is *not* a quality improvement.
* Official is ~27% faster (150s vs 205s per 97-frame leg). Irrelevant here:
  quality did not tie in official's favour, it simply tied, and render-recipe
  quality is never traded for speed on this project.

## Open follow-ups (do not reopen this lane for them)

1. **No A/A control exists anywhere in the method.** Re-rendering one arm twice
   and judging it against itself should return TIE on every seat. Until that
   null is run, no panel result on this project has a noise floor. This is the
   cheapest and highest-value fix and it should land before lane 2 is judged.
2. Admit a cell to judging only when arm-to-arm NCC at the final frame clears a
   threshold (~0.90); below that the arms are not comparable.
3. Contrast-match before judging, or ask a tonal question explicitly instead of
   pretending judges can ignore it.
4. Anchor crops to tracked content, not fixed pixel boxes.
5. Give the test card continuous readouts alongside the quantized ones.
6. Hands are the one anatomy gap across the fixture set.

## Provenance

* Workbench: `basline-models`, lane `staging/lane1_wan_ti2v/`.
* Frames: `ComfyUI/output/baseline_output/lane1_wan_ti2v/`, never `otr/obs`.
* Panels: `judge/PANEL_seed42.json`, `judge/PANEL_seed20260821.json`.
* Officer pass-1 receipts were lost in the per-fixture move and rebuilt from
  ComfyUI `/history`, each re-derived graph compared against the server's own
  record of what executed; digests match the original run log.
* Measurement only. No OTR production code was touched, no model downloaded.
