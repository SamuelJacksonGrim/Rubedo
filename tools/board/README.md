# Live board

A page on the metrics of a running Rubedo, and switches for the levers that can change at a step boundary.

`tools/` otherwise only observes. This is the one sanctioned actuator. It flips lever flags. It does not inject a vector into the field, and it does not call the ⊘ read on its own (that read calls `generate` and bumps symbol usage). Sacred shield, the manipulation ladder, ethical gates, and SystemRights are not on the panel.

## Start

From the repo root. Pretrain is on; that boot is the long one.

```
powershell -File tools/board/start-board.ps1
```

The page is [http://127.0.0.1:8780/](http://127.0.0.1:8780/). The train dashboard stays on [8770](http://127.0.0.1:8770/) and the machine board on [8740](http://127.0.0.1:8740/).

A short run, no pretrain, no dream-channel training, no rhythm-reader build:

```
python -m tools.board.run_live --run-dir tools/board/runs/smoke --skip-pretrain --no-dream-channel --no-rhythm-reader --steps 40 --threads 1
python -m tools.board.server --port 8780 --runs tools/board/runs
```

`--threads` (or `RUBEDO_THREADS` before the process starts) is the pin. A digest from another thread count will not match. Replay refuses the mismatch.

```
python -m tools.board.run_live --replay tools/board/runs/smoke --threads 1
```

## What a run folder holds

| File | What it is |
|------|------------|
| `metrics.jsonl` | One row every N steps, plus a closing row if the stop falls between samples. Append-only. |
| `metrics.sha256` | Digest of those rows with the machine-time fields removed. |
| `toggles.jsonl` | Every request the runner accepted or refused, with the step it was applied at. |
| `inbox/` | What the page writes. The runner reads it at the next step boundary and deletes the file. |
| `status.json` | Step, lever panel, overhead. |
| `schema.json` | The one-line meaning under each curve. The page does not hardcode those sentences. |
| `config.json` | Seed, workload, thread pin, and how the run stopped. |

Wall-clock fields (`overhead_ms`, `step_ms_mean`, `observe_ms_mean`) stay on the row for the page and are left out of the digest. Replay checks the digest, not the clock.

## What the panel will flip

Mid-run, because the step already reads the flag or the cycle already exposes the attach: D, F, C, E, G, novelty attenuation, the six-rhythm selector (only if the reader was built at boot), rupture upstream, the ⊘ consumer, the dream channel (only if the decoder was built at boot), the dream cycle, the bond accumulator, Fix 0-B, the binding leak, and λ.

Witness is not its own switch. The selector's read chooses witness or rupture. `rupture_upstream` chooses how a chosen rupture is applied.

Shown and refused: pretrain, eval mode, chorus, session persistence, the stream recorder, the ignition threshold gate (severed, not a switch that is waiting), the rhythm-read margin, the alignment EMA rate, and the dream-channel rate.

## Replay

`--replay <run>` builds the same stack under the same seed, re-applies `toggles.jsonl` at the same steps, and exits 1 if `metrics.sha256` differs. A request that arrived on the stopping boundary is applied on the way out of both runs, so it lands in the closing row when that row exists. It does not invent a step that never ran.

Workloads are `canonical` and `wide` (the probe rooms, not `main()`'s toy list). `themes` is a named hook and raises until a themes-plus-novelty room is actually added.
