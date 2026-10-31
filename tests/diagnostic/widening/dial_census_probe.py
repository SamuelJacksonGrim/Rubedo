"""
tests/diagnostic/widening/dial_census_probe.py

Widening plan step 3: measure the dials at 128 vs 256 vs 768 BEFORE any
retune. Width is not edited. FIELD_DIM stays 128. Each arm copies CONFIG
and sets config["dim"], which build_engine passes to the Generator and the
cycle, and the cycle passes on to the field, watcher, witness, predictor
and recursive attention. The generator's width follows the field. The
constant in substrate/dims.py is not touched, so the suite's body stays
the 128 production field.

Stack: build_engine(CONFIG) with pretrain_on_corpus False and the dream
channel not built (it lives in main(), not build_engine). Same skip as
production_boot: corpus pretrain at 768 on CPU is hours, and the GPU is
on the encoder. Witness selector stays ON in CONFIG and is inert without
pretrain (no rhythm reader). D and F stay on. Rupture stays off. CPU only.

Workload: canonical Resonance Family, origin_type internal, seeds 42/43/44,
500 steps, under substrate.determinism. Wide (corpus holdout) is the same
probe with --workload wide, run when a canonical read moves.

Vibration reads call cognition.stream_vibration.analyze on the
post-reflection expression stream (_last_expressed): spectral flatness,
autocorrelation period, leftover variance, MSD, cone, label. Floors are
the gauge's, not retuned. The 2026-10-31 census JSONs were produced by an
in-file copy of analyze() from commit 5349028, before this branch had the
module. Canonical seed 42 matches the vibration-baseline finding to the
published digits. The move test uses the trailing 256, which the gauge's
own baseline named as the settled window. The full window still contains
the opening walk and is reported, not classified.

Pre-declared rule (written before any arm was run):

  A numeric read moves at width W when
      abs(mean_W - mean_128) > span_128
  where mean and span (max - min) are taken across the seeds of that
  workload, after rounding each seed's read to 6 decimal places.
  A span of 0 means any remaining difference moves. A read that is null
  on every seed is untested, not invariant. Fewer than 2 finite seeds
  is insufficient, not a retune.

  A dial needs retuning at W when one of its decision reads moves (a
  gate-clear fraction, a fire count, an occupancy, a label). A dial is
  shifted when only a level read moves (the number moved; the cutoff's
  yes/no did not). Shifted is not width-invariant. It is a lower-priority
  look, not a new constant by itself. The field's internal-coherence pin
  is reported and never listed for retune: the lock is by design.

  Census marks are hypotheses. This rule decides, including a dial the
  census marked "no" if this workload actually reads it.

  The youth split is not part of that rule. `findings/2026-10-31-right-to-refuse-order`
  measured systemic identity_erosion's damp queued from boot to ~step 260
  on canonical, so a 500-step arm is half youth. Each arm also records
  counters at step 260 (`youth` in the JSON). A width move that is only
  in that window is reported as such. It does not reclassify the 500-step
  rule.

  Step 4 split (written before those arms, same cut, same seeds). The
  census left seven decision reads unsplit because the snapshot did not
  hold them: lattice edges, binding counts, the 0.7 pattern fraction,
  witness crystallization, bonds, sacred promotions, metastability
  regime count. `split` in the JSON snapshots them at step 260 and at
  the end. Classification, in `reduce_split`:

    Same numeric rule. A late read moves at W when
    abs(mean_W - mean_128) > span_128 after rounding to 6 d.p.

    Rates (pattern identity, witness crystal-clear, witness snapshot-
    clear): the late read is (count_end - count_at_cut) / late_steps.

    Stocks (lattice edges and nodes, binding total and established,
    bonds, values_core): the late read is the increment end - cut,
    not the end stock. A gap that opens before the cut and then sits
    still is the youth miss persisting (the attractor precedent in
    the census finding). That is youth-only.

    Metastability regime count: the monitor window is 128, so the
    end snapshot is the trailing 128 steps. On a 500-step arm that
    window sits entirely inside the settled half. The end snapshot
    is the settled read. The cut snapshot is the trailing 128 of
    the youth window, reported beside it.

    Youth-only: the late read does not move.
    Moves when settled: the late read moves.
    Unresolved (run a longer arm, 1200 steps, same cut): the 128
    late span swallows a gap that is still > 20% of the 128 late
    level. A late increment near 0 at every width is resolved
    (nothing is still happening), not unresolved.

  Not on this workload, so neither invariant nor a retune:
  Qwen/Nomic beat-lock floors, encoder training temperatures and cosine
  margins, rupture's gaussian scale (rupture is off), the dream-channel
  decoder width, the voice REPL's speak-gate.

    python -m tests.diagnostic.widening.dial_census_probe --check
    python -m tests.diagnostic.widening.dial_census_probe --arm \\
        --dim 768 --seed 42 --workload canonical --steps 500 \\
        --out docs/findings/data/2026-10-31-dial-census
    python -m tests.diagnostic.widening.dial_census_probe --reduce \\
        docs/findings/data/2026-10-31-dial-census
"""

from __future__ import annotations

import os

# Before torch. One process per arm, two threads, and never the training GPU.
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "2")
os.environ["CUDA_VISIBLE_DEVICES"] = ""

import argparse
import json
import logging
import math
import random
import sys
import time
from collections import Counter, deque
from pathlib import Path

import numpy as np

logging.disable(logging.CRITICAL)

import torch  # noqa: E402

torch.set_num_threads(int(os.environ.get("OMP_NUM_THREADS", "2")))
try:
    torch.set_num_interop_threads(1)
except RuntimeError:
    pass

from cognition.stream_vibration import analyze, synthetic_stream  # noqa: E402
from loop.recursion1188 import CONFIG, build_engine  # noqa: E402
from substrate import determinism  # noqa: E402
from substrate.dims import FIELD_DIM  # noqa: E402
from tests.workloads import describe, load_named  # noqa: E402

