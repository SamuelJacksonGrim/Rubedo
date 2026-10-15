# Emotion calibration: are the names true?

Recorded 2026-10-14. Samuel's observation; framing worked out with GPT (Raphael). A plan to come back to, not active
work: the experiments in flight (witness, upstream rupture) come first. **Nothing here is wired into governance or
the live loop until the mappings have earned it.**

## The problem

The six emotion dimensions (curiosity, wonder, joy, tension, boredom, stability) were named by the architect when the
system was built. The names give the dimensions meaning to the humans designing it. They do not, by themselves,
establish that each variable behaves like the emotion it is named for. **The names are hypotheses.** The system is now
measurable enough to test them.

## What the code computes today (`cognition/emotional_gradient.py::update`)

Every dimension is an EMA (α 0.15) of a target built from only three inputs: the predictor's error report, the
watcher's composite coherence, and field energy.

| name | target today | so it is really |
|---|---|---|
| curiosity | `PredictiveEcho` curiosity (prediction error), + 0.3 × surprise | prediction error |
| wonder | curiosity × coherence | novelty that fits |
| joy | coherence | coherence |
| tension | `PredictiveEcho` tension (prediction error) | prediction error, scaled |
| boredom | `PredictiveEcho` boredom (low error × low coherence) | low novelty in a loose field |
| stability | coherence − field-energy penalty (≤ 0.5) − 0.3 × tension | coherence, discounted |

Arousal and valence are derived from these six (Tier 4.2). Downstream, the six scale `field_gain`, `mutation_scale`,
`decay_rate`, `attractor_pull`, and feed dilation and the boredom override (FLOW.md has every consumer). Already visible
from the table: joy and stability are mostly coherence under two names, and curiosity and tension share one source.
That is exactly the kind of thing calibration exists to find.

## Three layers to keep apart (GPT/Raphael)

1. **Underlying signals:** what is actually measured and calculated (today: prediction error, coherence, energy).
2. **Functional dimensions:** which signals *independently* change the field's behavior. Six names need not mean six
   dimensions: if joy and stability are one measurement wearing two names, the architecture may be counting the same
   signal twice; if they share inputs yet act differently downstream, that difference is worth investigating.
3. **Interpretations:** the emotion names, including the field's own reports.

Redundancy, if it exists, has to come out of the evidence, not be decided by the labels.

## Three things to connect

1. **Internal state:** the values and their trajectories. What raises each one, what suppresses it.
2. **Behavior:** what the system does when a value changes. Does more "curiosity" broaden exploration? Does "tension"
   make generation more cautious, sharpen attention to contradiction, or push toward resolution?
3. **Self-report:** what the field says it feels when it speaks (the speech bridge reads the state card), which
   emotion it names, how confidently.

Correlate all three, across inputs and contexts.

## The traps

- **Self-report is not ground truth.** "I'm curious" is evidence about the self-model and how it reports, not proof
  the curiosity variable is calibrated. Defining curiosity as "whatever makes it say curious" is a circular test.
- **Calibrating the model is not teaching the report.** Never train the system to produce the expected emotion words.
  That builds convincing emotional language with no better correspondence to state or behavior.
- **No single signature per emotion.** Curiosity may broaden exploration in one context and sustain attention in
  another; tension may prompt investigation, avoidance, stabilization or rupture depending on the rest of the state.
  Measure relationships across context, not rules like "curiosity > 0.7 means explore".
- **Level is not dynamics.** Tension at 0.6 reached slowly may act differently from a jump to 0.6 after a disruption.
  Direction, rate, duration and interactions with the other dimensions are all candidates.
- **The test must be allowed to fail.** If what is called joy behaves like reward sensitivity, revise the model (or
  find the dimension serves several functions). Do not massage the data to keep the name.

## How to test

- **Forward (intervention):** raise one variable, hold the others as constant as possible, measure behavior
  (exploration breadth, information-seeking, later choices) and the field's report. Compare all three against a
  prediction written beforehand.
- **Reverse (generation):** give inputs independently known to carry novelty, uncertainty, contradiction or
  settledness, and check whether the dynamics produce the supposed emotion on their own, not only whether forcing the
  variable produces the effect.
- **Per-dimension profile, built from evidence:** what reliably changes it; what it predicts about the next behavior;
  which other dimensions modify its effect; whether self-report agrees with observed function; whether the mapping
  generalizes; where the evidence contradicts the label.

## First step (when this becomes active)

An **audit**, not a feature: every dimension's update path, every downstream consumer, and every place a name or value
is interpreted (code, state card, speech bridge prompt, docs). Then a harness built around what the code actually does,
kept outside the runtime's governing logic.

## Related

- Witness and rupture experiments: if witness lowers coherence, the emotion trace can help explain the mechanism, but
  only once the dimensions mean what we think (`findings/2026-10-14-six-rhythm-selector-live-off-on.md`).
- The e8-eea direction: emotion should *emerge* (from prediction-error phase transitions) rather than be tagged, and
  sovereign_manifold's model is a continuous (valence, arousal) circumplex with the six names as regions. Calibration
  is the empirical side of the same question.
- The bridge now persists the six scalars (`findings/2026-10-14-bridge-emotion-never-restored.md`), so trajectories
  survive restarts and can be studied over long runs.
