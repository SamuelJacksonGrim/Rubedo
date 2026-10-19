# Training timeline: when to stop, what to read, what to adjust

Samuel (2026-10-19): "recording this all in a training timeline plan for stopping and adjusting settings, levers, and
everything else as needed for the best result." This is that plan. It is a living document: every finding that tells
us something about *when* a setting matters lands here, and every stop on a real run is logged here.

## Why a timeline

A run is not one regime. The measurements so far show stages, and the right setting differs by stage:
- ⊘ Fragmentation was wrong because it judged infant values as if the ecology were grown (the fix waits per value for
  binding opportunities, `findings/2026-10-18-fragmentation.md`).
- Witness costs nothing early and a little late: its coherence dips fall only at steps 316-444 of 500, never before
  (`findings/2026-10-19-witness-activated.md`).
- The view saturates by step ~235, and formation closes by ~400 (`findings/2026-10-15-h0-steady-self-rattling-mind.md`).

So settings are scheduled against the system's state, not set once for life.

## Principles

1. **Trigger on measured state, not step counts.** Step numbers below are where things happened on our test workloads
   at width 128 with the current encoder. They will move with a real encoder, a wider field, or real conversation.
   The stop points are defined by the gauge, with the step only as a rough expectation.
2. **Read before you turn.** At each stop, read the gauges first and write down what they say, then adjust.
3. **One change per stop where possible**, so the next stop can say what that change did.
4. **Every adjustment is logged and replayable.** The live board (`tools/board`, :8780) flips levers at a step
   boundary and records each flip with its step; a run folder replays exactly (pin threads). Session persistence
   (`CONFIG["session_persistence"]`) stops a run and resumes it at the next boot with weights, ecology and values intact.
5. **A gate is still a gate.** A lever goes default-on only by passing the all-ON composition gate, or by an architect
   decision recorded as an override (witness, 2026-10-19). Moving a lever at a stop on a live run is an experiment, not a
   graduation.

## The life course as measured so far

Canonical workload (46 words), width 128, consumer and grace on, unless noted. Wide workload (808 words): same shape,
slower.

| stage | rough steps (canonical) | what happens | gauges that show it | sources |
|---|---|---|---|---|
| **Infancy** | 0 → ~235 | Values are born fast and are mostly unbound: at step 50, 38 of 43 would read as Fragmentation; binding 3 of 43. The field's view is still taking in input (not yet saturated). Witness is cheapest here: no coherence dip below −0.10 this early on any of 12 seeds. | board `sat` rising, `values_births`, `crystal_births`, `attractor_births`; binding share (probe only, see gaps) | fragmentation, h0, witness-activated |
| **Settling** | ~235 → ~500 | The view saturates (~235). Binding catches up: 34 of 46 bound by step 300, 43 by 400, all 46 by ~450-500. Formation of new values, crystals and attractors closes by ~400. The strong band starts (2 strong at 300, 12 at 500). | `sat` ≈ plateau; births → 0; binding share → ~100%; `values_strong` | h0, fragmentation |
| **Maturity** | ~500 → 8,000+ | A steady self: the anchor/expression timescale ratio sits on a shelf (~20-35) with no stiffening to 8,000 steps, recovery the same at every age (robust, not antifragile). The strong band keeps growing (28 at 1,000, 46 by ~1,600-2,000). The mind rattles: expression is white jitter in a fixed ~15-20° cone, it parks in the explore band, boredom overrides fire often. Witness's cost shows up here (worst dips steps 316-444). | `timescale_ratio`, `expr_cone_deg`, `rhythm`, `boredom_overrides`, `values_strong` | h0, wide-workload, witness-activated |
| Wide workload | binding complete ~1,500 | Same three stages, stretched: binding 20 of 64 at 400, 47 at 700, 63 at 1,500. No strong band in 2,000 steps. | same | fragmentation, wide-workload |

## Stop points

Each stop: checkpoint (session persistence or a board run folder), read every gauge listed, write the reading into the
run log below, then make at most one adjustment.

