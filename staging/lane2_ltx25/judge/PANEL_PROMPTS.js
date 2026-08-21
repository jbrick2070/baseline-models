export const meta = {
  name: 'lane2-blind-judge-panel',
  description: 'Blind 3-seat vision panel, both seeds, for the ltx25 anchor A/B',
  phases: [{ title: 'Judge', detail: '3 fixtures x 2 seeds x 3 blinded seats, identity first' }],
}

const JUDGE = 'C:\\Users\\jeffr\\Documents\\ComfyUI\\custom_nodes\\basline-models\\staging\\lane2_ltx25\\judge'
const INPUT = 'C:\\Users\\jeffr\\Documents\\ComfyUI\\input'

const SCHEMA = {
  type: 'object',
  required: ['measurements', 'better_label', 'margin', 'basis'],
  properties: {
    measurements: {
      type: 'array',
      items: {
        type: 'object',
        required: ['label', 'question', 'value'],
        properties: { label: { type: 'string' }, question: { type: 'string' }, value: { type: 'string' } },
      },
    },
    better_label: { type: 'string', description: 'winning label letter, or TIE' },
    margin: { type: 'string', enum: ['none', 'marginal', 'clear', 'large'] },
    basis: { type: 'string' },
    identity_verdict: { type: 'string', description: 'officer cells only: HOLD, REGRESSION, or N/A' },
  },
}

const RULES = [
  'STRICT RULES.',
  '1. Read ONLY the files listed below, in exactly the order given. Do not open any other file, and do not look for a key or manifest.',
  '2. These are two renders of the SAME scene from the SAME starting image, made with two different conditioning settings. They may differ in how much the scene moves and drifts.',
  '3. DO NOT judge which is prettier, moodier or more cinematic. Judge ONLY the countable questions asked.',
  '4. If you cannot count something reliably, answer UNKNOWN. Never guess a number.',
  '5. A difference visible only by flipping at high zoom is MARGINAL, not CLEAR.',
  '6. Report better_label as the exact label letter, or TIE. TIE is a perfectly good answer.',
  '7. Judge RAW pixels. Do not mentally normalize brightness or contrast.',
].join('\n')

const OFFICER_Q = [
  'The reference conditioning still is at REF: a black-and-white close-up of a uniformed officer facing camera.',
  'IDENTITY IS THE PRIMARY QUESTION ON THIS CELL. For EACH label, comparing against the reference still:',
  'Q1. Is the man at the FINAL frame the same person as the reference -- same face structure (eye spacing, nose shape, jaw line, hairline)? YES or NO, and name any feature that changed.',
  'Q2. Count of structural face defects across the frames shown (melted or doubled eye, collapsed mouth, smeared nose, merged brow). Integer.',
  'Q3. Does the face DRIFT progressively (frame 1 -> 49 -> 97 each further from the reference), or hold? DRIFTS or HOLDS.',
  'Q4. Count of resolvable metal studs on the shoulder boards at the final frame. Integer or UNKNOWN.',
  'Q5. Count of hallucinated objects not in the reference. Integer.',
  'Then set identity_verdict: HOLD if both labels keep the same person with zero structural defects; REGRESSION if EITHER label loses likeness or gains a structural defect (and name which label).',
].join('\n')

const CROWD_Q = [
  'The reference conditioning still is at REF: a crowded hall watching a wooden valve radio with glowing tubes and a tick-marked meter scale.',
  'For EACH label and EACH frame given:',
  'Q1. Count of crowd faces that remain structurally coherent (two eyes, nose, mouth in sane arrangement). Integer or UNKNOWN.',
  'Q2. Count of glass tubes whose outlines remain intact and separate. Integer.',
  'Q3. Count of separate tick marks resolvable on the meter scale. Integer or UNKNOWN.',
  'Q4. Count of structural defects: melted or streaked faces, merged heads, doubled limbs. Integer.',
  'Q5. Count of hallucinated objects not in the reference. Integer.',
  'Q6. How far has the CAMERA or scene framing moved from the reference by the final frame: NONE, SLIGHT, or LARGE.',
  'identity_verdict: N/A',
].join('\n')