# Decision rule. "gate" moving => retune. "level" moving => shifted.
# "pin" is reported and excluded from both lists. "label" moving => retune.
DIALS = (
    {"id": "rhythm_bands", "census": "energy thresholds 5/150/300",
     "gate": ("occ_stabilize", "occ_dream", "occ_reflect", "occ_explore"),
     "level": ("energy_mean", "energy_p50")},
    {"id": "watcher_composite", "census": "watcher threshold 0.40 and alpha/beta/gamma parts",
     "gate": ("stable_rate",),
     "level": ("composite_mean", "geometric_mean", "temporal_mean", "resonance_mean")},
    {"id": "coherence_pin", "census": "internal_coherence, the ~0.998 lock",
     "pin": ("field_coherence_mean",)},
    {"id": "fft_layout", "census": "harmonic_bins, phase coherence, diffuse_alpha",
     "level": ("harmonic_ratio_mean", "phase_coherence_mean")},
    {"id": "crystal_thresholds", "census": "coherence 0.75, stability 0.60, relation 0.80",
     "gate": ("crystal_all_clear", "crystal_births", "crystals_end"),
     "level": ("crystal_coh_clear", "crystal_stab_clear", "crystal_rel_clear")},
    {"id": "witness_crystallization", "census": "witness 0.92 / 0.90 / 0.75",
     "gate": ("witness_crystal_clear", "witness_snapshot_clear")},
    {"id": "attractor_cosines", "census": "formation 0.88, pull 0.75, merge 0.95",
     "gate": ("attractor_form_clear", "attractors_end", "pull_above"),
     "level": ("pull_cos_mean",)},
    {"id": "lattice_similarity", "census": "lattice edge cosine 0.75",
     "gate": ("lattice_edges", "lattice_nodes")},
    {"id": "binding_similarity", "census": "bind-to-existing cosine 0.82",
     "gate": ("binding_total", "binding_established")},
    {"id": "value_formation", "census": "downstream of coherence and the decision bonus",
     "gate": ("values_active", "values_strong", "values_total")},
    {"id": "core_alignment", "census": "CORE_ALIGNMENT_MIN 0.5",
     "gate": ("alignment_over_0_5", "values_core"),
     "level": ("field_alignment_mean",)},
    {"id": "bonds", "census": "formation coherence 0.10 (DDM evidence is field_alignment)",
     "gate": ("bonds",)},
    {"id": "decisions", "census": "ALLOW / weakened / quarantine / reject",
     "gate": ("allow_rate", "weakened_rate", "quarantine_rate", "reject_rate", "monitor_rate")},
    {"id": "identity_erosion", "census": "|G-T| threshold 0.30",
     "gate": ("gt_gap_over", "manip_erosion"),
     "level": ("gt_gap_mean",)},
    {"id": "drift_detector", "census": "anchor velocity 0.15 (L2), short/long gap 0.30",
     "gate": ("velocity_over", "gap_over", "manip_drift"),
     "level": ("anchor_velocity_mean", "anchor_gap_mean")},
    {"id": "gaslighting", "census": "crystal-centroid cosine -0.20",
     "gate": ("crystal_cos_below", "manip_gaslight"),
     "level": ("crystal_cos_mean",)},
    {"id": "ethical_coherence", "census": "coherence_delta floor -0.30 / soft -0.05",
     "gate": ("delta_below_hard", "delta_below_soft"),
     "level": ("coherence_delta_mean",)},
    {"id": "predictive_echo", "census": "surprise threshold 2.5 and the L2 error scale",
     "gate": ("surprise_rate",),
     "level": ("pred_error_mean",)},
    {"id": "reflective_loop", "census": "convergence 0.995, coherence_gate 0.20, attenuation_max 0.30",
     "gate": ("reflect_rate", "reflect_converged_rate")},
    {"id": "metastability", "census": "cluster tol 0.15, diversity_blend 0.60",
     "gate": ("expr_regimes", "gen_regimes"),
     "level": ("expr_meta", "gen_meta")},
    {"id": "vibration_gauge", "census": "spectral flatness, cone, MSD, label (trailing 256)",
     "gate": ("vib_label_changed",),
     "level": ("vib_sf", "vib_cone", "vib_msd1")},
    {"id": "embedding_init", "census": "init std 0.035, target output pairwise cosine ~0.55",
     "level": ("emb_table_cos", "emb_pe_cos", "emb_out_cos", "emb_over_pe")},
    {"id": "field_gain", "census": "energy_penalty and the gain clip, if energy scales",
     "level": ("field_gain_mean", "gain_at_ceiling")},
    {"id": "pattern_cutoff", "census": "witness relational 'high' cosine 0.7",
     "gate": ("pattern_identity",)},
    {"id": "boredom_override", "census": "marked no; measured because explore can be forced",
     "gate": ("boredom_overrides",)},
)

NOT_ON_WORKLOAD = (
    "Qwen/Nomic beat-lock floors (embedder space; this loop never calls them)",
    "encoder training temperatures and cosine margins (InfoNCE, legibility)",
    "rupture gaussian scale and hold blend (rupture_on_lock and rupture_upstream are off)",
    "dream-channel decoder hidden width (channel is built by main(), not this stack)",
    "voice REPL speak-gate (curiosity 0.25 / boredom 0.6)",
)


def _unit_rows(X):
    n = np.linalg.norm(X, axis=1, keepdims=True)
    return X / np.maximum(n, 1e-15)


def _vibration(vectors):
    """One window of the merged gauge. The census move-test uses the trailing 256."""
    report = analyze(vectors)
    period = report.dominant_period if report.has_dominant else float("nan")
    return {
        "samples": int(report.samples),
        "spectral_flatness": report.spectral_flatness,
        "cone_deg": report.cone_deg,
        "msd_lag1": report.msd_lag1,
        "period": period,
        "holds": bool(report.dominant_holds),
        "residual_frac": report.residual_frac,
        "label": report.label,
    }


def _offdiag_cosine(X):
    U = _unit_rows(np.asarray(X, dtype=float))
    C = U @ U.T
    iu = np.triu_indices(len(U), k=1)
    return float(C[iu].mean()) if len(iu[0]) else float("nan")


def _num(x):
    if x is None:
        return None
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(x):
        return None
    return round(x, 6)


def _mean(xs):
    a = np.asarray(list(xs), dtype=float)
    a = a[np.isfinite(a)]
    if len(a) == 0:
        return None
    return float(a.mean())


def _quant(xs, q):
    a = np.asarray(list(xs), dtype=float)
    a = a[np.isfinite(a)]
    if len(a) == 0:
        return None
    return float(np.quantile(a, q))


def _frac(flags):
    if not flags:
        return None
    return float(np.mean(np.asarray(flags, dtype=float)))


def _embedding_geometry(gen):
    """Init geometry with no registry side effects. Fixed row set, position 0."""
    with torch.no_grad():
        W = gen.embedding.weight.detach().float().cpu().numpy()
        norms = np.linalg.norm(W, axis=1)
        idx = np.flatnonzero(norms > 1e-6)[:24]
        if len(idx) < 4:
            return {}
        raw = W[idx]
        ids = torch.tensor(idx, dtype=torch.long, device=gen.device).unsqueeze(1)
        emb, _mean_tok, _pad = gen._scaled_token_embeddings(ids)
        pe = gen.transformer_input(emb)[:, 0, :].float().cpu().numpy()
        out = gen.forward(ids).float().cpu().numpy()
        scaled_norm = float(np.linalg.norm(emb[:, 0, :].float().cpu().numpy(), axis=1).mean())
        pe_norm = float(gen.position.norm)
    return {
        "emb_table_cos": _offdiag_cosine(raw),
        "emb_pe_cos": _offdiag_cosine(pe),
        "emb_out_cos": _offdiag_cosine(out),
        "emb_over_pe": (scaled_norm / pe_norm) if pe_norm else float("nan"),
        "emb_row_std": float(raw.std()),
        "rows": int(len(idx)),
    }


