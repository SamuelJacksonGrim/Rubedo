Pretrained occupancy confirmation for widening step 4.

Canonical workload. Production `build_engine`, 8-epoch corpus pretrain, eval,
thresholds 5 / 150 / 300, seeds 42–44 plus held-out 45/46, widths 128 / 256 / 768.
Settled-half occupancy (steps 261–500), energy-classified rhythm.

The 128 target is adapted from the pretrained 128 fit arms (seeds 42–44) and
written to `declaration.json` after those three finish and **before** any 256
or 768 occupancy is read. Do not invent that file. Do not score 256/768 against
the census youth replay.

    python -m tests.diagnostic.widening.rhythm_band_probe --batch-pretrained-free \
        docs/findings/data/2026-10-31-pretrained-occupancy --jobs 2

Rule: `tests/diagnostic/widening/rhythm_band_probe.py` (pretrained occupancy block).
Finding: `docs/findings/2026-10-31-settled-half-and-f9-gate.md`.
