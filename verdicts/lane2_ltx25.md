# Lane 2 verdict -- `ltx25` I2V anchor strength, ours (1.0) vs soft (0.7)

**RESULT: NO WIN. The shipped anchor 1.0 stands. Nothing is queued as an OTR
item.** The verdict was decided by the matrix pre-declared in `LANE.json`
BEFORE any render: no identity regression + no material gain = null at the
shipping output = the shipped default stands.

## The knob

ONE shipping constant, `LTX25_I2V_ANCHOR_STRENGTH = 1.0`
(`ltx25_recipe.py:223`), feeding BOTH `i2v.strength` and `refine_i2v.strength`
(`eng_ltx25.py:1042`, `:1099`). 1.0 is the node default nobody chose; 0.7 is
the sibling audio lane's deliberate soft anchor. The recipe's own note framed
this lane ("0.7 vs 1.0 has never been A/B'd on this model") and warned the
hard pin is what fights the live face-identity defect -- which made identity a
GATE here, not a score.

The r1 kibitz (Codex + Antigravity, scoped r1) resolved the arm shape: an
`i2v`-only change is not a shippable configuration, so both leaves moved
together, and holding stage 2 at 1.0 would have re-planted the original still
against a drifted stage-1 clip (frame-0/frame-1 discontinuity).

## What was run

Three fixtures (officer = identity gate, crowd = multi-face stress, testcard =
drift control) x 2 arms x 2 seeds = 12 legs, all success, 97 frames each at
1664x960, one server, sequential. Purity proven on staged AND submitted graphs:
changed set exactly `{i2v.strength, refine_i2v.strength}` -- two leaves, one
knob. The one deliberate shared ADAPT is documented in every STAGING.json:
`te` runs the registered `CLIPLoaderGGUFCPU` in BOTH arms, matching
production's runtime CPU pin (`eng_ltx25.py:1188`) placement-for-placement, so
the bench ran production's memory path (no OOM; encode spike deleted).

**A/A null (mandatory, once per lane): PASSED -- 97/97 frames byte-identical**
on a re-submitted identical graph. The ltx25 pipeline is bit-exact, so every
arm difference below is 100% the anchor knob.

## The panel

18 blinded seats (3 fixtures x 2 seeds x 3 seats), per-cell label permutations,
countable questions only, identity asked first on the officer.

**CORRECTION (completeness critic, verified by the driver):** this verdict
first claimed the permutation fix gave "5 distinct configurations across
cells". That number was lane 1's, measured over lane 1's eight cells, pasted
here unchecked. Over lane 2's SIX cells the digest yields only **3 distinct
maps, and seat1 read the soft arm first in 5 of 6 cells** -- all four of
seat1's decided votes went to that first-read label. The permutation was
therefore weaker than claimed. It does not change the outcome (those votes are
marginal, in the direction the verdict already discounts, and the identity
gate is unanimous across all seat positions), but the receipt now says what
actually ran. `seat_plan` has been re-derived to include the lane name and
seat index in the digest so the variation is real next lane.

| | soft | ours | TIE |
| :--- | :---: | :---: | :---: |
| officer (identity gate) | 0 | 0 | **6** |
| crowd | 3 | 3* | 0 |
| testcard | 3 | 1 | 2 |
| total | 6 | 4 | 8 |

*includes the panel's only CLEAR-margin call, for OURS (crowd/seed42 crops).

**The identity gate: HOLD, 6 of 6 seats.** Same man at frame 97 in both arms,
both seeds, zero structural defects, likeness explicitly re-verified against
the reference at zoom by every seat. The operative risk of softening the
anchor -- the one the recipe note warned about -- did not materialize within a
single clip at this operating point.

**No material gain either.** Every soft-leaning call is marginal, and
directions flip between seats and seeds (crowd: seed42 leans ours, seed20260821
leans soft). Lane 1 established what that pattern is: judge noise around a
null, not an effect. The driver's own reads agree: officer arms differ by
expression only; on crowd BOTH arms walk off the reference framing by f97
(NCC 0.77/0.81), soft merely walks further -- drift is a property of this
fixture under ltx25, not a virtue of either arm.

Temporal receipts (now standard fields): soft is slightly more active
everywhere and its worst-case officer spikes are ~50-70% larger (max 1.44/1.60
vs 0.99/0.95) -- small, but the direction favours the shipped hard anchor on
the fixture that matters.

## Bounds on this null

* **Within-clip only.** Production's face-identity concern is BETWEEN beats
  (a new conditioning still per beat); this lane tested still-to-clip
  retention. A multi-beat identity probe is a different lane.
* This operating point only: 832x480 latent x 97 frames, the shipping canvas.
* **The motion axis was structurally untested, not measured null (completeness
  critic; verified).** Every fixture prompt demands stillness ("static
  locked-off camera ... no camera move"), and the seats judged three still
  frames per arm -- on stillness-prompted fixtures judged from stills, "no
  motion advantage" was guaranteed regardless of the knob. The long-motion
  fixture the driver anchor planned (and r1 accepted pending a 12.121 purity
  receipt) was dropped without being recorded; this line is that record. The
  driver's motion read from the temporal receipts and frame inspections:
  officer motion is breathing-level in both arms (means 0.43-0.51), the crowd
  walks in both arms with soft walking further, the card is static in both.
  If the soft anchor is ever re-argued, it must be on a motion-demanding
  fixture -- 4 legs on the existing harness.
* **Two receipt notes from the critic, both verified:** soft's worst-case
  temporal spikes on the officer sit at the FIRST frame pair on both seeds
  (a start transient -- the discontinuity family r1 predicted -- where ours
  peaks mid-clip at pairs 82/69); and two crop regions mis-framed their
  questions (the crowd meter exits the fixed crop by f097; the card crops
  carry no colour-bar region), so the affected counts were answered from
  partial evidence -- including the lane's only CLEAR call. Crop regions get
  a per-fixture overlay check next lane.

## Provenance

Workbench `basline-models`, lane `staging/lane2_ltx25/`; frames under
`ComfyUI/output/baseline_output/lane2_ltx25/`, never `otr/obs`. Panel:
`judge/PANEL.json` (run `wf_4d925968-580`, 18/18 seats, 0 errors). r1 kibitz
receipt: `r1_judgment.md` (scoped r1, Codex + Antigravity, reported as such).
Sonnet QA on the frozen code diff: no urgent findings; both hardening notes
applied. Bible `12.122` promoted from this lane's API-translation failure.
Measurement only: no OTR production code touched, no model downloaded, shipped
recipes untouched.