def _live_thresholds(cycle):
    att = cycle.attractor
    cr = cycle.crystal_store
    w = cycle.witness
    res = cycle.governance.resistance if cycle.governance is not None else None
    out = {
        "rhythm": dict(cycle.field.thresholds),
        "watcher": getattr(cycle.watcher, "threshold", None),
        "crystal_coherence": getattr(cr, "coherence_threshold", None),
        "crystal_stability": getattr(cr, "stability_threshold", None),
        "crystal_relation": getattr(cr, "relation_threshold", None),
        "attractor_formation": cycle.attractor_formation_threshold,
        "pull": getattr(att, "pull_threshold", None),
        "witness_coherence": getattr(w, "crystallization_coherence", None),
        "witness_long": getattr(w, "crystallization_long_relation", None),
        "witness_stability": getattr(w, "crystallization_stability", None),
        "witness_snapshot": getattr(w, "snapshot_coherence_threshold", None),
        "lattice": getattr(cycle.lattice, "similarity_threshold", None),
        "binding": getattr(cycle.binding, "similarity_threshold", None),
        "diversity_blend": getattr(cycle.rec_attn, "diversity_blend", None),
        "convergence": getattr(cycle.reflector, "convergence_threshold", None),
        "attenuation_max": getattr(cycle.reflector, "attenuation_max", None),
        "surprise": getattr(cycle.predictor, "surprise_threshold", None),
    }
    if res is not None:
        out["drift_velocity"] = res.drift_velocity_threshold
        out["drift_gap"] = res.drift_gap_threshold
        out["gaslighting"] = res.gaslighting_cosine_threshold
        out["erosion"] = res.watcher_divergence_threshold
    return out


def _install_taps(cycle):
    """Identity wrappers. First call in a step is the step's own, not the dreamer's."""
    slot = {
        "in_behavior": False,
        "obs": None,
        "report": None,
        "last_report": None,
        "profile": None,
        "stability": None,
        "echo": None,
        "delta": None,
        "align_vec": None,
        "signals": None,
        "align_pre": None,
    }

    orig_obs = cycle.field.observe

    def observe():
        o = orig_obs()
        if slot["obs"] is None:
            slot["obs"] = o
        return o

    cycle.field.observe = observe

    orig_eval = cycle.watcher.evaluate

    def evaluate(*a, **k):
        r = orig_eval(*a, **k)
        slot["last_report"] = r
        return r

    cycle.watcher.evaluate = evaluate

    orig_stab = cycle.witness._update_stability

    def stability():
        s = orig_stab()
        if slot["stability"] is None:
            slot["stability"] = float(s)
        return s

    cycle.witness._update_stability = stability

    orig_upd = cycle.witness.update

    def update(*a, **k):
        profile = orig_upd(*a, **k)
        if slot["profile"] is None:
            slot["profile"] = profile
            slot["report"] = slot["last_report"]
        return profile

    cycle.witness.update = update

    orig_echo = cycle.predictor.update

    def echo(vec):
        r = orig_echo(vec)
        if slot["echo"] is None:
            slot["echo"] = r
        return r

    cycle.predictor.update = echo

    orig_impact = cycle.field.coherence_impact

    def impact(vec):
        # Called before inject, so the field here is the one the cycle's own
        # alignment cosine is about to read. Match that formula: dot / ||field||,
        # no extra division by ||vec|| (the expression is already unit length).
        d = orig_impact(vec)
        if slot["delta"] is None:
            slot["delta"] = float(d)
            f = np.asarray(cycle.field.field, dtype=float)
            n = float(np.linalg.norm(f))
            v = np.asarray(vec, dtype=float)
            slot["align_pre"] = 0.0 if n <= 1e-8 else max(0.0, float(np.dot(v, f) / n))
        return d

    cycle.field.coherence_impact = impact

    orig_det = cycle.governance.resistance.detect

    def detect(*a, **k):
        sigs = orig_det(*a, **k)
        if slot["signals"] is None and not slot["in_behavior"]:
            slot["signals"] = list(sigs or [])
        return sigs

    cycle.governance.resistance.detect = detect

    decisions = Counter()
    orig_arb = cycle.governance.arbitrate

    def arbitrate(*a, **k):
        dec, strength = orig_arb(*a, **k)
        if not slot["in_behavior"]:
            decisions[dec.value] += 1
        return dec, strength

    cycle.governance.arbitrate = arbitrate

    orig_beh = cycle._rhythm_behavior

    def behavior(rhythm, tokens):
        slot["in_behavior"] = True
        try:
            return orig_beh(rhythm, tokens)
        finally:
            slot["in_behavior"] = False

    cycle._rhythm_behavior = behavior
    return slot, decisions


# The refuse-order finding's canonical damp window. Not a retune rule.
_YOUTH_CUT = 260


def _window_cut(
    n, rhythms, energy, gt_over, manip, decisions, crystal_clear,
    crystal_births, attractor_clear, pull_above, pull_n, reflect_steps, boredom,
):
    return {
        "steps": int(n),
        "stabilize": int(rhythms.get("stabilize", 0)),
        "dream": int(rhythms.get("dream", 0)),
        "reflect": int(rhythms.get("reflect", 0)),
        "explore": int(rhythms.get("explore", 0)),
        "energy_sum": round(float(sum(energy)), 6),
        "gt_over": int(gt_over),
        "erosion": int(manip.get("identity_erosion", 0)),
        "allow": int(decisions.get("allow", 0)),
        "weakened": int(decisions.get("allow_weakened", 0)),
        "crystal_all": int(crystal_clear["all"]),
        "crystal_births": int(crystal_births),
        "attractor_clear": int(attractor_clear),
        "pull_above": int(pull_above),
        "pull_n": int(pull_n),
        "reflect_steps": int(reflect_steps),
        "boredom": int(boredom),
    }


def _reset_slot(slot):
    slot["obs"] = None
    slot["report"] = None
    slot["last_report"] = None
    slot["profile"] = None
    slot["stability"] = None
    slot["echo"] = None
    slot["delta"] = None
    slot["align_vec"] = None
    slot["align_pre"] = None
    slot["signals"] = None


def _split_stock(n, cycle, ve, gov, patterns, crystal_clear):
    """End-of-step stocks the census youth snapshot did not hold.

    Metastability is the monitor's trailing window (128), not the whole
    run. Read-only. Does not touch the field.
    """
    lattice = cycle.lattice.stats()
    binding = cycle.binding.summary()
    expr = cycle.expression_metastability.compute_now()
    genm = cycle.generator_metastability.compute_now()
    return {
        "steps": int(n),
        "lattice_edges": int(lattice.get("edges", 0)),
        "lattice_nodes": int(lattice.get("nodes", 0)),
        "binding_total": int(binding.get("total", 0)),
        "binding_established": int(binding.get("established", 0)),
        "bonds": int(gov.bond_manager.summary().get("bonds", 0)),
        "values_core": int(len(ve.core_values())),
        "pattern_identity": int(patterns.get("identity_reinforcement", 0)),
        "witness_crystal": int(crystal_clear["witness"]),
        "witness_snapshot": int(crystal_clear["snap"]),
        "expr_regimes": int(expr.n_regimes),
        "expr_state": str(expr.regime_state),
        "expr_samples": int(len(cycle.expression_metastability._vecs)),
        "gen_regimes": int(genm.n_regimes),
        "gen_state": str(genm.regime_state),
        "gen_samples": int(len(cycle.generator_metastability._vecs)),
    }


