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

## Bound

Four skipped segments (lane 1 crowd/42, lane 1 officer/20260821, lane 2
testcard/42, lane 3 march/20260821) are recorded as SKIPPED, not as ties. A
skip is an absence of evidence; a SAME is evidence.
