# Lane 1 pre-A/B receipt -- `wan_ti2v` sampling recipe

Bible `12.121` requires this receipt to exist *before* any render, because
single-variable discipline is routinely enforced on the graph delta between
arms and forgotten for the inputs both arms share. Two live instances on this
project were scored wrong for exactly that reason.

## 1. The conditioning input was inspected at native pixels

| Field | Value |
| :--- | :--- |
| File | `vram-recipe-lab/fixtures/portrait_16_9.png` |
| SHA-256 | `4fd6479da40a215ffda4867373ad330d6d45ab4bd34ffe3ad4c0db4fce40e375` |
| Native size | 1024 x 576 (16:9) |
| Staged to | `ComfyUI/input/portrait_16_9.png`, hash re-verified after copy |

Three 1:1 crops were cut and read at native pixels -- face, uniform, and a flat
background panel. The flat panel is the check that matters: a minted grid or
tiling defect shows up in smooth gradients long before it shows on a textured
face. It is a clean continuous gradient. The face crop is soft in the way a
frame grab is soft, with no square tiles at any scale.

**Finding: the defect class that voided the six earlier video-lane
eliminations -- an upstream-minted grid riding in on the still -- is ABSENT
from this conditioning input.** Nothing under test is already present in the
shared input.

## 2. Every shared input is aligned with the question this lane asks

The prompt describes the still it conditions on:

> 1950s black and white cinematic close-up of a military officer's face, facing
> the camera, holding his gaze steady, only subtle breathing and a slight head
> movement, static locked-off camera, single continuous shot, no cut, no scene
> change, no camera move.

The still is a black and white cinematic close-up of a uniformed officer facing
camera with a steady gaze. Prompt and conditioning agree, so neither arm is
being asked to walk away from the still -- the failure that made the earlier
identity-drift probe unscoreable.

The negative prompt, canvas (832 x 480), length (97 frames at 25 fps), CFG,
scheduler, denoise, tiling and every model file are the shipping engine's own
and are byte-identical across arms.

`Wan22ImageToVideoLatent` bilinear centre-scales the 1024 x 576 still to the
832 x 480 canvas internally. That happens identically in both arms and is
recorded here only so no later reader mistakes it for an arm difference.

## 3. Arm purity was proven mechanically, not by eye

`tools/purity_gate.py` flattens both graphs to dotted leaves and compares them
structurally. Any wiring or node-class difference fails the lane outright.

* Staged arms: 43 leaves compared, **3 changed**, changed set exactly
  `{ksampler.sampler_name, ksampler.steps, modelsampling.shift}`.
* Submitted graphs (what actually queued, per seed): 46 leaves, **4 changed** --
  the three knobs plus `save.filename_prefix`, which is a destination and
  cannot reach the sampler. Both legs of a seed carry the same seed value.
* The gate was negative-tested against an undeclared literal delta, a rewire,
  and a declared knob that failed to move. All three abort the lane.

## 4. The contrast

| Knob | OURS (shipping) | OFFICIAL |
| :--- | :--- | :--- |
| `KSampler.sampler_name` | `euler` | `uni_pc` |
| `KSampler.steps` | 30 | 20 |
| `ModelSamplingSD3.shift` | 5.0 | 8.0 |

Screened as a **bundle**. If the bundle wins, the knobs get decomposed
afterwards; decomposing a bundle that loses buys three renders of nothing.

Both arms were generated from the shipping engine `eng_wan_ti2v` through
`diffomatic.build_api_graph`, so everything outside the table is identical by
construction rather than by careful copying.