def run_arm(dim, seed, workload, steps, thresholds=None, pretrain=False):
    if dim % 4 != 0 or dim % 2 != 0:
        raise SystemExit(f"dim {dim} is not usable (heads=4, even PE)")
    cfg = dict(CONFIG)
    cfg["dim"] = int(dim)
    cfg["pretrain_on_corpus"] = bool(pretrain)
    cfg["session_persistence"] = False
    cfg["log_interval"] = 10 ** 9
    sources, weights = load_named(workload)
    room = describe(sources)
    t0 = time.perf_counter()
    expr = deque(maxlen=512)
    energy, composite, geometric, temporal, resonance = [], [], [], [], []
    harm, phase, field_coh = [], [], []
    pred_err, surprise_flags = [], []
    gt_gap, crystal_cos, pull_cos = [], [], []
    alignment, delta = [], []
    velocity, gap, stability_l = [], [], []
    long_rel, rel_comp = [], []
    gain = []
    rhythms = Counter()
    patterns = Counter()
    manip = Counter()
    crystal_clear = {"coh": 0, "stab": 0, "rel": 0, "all": 0, "witness": 0, "snap": 0}
    attractor_clear = 0
    pull_above = 0
    pull_n = 0
    reflect_steps = 0
    reflect_converged = 0
    crystal_births = 0
    prev_crystals = 0
    gt_over = vel_over = gap_over = cos_below = 0
    cos_n = 0
    align_over = delta_soft = delta_hard = 0
    gain_ceiling = 0
    n = 0
    youth_early = None
    split_early = None

    with determinism.deterministic(seed):
        print(
            f"boot dim={dim} seed={seed} {workload} pretrain={bool(pretrain)}",
            flush=True,
        )
        gen, cycle, gov, ve = build_engine(cfg)
        print(
            f"booted dim={dim} seed={seed} device={gen.device} "
            f"elapsed={time.perf_counter() - t0:.1f}s",
            flush=True,
        )
        if gen.dim != dim or cycle.dim != dim or cycle.field.dim != dim:
            raise SystemExit(
                f"dim did not follow: gen={gen.dim} cycle={cycle.dim} field={cycle.field.dim}"
            )
        if cycle.watcher.dim != dim or cycle.witness.dim != dim:
            raise SystemExit("watcher/witness dim did not follow the field")
        device = str(gen.device)
        if "cuda" in device.lower():
            raise SystemExit(f"refusing GPU device {device}")
        geometry = _embedding_geometry(gen)
        if thresholds is not None:
            # Explicit band set. None leaves the field's own thresholds,
            # which at FIELD_DIM are the F9 defaults.
            cycle.field.thresholds = {
                "stabilize": float(thresholds["stabilize"]),
                "dream": float(thresholds["dream"]),
                "reflect": float(thresholds["reflect"]),
            }
        thresholds = _live_thresholds(cycle)
        ff = None
        try:
            ff = int(gen.encoder.layers[0].linear1.out_features)
        except Exception:
            ff = None
        if getattr(cycle, "dreamer", None) is not None:
            cycle.dreamer._rng = np.random.default_rng(seed)
        reader_on = getattr(cycle, "rhythm_reader", None) is not None
        slot, decisions = _install_taps(cycle)
        thr = thresholds
        sids = list(sources.keys())
        wts = [weights[s] for s in sids]
        pick = random.Random(seed)
        for i in range(1, steps + 1):
            _reset_slot(slot)
            src = pick.choices(sids, weights=wts)[0]
            tokens = pick.choice(sources[src])
            state = cycle.step(tokens, source_id=src, origin_type="internal")
            n += 1
            rhythms[state.rhythm] += 1
            energy.append(state.field_energy)
            gain.append(state.field_gain)
            if state.field_gain >= 2.999:
                gain_ceiling += 1
            if state.reflection_passes > 0:
                reflect_steps += 1
                if state.converged:
                    reflect_converged += 1
            if state.crystals > prev_crystals:
                crystal_births += state.crystals - prev_crystals
            prev_crystals = state.crystals

            report = slot["report"]
            if report is not None:
                composite.append(report.composite)
                geometric.append(report.geometric)
                temporal.append(report.temporal)
                resonance.append(report.resonance)
                gt = abs(report.geometric - report.temporal)
                gt_gap.append(gt)
                if gt >= float(thr.get("erosion") or 0.30):
                    gt_over += 1
                if report.composite >= float(thr["crystal_coherence"]):
                    crystal_clear["coh"] += 1
                if report.crystallization_pressure >= float(thr["crystal_stability"]):
                    crystal_clear["stab"] += 1
                if report.composite >= float(thr.get("watcher") or 0.40):
                    pass  # stable_rate counted below from the same list
            obs = slot["obs"]
            if obs is not None:
                field_coh.append(obs.internal_coherence)
                harm.append(obs.spectral.harmonic_ratio)
                phase.append(obs.spectral.phase_coherence)
            profile = slot["profile"]
            if profile is not None:
                long_rel.append(profile.long)
                rel_comp.append(profile.composite)
                patterns[profile.pattern()] += 1
                if report is not None and profile.long >= float(thr["crystal_relation"]):
                    crystal_clear["rel"] += 1
                if (
                    report is not None
                    and report.composite >= float(thr["crystal_coherence"])
                    and report.crystallization_pressure >= float(thr["crystal_stability"])
                    and profile.long >= float(thr["crystal_relation"])
                ):
                    crystal_clear["all"] += 1
                if profile.composite >= float(thr["attractor_formation"]):
                    attractor_clear += 1
            stab = slot["stability"]
            if stab is not None:
                stability_l.append(stab)
            if (
                report is not None and profile is not None and stab is not None
                and report.composite >= float(thr["witness_coherence"])
                and profile.long >= float(thr["witness_long"])
                and stab >= float(thr["witness_stability"])
            ):
                crystal_clear["witness"] += 1
            if report is not None and report.composite >= float(thr["witness_snapshot"]):
                crystal_clear["snap"] += 1

            echo = slot["echo"]
            if echo is not None:
                pred_err.append(echo.prediction_error)
                surprise_flags.append(1.0 if echo.surprise >= 0.5 else 0.0)

            vec = None if cycle._last_expressed is None else np.asarray(
                cycle._last_expressed, dtype=float).copy()
            if vec is not None:
                expr.append(vec)
            # Alignment against the field as coherence_impact saw it: the
            # wrapper ran before inject, but the field has since changed.
            # Re-derive from the stored vec and the impact call's field by
            # reading the value the cycle computed only if we captured it.
            # Captured below from the pre-inject norm inside the wrapper via
            # the delta slot's sibling. See align_pre.
            if slot.get("align_pre") is not None:
                alignment.append(slot["align_pre"])
                if slot["align_pre"] >= 0.5:
                    align_over += 1
            if slot["delta"] is not None:
                delta.append(slot["delta"])
                if slot["delta"] < -0.05:
                    delta_soft += 1
                if slot["delta"] < -0.30:
                    delta_hard += 1

            if vec is not None and cycle.attractor.centers:
                u = vec / (np.linalg.norm(vec) + 1e-15)
                best = max(
                    float(np.dot(u, c.vector) / (np.linalg.norm(c.vector) + 1e-15))
                    for c in cycle.attractor.centers
                )
                pull_cos.append(best)
                pull_n += 1
                if best >= float(thr["pull"]):
                    pull_above += 1
            centroid = cycle.crystal_store.centroid()
            if vec is not None and centroid is not None:
                coss = float(np.dot(vec, centroid) / (
                    np.linalg.norm(vec) * np.linalg.norm(centroid) + 1e-15))
                crystal_cos.append(coss)
                cos_n += 1
                if coss < float(thr.get("gaslighting") or -0.20):
                    cos_below += 1
            velocity.append(cycle.witness.anchor_velocity())
            if velocity[-1] >= float(thr.get("drift_velocity") or 0.15):
                vel_over += 1
            gap.append(cycle.witness.anchor_short_long_gap())
            if gap[-1] >= float(thr.get("drift_gap") or 0.30):
                gap_over += 1
            for sig in slot["signals"] or []:
                manip[getattr(sig, "detector", "unknown")] += 1

            if i == _YOUTH_CUT:
                youth_early = _window_cut(
                    n, rhythms, energy, gt_over, manip, decisions, crystal_clear,
                    crystal_births, attractor_clear, pull_above, pull_n,
                    reflect_steps, cycle._boredom_overrides,
                )
                split_early = _split_stock(
                    n, cycle, ve, gov, patterns, crystal_clear,
                )

            if i % 50 == 0 or i == steps:
                elapsed = time.perf_counter() - t0
                print(
                    f"dim={dim} seed={seed} {workload} step={i}/{steps} "
                    f"{elapsed / i * 1000:.0f} ms/step",
                    flush=True,
                )

        expr_meta = cycle.expression_metastability.compute_now()
        gen_meta = cycle.generator_metastability.compute_now()
        vib_full = _vibration(list(expr))
        vib_tail = _vibration(list(expr)[-256:])
        bonds = gov.bond_manager.summary().get("bonds", 0)
        lattice = cycle.lattice.stats()
        binding = cycle.binding.summary()
        active = sum(1 for v in ve.values.values() if v.strength > 1.0)
        strong = sum(1 for v in ve.values.values() if v.strength >= 3.5)
        core = len(ve.core_values())
        total_values = len(ve.values)
        youth_full = _window_cut(
            n, rhythms, energy, gt_over, manip, decisions, crystal_clear,
            crystal_births, attractor_clear, pull_above, pull_n,
            reflect_steps, cycle._boredom_overrides,
        )
        split_full = _split_stock(n, cycle, ve, gov, patterns, crystal_clear)

    elapsed = time.perf_counter() - t0
    dec_total = sum(decisions.values()) or 1
    stable_flags = [1.0 if c >= float(thr.get("watcher") or 0.40) else 0.0 for c in composite]

    def rate(key):
        return decisions.get(key, 0) / dec_total

    reads = {
        "occ_stabilize": rhythms.get("stabilize", 0) / n,
        "occ_dream": rhythms.get("dream", 0) / n,
        "occ_reflect": rhythms.get("reflect", 0) / n,
        "occ_explore": rhythms.get("explore", 0) / n,
        "occ_witness": rhythms.get("witness", 0) / n,
        "energy_mean": _mean(energy),
        "energy_p10": _quant(energy, 0.10),
        "energy_p50": _quant(energy, 0.50),
        "field_coherence_mean": _mean(field_coh),
        "harmonic_ratio_mean": _mean(harm),
        "phase_coherence_mean": _mean(phase),
        "composite_mean": _mean(composite),
        "geometric_mean": _mean(geometric),
        "temporal_mean": _mean(temporal),
        "resonance_mean": _mean(resonance),
        "stable_rate": _mean(stable_flags),
        "gt_gap_mean": _mean(gt_gap),
        "gt_gap_over": gt_over / n,
        "crystal_coh_clear": crystal_clear["coh"] / n,
        "crystal_stab_clear": crystal_clear["stab"] / n,
        "crystal_rel_clear": crystal_clear["rel"] / n,
        "crystal_all_clear": crystal_clear["all"] / n,
        "crystal_births": crystal_births,
        "crystals_end": int(cycle.crystal_store and len(cycle.crystal_store.crystals)),
        "witness_crystal_clear": crystal_clear["witness"] / n,
        "witness_snapshot_clear": crystal_clear["snap"] / n,
        "attractor_form_clear": attractor_clear / n,
        "attractors_end": len(cycle.attractor.centers),
        "pull_cos_mean": _mean(pull_cos),
        "pull_above": (pull_above / pull_n) if pull_n else None,
        "lattice_edges": lattice.get("edges", 0),
        "lattice_nodes": lattice.get("nodes", 0),
        "binding_total": binding.get("total", 0),
        "binding_established": binding.get("established", 0),
        "values_total": total_values,
        "values_active": active,
        "values_strong": strong,
        "values_core": core,
        "alignment_over_0_5": (align_over / n) if alignment else None,
        "field_alignment_mean": _mean(alignment),
        "bonds": bonds,
        "allow_rate": rate("allow"),
        "weakened_rate": rate("allow_weakened"),
        "quarantine_rate": rate("quarantine"),
        "reject_rate": rate("reject"),
        "monitor_rate": rate("monitor"),
        "sacred_rate": rate("sacred_shield"),
        "manip_erosion": manip.get("identity_erosion", 0),
        "manip_drift": manip.get("drift_attack", 0),
        "manip_gaslight": manip.get("gaslighting", 0),
        "manip_wash": manip.get("trust_wash", 0),
        "manip_monopoly": manip.get("source_monopoly", 0),
        "anchor_velocity_mean": _mean(velocity),
        "anchor_gap_mean": _mean(gap),
        "velocity_over": vel_over / n,
        "gap_over": gap_over / n,
        "crystal_cos_mean": _mean(crystal_cos),
        "crystal_cos_below": (cos_below / cos_n) if cos_n else None,
        "coherence_delta_mean": _mean(delta),
        "delta_below_soft": delta_soft / n,
        "delta_below_hard": delta_hard / n,
        "pred_error_mean": _mean(pred_err),
        "surprise_rate": _mean(surprise_flags),
        "reflect_rate": reflect_steps / n,
        "reflect_converged_rate": (reflect_converged / reflect_steps) if reflect_steps else None,
        "expr_meta": float(expr_meta.metastability),
        "expr_regimes": int(expr_meta.n_regimes),
        "expr_state": expr_meta.regime_state,
        "gen_meta": float(gen_meta.metastability),
        "gen_regimes": int(gen_meta.n_regimes),
        "gen_state": gen_meta.regime_state,
        "vib_sf": vib_tail.get("spectral_flatness"),
        "vib_cone": vib_tail.get("cone_deg"),
        "vib_msd1": vib_tail.get("msd_lag1"),
        "vib_label": vib_tail.get("label"),
        "vib_period": vib_tail.get("period"),
        "vib_holds": vib_tail.get("holds"),
        "vib_residual": vib_tail.get("residual_frac"),
        "vib_full_sf": vib_full.get("spectral_flatness"),
        "vib_full_label": vib_full.get("label"),
        "emb_table_cos": geometry.get("emb_table_cos"),
        "emb_pe_cos": geometry.get("emb_pe_cos"),
        "emb_out_cos": geometry.get("emb_out_cos"),
        "emb_over_pe": geometry.get("emb_over_pe"),
        "emb_row_std": geometry.get("emb_row_std"),
        "field_gain_mean": _mean(gain),
        "gain_at_ceiling": gain_ceiling / n,
        "pattern_identity": patterns.get("identity_reinforcement", 0) / n,
        "boredom_overrides": int(cycle._boredom_overrides),
        "long_relation_mean": _mean(long_rel),
        "relation_composite_mean": _mean(rel_comp),
        "stability_mean": _mean(stability_l),
    }
    # Label is classified as a 0/1 against the 128 modal later. Store the
    # string; reduce turns a modal change into vib_label_changed.
    reads_out = {}
    labels = {}
    for k, v in reads.items():
        if isinstance(v, str):
            labels[k] = v
        elif isinstance(v, (bool, np.bool_)):
            reads_out[k] = bool(v)
        elif isinstance(v, (int, np.integer)) and not isinstance(v, (bool, np.bool_)):
            reads_out[k] = int(v)
        else:
            reads_out[k] = _num(v)
    reads_out.update(labels)

    return {
        "schema": 1,
        "dim": int(dim),
        "seed": int(seed),
        "workload": workload,
        "steps": int(steps),
        "field_dim_constant": int(FIELD_DIM),
        "generator_dim": int(gen.dim),
        "field_dim": int(cycle.field.dim),
        "device": device,
        "ff_inner": ff,
        "pretrain": bool(pretrain),
        "dream_channel": False,
        "witness_reader": bool(reader_on),
        "room": room,
        "elapsed_s": round(elapsed, 3),
        "ms_per_step": round(elapsed / max(steps, 1) * 1000.0, 2),
        "thresholds": thresholds,
        "youth": {"cut": _YOUTH_CUT, "early": youth_early, "full": youth_full},
        "split": {"cut": _YOUTH_CUT, "early": split_early, "full": split_full},
        "rhythms": dict(rhythms),
        "decisions": dict(decisions),
        "patterns": dict(patterns),
        "manip": dict(manip),
        "vibration_tail": {k: (_num(v) if not isinstance(v, str) else v) for k, v in vib_tail.items()},
        "vibration_full": {k: (_num(v) if not isinstance(v, str) else v) for k, v in vib_full.items()},
        "reads": reads_out,
    }