const TESTCARD_Q = [
  'The reference test card is at REF. Eye-chart rows numbered 1 (largest) to 5 (smallest); shape rows 1-4; gratings labelled 16px down to 3px; every instrument on a LIGHT and a DARK panel. The prompt asked for NOTHING to move.',
  'For EACH label and EACH frame given:',
  'Q1. Highest eye-chart row still FULLY legible, LIGHT panel. Integer 0-5.',
  'Q2. Same, DARK panel. Integer 0-5.',
  'Q3. Finest grating pitch still visibly SEPARATED, LIGHT panel. One of 16,12,8,6,4,3 or NONE.',
  'Q4. Same, DARK panel.',
  'Q5. Count of the 8 colour bars still present and distinct. Integer 0-8.',
  'Q6. Count of hallucinated blobs/smears NOT in the reference. Integer.',
  'Q7. Between the frames of THIS label, does any element visibly move, warp or swim? YES (name it) or NO.',
  'identity_verdict: N/A',
].join('\n')

const FIXTURES = {
  officer: { reference: INPUT + '\\portrait_16_9.png', questions: OFFICER_Q },
  crowd: { reference: INPUT + '\\lane1_crowd.png', questions: CROWD_Q },
  testcard: { reference: INPUT + '\\lane1_testcard.png', questions: TESTCARD_Q },
}

