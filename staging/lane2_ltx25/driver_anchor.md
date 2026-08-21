# Lane 2 driver anchor -- `ltx25` stage-1 I2V anchor 0.7 vs 1.0

Written by the driver from the real Windows files BEFORE any panel sees it.
Every claim below carries its file and line. The panel proposes; the driver
disposes, and every panel claim gets re-checked against these same files.

## What actually ships

`eng_ltx25` builds a 29-node AV graph. Confirmed API-submittable end to end via
`diffomatic.build_api_graph('eng_ltx25')` -- no node resolves to a local Python
class, so unlike the LTX sigma-injector worry this lane CAN be staged as two
API arms exactly like lane 1.

Grounded values, read off the built graph:

| Node | Class | Literals |
| :--- | :--- | :--- |
| `i2v` | `LTXVImgToVideoInplace` | `strength 1.0`, `bypass false` |
| `refine_i2v` | `LTXVImgToVideoInplace` | `strength 1.0`, `bypass false` |
| `emptylatent` | `EmptyLTXVLatentVideo` | 832x480, length 97 |
| `sched` | `LTXVScheduler` | steps 8, max_shift 2.05, base_shift 0.95, terminal 0.1 |
| `guider` | `LTXVDualCFGGuider` | video_cfg 1.0, audio_cfg 1.0 |
| `decode` | `VAEDecodeTiled` | final decode |

The knob under test is declared in the recipe as a constant:
`LTX25_I2V_ANCHOR_STRENGTH = 1.0` (`nodes/_otr_video_engines/ltx25_recipe.py:224`).

## Why this lane exists, in the recipe's own words

`ltx25_recipe.py:207-215` says, corrected 2026-08-19: **1.0 IS THE NODE'S
UNTOUCHED DEFAULT, NOT A MEASUREMENT.** `LTXVImgToVideoInplace` ships `strength`
defaulting to 1.0 and the recipe never touched the widget. The sibling audio
lane deliberately uses **0.7, a SOFT anchor**, with a written reason
(`eng_ltx_av.py:972`). So this is one deliberate choice and one default nobody
set -- not two teams disagreeing.

The same note names this lane almost verbatim: *"If it ever wants revisiting,
the honest framing is '0.7 vs 1.0 has never been A/B'd on this model'."*

## THE ASYMMETRY THAT MUST SHAPE THE JUDGING

`ltx25_recipe.py:216-219`: *"A hard pin at frame 0 is the correct default for
OTR's actual problem -- 'a character's face changing between beats' is a live
CORRECTNESS defect in CLAUDE.md, and the harder anchor is the one that fights
it."*

So the risk is NOT symmetric. A softer anchor plausibly produces freer, more
natural motion -- which reads as "better" on any loose question -- while
regressing the exact correctness defect the project is still fighting. A lane
that asks "which looks better" will pick 0.7 and be wrong.

**Therefore: identity preservation is a GATE, not one score among many.** If 0.7
loosens identity at all, it loses regardless of how much nicer the motion looks.
Lane 1 already proved judges cannot set aside an axis they are told to ignore
(tone fed their counts), so identity must be asked FIRST and counted explicitly
against the conditioning still.

## THE THREE FORKS THE PANEL IS FOR

**FORK 1 -- does the contrast move one anchor or both?** There are TWO
`LTXVImgToVideoInplace` nodes at strength 1.0: `i2v` (stage 1) and `refine_i2v`
(the stage-2 refine re-anchor, which re-plants the same still). The voted lane
says "stage-1 anchor", which reads as `i2v` only. But if stage 2 re-pins at 1.0,
it may simply restore the hard anchor and the A/B returns "no difference" for a
MECHANISTIC reason -- an uncontrolled downstream variable, exactly Bible
12.121's failure mode, which is what voided six earlier eliminations.
* (a) `i2v` only -- literal reading of the vote; risks a masked null.
* (b) both anchors -- tests "soft anchoring" as a doctrine; but that is a
  different, larger question than the one voted.