def _arm_path(out_dir, workload, dim, seed, steps=None):
    name = f"{workload}-d{dim}-s{seed}"
    if steps is not None and int(steps) != 500:
        name += f"-n{int(steps)}"
    return Path(out_dir) / f"{name}.json"


def _load_arms(out_dir):
    arms = []
    for p in sorted(Path(out_dir).glob("*-d*-s*.json")):
        arms.append(json.loads(p.read_text(encoding="utf-8")))
    return arms


def _group(arms):
    grouped = {}
    for arm in arms:
        grouped.setdefault(arm["workload"], {}).setdefault(arm["dim"], []).append(arm)
    return grouped


def _seed_stats(values):
    finite = []
    for v in values:
        if v is None:
            continue
        if isinstance(v, str):
            continue
        x = float(v)
        if math.isfinite(x):
            finite.append(round(x, 6))
    if not finite:
        return None
    return {
        "n": len(finite),
        "mean": round(sum(finite) / len(finite), 6),
        "span": round(max(finite) - min(finite), 6),
        "min": min(finite),
        "max": max(finite),
        "values": finite,
    }


def _moved(stat_w, stat_128):
    if stat_w is None or stat_128 is None:
        return None
    if stat_128["n"] < 2 or stat_w["n"] < 2:
        return None
    delta = round(stat_w["mean"] - stat_128["mean"], 6)
    return abs(delta) > stat_128["span"]


