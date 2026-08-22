# Lane 6 verdict -- `wan_ti2v` tiled vs untiled VAE decode

**RESULT ON THE PRE-DECLARED MATRIX: NO WIN. No tile seam exists, which was the
declared win condition. The shipped `VAEDecodeTiled` recipe is NOT changed.**

**BUT THE LANE FOUND SOMETHING ITS MATRIX DID NOT ANTICIPATE, AND IT IS LARGE:
tiled decode costs 4-5x more frame-to-frame churn on flat graphic content.**
That is recorded here as a measured observation with its numbers, and it is
NOT converted into a retroactive win. It wants its own lane with a temporal
matrix declared before rendering, and it wants the operator's decision, because
it touches a recipe he has protected.

8/8 legs succeeded. Workbench `846c87c`+; receipts `LANE.json`, `ANALYSIS.json`,
`*/STAGING.json`, `*/ARMS.sha256`; frames under
`output/baseline_output/lane6_wan_tiled_decode/`, never `otr/obs`.

## What was contrasted, and why the arms are unusually clean

One node. `vaedecode`: `VAEDecodeTiled` (tile 256, overlap 64, temporal 16,
temporal-overlap 8) -> `VAEDecode`. Both arms generated from the shipping
engine via `diffomatic.build_api_graph`, so everything upstream is identical by
construction. **Purity gate passed on both fixtures with the changed set exactly
the declared class swap.**

**The shipped recipe was not touched.** `tiled_vae` is a frozen recipe field
whose env knob only binds under the prequalification consent act; this lane did
not open that act and swapped a node in the staged API JSON instead.

**The arms shared their latents, and that is provable rather than assumed.**
Arm-to-arm NCC is **0.9931-0.9999** across all 12 scored frames. Independently
sampled arms in this programme score far lower -- lane 5's i2v arms ran
0.40-0.69, lane 3's t2v arms 0.14-0.74. A number this high can only mean
ComfyUI served the candidate leg the cached `KSampler` output, which the graphs
make inevitable: they differ *only* below the sampler. **So the decoder is
isolated perfectly, and every difference below is the decoder's doing.**

*(Corollary, and a trap avoided: the raw leg times -- ~180s for `ours` against
~18-20s for `candidate` -- do NOT mean untiled decode is 9x faster. The `ours`
leg of each pair paid for the sampling; the candidate leg decoded a cached
latent. A clean decode-time comparison was never run and none is claimed here.)*

## 1. There is no tile seam. The classic tiling artifact simply is not present.

| cell | f001 | f049 | f097 | admitted |
| :-- | :-- | :-- | :-- | :-: |
| crowd/42 | 1.026 / 0.969 | 0.990 / 1.002 | 1.062 / 1.093 | 3/3 |
| crowd/20260821 | 1.026 / 0.969 | 1.049 / 1.074 | 1.072 / 1.029 | 3/3 |
| testcard/42 | 0.640 / 0.913 | 1.026 / 0.957 | 0.849 / 0.871 | 3/3 |
| testcard/20260821 | 0.640 / 0.913 | 0.985 / 0.966 | 0.871 / 0.956 | 3/3 |

*(column ratio / row ratio; threshold for "seam" was declared at 1.15)*

The metric takes the per-pixel difference between arms and asks whether it
concentrates on the tile lattice. **It does not** -- the highest value across 24
measurements is 1.093, and most sit at or below 1.0. Spatially the two decoders
are near-identical: max mean absolute difference **5.2/255 = 2%**.

**A defect in the instrument, found and fixed mid-analysis.** The first version
stepped the lattice by `TILE` (256). Overlapping tiles advance by the **stride**
(`TILE - OVERLAP` = 192), so that mask marked columns no tile edge passes
through and missed real ones. Correcting it moved the ratios from ~0.76-0.99 to
~0.97-1.09 -- the fix mattered, and the no-seam conclusion survived it. Had the
conclusion been drawn on the broken mask it would have been right by luck.

## 2. THE FINDING: tiled decode churns 4-5x more on flat graphic content

Consecutive-frame absolute difference across all 97 frames, both arms:

| cell | arm | mean | **median** | p95 |
| :-- | :-- | --: | --: | --: |
| testcard/42 | ours (tiled) | 2.934 | **2.828** | 5.226 |
| testcard/42 | candidate (untiled) | 1.046 | **0.662** | 2.595 |
| testcard/20260821 | ours (tiled) | 2.761 | **2.825** | 4.195 |
| testcard/20260821 | candidate (untiled) | 0.720 | **0.580** | 1.319 |
| crowd/42 | ours | 2.562 | 2.373 | 5.024 |
| crowd/42 | candidate | 2.029 | 1.672 | 5.172 |
| crowd/20260821 | ours | 3.402 | 2.874 | 7.508 |
| crowd/20260821 | candidate | 3.047 | 2.321 | 7.327 |

**On the test card the tiled arm churns 4.3x and 4.9x more at the median**, at
both seeds. The test card's prompt demands a static, rigid card
(*"flat, square and rigid ... locked-off camera"*), so on that fixture
frame-to-frame change is unwanted by construction: **this is flicker, and lower
is better.**

**The p95 and max values are close between arms** (8.77 vs 8.33; 5.55 vs 4.71).
So this is not a handful of large events -- it is the BASELINE that differs. The
tiled arm is in constant low-level motion where the untiled arm sits still.

**On real content the gap collapses to 1.2-1.4x**, which is what one would
expect: the crowd fixture has legitimate motion that swamps the effect.

### The frozen-clip check, because low churn can also mean a dead clip

A clip that barely changes scores low whether it is holding a rigid card (good)
or stuck (bad). Whole-clip excursion, frame 1 to frame 97:

| cell | ours | candidate |
| :-- | --: | --: |
| testcard/42 | 18.557 | 17.752 |
| testcard/20260821 | 17.400 | 16.333 |
| crowd/42 | 8.995 | 8.782 |
| crowd/20260821 | 12.480 | 12.830 |

**Both arms travel the same distance -- within 6% everywhere.** The untiled arm
is not frozen; it reaches the same place by a smoother path. Same trajectory,
less jitter along it, which is the textbook signature of removing flicker rather
than removing life.

## 3. Why this is NOT called a win here

`LANE.json` declared before rendering that a seam *"is the candidate's win
condition and the only one that matters"*. **No seam was found, so on the
declared matrix this lane is a NO WIN and the shipped recipe stands.**

Promoting the temporal result to a win now would be exactly the move lane 5
refused -- *"judging anyway, or lowering the floor to catch a cell once the
numbers were visible, would be moving the goalposts after seeing the data."*
The prior was reasonable (seams are the classic tiling artifact) and it was
simply wrong about which defect tiling produces here.

**So the finding is recorded, not cashed.** What it earns is a follow-up lane
with a temporal matrix declared up front, and an operator decision -- not a
recipe edit made by the driver on the strength of an unplanned measurement.

## 4. What the operator is owed, in one paragraph

Tiling was frozen ON for VRAM at the 8 GB tier, on the LTX tier's evidence, and
the engine's own comment calls those numbers *"context for a future WAN sweep
and not a claim about these numbers"* (`eng_wan_ti2v.py:221-226`). This was that
sweep. It found no seam and a 4-5x temporal cost on flat graphic content at both
seeds, with the arms otherwise 98% identical. **His standing directive is that
the recipes are not on the table and that no VRAM or speed finding justifies a
change -- but this is a QUALITY finding, which is the one kind that directive
does not cover.** It is his call, and it needs the missing half first: what
untiled decode actually costs in VRAM on this box, which this lane did not
measure.

## 5. Bounds

* **Decode-time and VRAM were NOT measured.** Caching confounded the timings and
  no peak probe was run per arm. The whole cost side of the trade is missing.
* Two fixtures, two seeds, 12 scored frames. No blind panel and no operator eye.
* The temporal metric is a whole-frame mean absolute difference. It does not
  localise the churn or prove it is visible to a viewer at 25fps.
* Flat graphic content is where the effect is large; ordinary content showed
  1.2-1.4x. Most OTR beats are ordinary content.
* `still_word` cards ARE flat graphic content, so they are the production case
  most likely to be affected -- and they are ~3% of episodes.
