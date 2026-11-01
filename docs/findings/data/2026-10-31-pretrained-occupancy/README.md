Pretrained occupancy confirmation for widening step 4.

Canonical workload. Production `build_engine`, 8-epoch corpus pretrain, eval,
thresholds 5 / 150 / 300, seeds 42–44 plus held-out 45/46, widths 128 / 256 / 768.
Settled-half occupancy (steps 261–500), energy-classified rhythm.

The 128 target is adapted from the pretrained 128 fit arms (seeds 42–44) and
written to `declaration.json` after those three finish and **before** any 256
or 768 occupancy is read. Do not invent that file. Do not score 256/768 against
the census youth replay.

Landed 2026-10-31. `declaration.json` explore mean 0.009722, span 0.029167,
mixed 0/7/0. Scoring: PRETRAINED OCCUPANCY FAIL (16). 128 held-out explore
0.047917; 768 fit 0.058333; 768 held-out 0.120833. Step 4 is no band retune.

    python -m tests.diagnostic.widening.rhythm_band_probe --batch-pretrained-free \
        docs/findings/data/2026-10-31-pretrained-occupancy --jobs 2
    python -m tests.diagnostic.widening.rhythm_band_probe --score-pretrained \
        docs/findings/data/2026-10-31-pretrained-occupancy

Rule: `tests/diagnostic/widening/rhythm_band_probe.py` (pretrained occupancy block).
Finding: `docs/findings/2026-10-31-pretrained-occupancy.md`.