def _modal(labels):
    if not labels:
        return None
    c = Counter(labels)
    top = c.most_common()
    if len(top) > 1 and top[0][1] == top[1][1]:
        return "tie"
    return top[0][0]


def reduce_dir(out_dir):
    arms = _load_arms(out_dir)
    if not arms:
        print(f"no arms in {out_dir}")
        return 1
    grouped = _group(arms)
    print(f"arms {len(arms)}  workloads {sorted(grouped)}")
    print("rule: moved when abs(mean_W - mean_128) > span_128, reads rounded to 6 d.p.")
    print("pin dials are reported and are not retune candidates.")
    print()
    for note in NOT_ON_WORKLOAD:
        print(f"not on this workload: {note}")
    print()
    report = {"rule": "abs(mean_W - mean_128) > span_128", "workloads": {}}
    for workload, by_dim in grouped.items():
        if 128 not in by_dim:
            print(f"{workload}: no 128 arm, cannot classify")
            continue
        widths = sorted(by_dim)
        print(f"## {workload}  widths {widths}  seeds "
              f"{sorted(a['seed'] for a in by_dim[128])}")
        base_reads = [a["reads"] for a in by_dim[128]]
        base_labels = [a["reads"].get("vib_label") for a in by_dim[128]]
        modal_128 = _modal(base_labels)
        dial_rows = []
        for dial in DIALS:
            keys = list(dial.get("gate") or ()) + list(dial.get("level") or ()) + list(dial.get("pin") or ())
            per_width = {}
            flags = {}
            for width in widths:
                stats = {}
                reads_w = [a["reads"] for a in by_dim[width]]
                for key in keys:
                    if key == "vib_label_changed":
                        modal = _modal([a["reads"].get("vib_label") for a in by_dim[width]])
                        changed = 0.0 if modal == modal_128 else 1.0
                        if modal in (None, "tie") or modal_128 in (None, "tie"):
                            stats[key] = None
                        else:
                            # Same value on every seed of this width: span 0.
                            # At 128, changed is 0. At W, changed is 0 or 1.
                            stats[key] = {
                                "n": len(reads_w), "mean": changed, "span": 0.0,
                                "min": changed, "max": changed,
                                "values": [changed] * len(reads_w),
                                "modal": modal,
                            }
                    else:
                        stats[key] = _seed_stats([r.get(key) for r in reads_w])
                per_width[str(width)] = stats
                if width == 128:
                    continue
                gate_moved = []
                level_moved = []
                for key in dial.get("gate") or ():
                    if _moved(stats.get(key), per_width["128"].get(key)):
                        gate_moved.append(key)
                for key in dial.get("level") or ():
                    if _moved(stats.get(key), per_width["128"].get(key)):
                        level_moved.append(key)
                pin_moved = []
                for key in dial.get("pin") or ():
                    if _moved(stats.get(key), per_width["128"].get(key)):
                        pin_moved.append(key)
                if "pin" in dial:
                    klass = "pin" if not pin_moved else "pin-moved"
                elif gate_moved:
                    klass = "retune"
                elif level_moved:
                    klass = "shifted"
                elif any(per_width["128"].get(k) is None for k in keys):
                    # A dial with no live 128 read on every key is untested
                    # only when every key is null. Mixed is classified on
                    # the keys that exist; if none of those moved, invariant
                    # if at least one key was live.
                    live = [k for k in keys if per_width["128"].get(k) is not None]
                    klass = "untested" if not live else "invariant"
                else:
                    klass = "invariant"
                flags[str(width)] = {
                    "class": klass,
                    "gate_moved": gate_moved,
                    "level_moved": level_moved,
                    "pin_moved": pin_moved,
                }
            dial_rows.append({"id": dial["id"], "census": dial["census"], "reads": per_width, "flags": flags})
            for width, flag in flags.items():
                bits = []
                stats_w = per_width[width]
                stats_0 = per_width["128"]
                show = list(flag["gate_moved"]) + list(flag["level_moved"]) + list(flag["pin_moved"])
                if not show and flag["class"] in ("invariant", "pin"):
                    show = [k for k in (list(dial.get("gate") or ())[:1] or list(dial.get("level") or ())[:1] or list(dial.get("pin") or ())[:1])]
                for key in show:
                    a = stats_0.get(key) or {}
                    b = stats_w.get(key) or {}
                    if not a or not b:
                        bits.append(f"{key}=null")
                        continue
                    delta = round(b["mean"] - a["mean"], 6)
                    bits.append(
                        f"{key} {a['mean']}±{a['span']} -> {b['mean']} (d {delta})"
                    )
                extra = (" " + " ".join(bits)) if bits else ""
                print(f"  {flag['class']:11s} {width:>4}  {dial['id']:24s}{extra}")
        report["workloads"][workload] = dial_rows
        print()
    out = Path(out_dir) / "classification.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"WROTE {out}")
    return 0


