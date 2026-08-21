# Operator eye pass -- all four lanes, 2026-08-21

The voted method names the operator's eye as the final judge seat. Across lanes
1-4 it had never been exercised; the blocker was friction, not willingness --
twenty-four pair clips in four directories with a key to cross-reference. The
reel (`tools/make_operator_reel.py`, 24 segments, 93s) collapsed that to one
file and one sitting.

**Conditions: blind.** LEFT/RIGHT alternate per fixture
(`make_clips.left_arm_for`), no arm is named anywhere on screen or on the
viewer page, and each segment carries a countable question rather than a
preference question. No prior lane result was shown. Decoded against each
lane's own `_clips/CLIPS.json` `left_right_mapping` AFTER the calls were in.

## The tally

| | count |
| :--- | :---: |
| SAME | **15** |
| decided | 5 |
| skipped | 4 |
| total | 24 |

Operator's own summary, unprompted: *"overall mostly the same."*

## The five decided calls, decoded

| seg | cell | call | resolves to |
| :--- | :--- | :---: | :--- |
| 3 | lane 1 crowd seed 20260821 | RIGHT | official |
| 12 | lane 2 officer seed 42 | RIGHT | soft |
| 16 | lane 3 march seed 42 | LEFT | **half** |
| 18 | lane 3 portrait seed 42 | LEFT | ours |
| 22 | lane 4 crowd seed 42 | LEFT | ours |

Candidates 3, shipped 2.

## What it does and does not change

**It overturns nothing.** No lane drew a consistent operator preference across
BOTH of its seeds -- every decided call sits beside a sibling cell the operator
marked SAME. That is the pattern lane 1 established and named: judge noise
around a null rather than an effect. All four verdicts stand as written.

**Segment 16 is the one that matters, and it is not a win.** march/seed42 is
where two of three blinded seats called `half`, and where the driver's strip
read claimed the opposite -- "ours plays its instruments, half carries them."
The lane 3 completeness critic found that claim unsupported by the seats and it
was withdrawn earlier the same day. The operator's independent eye now lands on
`half` as well. **Three independent reads converge, and the one that was wrong
was the driver's.** The withdrawal was correct, and it is now corroborated by
the seat the method reserved as final.

## Two disagreements, both recorded rather than resolved

* **Eye vs metric, lane 1 crowd/20260821.** The operator picked official; the
  temporal receipts put official BEHIND on 7 of 8 cells, and the test card's
  grey wedge put it behind on tone neutrality. One cell of four, against a
  measurement that spans eight. Recorded as a disagreement, not a correction --
  a single eye call does not outweigh a measured trend, and a measured trend
  does not make an eye call wrong about that cell.
* **Lane 4 cell mismatch.** The operator's lane 4 call is on crowd/seed42,
  while the instrument anomaly (-19 px drift against a locked-camera prompt,
  +14% temporal churn) is on crowd/seed20260821 -- which he marked SAME. The
  eye and the instrument are pointing at different cells, so neither
  corroborates the other here.

## ADDENDUM -- the operator returned to a SKIPPED segment with a specific defect

After submitting his calls the operator went back to segment 15
(**lane 3 march seed 20260821**, which he had SKIPPED) and pointed at the RIGHT
panel: *"drum is by itself, no person playing it."* lane 3 march is
`LEFT=half, RIGHT=ours`, so he was pointing at the **SHIPPED 0.70 arm**.

**Verified by the driver at native pixels, both arms, same seed, same frame:**

* `ours_seed20260821/frame_00049_.png` -- four bandsmen, **all four playing
  trumpets**, and the snare drum floating at waist height between the first two
  with no carrier: no straps, no arms on it, no drummer. An orphan object.
* `ours_seed20260821/frame_00097_.png` -- the drum is still there with a
  partially formed red figure behind it, half-attached rather than carried.
* `half_seed20260821/frame_00049_.png` -- the drum is **carried by a
  red-uniformed bandsman with visible hands on it**.

**This is a third independent convergence on the same observation.** Blinded
seat1 recorded it for this exact cell -- "its snare drum is carried and played
by a visible drummer in every frame, while A's drum floats with no carrier in
two of three frames -- an at-a-glance orphan object" -- and the KEY for
march/seed20260821 makes seat1's A the `ours` arm. The seat, the operator's
eye, and the frames agree.

**What it changes.** Not the verdict: this cell already voted `half` in the
tally (march 3-3), so the finding is counted, and the candidate still showed no
material gain overall. What it does is finish off the driver's withdrawn strip
read. That read claimed "ours plays its instruments (trumpets raised, snare
carried), half mostly carries horns at its sides." The critic showed the seats
contradicted it at seed 42; the operator has now contradicted it at seed
20260821, on the very detail it asserted. The claim was wrong at BOTH seeds and
its withdrawal is correct at both.

**What it does NOT license, and this bound is load-bearing.** It is ONE cell of
ONE lane, on a t2v lane where the arms legitimately compose different scenes
from the same seed (arm-to-arm NCC 0.2587 here -- essentially uncorrelated), so
an orphan object in one arm is substantially scene luck rather than a proven
property of the strength value. **And it is on the TEXT-ONLY path, which
production does not use by default** (`OTR_ENABLE_LTX_I2V` defaults to `"1"`).
So it is not evidence that shipped episodes carry orphan objects. It IS a
concrete reason to look for structural defects on the i2v path when lane 5
runs -- an operator-visible orphan object is exactly the class of defect that
would embarrass a published episode, and nobody has yet looked for it on the
path production actually renders.

## Bound

Four skipped segments (lane 1 crowd/42, lane 1 officer/20260821, lane 2
testcard/42, lane 3 march/20260821) are recorded as SKIPPED, not as ties. A
skip is an absence of evidence; a SAME is evidence.