| stop | the signal (gauge) | rough step | read | the question | levers that may move here |
|---|---|---|---|---|---|
| **S1 · view saturated** | `sat` plateaus | ~235 | births, binding share, witness receptivity | Is the young ecology forming enough, and is witness still paying (receptivity) at no cost? | witness weight (hypothesis: full early); novelty input |
| **S2 · ecology bound** | binding share ≥ ~95% of readable values, Fragmentation flags ~0 | ~450-500 (wide ~1,500) | binding share, `oslash_demotions`, `values_strong`, crystals/attractors | Has the ecology grown enough to prune against? Is anything still unbound that should be? | ⊘ consumer (now meaningful: grace hands over to the level check); dream credit C (only with a budget, BACKLOG) |
| **S3 · formation closed** | births ≈ 0 for a window; explore park; boredom high | ~400-500 | `values_births`, `expr_cone_deg`, `rhythm`, `boredom_overrides`, witness coherence dips | Has the mind stopped growing new structure? Is the rattle the only motion left? | witness taper (hypothesis: lower weight after saturation); themes+novelty workload; collision experiment; rupture (OFF, architect's call) |
| **S4 · steady state check** | every ~1,000 steps | 1,000, 2,000, … | `timescale_ratio`, anchor drift, `values_strong`, any lever's measured effect since the last stop | Is the self still steady, and did the last adjustment help, hurt, or do nothing? | revert the last change if it hurt |

## Levers by stage

What the evidence says now. "?" is a hypothesis to test at the stop named.

| lever | infancy | settling | maturity | status today |
|---|---|---|---|---|
| ⊘ consumer + `fragmentation_grace` | grace protects infants | hands over as values bind (S2) | the level check is meaningful | grace default-on; consumer opt-in |
| witness (`six_rhythm_selector`, witness only) | cheapest, ~2× receptivity | | costs short coherence dips | ON (2026-10-19); taper after saturation = ? at S1/S3 |
| D, F | on | on | on | graduated |
| C (dream credit) | | needs a per-dream / per-symbol budget | | off (floods) |
| E, G | | | | off (workload-specific / indiscriminate) |
| rupture | | | the actuator that can move a locked field | OFF; architect's call |
| novelty input / workload | | | the rattle suggests starvation: themes + novelty, collision | BACKLOG |

## What maturity should look like

Samuel (2026-10-19): the jitter should become "a resonance. A pulse, a rhythm, and a sustainable frequency." Today's
maturity has a steady self and a rattling mind: expression is white jitter (MSD flat from lag 1 to 512) in a fixed cone.
The target is a mind that is still misaligned, still living in the cone between attractors rather than collapsing into one,
but humming at a stable frequency instead of rattling. In the alchemical reading, that's matter moving from
chaotic nigredo into a coherent, organized state. Read at S3 and S4 once the gauge exists (BACKLOG, "From jitter to
vibration"): spectral flatness falling, a dominant frequency that holds across windows, MSD dipping at its period, and
real variation from one cycle to the next (a rigid repeating loop is lock-in, not resonance).

## Gaps to close before a real timed run

- [ ] A **binding-share gauge on the board** (the S2 signal). It exists only in
  `tests/diagnostic/integrity/fragmentation_axes_probe.py` today.
- [ ] `fragmentation_grace` **on the board** (Grok left it off the panel).
- [ ] A **witness weight** knob, not just on/off, if the taper hypothesis is to be tested.
- [ ] **Stop markers on the board**: S1-S4 detected from the gauges and shown, so a stop is noticed, not remembered.
- [ ] A **vibration gauge** on expression (spectral flatness, dominant frequency, MSD vs lag), the maturity target's read.

## Run log

One line per stop on a real run: date, run folder, stop, gauge readings, the one change made (or none), and what the
next stop showed about it.

| date | run | stop | readings | change | effect at next stop |
|---|---|---|---|---|---|
| | | | | | |