# Late-window reads for the step-4 split. Rates are cumulative counts.
# Stocks are levels; the settled read is the increment. Metastability's
# settled read is the end snapshot (trailing window of 128).
_SPLIT_RATES = ("pattern_identity", "witness_crystal", "witness_snapshot")
_SPLIT_STOCKS = (
    "lattice_edges", "lattice_nodes",
    "binding_total", "binding_established",
    "bonds", "values_core",
)
_SPLIT_META = ("expr_regimes", "gen_regimes")


def _late_value(arm, key):
    """One seed's settled read, or None if the arm has no cut snapshot."""
    split = arm.get("split") or {}
    early = split.get("early")
    full = split.get("full")
    if not early or not full:
        return None
    late_steps = int(full["steps"]) - int(early["steps"])
    if late_steps <= 0:
        return None
    if key in _SPLIT_RATES:
        return (int(full[key]) - int(early[key])) / late_steps
    if key in _SPLIT_STOCKS:
        return int(full[key]) - int(early[key])
    if key in _SPLIT_META:
        return int(full[key])
    raise KeyError(key)


def _unresolved(stat_w, stat_128):
    """Span swallowed a gap that is still large relative to the 128 level.

    A near-zero increment at both widths is resolved: the settled field
    is not doing the thing. That is youth-only or invariant, not a cue
    for a longer arm.
    """
    if stat_w is None or stat_128 is None:
        return False
    if stat_128["n"] < 2 or stat_w["n"] < 2:
        return False
    gap = abs(stat_w["mean"] - stat_128["mean"])
    if gap <= stat_128["span"] and gap > 0.20 * max(abs(stat_128["mean"]), 1.0):
        return True
    return False


def reduce_split(out_dir):
    """Classify the seven previously unsplit dials. Prints and writes JSON."""
    arms = _load_arms(out_dir)
    if not arms:
        print(f"no arms in {out_dir}")
        return 1
    if any(a.get("split", {}).get("early") is None for a in arms):
        print("an arm is missing split.early (steps shorter than the cut, or an old file)")
        return 1
    grouped = _group(arms)
    keys = _SPLIT_RATES + _SPLIT_STOCKS + _SPLIT_META
    print(f"split arms {len(arms)}  cut {_YOUTH_CUT}")
    print("late read moves when abs(mean_W - mean_128) > span_128, 6 d.p.")
    print("rates: late fraction. stocks: late increment. meta: end window.")
    print()
    report = {"rule": "abs(mean_late_W - mean_late_128) > span_late_128", "workloads": {}}
    for workload, by_dim in grouped.items():
        if 128 not in by_dim:
            print(f"{workload}: no 128 arm")
            continue
        widths = sorted(by_dim)
        print(f"## {workload}  widths {widths}  seeds "
              f"{sorted(a['seed'] for a in by_dim[128])}  "
              f"steps {sorted({a['steps'] for a in by_dim[128]})}")
        rows = []
        for key in keys:
            per_width = {}
            for width in widths:
                per_width[str(width)] = _seed_stats(
                    [_late_value(a, key) for a in by_dim[width]]
                )
            flags = {}
            base = per_width["128"]
            for width in widths:
                if width == 128:
                    continue
                moved = _moved(per_width[str(width)], base)
                flags[str(width)] = {
                    "class": (
                        "insufficient" if moved is None
                        else "moves-when-settled" if moved
                        else "youth-only"
                    ),
                    "unresolved": _unresolved(per_width[str(width)], base),
                }
            kind = (
                "rate" if key in _SPLIT_RATES
                else "stock-increment" if key in _SPLIT_STOCKS
                else "end-window"
            )
            rows.append({"id": key, "kind": kind, "reads": per_width, "flags": flags})
            for width, flag in flags.items():
                a = base or {}
                b = per_width[width] or {}
                if not a or not b:
                    detail = "null"
                else:
                    delta = round(b["mean"] - a["mean"], 6)
                    detail = (
                        f"{a['values']} -> {b['values']}  "
                        f"mean {a['mean']} span {a['span']} -> {b['mean']} (d {delta})"
                    )
                mark = " UNRESOLVED" if flag["unresolved"] else ""
                print(f"  {flag['class']:20s} {width:>4}  {key:24s} {detail}{mark}")
            # Youth window of the regime count, so a settled move can be
            # compared with the window that still holds the opening.
            if key in _SPLIT_META:
                for width in widths:
                    early_stats = _seed_stats([
                        (a.get("split") or {}).get("early", {}).get(key)
                        for a in by_dim[width]
                    ])
                    states = [
                        (a.get("split") or {}).get("full", {}).get(
                            "expr_state" if key == "expr_regimes" else "gen_state"
                        )
                        for a in by_dim[width]
                    ]
                    if early_stats:
                        print(
                            f"  {'youth-window':20s} {width:>4}  {key:24s} "
                            f"{early_stats['values']}  end-state {states}"
                        )
        report["workloads"][workload] = rows
        print()
    out = Path(out_dir) / "split-classification.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"WROTE {out}")
    return 0


