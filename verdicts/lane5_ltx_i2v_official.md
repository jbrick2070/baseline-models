# Lane 5 verdict -- the OFFICIAL ltx_video pairing, on the i2v path

**RESULT: NO WIN. The shipped `_LTX_DISTILLED_LORA_STRENGTH = 0.70` on
`ltx-2.3-22b-distilled-lora-384-1.1` stands. Nothing is queued as an OTR item.**

This lane existed to close the two bounds lane 3 wrote into its own verdict,
and it closes both.

## What was tested, and why it is different from lane 3

Lane 3 screened 0.7 vs 0.5 on OUR LoRA, through `_build_graph` -- the
**text-only** builder. Its completeness critic then found that production
defaults to image-conditioned (`_i2v_enabled()` reads `OTR_ENABLE_LTX_I2V` with
a default of `"1"`, `eng_ltx_video.py:931`), so that null was proven on a path
the show does not use. Lane 3 also said in writing that it "says nothing about
the official file+strength combination."

Lane 5 fixes both:

* **The path.** Staged through `_build_graph_i2v` via the new
  `diffomatic.build_api_graph(builder_name=...)`, so the graphs carry
  `LoadImage -> LTXVImgToVideoConditionOnly` -- 16 nodes, not 14.
* **The file.** The candidate is the official pairing the ComfyUI template
  actually ships: `ltx_2.3_22b_distilled_1.1_lora_dynamic_fro09_avg_rank_111_bf16`
  (2.74 GB, `Comfy-Org/ltx-2.3`) at strength 0.5, downloaded on operator
  authorization and verified byte-exact (2,741,024,390 bytes, 4,980 tensors).

**A BUNDLED SCREEN, and the price was stated before rendering.** File and
strength move together because that pair IS the official configuration.
A win could not have been attributed to either alone without a decomposition
lane. It is a loss, so no decomposition is owed.

8 legs (2 fixtures x 2 arms x 2 seeds), all success, 97 frames each. Purity
proven on staged AND submitted graphs: changed set exactly
`{lora.lora_name, lora.strength_model}` plus the output destination.
The official arm rendered consistently FASTER (100-110s vs 110-140s), which is
what a 2.74 GB LoRA against a 7.6 GB one should do.

## The A/A null, and why it matters more than usual here

**97/97 frames byte-identical; NCC exactly 1.000000 at f049 and f097.**
The i2v pipeline is bit-exact, so the correlation noise floor is 1.0 and every
departure below it is caused by the knob.

This was not ceremony. The admission floor of ~0.90 was calibrated on
`wan_ti2v` in lane 1, where arms tracked at 0.89-0.999, and applying it to a
different engine without re-validating it would have been an assumption
wearing a receipt's clothes. The A/A settles it: the gate measures the arms,
not the engine.

## The admission gate fired, and the lane is NOT judged

`LANE.json` declared BEFORE rendering that on an i2v lane the arms share a
conditioning still, so arm-to-arm NCC is "a real admission gate here, not
merely a flag." Final-frame arm-to-arm correlation:

| cell | f001 | f049 | f097 | admitted |
| :--- | :---: | :---: | :---: | :---: |
| crowd/seed42 | 0.9990 | 0.7115 | 0.6850 | no |
| crowd/seed20260821 | 0.9995 | 0.9582 | 0.3955 | no |
| portrait/seed42 | 0.9998 | 0.4677 | 0.6653 | no |
| portrait/seed20260821 | 0.9998 | 0.3991 | 0.4236 | no |

**0 of 4 cells admitted.** No blind panel was run and no cell-by-cell "which is
better" claim is made. Judging anyway, or lowering the floor to catch
`crowd/seed20260821` at f049 once the numbers were visible, would be moving the
goalposts after seeing the data -- which is exactly how lane 3 produced a 9-8
split that carried no signal.

## What decides it, then

**The operator's eye, which is the final seat in the voted method.** Shown the
frames without being told which arm was which, unprompted: *"they all look
good"* and *"compared to what we saw yesterday the differences are minute."*
When the shipped arm and the official arm both look good to the person shipping
the product, the shipped one stands -- switching costs a change and buys
nothing demonstrable. The burden was the candidate's and it did not clear it.

Supporting, none of it decisive on its own: temporal means are close and split
(official lower in 3 of 4 cells, within the noise earlier lanes established);
the orphan-object hunt the operator defined after lane 3 found nothing pointed
on either arm.

## THE REAL FINDING, and it is not an A/B result

**Both arms walk away from their conditioning still.** Per-arm NCC against the
still it was handed:

| cell | f001 (both) | f097 ours | f097 official |
| :--- | :---: | :---: | :---: |
| crowd/seed42 | ~0.997 | 0.1354 | 0.1142 |
| crowd/seed20260821 | ~0.997 | 0.3391 | **0.7938** |
| portrait/seed42 | ~0.999 | 0.3571 | 0.3704 |
| portrait/seed20260821 | ~0.999 | 0.3096 | 0.2909 |

Frame 1 IS the still (~0.999) -- the wrapper doing its job. By frame 97 both
arms sit at 0.11-0.36 against it.

**Stated carefully, because it is easy to overclaim:** some decorrelation is
CORRECT. It is video, things move, and a static reference naturally correlates
less as a scene evolves. This is not, by itself, evidence of a defect. What it
IS: the first measurement of still-retention on the path production actually
renders, and it belongs to the same family as the open "face and costume change
between beats" item. A future lane wanting to chase that now has a number and a
tool (`tools/ncc_stats.py`) instead of an impression.

One asymmetry, with its limit: on `crowd/seed20260821` the official arm held
the still at 0.794 against ours at 0.339 -- more than twice as close. The other
three cells are level. **One outlier cell cannot separate a real effect from
scene luck**, and it is recorded as an observation, not a finding.

## Bounds

* **Bundled screen:** file and strength moved together; this lane cannot say
  which of the two, if either, matters.
* **Two fixtures, not three.** The authored test card was deliberately excluded:
  it is drawn at 832x480 and its value is that element sizes are KNOWN at the
  render canvas (`make_testcard` says so in its own docstring). At 1024x576 it
  would be judged through a resampler, destroying the acuity ladder.
  Re-authoring it at this canvas is a follow-up.
* **The admission floor is inherited from lane 1** and validated here only in
  the sense that the A/A proves it measures arms rather than engine noise.
  Whether ~0.90 is the RIGHT floor for an LTX i2v clip at 97 frames is not
  established; what is established is that these four cells fall far below it.
* Same-canvas, same-length, two seeds, one server, sequential.

## Provenance

Workbench `basline-models`, lane `staging/lane5_ltx_i2v_official/`; frames
under `ComfyUI/output/baseline_output/lane5_ltx_i2v_official/`, never
`otr/obs`. Receipts: `NCC.json`, `crowd/render/AA_CONTROL.json`,
`*/render/RENDER.json`, `*/STAGING.json`. Measurement only: no OTR production
code touched, shipped recipes unchanged.
