# Lane 7 verdict -- `ltx25` anchor on the MOTION axis

**RESULT: NO WIN. The shipped `LTX25_I2V_ANCHOR_STRENGTH = 1.0` stands. Nothing
is queued as an OTR item.**

**But this lane CLOSES lane 2's bound rather than restating it, and it does so by
finding out that the question cannot be answered the way lane 2 assumed.**

8/8 legs succeeded. Purity gate clean on both fixtures: changed set EXACTLY
`[i2v.strength, refine_i2v.strength]`, 29 nodes and 112 leaves per side.
Workbench `8922eba`+; frames under
`output/baseline_output/lane7_ltx25_motion/`, never `otr/obs`.

## Why this lane existed

Lane 2 screened anchor 1.0 vs 0.7 and closed NO WIN, then wrote its own bound:

> *"the MOTION axis was structurally untested (every prompt demanded stillness,
> seats judged stills) -- if soft is ever re-argued it takes one
> motion-demanding fixture, 4 legs on the existing harness."*

Same contrast, unchanged. One constant feeds both `i2v.strength` and
`refine_i2v.strength`, so both leaves move together exactly as production does;
an i2v-only arm is not shippable and was not staged. The `CLIPLoaderGGUFCPU`
adapt is carried in BOTH arms, as lane 2 established.

## 1. THE MOTION GATE PASSED, and that is the lane's first real result

Lane 4 established that a prompt demanding movement does not produce it -- its
`testcard_motion` returned **0.0 px** translation in both arms at both seeds. So
this lane declared, before rendering, that a clip failing to move means the
FIXTURE failed, not that soft ties on motion.

| clip | excursion (f001 -> f097) | churn | moved |
| :-- | --: | --: | :-: |
| crossing/ours/42 | 47.045 | 15.553 | yes |
| crossing/soft/42 | 48.484 | 15.189 | yes |
| crossing/ours/20260821 | 48.303 | 15.834 | yes |
| crossing/soft/20260821 | 49.974 | 14.879 | yes |
| turning/ours/42 | 42.071 | 14.371 | yes |
| turning/soft/42 | 39.043 | 15.812 | yes |
| turning/ours/20260821 | 44.867 | 15.329 | yes |
| turning/soft/20260821 | 44.146 | 14.058 | yes |

**8 of 8 moved, and not marginally.** Excursion 39-50 against a declared floor
of 6.0. For scale, lane 6's crowd fixture -- which moves without being asked to
-- scored 9-12 excursion and 2.5-3.4 churn. **These clips move roughly four to
five times harder than that**, and vastly harder than lane 2's stillness
prompts, which asked for *"only subtle breathing and a slight head movement"*.

**So lane 2's structural gap is genuinely closed. The motion axis has now been
exercised.** That is the thing lane 2 could not say.

## 2. THE ADMISSION GATE REJECTED ALL FOUR CELLS. No panel was run.

Arm-to-arm NCC:

| cell | f001 | f049 | f097 | admitted |
| :-- | --: | --: | --: | :-: |
| crossing/seed42 | 0.9991 | 0.7911 | 0.5587 | no |
| crossing/seed20260821 | 0.9987 | 0.4860 | 0.6237 | no |
| turning/seed42 | 0.9995 | 0.4382 | 0.1660 | no |
| turning/seed20260821 | 0.9996 | 0.0669 | 0.3863 | no |

**0 of 4 admitted** against the ~0.90 floor lane 1 calibrated and lane 5
validated. Frame 1 is the shared conditioning still (~0.999, the wrapper doing
its job) and by frame 97 the arms have composed entirely different motion.

This is the same shape lane 3 and lane 5 hit, and for the same reason: once the
arms are free to move, one seed produces two different scenes and *"which is
better"* is the wrong question. **Judging anyway, or lowering the floor now that
the numbers are visible, is the goalpost move lane 5 refused.** No cell-by-cell
quality claim is made.

## 3. THE SUBSTANTIVE FINDING: under motion, the anchor stops governing departure

This is the mechanism the lane assumed. A soft anchor is supposed to let the
clip depart further from its conditioning still -- invisible on a stillness
fixture, which is exactly why lane 2's null was bounded. Per-arm NCC of the
final frame against the conditioning still:

| cell | ours (1.0) | soft (0.7) | soft departs more? |
| :-- | --: | --: | :-: |
| crossing/seed42 | 0.0219 | 0.0254 | no |
| crossing/seed20260821 | 0.0238 | -0.0027 | yes |
| turning/seed42 | 0.0080 | 0.1417 | no |
| turning/seed20260821 | 0.2103 | -0.0019 | yes |

**Two of four. A coin flip -- the assumed mechanism does not reproduce.**

And the more important number is the absolute one: **every value is essentially
zero.** Seven of the eight sit between -0.003 and 0.21, meaning that under a
genuine motion demand **BOTH arms end up almost completely uncorrelated with the
still they were handed**, regardless of anchor strength.

**So the anchor does not measurably govern final departure once the prompt
demands large movement.** That reframes lane 2's bound instead of merely
answering it: the motion axis was worth testing, and the answer is that this
knob has little left to control by the end of a moving clip. It also explains
the admission failures -- if neither arm is held to the still, they are free to
diverge, and they do.

## 4. What this means for the programme

**A seventh null, and the shipped value stands.** But unlike a bare tie this one
carries a mechanism: the knob's authority decays under motion. Anyone re-arguing
the soft anchor now has to explain what it would control, on a path where both
values end up equally far from the conditioning image.

**Lane 2's bound is discharged.** It asked for one motion-demanding fixture and
four legs; it got two fixtures and eight, the gate passed decisively, and the
axis is tested. It should not be re-opened as "untested" again.

## 5. Bounds

* **No panel, no operator eye, no quality claim.** The admission gate refused
  every cell, so this verdict rests on instruments only.
* Two fixtures, two seeds, both i2v-conditioned. The `crossing` fixture puts a
  crowd through the frame; `turning` puts identity under head rotation.
* The anchor measurement is whole-frame NCC against the conditioning still. It
  says the clip departed; it does not say the FACE changed, which is the
  separate open item.
* The arms sampled independently here (~200s per leg, no shared latent), unlike
  lane 6 where the contrast sat below the sampler. That is correct for this
  contrast and it is also why divergence is so wide.
* Nothing here revisits lane 2's within-clip identity gate, which held 6/6.