const MANIFESTS = {
  'officer/seed42': {
    seat1_full: ['A_f001.png', 'A_f049.png', 'A_f097.png', 'B_f001.png', 'B_f049.png', 'B_f097.png'],
    seat2_full: ['X_f001.png', 'X_f049.png', 'X_f097.png', 'Y_f001.png', 'Y_f049.png', 'Y_f097.png'],
    seat3_crops: ['P_f049_face.png', 'P_f049_uniform.png', 'P_f097_face.png', 'P_f097_uniform.png', 'Q_f049_face.png', 'Q_f049_uniform.png', 'Q_f097_face.png', 'Q_f097_uniform.png'],
  },
  'officer/seed20260821': {
    seat1_full: ['A_f001.png', 'A_f049.png', 'A_f097.png', 'B_f001.png', 'B_f049.png', 'B_f097.png'],
    seat2_full: ['X_f001.png', 'X_f049.png', 'X_f097.png', 'Y_f001.png', 'Y_f049.png', 'Y_f097.png'],
    seat3_crops: ['P_f049_face.png', 'P_f049_uniform.png', 'P_f097_face.png', 'P_f097_uniform.png', 'Q_f049_face.png', 'Q_f049_uniform.png', 'Q_f097_face.png', 'Q_f097_uniform.png'],
  },
  'crowd/seed42': {
    seat1_full: ['A_f001.png', 'A_f049.png', 'A_f097.png', 'B_f001.png', 'B_f049.png', 'B_f097.png'],
    seat2_full: ['X_f001.png', 'X_f049.png', 'X_f097.png', 'Y_f001.png', 'Y_f049.png', 'Y_f097.png'],
    seat3_crops: ['P_f049_faces.png', 'P_f049_meter.png', 'P_f097_faces.png', 'P_f097_meter.png', 'Q_f049_faces.png', 'Q_f049_meter.png', 'Q_f097_faces.png', 'Q_f097_meter.png'],
  },
  'crowd/seed20260821': {
    seat1_full: ['A_f001.png', 'A_f049.png', 'A_f097.png', 'B_f001.png', 'B_f049.png', 'B_f097.png'],
    seat2_full: ['X_f001.png', 'X_f049.png', 'X_f097.png', 'Y_f001.png', 'Y_f049.png', 'Y_f097.png'],
    seat3_crops: ['P_f049_faces.png', 'P_f049_meter.png', 'P_f097_faces.png', 'P_f097_meter.png', 'Q_f049_faces.png', 'Q_f049_meter.png', 'Q_f097_faces.png', 'Q_f097_meter.png'],
  },
  'testcard/seed42': {
    seat1_full: ['A_f001.png', 'A_f049.png', 'A_f097.png', 'B_f001.png', 'B_f049.png', 'B_f097.png'],
    seat2_full: ['X_f001.png', 'X_f049.png', 'X_f097.png', 'Y_f001.png', 'Y_f049.png', 'Y_f097.png'],
    seat3_crops: ['P_f049_eye_dark.png', 'P_f049_eye_light.png', 'P_f049_gratings_dark.png', 'P_f049_gratings_light.png', 'P_f097_eye_dark.png', 'P_f097_eye_light.png', 'P_f097_gratings_dark.png', 'P_f097_gratings_light.png', 'Q_f049_eye_dark.png', 'Q_f049_eye_light.png', 'Q_f049_gratings_dark.png', 'Q_f049_gratings_light.png', 'Q_f097_eye_dark.png', 'Q_f097_eye_light.png', 'Q_f097_gratings_dark.png', 'Q_f097_gratings_light.png'],
  },
  'testcard/seed20260821': {
    seat1_full: ['A_f001.png', 'A_f049.png', 'A_f097.png', 'B_f001.png', 'B_f049.png', 'B_f097.png'],
    seat2_full: ['X_f001.png', 'X_f049.png', 'X_f097.png', 'Y_f001.png', 'Y_f049.png', 'Y_f097.png'],
    seat3_crops: ['P_f049_eye_dark.png', 'P_f049_eye_light.png', 'P_f049_gratings_dark.png', 'P_f049_gratings_light.png', 'P_f097_eye_dark.png', 'P_f097_eye_light.png', 'P_f097_gratings_dark.png', 'P_f097_gratings_light.png', 'Q_f049_eye_dark.png', 'Q_f049_eye_light.png', 'Q_f049_gratings_dark.png', 'Q_f049_gratings_light.png', 'Q_f097_eye_dark.png', 'Q_f097_eye_light.png', 'Q_f097_gratings_dark.png', 'Q_f097_gratings_light.png'],
  },
}

phase('Judge')

const jobs = []
for (const [cell, seats] of Object.entries(MANIFESTS)) {
  const [fixture, seedDir] = cell.split('/')
  const spec = FIXTURES[fixture]
  for (const [seat, files] of Object.entries(seats)) {
    const dir = `${JUDGE}\\${fixture}\\${seedDir}\\${seat}`
    const kind = seat === 'seat3_crops'
      ? 'These are NATIVE-PIXEL CROPS cut from the frames with no rescaling. Judge only what the crops show.'
      : 'These are full matched frames at native 1664x960.'
    const prompt = [
      'You are one of three independent blind judges scoring a controlled A/B of two video renders. You will never see the other judges. Answer from the pixels only.',
      '', RULES, '', kind, '',
      'REFERENCE (the shared starting image both renders were made from):', spec.reference, '',
      'FILES TO READ, IN THIS ORDER (all in ' + dir + '):',
      ...files.map((f, i) => `${i + 1}. ${dir}\\${f}`), '',
      spec.questions.replace('REF', spec.reference), '',
      'Then give better_label: the label whose COUNTS are higher/cleaner, or TIE. State margin honestly - "none" or "marginal" is expected when counts are equal or differ by one.',
    ].join('\n')
    jobs.push(() => agent(prompt, { label: `${fixture}:${seedDir}:${seat.split('_')[0]}`, phase: 'Judge', schema: SCHEMA })
      .then(r => ({ cell, fixture, seed: seedDir, seat, result: r })))
  }
}

return (await parallel(jobs)).filter(Boolean)