* (c) both, as two separate arms (three-arm lane) -- most informative, most
  expensive, and breaks the two-arm purity-gate shape.
**RESOLVED BY THE DRIVER AFTER THIS ANCHOR WENT OUT -- and it goes AGAINST the
driver's provisional read. Both anchors read the SAME CONSTANT.**
`eng_ltx25.py:1042` (`i2v`) and `eng_ltx25.py:1099` (`refine_i2v`) each take
`R.LTX25_I2V_ANCHOR_STRENGTH`, defined once at `ltx25_recipe.py:223`. There is
exactly ONE knob in shipping code and it drives BOTH anchors.

Consequences:
* Option (a), `i2v` only, is **not a shippable configuration**. Reaching it
  requires splitting one constant into two, which is itself a design change and
  is not what the lane voted.
* Option (b) is simply *what changing the constant does*, so it is the honest
  arm. The declared contrast becomes `i2v.strength` AND `refine_i2v.strength`,
  1.0 -> 0.7 -- two graph leaves representing ONE shipping knob. The purity gate
  must declare both and the receipt must say plainly that they are one knob, or
  a later reader will count two undeclared deltas.
* The masked-null worry is therefore real but self-cancelling: because the
  constant moves both, stage 2 cannot re-pin at 1.0 while stage 1 sits at 0.7.
* `eng_ltx25.py:1096-1098` says the second anchor exists because
  `LTXVLatentUpsampler` deliberately drops `noise_mask`, and the full-strength
  anchor "recreates it while planting the same still into the doubled latent".
  So softening it also softens that mask reconstruction -- a second-order effect
  the panel should be asked about, and the reason this lane is a design fork
  rather than a knob twiddle.

The panel received this anchor with Fork 1 still open; their independent reads
are graded against the finding above.

**FORK 2 -- what is the fixture, given this is an AV engine?** The graph carries
`audiovae`, `emptyaudio` (`LTXVEmptyLatentAudio`), `concat`/`separate` AV pairs
and a modality guidance node. The builder fixture feeds `diffomatic.wav`. A real
lane needs a real audio input, and audio content plausibly interacts with anchor
strength through `LTXVModalityGuidance`. Options: reuse a fixture wav from
`vram-recipe-lab/fixtures/`, or run silent. Unresolved.

**FORK 3 -- do lane 1's fixtures transfer?** Lane 1's four fixtures were chosen
for a sampler screen. For an ANCHOR test the discriminating content is different:
what matters is a subject whose identity can drift (faces), not fine texture. The
test card is nearly useless here -- it has no identity to lose and no natural
motion. Provisional: officer (identity, the real risk), crowd (many faces), and
a NEW long-motion fixture; drop controlroom and testcard, or keep testcard purely
as a drift detector since it should not move at all.

## Method carried from lane 1, non-negotiable

* Both arms generated from the shipping engine via `build_api_graph`; purity
  gate on staged AND submitted graphs.
* A/A null once per lane (`tools/run_aa_control.py`). Pipeline was bit-exact on
  wan; re-prove it here.
* **NCC admission threshold ~0.90** at the final frame. Below it the arms are
  not the same scene and "which is better" is the wrong question.
* Contrast-match before judging, or ask about tone outright.
* Per-leg temporal metrics via `tools/temporal_stats.py`.
* Seat permutation now varies per (fixture, seed) -- the fixed map was a lane 1
  defect.

## What the driver wants from the panel

1. Fork 1 above -- is `i2v`-only a real test or a masked null, and if masked,
   what is the cheapest honest way to detect that?
2. Whether identity-as-a-gate is the right framing, or whether it over-constrains
   a lane whose whole point is that 1.0 was never chosen deliberately.
3. Fork 2 (audio fixture) and Fork 3 (which fixtures) -- concrete picks.
4. Anything in the 29-node graph that makes `strength` NOT a clean single knob.
