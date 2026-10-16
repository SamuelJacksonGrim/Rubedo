# Live board

Branch `grok/live-board`. The page is the one `tools/` path that acts, and it only flips lever flags at a step boundary. It does not inject into the field.

## Start

Production shape (pretrain on, the long boot). Do not leave this running inside a session whose children get killed:

```
powershell -File tools/board/start-board.ps1
```

Page: http://127.0.0.1:8780/ . Train dashboard stays on 8770, machine board on 8740.

Short smoke, no pretrain, no dream-channel training, no rhythm-reader build. Pin threads; the digest moves if you don't.

```
python -m tools.board.run_live --run-dir tools/board/runs/smoke --skip-pretrain --no-dream-channel --no-rhythm-reader --steps 40 --threads 1
python -m tools.board.server --port 8780 --runs tools/board/runs
python -m tools.board.run_live --replay tools/board/runs/smoke --threads 1
```

`--threads` is read from the process argv before numpy. A second value after import is refused. `RUBEDO_THREADS` is the pin when the flag is absent.

## On the panel, and why

These are flags the step already reads, or attaches the cycle already exposes. Flipping one does not rebuild the stack.

| Id | Why it can move mid-run |
|----|-------------------------|
| D | Like-for-like coherence, on the field and the watcher together. |
| F | A systemic damp still pays the value engine as if the step were allowed. Named damps are untouched. |
| C | A dream crystal is credited to the memories it recombined. |
| E | Values learn from alignment against its own recent average. |
| G | Satisfaction reads valence instead of the coherence delta. |
| Novelty attenuation | The reflective loop may loosen, up to the 0.30 ceiling. |
| Six-rhythm selector | Only if the reader was built at boot. Off, energy alone picks the four bands. |
| Rupture upstream | How a chosen rupture is applied. Not a second copy of the selector. |
| ⊘ consumer | Named pathologies only. Off, the read is not asked. |
| Dream channel | Only if the decoder was built at boot. Gates the self-dialogue coin. Does not train. |
| Dream cycle | Gates the existing driver. That call writes crystals and the field. It is not a silent flag. |
| Bond accumulator | Quality integrates to a bound. Off drops the evidence. On again starts at zero. |
| Fix 0-B | Diversity fitness. The first window pays nothing. Off clears the private profiles so the term actually leaves decay. |
| Binding leak | On is the measured 0.10. Sacred and protected symbols stay exempt. |
| λ | First on ignites at 2. Off detaches the gate and keeps the scalar. On again reattaches the same ledger. |

Witness is not its own switch. The selector's read chooses witness or rupture. The rhythm curve is the energy band. A second mix, "what ran", shows witness, rupture, and a boredom-forced explore. With the selector off the cycle does not record the act, so a boredom force is taken from the override counter.

## Not on the panel, and why

Shown, refused, with the reason on the row:

- Pretrain, chorus, session persistence. Boot or shutdown. A live toggle cannot untrain a generator.
- Eval mode. The operating regime, not a lever.
- Stream recorder. Observe-only. Not a lever.
- Ignition threshold gate. Standing policy: severed, not waiting on a measurement.
- Rhythm-read margin, alignment EMA rate, dream-channel rate. Dials left at boot. The switches next to them are the selector, E, and the dream channel.

Not shown at all, and a control file that names them is refused: sacred shield, the manipulation ladder, ethical gates, SystemRights.

`named_only=False` on the ⊘ consumer is not offered. It is documented to collapse.

## Where the sketch was wrong

- Do not pre-arm Fix 0-B at boot. That would not be the CONFIG-shaped cycle. Turning it off must clear `registry._profiles`. Stopping new credit and leaving the private weights in place keeps the fitness term in decay. Stored EMA credits stay on the symbols and are unread.
- A single rewritten `control.json` loses a request when the runner's "applied" rewrite races the page. The inbox is one file per request, written by replace, so the runner only sees complete JSON.
- `main()` sleeps 0.02 s between steps. The board does not. That sleep is wall clock. Replay forces delay 0, and the digest drops `overhead_ms`, `step_ms_mean`, and `observe_ms_mean`.
- The dream decoder and the rhythm centroids are boot work. The runtime switches only gate calls that already exist.
- A redundant "turn the bond accumulator on" must not rebuild it. Rebuilding resets V and the private noise stream.
- The board must not call ⊘ `read()` or `snapshot()` itself. `read()` calls `generate` and bumps symbol usage. The advisory on the row is whatever the consumer's own `apply()` already asked for. Consumer off: the row says not read. While the consumer is detached, `oslash_demotions_total` is 0 even though the held object still has its history. The window sum is the pulls that happened inside the window.
- The canonical workload is the Resonance Family probe room, not `main()`'s four-by-three toy list. `themes` raises. The phrases are not invented here.
- The page is its own, in this repo. `tools/train-dashboard` is not in this tree and is not an actuator.

A toggle logged at a step that never ran (stop arrived on the same boundary) is in `toggles.jsonl`. It is in the metrics digest only when the stop falls between samples, because the closing row is written after that boundary. Replay does the same thing. It does not invent a step.

## Overhead

1 thread, pretrain off, dream channel not built, rhythm reader not built, canonical room. Observe is every step. The window math is every N steps. The first window pays about 6–7 ms once, to import the probe estimators. After that:

| Run | Step | Observe | Window math | Overhead per step |
|-----|------|---------|-------------|-------------------|
| 30 steps, window 24, every 12 (the suite test) | ~13 ms | 0.07 ms | ~0.3 ms | 0.26 ms (2% of the step; includes the one import) |
| 256 steps, window 256, every 64 | 36 ms by the end (6 ms at the start) | 0.07 ms | 2.8 ms at a full window | 0.13 ms (0.4% of the step) |

The step got slower as the field saturated. The metric cost did not follow it. Neither run is a pretrained production boot; the share above is against a cold generator.

## Checked

`tests.integration.live_board` (inbox toggle at step 18, closing row at step 30, replay digest `57c58aa12360a327…`), `tests.doc_accuracy.verify_docs`, `tests.integration.determinism_replay`, `tests.doc_accuracy.hardcoded_dim`. The page was fetched and a control POST was checked in-process. It was not clicked in a browser.
