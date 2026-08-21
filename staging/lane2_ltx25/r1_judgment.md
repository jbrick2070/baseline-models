# r1 judgment -- lane 2 `ltx25` anchor 0.7 vs 1.0

Driver: Claude (Cowork). Reviewers: Codex + Antigravity. Both lanes returned
non-empty reviews; roster complete for r1. Every claim below was checked against
the real Windows files before acceptance.

## ACCEPTED -- driver errors the panel caught

**A1. FORK 2 was invented. Delete it.** CONFIRMED, both reviewers.
`eng_ltx25.py:353` sets `family = "image_to_video"` with the comment "nothing
about this lane consumes audio ... the audio latent it computes is thrown away";
`required_inputs = ("text_prompt", "init_image")` (`:365`); `_build_graph`'s
signature (`:899`) has no audio parameter; `LTX25_CFG_MODALITY = 1.0`
(`ltx25_recipe.py:120`). Diffomatic's `diffomatic.wav` is a generic fixture field
that is never passed. There is no audio fork. The lane runs the built-in
`emptyaudio` path in both arms.

**A2. Dropping the test card violates a binding rule I wrote myself.** CONFIRMED
(Codex). `docs/GO_FORWARD_PLAN.md:312-319`: "Every lane carries hard content AND
the authored test card." Antigravity argued the opposite -- that a card with no
face cannot test drift -- and it is right about the card's *identity* value but
wrong about the rule. Resolution: the card stays as a **drift/control** fixture,
explicitly excluded from the identity gate. A card that must not move at all is a
clean flicker detector, which is precisely what an anchor change could disturb.

**A3. NCC ~0.90 is the wrong gate for THIS lane.** CONFIRMED, both reviewers,
by different routes. Codex: NCC measures pixel correspondence, not identity, and
would reject the intended freer-motion effect. Antigravity: the soft arm is
*designed* to drift, so a strict gate produces false rejections. Both are right,
and the lane 1 rule was written for a sampler screen where divergence meant "not
the same scene". Resolution: for anchor lanes NCC is a **flag, not a gate**;
identity is judged directly against the conditioning still on native-pixel face
crops, and `tools/temporal_stats.py` carries the stability axis.

**A4. `build_api_graph` proves serialization, not submittability.** CONFIRMED
(Codex). Lane 1 additionally verified every class and model filename against a
live `/object_info`; lane 2 has not. Required before any render planning.

**A5. Pre-declare the verdict matrix before rendering.** ACCEPTED (Codex).
Lane 1's own refutation faulted the absence of a pre-registered decision rule.
Adopted: identity regression = LOSS regardless of motion gain; identity hold plus
material motion/stability gain = candidate WIN; null at the shipping output =
LOSS; semantic scene failure = invalid cell, fix the fixture, not a vote.

**A6. Judge identity on RAW crops, not contrast-normalized ones.** ACCEPTED
(Codex). Lane 1's contrast-matching rule was written to stop tone feeding
*detail* counts; applying it to facial evidence could alter the evidence. Raw
first, normalized copies only for secondary motion/detail questions.

## REJECTED -- with reason

**R1. Codex: "keep the decision contrast strictly `i2v.strength`" and "cut both
anchors".** REJECTED as a MISREAD of the shipping knob. Codex describes stage
two as a "fixed 1.0 re-anchor", but `eng_ltx25.py:1042` and `:1099` BOTH read
the same symbol `R.LTX25_I2V_ANCHOR_STRENGTH`, defined once at
`ltx25_recipe.py:223`. There is exactly one knob in shipping code and it drives
both anchors. An `i2v`-only arm is therefore not a shippable configuration --
reaching it requires splitting one constant into two, which is a code change
nobody voted. Codex's own stated principles (final shipping output is
authoritative; keep the voted single-knob contrast) point to the constant-level
change once that identity is known.

Antigravity reached the same destination independently and added the mechanism:
holding stage 2 at 1.0 while stage 1 sits at 0.7 forcibly replants the original
still into the doubled latent, which would put a discontinuity between frame 0
and frame 1 (`eng_ltx25.py:1096-1099`). Two of three, plus the source, against
one.

**R2. Antigravity: drop `controlroom` and add `smoker_portrait_001.png`.**
PARTIALLY REJECTED. Dropping controlroom is fine -- it is a texture fixture and
this is an identity lane. Adding a new fixture is accepted in principle, but the
file must pass the 12.121 input-purity receipt (native-pixel inspection, prompt
describing the still) before it is admitted, and that has not been done.

## THE BLOCKER r1 SURFACED -- goes to the operator, not into a build

**B1. `ltx25` may not be honestly A/B-able as an API submission at all.**
Antigravity flagged the dynamic loader subclass; grounding it turned a
should-fix into a blocker.

`eng_ltx25.py:1188`, inside `render_clip`:
`classes["te"] = _cpu_pinned_clip_loader(classes["te"])`. That builds a runtime
subclass of the installed `CLIPLoaderGGUF` pinning the text encoder to CPU.
Its docstring (`:120-147`) records why: a GPU-side encode of the Gemma-4 12B Q5
GGUF transiently demands ~15.6 GiB, "a COIN FLIP per shot" against a 15.92 GiB
card, and on the 2026-08-19 canonical leg the fifth encode lost it. Pinning takes
the encode from ~13,760 MB to ~0 MB.

The substitution happens AFTER class resolution and BEFORE `_build_graph`, and is
invisible in the graph JSON -- `_node_candidates` still says `te ->
CLIPLoaderGGUF`, which is what `build_api_graph` faithfully emits. So an API-
submitted arm would silently run the STOCK loader, reintroducing the exact spike
that OOM'd a real leg, and would not reproduce production's memory path either
way. Lane 1's "identical by construction" guarantee does not hold here.

This is also a gap in my own tool: `build_api_graph` fails closed on local
Python classes in `_internal_class_map`, but a dynamically-subclassed REGISTERED
node passes straight through looking clean.

Options, none free:
* **(a) In-process harness.** Drive both arms through the engine the way
  production does, so the CPU pin is present. Highest fidelity; a different
  harness from lane 1 and more work.
* **(b) API arms with the stock loader.** Cheapest; risks OOM and knowingly
  measures a non-production memory path. A result from it is not a production
  claim.
* **(c) Re-order the lane.** Take `ltx_video` LoRA strength 0.5 vs 0.7 (lane 3)
  first if it has no equivalent runtime substitution, and return to ltx25 once
  the harness exists.

Driver's recommendation: **(a)**, with **(c)** as the cheap unblock if the
operator wants renders sooner. Not started; this is an operator decision.

## Roster and spend

r1 only: 2 external calls (Codex, Antigravity). The remaining rounds are NOT
run, because r1 surfaced a harness blocker that would invalidate r2-r4 planning.
This is a scoped r1, not a four-round arc, and must not be reported as one.