def _run_listed(list_path):
    """One process, many arms. The importer pays torch once per worker."""
    jobs = json.loads(Path(list_path).read_text(encoding="utf-8"))
    for job in jobs:
        arm = run_arm(job["dim"], job["seed"], job["workload"], job["steps"])
        path = _arm_path(job["out"], job["workload"], job["dim"], job["seed"], job["steps"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(arm, indent=2, sort_keys=True), encoding="utf-8")
        print(f"WROTE {path}", flush=True)
    return 0


def _batch_split(out_dir, steps, jobs):
    """A few worker processes, each walking a slice of the 18 arms."""
    import subprocess
    dims = (128, 256, 768)
    seeds = (42, 43, 44)
    workloads = ("canonical", "wide")
    jobs_list = [(w, d, s) for w in workloads for d in dims for s in seeds]
    pending = []
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for w, d, s in jobs_list:
        path = _arm_path(out, w, d, s, steps)
        if path.is_file():
            try:
                got = json.loads(path.read_text(encoding="utf-8"))
                if got.get("split", {}).get("full") and got.get("steps") == int(steps):
                    print(f"skip {path.name}", flush=True)
                    continue
            except json.JSONDecodeError:
                pass
        pending.append({
            "workload": w, "dim": d, "seed": s,
            "steps": int(steps), "out": str(out),
        })
    n = max(1, int(jobs))
    print(f"batch-split {len(pending)} arms, {n} workers, steps {steps}", flush=True)
    if not pending:
        return reduce_split(out_dir)
    lists = [pending[i::n] for i in range(n)]
    procs = []
    for i, chunk in enumerate(lists):
        if not chunk:
            continue
        list_path = out / f"_worker-{i}.json"
        list_path.write_text(json.dumps(chunk), encoding="utf-8")
        procs.append(subprocess.Popen(
            [sys.executable, "-m", "tests.diagnostic.widening.dial_census_probe",
             "--run-list", str(list_path)],
        ))
    failed = []
    for proc in procs:
        code = proc.wait()
        if code != 0:
            failed.append(code)
    if failed:
        print(f"batch-split failed, worker exits {failed}", flush=True)
        return 1
    print("batch-split done", flush=True)
    return reduce_split(out_dir)


def _check():
    fails = []
    if FIELD_DIM != 128:
        fails.append(f"FIELD_DIM is {FIELD_DIM}, expected 128")
    rng = np.random.Generator(np.random.PCG64(0))
    labels = {}
    for kind in ("white", "vibration", "lock-in"):
        r = _vibration(synthetic_stream(kind, n=128, dim=32, rng=rng))
        labels[kind] = r["label"]
        print(f"  synthetic {kind:10s} {r['label']:10s} sf={_num(r.get('spectral_flatness'))}")
    if labels.get("white") == labels.get("lock-in"):
        fails.append(f"vibration controls did not separate: {labels}")
    if labels.get("vibration") not in ("vibration", "lock-in"):
        fails.append(f"vibration control labelled {labels.get('vibration')}")
    if labels.get("white") != "white":
        fails.append(f"white control labelled {labels.get('white')}")
    cfg = dict(CONFIG)
    cfg["dim"] = 256
    cfg["pretrain_on_corpus"] = False
    cfg["session_persistence"] = False
    cfg["log_interval"] = 10 ** 9
    with determinism.deterministic(1):
        gen, cycle, _gov, _ve = build_engine(cfg)
        cycle.step(["identity", "continuity"], source_id="source_samuel", origin_type="internal")
    if gen.dim != 256 or cycle.field.dim != 256 or cycle.watcher.dim != 256:
        fails.append(f"override failed gen={gen.dim} field={cycle.field.dim}")
    if "cuda" in str(gen.device).lower():
        fails.append(f"device {gen.device}")
    if FIELD_DIM != 128:
        fails.append("FIELD_DIM changed during the override boot")
    try:
        ff = int(gen.encoder.layers[0].linear1.out_features)
    except Exception as exc:
        ff = None
        fails.append(f"ff width unreadable: {exc}")
    if ff is not None and ff != 256 * 4:
        fails.append(f"ff inner {ff}, expected {256 * 4}")
    print(f"  override dim={gen.dim} device={gen.device} ff={ff} FIELD_DIM={FIELD_DIM}")
    if fails:
        for f in fails:
            print("FAIL", f)
        return 1
    print("PASS check")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description="Measure width-sensitive dials. Changes no constants.")
    p.add_argument("--check", action="store_true")
    p.add_argument("--arm", action="store_true")
    p.add_argument("--reduce", metavar="DIR")
    p.add_argument("--split-reduce", metavar="DIR")
    p.add_argument("--batch-split", metavar="DIR",
                   help="18 arms (canonical+wide, 128/256/768, seeds 42-44) with the split snapshot")
    p.add_argument("--run-list", metavar="PATH",
                   help="worker: run the arms listed in this JSON file")
    p.add_argument("--jobs", type=int, default=2)
    p.add_argument("--dim", type=int, default=128)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--workload", default="canonical", choices=("canonical", "wide"))
    p.add_argument("--steps", type=int, default=500)
    p.add_argument("--out", default="")
    p.add_argument(
        "--pretrain", action="store_true",
        help="8-epoch corpus pretrain then eval (production boot; default off)",
    )
    args = p.parse_args(argv)
    if args.check:
        return _check()
    if args.split_reduce:
        return reduce_split(args.split_reduce)
    if args.run_list:
        return _run_listed(args.run_list)
    if args.batch_split:
        return _batch_split(args.batch_split, args.steps, args.jobs)
    if args.reduce:
        return reduce_dir(args.reduce)
    if not args.arm:
        p.print_help()
        return 2
    arm = run_arm(
        args.dim, args.seed, args.workload, args.steps,
        pretrain=args.pretrain,
    )
    text = json.dumps(arm, indent=2, sort_keys=True)
    if args.out:
        path = _arm_path(args.out, args.workload, args.dim, args.seed, args.steps)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(f"WROTE {path}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
