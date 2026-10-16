"""
tests/diagnostic/metastability/h0_probe.py

H0 on the ordinary path. Witness and rupture stay OFF. No runtime, gate, or
lever-default change: every nudge is applied to a forked copy inside this probe.

Stack: all_levers_composition_probe.build_all_on (the all-ON stack).
Workload: the composition gate's workload A — Resonance Family phrases, no
witness phrases, origin_type internal — under substrate.determinism, so a seed
replays. The workload Random is the gate's random.Random(seed), not the RNG
the cycle draws from.

Subcommands:
    time    cost per 1k steps, estimator self-check, one bit-exact fork
    run     long trajectory, MSD / timescale ratio, lead, recovery vs age

What this measures, and the versions that are well-posed:

  Shape. MSD(tau) of each stream, and the same on the unit direction of the
  raw field and the tanh view. The raw field is an unnormalized leaky sum, so
  its norm equilibrating is not directional drift. Alpha is fit on a short-lag
  band and a long-lag band; a bounded series looks diffusive at short lag and
  flat at long lag.

  Timescale. Integrated autocorrelation and the lag where rho falls below 1/e,
  per window. A window whose variance is at the noise floor is reported as
  frozen, not given a finite tau. The ratio uses the 1/e time. effective_lr is
  clip(watcher_composite^2, 0.01, 1), the formula witness.update applies. That
  composite is not field internal_coherence (the ~0.998 gauge). Both are recorded.

  Who leads. Cross-correlation of displacements, then the same after removing
  the contemporaneous expressed-vector displacement (the shared driver). The
  fork is the causal test. The field nudge is tangential to the raw field at
  the calibration age: a radial nudge is what tanh saturation is built to hide,
  and that radial view-delta is reported beside it, not used as the experiment.
  The anchor nudge is applied to the three EMA layers and the composite is
  recomputed with the witness's own weights. Writing only the composite would
  be gone on the next update(), which overwrites it from the layers.

  Recovery. Divergence from the unperturbed twin (the plain run), not from the
  pre-hit vector. The system moves anyway. Repeated hits are compared to a
  single hit at the same age, so "faster" is not just "older".

Perturbation size is chosen once per seed from the median per-step motion
before the first fork age: 100x that median, floored at 1e-4 and capped at
1e-2 (L2). That is above float64 dust (~1e-15) and below the manipulation
detector's anchor-velocity threshold (0.15). The direction comes from a
private PCG64, never from the cycle's RNG.

Raw vectors go to the scratch directory this probe prints. A compressed summary
is written under docs/findings/data/ only when --summary is set.

    python -m tests.diagnostic.metastability.h0_probe time --steps 400 --seed 42
    python -m tests.diagnostic.metastability.h0_probe run --steps 20000 --seeds 42,43
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import pickle
import random
import sys
import time
from pathlib import Path

import numpy as np

logging.disable(logging.CRITICAL)

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from substrate import determinism  # noqa: E402
from tests._common import RESONANCE_FAMILY_SOURCES, RESONANCE_FAMILY_WEIGHTS  # noqa: E402
from tests.diagnostic.integrity.all_levers_composition_probe import build_all_on  # noqa: E402

RHYTHM_CODE = {"stabilize": 0, "dream": 1, "reflect": 2, "explore": 3}
VAR_FLOOR = 1e-18          # mean ||x - mean||^2 below this: the window is frozen
DIVERGE_FLOOR = 1e-9       # above float dust, below any nudge we actually apply
VIEW_FLOOR = 1e-4          # smallest view / anchor L2 nudge we will call readable
NUDGE_CAP = 1e-2           # largest anchor/view kick: still << drift-detector threshold 0.15
RAW_NUDGE_CAP = 1.0        # raw-field L2 cap. Chasing a view target past this is not a nudge:
                           # on a saturated field tanh is already ±1 in float64, and a
                           # bigger raw kick would move the energy band.
DESAT_RMS = 1.5            # separate, labeled experiment: rescale the raw field to this
                           # per-component rms so the view can leave ±1. Not a nudge.
PRIVATE_SEED = 0xA11CE


# ---------------------------------------------------------------------------
# Workload A (the composition gate's canonical arm, no witness phrases)
# ---------------------------------------------------------------------------

def workload_sources():
    sids = list(RESONANCE_FAMILY_SOURCES)
    weights = [RESONANCE_FAMILY_WEIGHTS[s] for s in sids]
    return sids, weights


def draw(pick, sids, weights):
    src = pick.choices(sids, weights=weights)[0]
    toks = pick.choice(RESONANCE_FAMILY_SOURCES[src])
    return src, toks


# ---------------------------------------------------------------------------
# Estimators
# ---------------------------------------------------------------------------

def _lags_for(n, limit):
    raw = [1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128,
           192, 256, 384, 512, 768, 1024, 1536, 2048, 3072, 4096, 6144, 8192]
    cap = max(2, min(limit, n // 2))
    return [L for L in raw if L <= cap]


def msd_curve(X, lags):
    """Mean squared displacement of rows of X at each lag. X is (T, D)."""
    out = np.full(len(lags), np.nan)
    T = len(X)
    for i, lag in enumerate(lags):
        if lag <= 0 or lag >= T:
            continue
        d = X[lag:] - X[:-lag]
        out[i] = float(np.mean(np.sum(d * d, axis=1)))
    return out


def loglog_alpha(lags, msd):
    lags = np.asarray(lags, dtype=float)
    msd = np.asarray(msd, dtype=float)
    ok = (lags > 0) & (msd > 0) & np.isfinite(msd)
    if int(ok.sum()) < 3:
        return float("nan"), float("nan")
    x = np.log(lags[ok])
    y = np.log(msd[ok])
    x = x - x.mean()
    y = y - y.mean()
    denom = float(np.dot(x, x))
    if denom < 1e-18:
        return float("nan"), float("nan")
    alpha = float(np.dot(x, y) / denom)
    resid = y - alpha * x
    ss_res = float(np.dot(resid, resid))
    ss_tot = float(np.dot(y, y))
    r2 = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else float("nan")
    return alpha, r2


def unit_rows(X):
    n = np.linalg.norm(X, axis=1, keepdims=True)
    return X / np.maximum(n, 1e-15)


def timescale(X, max_lag):
    """Autocorrelation time of a vector series.

    rho(lag) = mean_t (x(t)-mu) · (x(t+lag)-mu) / mean ||x-mu||^2.
    tau_int stops at the first non-positive rho (Sokal's initial positive
    sequence). tau_e is the smallest lag with rho < 1/e. A window with
    variance under VAR_FLOOR is frozen: tau is not identified.
    """
    T = len(X)
    Y = X - X.mean(axis=0, keepdims=True)
    var = float(np.mean(np.sum(Y * Y, axis=1)))
    rms = float(np.sqrt(max(var, 0.0)))
    if T < 8 or var < VAR_FLOOR:
        return {"status": "frozen", "var": var, "rms": rms,
                "tau_int": float("inf"), "tau_e": float("inf"), "rho1": float("nan")}
    max_lag = int(min(max_lag, T // 2))
    rhos = np.empty(max_lag)
    for lag in range(1, max_lag + 1):
        rhos[lag - 1] = float(np.mean(np.sum(Y[lag:] * Y[:-lag], axis=1)) / var)
    pos = 0.0
    for r in rhos:
        if r <= 0:
            break
        pos += float(r)
    tau_int = 0.5 + pos
    below = np.where(rhos < np.exp(-1.0))[0]
    if len(below):
        tau_e = float(below[0] + 1)
        status = "measured"
    else:
        tau_e = float("inf")
        status = "slower than window"
    return {"status": status, "var": var, "rms": rms, "tau_int": float(tau_int),
            "tau_e": tau_e, "rho1": float(rhos[0]), "max_lag": max_lag}


def xcorr(da, db, max_lag):
    """Normalized displacement cross-correlation.

    Positive lag means db is later than da: da leads. Coefficient is in
    [-1, 1] by Cauchy-Schwarz on the paired rows.
    """
    lags = list(range(-max_lag, max_lag + 1))
    rho = np.full(len(lags), np.nan)
    for i, lag in enumerate(lags):
        if lag < 0:
            a, b = da[-lag:], db[:lag]
        elif lag > 0:
            a, b = da[:-lag], db[lag:]
        else:
            a, b = da, db
        if len(a) < 2:
            continue
        num = float(np.mean(np.sum(a * b, axis=1)))
        ea = float(np.mean(np.sum(a * a, axis=1)))
        eb = float(np.mean(np.sum(b * b, axis=1)))
        den = (ea * eb) ** 0.5
        rho[i] = num / den if den > 0 else float("nan")
    return lags, rho


def residualize(d, driver):
    """Remove, at each time, the part of d parallel to driver."""
    dots = np.sum(d * driver, axis=1)
    n2 = np.sum(driver * driver, axis=1)
    coef = np.divide(dots, n2, out=np.zeros_like(dots), where=n2 > 1e-30)
    return d - coef[:, None] * driver


def first_above(div, floor=DIVERGE_FLOOR):
    idx = np.flatnonzero(np.asarray(div) > floor)
    return int(idx[0]) if len(idx) else None


def recovery_of(div, initial):
    """Return to the twin. div[0] is the kick; recovery is looked for after it.

    absorbed  — fell to 10% of the kick and finished there
    persists  — still above 10% at the horizon, and did not run away
    grows     — finished at >= 2x the kick
    """
    div = np.asarray(div, dtype=float)
    if not np.isfinite(initial) or initial < DIVERGE_FLOOR:
        return {"class": "no-kick", "t_rec": None, "residual": float("nan"),
                "peak_over_kick": float("nan")}
    residual = float(div[-1] / initial)
    peak = float(np.nanmax(div) / initial)
    below = np.flatnonzero(div[1:] <= 0.1 * initial)
    t_rec = int(below[0] + 1) if len(below) else None
    if residual >= 2.0:
        kind = "grows"
    elif t_rec is not None and residual < 0.1:
        kind = "absorbed"
    elif residual < 0.1:
        kind = "absorbed"
    else:
        kind = "persists"
    return {"class": kind, "t_rec": t_rec, "residual": residual, "peak_over_kick": peak}


# ---------------------------------------------------------------------------
# Perturbation (no shared RNG)
# ---------------------------------------------------------------------------

def private_direction(dim, seed, salt):
    g = np.random.Generator(np.random.PCG64([PRIVATE_SEED, int(seed), int(salt)]))
    v = g.normal(size=dim)
    n = float(np.linalg.norm(v))
    return v / (n if n > 0 else 1.0)


def tangential(direction, axis):
    axis = np.asarray(axis, dtype=float)
    n = float(np.linalg.norm(axis))
    if n < 1e-12:
        out = np.asarray(direction, dtype=float).copy()
    else:
        u = axis / n
        out = np.asarray(direction, dtype=float) - u * float(np.dot(direction, u))
    n2 = float(np.linalg.norm(out))
    if n2 < 1e-12:
        # The draw landed on the axis. Step to the next coordinate.
        out = np.zeros(len(axis))
        out[0] = 1.0
        out = out - (axis / n) * float(axis[0] / n) if n >= 1e-12 else out
        n2 = float(np.linalg.norm(out))
    return out / (n2 if n2 > 0 else 1.0)


def _anchor_from_layers(witness, short, mid, long):
    raw = (witness.short_weight * short
           + witness.mid_weight * mid
           + witness.long_weight * long)
    return raw / (float(np.linalg.norm(raw)) + 1e-8)


def anchor_disp(witness, direction, scale):
    new = _anchor_from_layers(
        witness,
        witness._short + scale * direction,
        witness._mid + scale * direction,
        witness._long + scale * direction,
    )
    return float(np.linalg.norm(new - witness._anchor))


def view_disp(raw, direction, scale):
    return float(np.linalg.norm(np.tanh(raw + scale * direction) - np.tanh(raw)))


def solve_scale(disp_fn, target, hi_cap=1e3):
    """Largest scale whose displacement is still <= target, unless even a
    vanishing scale overshoots (returns a tiny scale) or the response
    saturates before the target (returns the scale where it stopped growing)."""
    if disp_fn(0.0) >= target:
        return 0.0, disp_fn(0.0)
    hi = 1e-6
    prev = disp_fn(hi)
    stalled = False
    while prev < target and hi < hi_cap:
        nxt = hi * 2.0
        d = disp_fn(nxt)
        if d < prev * 1.001 and d < target:
            stalled = True
            break
        hi = nxt
        prev = d
    if stalled or prev < target:
        return hi, prev
    lo = 0.0
    for _ in range(50):
        mid = 0.5 * (lo + hi)
        if disp_fn(mid) < target:
            lo = mid
        else:
            hi = mid
    return hi, disp_fn(hi)


def apply_field(field, direction, scale):
    field.field = field.field + scale * direction


def apply_anchor(witness, direction, scale):
    witness._short = witness._short + scale * direction
    witness._mid = witness._mid + scale * direction
    witness._long = witness._long + scale * direction
    witness._anchor = _anchor_from_layers(witness, witness._short, witness._mid, witness._long)
    # _prev_anchor is left where the last real step put it, so this is a
    # genuine one-step jump. The nudge cap keeps that jump far under the
    # 0.15 drift-detector threshold.


def apply_desat(field, target_rms=DESAT_RMS):
    """Rescale the raw field to `target_rms` per component. The view then leaves ±1."""
    raw = np.asarray(field.field, dtype=np.float64)
    rms = float(np.sqrt(np.mean(raw * raw)))
    if rms < 1e-8:
        return
    field.field = raw * (target_rms / rms)


def choose_nudges(witness, raw, seed, med_view, med_anchor):
    """One tangential field nudge and one anchor-layer nudge, frozen for the seed.

    The field scale is whatever would move the view by the target, but never
    above RAW_NUDGE_CAP. Past that cap the view target is unreachable because
    tanh has already saturated to ±1, and a larger raw displacement would be a
    different experiment (see apply_desat).
    """
    target_view = float(np.clip(100.0 * med_view, VIEW_FLOOR, NUDGE_CAP))
    target_anchor = float(np.clip(100.0 * med_anchor, VIEW_FLOOR, NUDGE_CAP))
    d_field = tangential(private_direction(len(raw), seed, 1), raw)
    d_anchor = tangential(private_direction(len(raw), seed, 2), witness._anchor)
    s_field, got_view = solve_scale(lambda s: view_disp(raw, d_field, s), target_view)
    s_anchor, got_anchor = solve_scale(lambda s: anchor_disp(witness, d_anchor, s), target_anchor)
    field_capped = s_field > RAW_NUDGE_CAP
    if field_capped:
        s_field = RAW_NUDGE_CAP
        got_view = view_disp(raw, d_field, s_field)
    if s_anchor > 1.0:
        s_anchor = 1.0
        got_anchor = anchor_disp(witness, d_anchor, s_anchor)
    radial = raw / (float(np.linalg.norm(raw)) + 1e-12)
    radial_view = view_disp(raw, radial, s_field)
    nudged = raw + s_field * d_field
    return {
        "target_view": target_view,
        "target_anchor": target_anchor,
        "med_view": float(med_view),
        "med_anchor": float(med_anchor),
        "s_field": float(s_field),
        "s_anchor": float(s_anchor),
        "got_view": float(got_view),
        "got_anchor": float(got_anchor),
        "field_capped": bool(field_capped),
        "view_bit_identical": bool(np.array_equal(np.tanh(raw), np.tanh(nudged))),
        "radial_view_at_same_raw_l2": float(radial_view),
        "d_field": d_field,
        "d_anchor": d_anchor,
        "mean_sech2": float(np.mean(1.0 - np.tanh(raw) ** 2)),
        "raw_rms": float(np.sqrt(np.mean(raw * raw))),
    }


# ---------------------------------------------------------------------------
# Snapshot (pickle, so the live cycle is not kept twice in RAM)
# ---------------------------------------------------------------------------

def _np_state():
    st = np.random.get_state()
    copied = []
    for item in st:
        copied.append(np.array(item, copy=True) if isinstance(item, np.ndarray) else item)
    return tuple(copied)


def capture_rng():
    """The cycle's RNG only. Two forked cycles that share a process must each
    start a step from this same snapshot, or the second one draws the numbers
    the first one already consumed."""
    import torch
    return {
        "py": pickle.dumps(random.getstate(), protocol=pickle.HIGHEST_PROTOCOL),
        "np": _np_state(),
        "torch": torch.random.get_rng_state().clone(),
        "clock": pickle.dumps(determinism._clock, protocol=pickle.HIGHEST_PROTOCOL),
        "seq": pickle.dumps(determinism._seq, protocol=pickle.HIGHEST_PROTOCOL),
        "keys": pickle.dumps(determinism._keys, protocol=pickle.HIGHEST_PROTOCOL),
    }


def restore_rng(snap):
    import torch
    determinism._clock = pickle.loads(snap["clock"])
    determinism._seq = pickle.loads(snap["seq"])
    determinism._keys = pickle.loads(snap["keys"])
    random.setstate(pickle.loads(snap["py"]))
    np.random.set_state(snap["np"])
    torch.random.set_rng_state(snap["torch"].clone())


def capture(cycle, pick):
    snap = capture_rng()
    snap["cycle"] = pickle.dumps(cycle, protocol=pickle.HIGHEST_PROTOCOL)
    snap["pick"] = pick.getstate()
    return snap


def restore(snap, pick):
    cycle = pickle.loads(snap["cycle"])
    # Set RNG after the unpickle. Loading a module must not leave the stream
    # where the next step will draw from.
    restore_rng(snap)
    pick.setstate(snap["pick"])
    return cycle


def weight_digest(gen):
    h = hashlib.sha256()
    for p in gen.parameters():
        h.update(np.ascontiguousarray(p.detach().cpu().numpy()).tobytes())
    return h.hexdigest()


def value_digest(ve):
    h = hashlib.sha256()
    items = sorted(ve.values.items(), key=lambda kv: str(kv[0]))
    for k, v in items:
        h.update(str(k).encode())
        h.update(np.float64(v.strength).tobytes())
        h.update(np.int64(v.dissolved_at_step).tobytes())
        h.update(np.int64(v.birth_step).tobytes())
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Recording
# ---------------------------------------------------------------------------

class Trace:
    def __init__(self, steps, dim):
        self.steps = steps
        self.dim = dim
        self.raw = np.empty((steps, dim), np.float64)
        self.view = np.empty((steps, dim), np.float64)
        self.anchor = np.empty((steps, dim), np.float64)
        self.short = np.empty((steps, dim), np.float64)
        self.mid = np.empty((steps, dim), np.float64)
        self.long = np.empty((steps, dim), np.float64)
        self.expr = np.empty((steps, dim), np.float64)
        self.field_coh = np.empty(steps, np.float64)
        self.watcher = np.empty(steps, np.float64)
        self.eff_lr = np.empty(steps, np.float64)
        self.sat = np.empty(steps, np.float64)
        self.sat99 = np.empty(steps, np.float64)
        self.view_gain = np.empty(steps, np.float64)
        self.raw_norm = np.empty(steps, np.float64)
        self.expr_norm = np.empty(steps, np.float64)
        self.live = np.empty(steps, np.int32)
        self.births = np.empty(steps, np.int32)
        self.ever = np.empty(steps, np.int32)
        self.attractors = np.empty(steps, np.int32)
        self.crystals = np.empty(steps, np.int32)
        self.rhythm = np.empty(steps, np.int16)
        self.boredom = np.empty(steps, np.int32)
        self.inputs = [None] * steps
        self.weights_at = {}
        self.values_at = {}
        # RNG state after this step, i.e. what the next step draws from.
        # Saved only inside fork windows. A perturbed step is started from the
        # plain run's state, so a branch that draws extra numbers cannot shift
        # every later step off the plain noise sequence.
        self.rng_at = {}


def record_step(tr, i, cycle, ve, state, src, toks, boredom_before):
    raw = np.asarray(cycle.field.field, dtype=np.float64)
    view = np.tanh(raw)
    expr = np.asarray(cycle._last_expressed, dtype=np.float64)
    tr.raw[i] = raw
    tr.view[i] = view
    tr.anchor[i] = np.asarray(cycle.witness._anchor, dtype=np.float64)
    tr.short[i] = np.asarray(cycle.witness._short, dtype=np.float64)
    tr.mid[i] = np.asarray(cycle.witness._mid, dtype=np.float64)
    tr.long[i] = np.asarray(cycle.witness._long, dtype=np.float64)
    tr.expr[i] = expr
    tr.field_coh[i] = float(cycle.field.internal_coherence())
    tr.watcher[i] = float(state.coherence)
    tr.eff_lr[i] = float(np.clip(state.coherence ** 2, 0.01, 1.0))
    abs_view = np.abs(view)
    tr.sat[i] = float(np.mean(abs_view > 0.95))
    tr.sat99[i] = float(np.mean(abs_view > 0.99))
    tr.view_gain[i] = float(np.mean(1.0 - view ** 2))
    tr.raw_norm[i] = float(np.linalg.norm(raw))
    tr.expr_norm[i] = float(np.linalg.norm(expr))
    vals = list(ve.values.values())
    tr.live[i] = sum(1 for v in vals if v.dissolved_at_step < 0)
    tr.births[i] = sum(1 for v in vals if v.birth_step == ve._step)
    tr.ever[i] = len(vals)
    tr.attractors[i] = len(cycle.attractor.centers)
    tr.crystals[i] = len(cycle.crystal_store.crystals)
    tr.rhythm[i] = RHYTHM_CODE.get(state.rhythm, 4)
    tr.boredom[i] = int(cycle._boredom_overrides - boredom_before)
    tr.inputs[i] = (src, tuple(toks))


def arrays_equal(live, stored):
    live = np.asarray(live)
    stored = np.asarray(stored)
    if live.shape != stored.shape:
        return False
    if live.dtype != stored.dtype:
        stored = stored.astype(live.dtype)
    return np.array_equal(live, stored)


# ---------------------------------------------------------------------------
# One seed
# ---------------------------------------------------------------------------

def _step(cycle, pick, sids, weights):
    boredom = cycle._boredom_overrides
    src, toks = draw(pick, sids, weights)
    state = cycle.step(list(toks), source_id=src, origin_type="internal")
    return state, src, toks, boredom


def run_plain(seed, steps, ages, horizon, progress=True, checkpoint_dir=None):
    """Plain ordinary-path run. Returns the trace, the cycle's companions, and
    pickled snapshots taken after each age in `ages`."""
    sids, weights = workload_sources()
    t_build = time.perf_counter()
    gen, cycle, gov, ve, ledger, consumer, report, pretrained = build_all_on()
    build_s = time.perf_counter() - t_build
    if cycle.six_rhythm_selector or cycle.config.get("rupture_on_lock", False):
        raise RuntimeError("witness selector or rupture is on; this probe refuses to run")
    pick = random.Random(seed)
    tr = Trace(steps, cycle.field.dim)
    snaps = {}
    # Hashes at the fork and at the horizon end, so the unperturbed replay can
    # be checked past the vectors. Every 500 steps covers the repeated-exposure
    # comparison points without hashing the generator on every step.
    weight_points = set(ages) | {a + horizon for a in ages} | {steps}
    weight_points |= set(range(500, steps + 1, 500))
    bucket = time.perf_counter()
    bucket_n = 0
    rates = []
    for i in range(steps):
        state, src, toks, boredom = _step(cycle, pick, sids, weights)
        record_step(tr, i, cycle, ve, state, src, toks, boredom)
        step_no = i + 1
        if step_no in weight_points or step_no == steps:
            tr.weights_at[step_no] = weight_digest(gen)
            tr.values_at[step_no] = value_digest(ve)
        if any(age <= step_no < age + horizon for age in ages):
            tr.rng_at[step_no] = capture_rng()
        if step_no in ages:
            snaps[step_no] = capture(cycle, pick)
            if progress:
                print(f"  snapshot at step {step_no}  ({len(snaps[step_no]['cycle'])/1e6:.1f} MB)",
                      flush=True)
        if checkpoint_dir is not None and step_no % 1000 == 0:
            _save_partial(checkpoint_dir, seed, tr, step_no)
        bucket_n += 1
        if progress and bucket_n == 250:
            dt = time.perf_counter() - bucket
            rates.append((step_no, dt / bucket_n))
            print(f"  step {step_no:6d}  {dt / bucket_n * 1e3:7.2f} ms/step"
                  f"  coh {tr.field_coh[i]:.4f}  watch {tr.watcher[i]:.3f}"
                  f"  lr {tr.eff_lr[i]:.3f}  sat {tr.sat[i]:.2f}"
                  f"  |raw| {tr.raw_norm[i]:.2f}  gain {tr.view_gain[i]:.4f}"
                  f"  rhythm {state.rhythm:9s}  live {tr.live[i]}"
                  f"  attr {tr.attractors[i]}  cryst {tr.crystals[i]}",
                  flush=True)
            bucket = time.perf_counter()
            bucket_n = 0
    return {
        "trace": tr,
        "snaps": snaps,
        "gen": gen,
        "build_s": build_s,
        "rates": rates,
        "pretrained": pretrained,
        "dim": cycle.field.dim,
    }


def _bind_pick(snap):
    pick = random.Random(0)
    return pick


def stream_dists(cycle, tr, step):
    """L2 distance of the live cycle from the plain trace at 1-based step."""
    idx = step - 1
    raw = np.asarray(cycle.field.field, dtype=np.float64)
    expr = np.asarray(cycle._last_expressed, dtype=np.float64)
    return {
        "raw": float(np.linalg.norm(raw - tr.raw[idx])),
        "view": float(np.linalg.norm(np.tanh(raw) - tr.view[idx])),
        "anchor": float(np.linalg.norm(np.asarray(cycle.witness._anchor, np.float64) - tr.anchor[idx])),
        "short": float(np.linalg.norm(np.asarray(cycle.witness._short, np.float64) - tr.short[idx])),
        "mid": float(np.linalg.norm(np.asarray(cycle.witness._mid, np.float64) - tr.mid[idx])),
        "long": float(np.linalg.norm(np.asarray(cycle.witness._long, np.float64) - tr.long[idx])),
        "expr": float(np.linalg.norm(expr - tr.expr[idx])),
    }


def verify_unperturbed(snap, tr, age, horizon, sids, weights):
    """The unperturbed fork must match the plain run bit for bit."""
    pick = _bind_pick(snap)
    cycle = restore(snap, pick)
    ve = cycle.value_engine
    mismatches = []
    for h in range(1, horizon + 1):
        step = age + h
        state, src, toks, _ = _step(cycle, pick, sids, weights)
        if tr.inputs[step - 1] != (src, tuple(toks)):
            mismatches.append(f"step {step}: input {src} {toks} != {tr.inputs[step - 1]}")
            break
        if not arrays_equal(cycle.field.field, tr.raw[step - 1]):
            mismatches.append(f"step {step}: raw field")
        if not arrays_equal(cycle.witness._anchor, tr.anchor[step - 1]):
            mismatches.append(f"step {step}: anchor")
        if not arrays_equal(cycle.witness._short, tr.short[step - 1]):
            mismatches.append(f"step {step}: short")
        if not arrays_equal(cycle.witness._mid, tr.mid[step - 1]):
            mismatches.append(f"step {step}: mid")
        if not arrays_equal(cycle.witness._long, tr.long[step - 1]):
            mismatches.append(f"step {step}: long")
        if not arrays_equal(cycle._last_expressed, tr.expr[step - 1]):
            mismatches.append(f"step {step}: expressed")
        if int(tr.rhythm[step - 1]) != RHYTHM_CODE.get(state.rhythm, 4):
            mismatches.append(f"step {step}: rhythm {state.rhythm}")
        if len(mismatches) >= 6:
            break
    end = age + horizon
    w_ok = True
    v_ok = True
    if end in tr.weights_at:
        w_ok = weight_digest(cycle.generator) == tr.weights_at[end]
        if not w_ok:
            mismatches.append(f"step {end}: generator weights")
    if end in tr.values_at:
        v_ok = value_digest(ve) == tr.values_at[end]
        if not v_ok:
            mismatches.append(f"step {end}: value digest")
    return {"ok": not mismatches, "mismatches": mismatches, "horizon": horizon}


def fork_horizon(snap, tr, age, horizon, sids, weights, perturb):
    """Perturb the restored state, then walk `horizon` steps against the plain trace."""
    pick = _bind_pick(snap)
    cycle = restore(snap, pick)
    perturb(cycle)
    names = ("raw", "view", "anchor", "short", "mid", "long", "expr")
    series = {k: np.empty(horizon + 1) for k in names}
    series_lr = np.empty(horizon + 1)
    rhythm_mismatch = 0
    immediate = stream_dists(cycle, tr, age)
    for k in names:
        series[k][0] = immediate[k]
    series_lr[0] = float("nan")  # lr is a property of a step, not of the nudged state
    for h in range(1, horizon + 1):
        step = age + h
        # Plain-run noise for this step. See Trace.rng_at.
        if (step - 1) not in tr.rng_at:
            raise RuntimeError(f"no plain-run RNG snapshot before step {step}")
        restore_rng(tr.rng_at[step - 1])
        state, src, toks, _ = _step(cycle, pick, sids, weights)
        if tr.inputs[step - 1] != (src, tuple(toks)):
            raise RuntimeError(
                f"perturbed fork drew a different input at step {step}: "
                f"{(src, tuple(toks))} != {tr.inputs[step - 1]}"
            )
        d = stream_dists(cycle, tr, step)
        for k in names:
            series[k][h] = d[k]
        series_lr[h] = float(np.clip(state.coherence ** 2, 0.01, 1.0))
        if RHYTHM_CODE.get(state.rhythm, 4) != int(tr.rhythm[step - 1]):
            rhythm_mismatch += 1
    out = {
        "immediate": immediate,
        "series": series,
        "eff_lr": series_lr,
        "rhythm_mismatch": rhythm_mismatch,
        "plain_eff_lr_mean": float(np.mean(tr.eff_lr[age:age + horizon])),
        "fork_eff_lr_mean": float(np.nanmean(series_lr[1:])),
    }
    for name in ("raw", "view", "anchor", "expr"):
        # Recovery is only meaningful for a stream the nudge actually moved.
        # A stream that was not written starts at distance ~0; calling that
        # "absorbed" would be a false reading. Those get a propagation class.
        own_initial = immediate[name]
        if own_initial > DIVERGE_FLOOR:
            klass = recovery_of(series[name], own_initial)
        else:
            klass = propagation_of(series[name])
        out[name] = {
            "first": first_above(series[name]),
            "recovery": klass,
            "end": float(series[name][-1]),
            "peak": float(np.max(series[name])),
        }
    return out


def propagation_of(div, floor=DIVERGE_FLOOR):
    """What a stream we did not touch does after the nudge.

    unmoved                  — never left the twin
    propagated-then-absorbed — left, then the distance fell back under the floor
    propagated-and-grew      — still departing at the horizon
    propagated               — left and the distance held
    """
    div = np.asarray(div, dtype=float)
    first = first_above(div, floor)
    end = float(div[-1])
    peak = float(np.max(div))
    if first is None:
        kind = "unmoved"
        t_rec = None
    else:
        back = np.flatnonzero(div[first:] < floor)
        t_rec = int(back[0] + first) if len(back) else None
        # `peak` includes the endpoint, so end >= 2*peak can never happen.
        # Growth is relative to the divergence a few steps after it first appears.
        onset = float(div[min(first + 5, len(div) - 1)])
        if end > 2.0 * max(onset, floor) and end >= 0.5 * peak:
            kind = "propagated-and-grew"
        elif t_rec is not None and end < floor:
            kind = "propagated-then-absorbed"
        else:
            kind = "propagated"
    return {"class": kind, "t_rec": t_rec, "residual": float("nan"),
            "peak_over_kick": float("nan")}


def median_step(tr, a, b):
    """Median per-step L2 motion on [a, b) (0-based, motion ending at index)."""
    a = max(a, 1)
    b = min(b, tr.steps)
    if b <= a:
        return 0.0, 0.0
    dv = np.linalg.norm(tr.view[a:b] - tr.view[a - 1:b - 1], axis=1)
    da = np.linalg.norm(tr.anchor[a:b] - tr.anchor[a - 1:b - 1], axis=1)
    return float(np.median(dv)), float(np.median(da))


def _save_partial(checkpoint_dir, seed, tr, step_no):
    path = Path(checkpoint_dir) / f"partial_seed{seed}.npz"
    np.savez_compressed(
        path, n=np.int32(step_no),
        raw=tr.raw[:step_no], view=tr.view[:step_no], anchor=tr.anchor[:step_no],
        short=tr.short[:step_no], mid=tr.mid[:step_no], long=tr.long[:step_no],
        expr=tr.expr[:step_no], field_coh=tr.field_coh[:step_no], watcher=tr.watcher[:step_no],
        eff_lr=tr.eff_lr[:step_no], sat=tr.sat[:step_no], sat99=tr.sat99[:step_no],
        view_gain=tr.view_gain[:step_no], raw_norm=tr.raw_norm[:step_no],
        expr_norm=tr.expr_norm[:step_no], live=tr.live[:step_no], births=tr.births[:step_no],
        ever=tr.ever[:step_no], attractors=tr.attractors[:step_no],
        crystals=tr.crystals[:step_no], rhythm=tr.rhythm[:step_no], boredom=tr.boredom[:step_no],
    )
    print(f"  checkpoint {path} ({step_no} steps)", flush=True)


def run_seed(seed, steps, ages, horizon, repeat_spacing, repeat_hits, progress=True,
             checkpoint_dir=None):
    ages = [a for a in ages if 100 < a and a + horizon <= steps]
    if progress:
        print(f"\n=== seed {seed}  steps {steps}  fork ages {ages}  horizon {horizon}", flush=True)
    sids, weights = workload_sources()
    with determinism.deterministic(seed):
        plain = run_plain(seed, steps, ages, horizon, progress=progress,
                          checkpoint_dir=checkpoint_dir)
        tr = plain["trace"]
        if not ages:
            return {"seed": seed, "plain": plain, "nudges": None, "forks": {}, "repeat": None,
                    "verify": {}}
        cal_age = ages[0]
        med_view, med_anchor = median_step(tr, 100, cal_age)
        # The snapshot's cycle is the calibration state. Unpickle once.
        pick = _bind_pick(plain["snaps"][cal_age])
        cal_cycle = restore(plain["snaps"][cal_age], pick)
        # restore() replaced the globals. The plain run is finished, so that is allowed.
        nudges = choose_nudges(cal_cycle.witness, np.asarray(cal_cycle.field.field, np.float64),
                               seed, med_view, med_anchor)
        del cal_cycle
        if progress:
            print(f"  nudge: median step view {med_view:.3e} anchor {med_anchor:.3e}", flush=True)
            print(f"         target view {nudges['target_view']:.3e} -> scale {nudges['s_field']:.4e}"
                  f" achieved {nudges['got_view']:.3e}", flush=True)
            print(f"         target anchor {nudges['target_anchor']:.3e} -> scale {nudges['s_anchor']:.4e}"
                  f" achieved {nudges['got_anchor']:.3e}", flush=True)
            print(f"         radial nudge of the same raw L2 moves the view by "
                  f"{nudges['radial_view_at_same_raw_l2']:.3e}"
                  f"  (mean sech^2 {nudges['mean_sech2']:.4e}, raw rms {nudges['raw_rms']:.2f})",
                  flush=True)
            print(f"         field scale capped={nudges['field_capped']}"
                  f"  tanh bit-identical after the nudge={nudges['view_bit_identical']}",
                  flush=True)

        verify = {}
        forks = {}
        for age in ages:
            snap = plain["snaps"][age]
            # Weight digest at the horizon end was not stored unless that step
            # is itself an age. Store comparison uses whatever run_plain saved;
            # also compare the vectors on every step, which is the real check.
            v = verify_unperturbed(snap, tr, age, horizon, sids, weights)
            verify[age] = v
            if progress:
                print(f"  verify age {age}: {'OK' if v['ok'] else 'FAIL'} {v['mismatches'][:3]}",
                      flush=True)
            if not v["ok"]:
                forks[age] = None
                continue

            def pert_field(cycle, _n=nudges):
                apply_field(cycle.field, _n["d_field"], _n["s_field"])

            def pert_anchor(cycle, _n=nudges):
                apply_anchor(cycle.witness, _n["d_anchor"], _n["s_anchor"])

            def pert_desat(cycle):
                apply_desat(cycle.field)

            forks[age] = {
                "field": fork_horizon(snap, tr, age, horizon, sids, weights, pert_field),
                "anchor": fork_horizon(snap, tr, age, horizon, sids, weights, pert_anchor),
                # Not a nudge. Asks whether a view that has left ±1 still drives
                # the anchor and the expression, and how fast the view re-saturates.
                "desat": fork_horizon(snap, tr, age, horizon, sids, weights, pert_desat),
            }
            if progress:
                for which in ("field", "anchor", "desat"):
                    f = forks[age][which]
                    print(f"  fork {which:6s} @ {age}: kick view {f['immediate']['view']:.3e}"
                          f" anchor {f['immediate']['anchor']:.3e} expr {f['immediate']['expr']:.3e}",
                          flush=True)
                    for stream in ("view", "anchor", "expr", "raw"):
                        info = f[stream]
                        rec = info["recovery"]
                        print(f"       {stream:6s} first>{DIVERGE_FLOOR:.0e}={info['first']}"
                              f"  {rec['class']:8s} t_rec={rec['t_rec']}  "
                              f"end/kick={rec['residual']:.3f}  end={info['end']:.3e}",
                              flush=True)
                    print(f"       rhythm mismatches {f['rhythm_mismatch']}"
                          f"  eff_lr fork {f['fork_eff_lr_mean']:.4f}"
                          f" vs plain {f['plain_eff_lr_mean']:.4f}",
                          flush=True)

        repeat = None
        if cal_age in plain["snaps"] and repeat_hits > 0:
            def pert_field(cycle, _n=nudges):
                apply_field(cycle.field, _n["d_field"], _n["s_field"])

            def pert_anchor(cycle, _n=nudges):
                apply_anchor(cycle.witness, _n["d_anchor"], _n["s_anchor"])

            repeat = {
                "field": repeated_exposure(
                    plain["snaps"][cal_age], tr, cal_age, repeat_spacing, repeat_hits,
                    pert_field, "raw", sids, weights, progress=progress, label="field"),
                "anchor": repeated_exposure(
                    plain["snaps"][cal_age], tr, cal_age, repeat_spacing, repeat_hits,
                    pert_anchor, "anchor", sids, weights, progress=progress, label="anchor"),
            }
        # Drop the pickled cycles before returning; the caller saves arrays.
        plain["snaps"] = {a: len(blob["cycle"]) for a, blob in plain["snaps"].items()}
        return {"seed": seed, "plain": plain, "nudges": nudges, "forks": forks,
                "repeat": repeat, "verify": verify, "ages": ages}


def repeated_exposure(snap0, tr, start, spacing, hits, perturb, kick, sids, weights,
                      progress=True, label=""):
    """Same nudge, `spacing` steps apart, on one lineage.

    After each hit the recovery reference is a twin branched at that moment
    and not hit again — so previous hits are in both copies, and only this
    hit differs. The single-shot fork at the same age (from the plain run) is
    the age control. `kick` is which stream's distance defines recovery.
    """
    if start + hits * spacing > tr.steps:
        hits = max(0, (tr.steps - start) // spacing)
    out = []
    snap = snap0
    for k in range(hits):
        age = start + k * spacing
        if age + spacing > tr.steps:
            break

        # Twin: this history, no new hit. Exposed: the hit, then the same inputs.
        pick_t = _bind_pick(snap)
        twin = restore(snap, pick_t)
        pick_e = _bind_pick(snap)
        exposed = restore(snap, pick_e)
        perturb(exposed)
        names = ("raw", "view", "anchor", "expr")
        series = {n: np.empty(spacing + 1) for n in names}
        for n in names:
            series[n][0] = float(np.linalg.norm(
                _vec(exposed, n) - _vec(twin, n)))
        rhythm_mismatch = 0
        for h in range(1, spacing + 1):
            # One shared RNG stream, not two. Each copy must draw the numbers
            # the plain run would have drawn on this step; then the stream
            # advances once.
            rng_before = capture_rng()
            st_t, src_t, toks_t, _ = _step(twin, pick_t, sids, weights)
            rng_after = capture_rng()
            restore_rng(rng_before)
            st_e, src_e, toks_e, _ = _step(exposed, pick_e, sids, weights)
            restore_rng(rng_after)
            if (src_t, tuple(toks_t)) != (src_e, tuple(toks_e)):
                raise RuntimeError(f"repeated exposure inputs diverged at hit {k} step {h}")
            for n in names:
                series[n][h] = float(np.linalg.norm(_vec(exposed, n) - _vec(twin, n)))
            if st_t.rhythm != st_e.rhythm:
                rhythm_mismatch += 1
        initial = series[kick][0]
        rec = recovery_of(series[kick], initial)
        # What the exposed lineage is carrying, versus the never-hit plain run
        # at this same step (the age-matched naive state is `tr` at age; the
        # exposed state is `exposed` after `spacing` steps, i.e. at the next age).
        end_step = age + spacing
        row = {
            "hit": k,
            "age": age,
            "end_step": end_step,
            "initial_kick": float(initial),
            "initial_anchor": float(series["anchor"][0]),
            "initial_expr": float(series["expr"][0]),
            "initial_raw": float(series["raw"][0]),
            "initial_view": float(series["view"][0]),
            "recovery": rec,
            "first_view": first_above(series["view"]),
            "first_anchor": first_above(series["anchor"]),
            "first_expr": first_above(series["expr"]),
            "first_raw": first_above(series["raw"]),
            "end_view": float(series["view"][-1]),
            "end_anchor": float(series["anchor"][-1]),
            "end_expr": float(series["expr"][-1]),
            "end_raw": float(series["raw"][-1]),
            "rhythm_mismatch": rhythm_mismatch,
            "series_kick": series[kick],
            "kick": kick,
            "exposed_live": _live(exposed),
            "exposed_attractors": len(exposed.attractor.centers),
            "exposed_crystals": len(exposed.crystal_store.crystals),
            "exposed_weights": weight_digest(exposed.generator),
            "plain_live": int(tr.live[end_step - 1]),
            "plain_attractors": int(tr.attractors[end_step - 1]),
            "plain_crystals": int(tr.crystals[end_step - 1]),
            "plain_weights": tr.weights_at.get(end_step),
            "plain_sat": float(tr.sat[end_step - 1]),
            "exposed_sat": float(np.mean(np.abs(np.tanh(exposed.field.field)) > 0.95)),
        }
        out.append(row)
        if progress:
            print(f"  repeat {label} hit {k} @ {age}: kick {kick} {initial:.3e}  "
                  f"{rec['class']} t_rec={rec['t_rec']} end/kick={rec['residual']:.3f}"
                  f"  anchor-first={row['first_anchor']} expr-first={row['first_expr']}"
                  f"  live {row['exposed_live']} vs plain {row['plain_live']}"
                  f"  attr {row['exposed_attractors']}/{row['plain_attractors']}"
                  f"  cryst {row['exposed_crystals']}/{row['plain_crystals']}",
                  flush=True)
        # Continue the exposed lineage. Re-capture after the hit's window,
        # which is exactly the next hit's starting state.
        snap = capture(exposed, pick_e)
        del twin, exposed
    return out


def _vec(cycle, name):
    if name == "raw":
        return np.asarray(cycle.field.field, np.float64)
    if name == "view":
        return np.tanh(np.asarray(cycle.field.field, np.float64))
    if name == "anchor":
        return np.asarray(cycle.witness._anchor, np.float64)
    if name == "expr":
        return np.asarray(cycle._last_expressed, np.float64)
    raise KeyError(name)


def _live(cycle):
    ve = cycle.value_engine
    return sum(1 for v in ve.values.values() if v.dissolved_at_step < 0)


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

STREAMS = ("raw", "view", "anchor", "short", "mid", "long", "expr")


def _windows(n, size):
    if n < size * 2:
        third = n // 3
        return [(0, third, "early"), (third, 2 * third, "mid"), (2 * third, n, "late")]
    out = []
    labels = ["early", "mid", "late"]
    # Three equal blocks, so "does the shape change with age" is one comparison.
    third = n // 3
    edges = [0, third, 2 * third, n]
    for i in range(3):
        out.append((edges[i], edges[i + 1], labels[i]))
    return out


def analyze_shape(tr):
    n = tr.steps
    limit = max(n // 5, 32)
    lags = _lags_for(n, limit)
    windows = _windows(n, 2000)
    shape = {}
    for name in STREAMS:
        X = getattr(tr, name if name != "expr" else "expr")
        shape[name] = {"full": _one_msd(X, lags)}
        for a, b, label in windows:
            shape[name][label] = _one_msd(X[a:b], _lags_for(b - a, max((b - a) // 5, 16)))
    # Direction, separate from magnitude. The raw norm moving is not a turn.
    shape["raw_dir"] = {}
    shape["view_dir"] = {}
    Ur, Uv = unit_rows(tr.raw), unit_rows(tr.view)
    shape["raw_dir"]["full"] = _one_msd(Ur, lags)
    shape["view_dir"]["full"] = _one_msd(Uv, lags)
    for a, b, label in windows:
        ll = _lags_for(b - a, max((b - a) // 5, 16))
        shape["raw_dir"][label] = _one_msd(Ur[a:b], ll)
        shape["view_dir"][label] = _one_msd(Uv[a:b], ll)
    return shape, lags, windows


def _one_msd(X, lags):
    msd = msd_curve(X, lags)
    short = [(L, m) for L, m in zip(lags, msd) if 1 <= L <= 32 and np.isfinite(m)]
    long = [(L, m) for L, m in zip(lags, msd) if L >= 64 and np.isfinite(m)]
    a_s, r_s = loglog_alpha(*zip(*short)) if len(short) >= 3 else (float("nan"), float("nan"))
    a_l, r_l = loglog_alpha(*zip(*long)) if len(long) >= 3 else (float("nan"), float("nan"))
    return {"lags": list(lags), "msd": msd, "alpha_short": a_s, "r2_short": r_s,
            "alpha_long": a_l, "r2_long": r_l}


def analyze_timescales(tr, win=2000):
    n = tr.steps
    rows = []
    edges = list(range(0, n, win))
    if not edges or edges[-1] != n:
        edges.append(n)
    # Drop a short tail rather than report a noisy partial window.
    blocks = [(edges[i], edges[i + 1]) for i in range(len(edges) - 1)
              if edges[i + 1] - edges[i] >= win // 2]
    if not blocks:
        blocks = [(0, n)]
    for a, b in blocks:
        row = {"a": a, "b": b}
        for name in STREAMS:
            X = getattr(tr, name)
            row[name] = timescale(X[a:b], max_lag=min(500, (b - a) // 4))
        row["ratio"] = _ratio(row["anchor"]["tau_e"], row["expr"]["tau_e"])
        row["eff_lr"] = float(np.mean(tr.eff_lr[a:b]))
        row["field_coh"] = float(np.mean(tr.field_coh[a:b]))
        row["watcher"] = float(np.mean(tr.watcher[a:b]))
        row["sat"] = float(np.mean(tr.sat[a:b]))
        rows.append(row)
    # One long window so a slow anchor is not censored by the 500-lag cap
    # of the short blocks, when the run is long enough to see it.
    long = {}
    cap = min(2000, n // 4)
    for name in STREAMS:
        long[name] = timescale(getattr(tr, name), max_lag=cap)
    long["ratio"] = _ratio(long["anchor"]["tau_e"], long["expr"]["tau_e"])
    return rows, long


def _ratio(ta, te):
    if ta == float("inf") and te == float("inf"):
        return {"value": float("nan"), "bound": "both unresolved"}
    if te == float("inf"):
        return {"value": 0.0, "bound": "expression unresolved"}
    if ta == float("inf"):
        return {"value": float("inf"), "bound": "anchor slower than window"}
    if not te:
        return {"value": float("nan"), "bound": "expression tau is 0"}
    return {"value": float(ta / te), "bound": "measured"}


def analyze_lead(tr, max_lag=40):
    view_d = np.diff(tr.view, axis=0)
    raw_d = np.diff(tr.raw, axis=0)
    anch_d = np.diff(tr.anchor, axis=0)
    expr_d = np.diff(tr.expr, axis=0)
    out = {}
    pairs = {
        "view_anchor": (view_d, anch_d),
        "raw_anchor": (raw_d, anch_d),
        "view_expr": (view_d, expr_d),
        "anchor_expr": (anch_d, expr_d),
    }
    for name, (a, b) in pairs.items():
        lags, rho = xcorr(a, b, max_lag)
        out[name] = _xcorr_summary(lags, rho, a, b)
    rv = residualize(view_d, expr_d)
    ra = residualize(anch_d, expr_d)
    rr = residualize(raw_d, expr_d)
    for name, (a, b) in {"view_anchor_resid": (rv, ra), "raw_anchor_resid": (rr, ra)}.items():
        lags, rho = xcorr(a, b, max_lag)
        out[name] = _xcorr_summary(lags, rho, a, b)
    out["resid_energy_view"] = _energy_left(view_d, rv)
    out["resid_energy_anchor"] = _energy_left(anch_d, ra)
    return out


def _energy_left(original, resid):
    num = float(np.mean(np.sum(resid * resid, axis=1)))
    den = float(np.mean(np.sum(original * original, axis=1)))
    return num / den if den > 0 else float("nan")


def _xcorr_summary(lags, rho, a, b):
    rms_a = float(np.sqrt(np.mean(np.sum(a * a, axis=1))))
    rms_b = float(np.sqrt(np.mean(np.sum(b * b, axis=1))))
    if not np.any(np.isfinite(rho)):
        peak_lag, peak, lag0 = None, float("nan"), float("nan")
    else:
        j = int(np.nanargmax(np.abs(rho)))
        peak_lag = int(lags[j])
        peak = float(rho[j])
        lag0 = float(rho[lags.index(0)])
    return {"lags": lags, "rho": rho, "peak_lag": peak_lag, "peak": peak, "lag0": lag0,
            "rms_a": rms_a, "rms_b": rms_b,
            "identified": rms_a > 1e-10 and rms_b > 1e-10}


def self_check_estimators():
    """Known series, so a bug in MSD / tau cannot hide inside a 20k-step run."""
    g = np.random.Generator(np.random.PCG64(0))
    T, D = 4000, 4
    noise = g.normal(size=(T, D))
    diff = np.cumsum(noise, axis=0)
    drift = (np.arange(T, dtype=float)[:, None]) * np.ones(D)
    const = np.ones((T, D))
    lags = _lags_for(T, 512)
    problems = []

    def alpha_band(X, lo, hi):
        msd = msd_curve(X, lags)
        pts = [(L, m) for L, m in zip(lags, msd) if lo <= L <= hi and m > 0]
        return loglog_alpha(*zip(*pts))

    a_diff, _ = alpha_band(diff, 4, 64)
    a_drift, _ = alpha_band(drift, 4, 256)
    if not (0.75 <= a_diff <= 1.25):
        problems.append(f"diffusion alpha {a_diff:.3f}, expected ~1")
    if not (1.75 <= a_drift <= 2.25):
        problems.append(f"drift alpha {a_drift:.3f}, expected ~2")
    fr = timescale(const, 200)
    if fr["status"] != "frozen":
        problems.append(f"constant series status {fr['status']}, expected frozen")
    # AR(1) with phi=0.9 has tau_int ≈ 0.5 + phi/(1-phi) = 9.5 on a long series.
    phi = 0.9
    ar = np.zeros(T)
    for t in range(1, T):
        ar[t] = phi * ar[t - 1] + noise[t, 0]
    ts = timescale(ar[:, None], 400)
    if ts["status"] == "frozen" or not (5.0 <= ts["tau_int"] <= 20.0):
        problems.append(f"AR(0.9) tau_int {ts['tau_int']}, expected ~9.5")
    # b is a delayed by 3 steps: peak lag must be +3 (a leads).
    a = noise
    b = np.zeros_like(a)
    b[3:] = a[:-3]
    lags_c, rho = xcorr(np.diff(a, axis=0), np.diff(b, axis=0), 10)
    # diff of a shift-3 series peaks near lag 3
    j = int(np.nanargmax(rho))
    if abs(lags_c[j] - 3) > 1:
        problems.append(f"xcorr peak lag {lags_c[j]}, expected ~3")
    return problems


def fmt_tau(ts):
    if ts["status"] == "frozen":
        return f"frozen rms={ts['rms']:.2e}"
    te = ts["tau_e"]
    te_s = ">{0}".format(ts.get("max_lag", "")) if te == float("inf") else f"{te:.0f}"
    return f"tau_e={te_s} tau_int={ts['tau_int']:.1f} rho1={ts['rho1']:.3f} rms={ts['rms']:.2e} ({ts['status']})"


def fmt_ratio(r):
    v = r["value"]
    if r["bound"] == "anchor slower than window":
        return f">{v if np.isfinite(v) else ''} ({r['bound']})" if np.isfinite(v) else f"anchor slower than window / expression finite — ratio unbounded above"
    if isinstance(v, float) and v == float("inf"):
        return r["bound"]
    if isinstance(v, float) and not np.isfinite(v):
        return r["bound"]
    return f"{v:.2f} ({r['bound']})"


def write_report(path, results):
    lines = []
    w = lines.append
    w("H0 probe report")
    w("")
    for res in results:
        seed = res["seed"]
        tr = res["plain"]["trace"]
        w(f"===== seed {seed}  steps {tr.steps}  dim {tr.dim}  build {res['plain']['build_s']:.1f}s")
        if res["plain"]["rates"]:
            first = res["plain"]["rates"][0][1] * 1000
            last = res["plain"]["rates"][-1][1] * 1000
            w(f"ms/step first-bucket {first:.2f}  last-bucket {last:.2f}")
        w(f"field coherence start/mid/end "
          f"{tr.field_coh[0]:.4f} / {tr.field_coh[tr.steps // 2]:.4f} / {tr.field_coh[-1]:.4f}")
        w(f"watcher composite start/mid/end "
          f"{tr.watcher[0]:.4f} / {tr.watcher[tr.steps // 2]:.4f} / {tr.watcher[-1]:.4f}")
        w(f"eff_lr mean {tr.eff_lr.mean():.4f}  min {tr.eff_lr.min():.4f}  max {tr.eff_lr.max():.4f}")
        w(f"sat|tanh|>0.95 start/mid/end {tr.sat[0]:.3f} / {tr.sat[tr.steps // 2]:.3f} / {tr.sat[-1]:.3f}"
          f"   >0.99 end {tr.sat99[-1]:.3f}")
        w(f"view gain sech^2 start/mid/end {tr.view_gain[0]:.4f} / "
          f"{tr.view_gain[tr.steps // 2]:.4f} / {tr.view_gain[-1]:.4f}")
        w(f"|raw| start/mid/end {tr.raw_norm[0]:.3f} / {tr.raw_norm[tr.steps // 2]:.3f} / {tr.raw_norm[-1]:.3f}")
        w(f"|expr| mean {tr.expr_norm.mean():.3f}")
        w(f"live values end {int(tr.live[-1])}  ever born {int(tr.ever[-1])}  "
          f"births sum {int(tr.births.sum())}")
        w(f"attractors end {int(tr.attractors[-1])}  crystals end {int(tr.crystals[-1])}")
        w(f"boredom overrides {int(tr.boredom.sum())}")
        codes, counts = np.unique(tr.rhythm, return_counts=True)
        inv = {v: k for k, v in RHYTHM_CODE.items()}
        w("rhythm " + " ".join(f"{inv.get(int(c), c)}:{int(n)}" for c, n in zip(codes, counts)))
        # Displacement from the step-500 state, and from the start, so the
        # 0.00012-style number is a curve rather than one bound.
        if tr.steps > 500:
            base = 499
            w(f"||view(t)-view(500)|| end {np.linalg.norm(tr.view[-1] - tr.view[base]):.6e}")
            w(f"||raw(t)-raw(500)|| end {np.linalg.norm(tr.raw[-1] - tr.raw[base]):.6e}")
            w(f"||anchor(t)-anchor(500)|| end {np.linalg.norm(tr.anchor[-1] - tr.anchor[base]):.6e}")
            w(f"||expr(t)-expr(500)|| end {np.linalg.norm(tr.expr[-1] - tr.expr[base]):.6e}")
        w("")
        shape, lags, windows = analyze_shape(tr)
        res["shape"] = shape
        w("-- MSD alpha (short lags 1..32, long lags >=64). ~0 bounded, ~1 diffusive, ~2 drift")
        for name in list(STREAMS) + ["raw_dir", "view_dir"]:
            block = shape[name]
            bits = []
            for label in ["full", "early", "mid", "late"]:
                if label not in block:
                    continue
                s = block[label]
                bits.append(f"{label}: a_s={s['alpha_short']:.2f} (r2 {s['r2_short']:.2f})"
                            f" a_l={s['alpha_long']:.2f} (r2 {s['r2_long']:.2f})"
                            f" msd1={_msd_at(s, 1):.3e} msd128={_msd_at(s, 128):.3e}"
                            f" msd_last={s['msd'][np.where(np.isfinite(s['msd']))[0][-1]]:.3e}")
            w(f"  {name:8s} " + " | ".join(bits))
        w("")
        rows, long = analyze_timescales(tr)
        res["timescales"] = rows
        res["timescale_long"] = long
        w("-- timescale per window (tau_e = lag where rho drops below 1/e)")
        for row in rows:
            w(f"  steps {row['a']+1}-{row['b']}  eff_lr {row['eff_lr']:.4f}"
              f"  field_coh {row['field_coh']:.4f}  watcher {row['watcher']:.3f}  sat {row['sat']:.3f}")
            for name in STREAMS:
                w(f"    {name:8s} {fmt_tau(row[name])}")
            w(f"    ratio tau_anchor/tau_expr = {fmt_ratio(row['ratio'])}")
        w("  full-run (longer lag cap):")
        for name in STREAMS:
            w(f"    {name:8s} {fmt_tau(long[name])}")
        w(f"    ratio = {fmt_ratio(long['ratio'])}")
        w("")
        lead = analyze_lead(tr)
        res["lead"] = lead
        w("-- cross-correlation of displacements. positive lag: the second stream is later (first leads)")
        for name in ("view_anchor", "raw_anchor", "view_expr", "anchor_expr",
                     "view_anchor_resid", "raw_anchor_resid"):
            s = lead[name]
            w(f"  {name:22s} identified={s['identified']}  lag0={s['lag0']:.4f}"
              f"  peak_lag={s['peak_lag']} peak={s['peak']:.4f}"
              f"  rms {s['rms_a']:.3e} {s['rms_b']:.3e}")
        w(f"  residual energy left after removing expression: "
          f"view {lead['resid_energy_view']:.3f}  anchor {lead['resid_energy_anchor']:.3f}")
        w("")
        if res["nudges"]:
            n = res["nudges"]
            w("-- nudge (frozen for this seed)")
            w(f"  median step view {n['med_view']:.3e} anchor {n['med_anchor']:.3e}")
            w(f"  field scale {n['s_field']:.4e} achieved view {n['got_view']:.3e}"
              f" (target {n['target_view']:.3e}) capped={n.get('field_capped')}"
              f" tanh_bit_identical={n.get('view_bit_identical')} raw_rms={n.get('raw_rms')}")
            w(f"  anchor scale {n['s_anchor']:.4e} achieved anchor {n['got_anchor']:.3e}"
              f" (target {n['target_anchor']:.3e})")
            w(f"  same raw L2, radial direction, view moves {n['radial_view_at_same_raw_l2']:.3e}")
            w(f"  mean sech^2 at calibration {n['mean_sech2']:.4f}")
        w("-- forks")
        for age, v in res["verify"].items():
            w(f"  verify @{age}: {'OK' if v['ok'] else 'FAIL'} {v['mismatches'][:4]}")
        for age, pair in res["forks"].items():
            if pair is None:
                w(f"  fork @{age}: skipped, verify failed")
                continue
            for which, f in pair.items():
                w(f"  {which} @{age} rhythm_mismatch={f['rhythm_mismatch']}"
                  f" eff_lr {f['fork_eff_lr_mean']:.4f} vs plain {f['plain_eff_lr_mean']:.4f}")
                w(f"    immediate raw {f['immediate']['raw']:.3e} view {f['immediate']['view']:.3e}"
                  f" anchor {f['immediate']['anchor']:.3e} expr {f['immediate']['expr']:.3e}")
                for stream in ("raw", "view", "anchor", "expr"):
                    info = f[stream]
                    rec = info["recovery"]
                    w(f"    {stream:6s} first={info['first']} class={rec['class']}"
                      f" t_rec={rec['t_rec']} end/kick={rec['residual']:.4f}"
                      f" peak={info['peak']:.3e} end={info['end']:.3e}")
        w("-- repeated exposure")
        if not res["repeat"]:
            w("  none")
        else:
            blocks = res["repeat"].items() if isinstance(res["repeat"], dict) else [("field", res["repeat"])]
            for label, rows in blocks:
                w(f"  [{label}]")
                for row in rows:
                    rec = row["recovery"]
                    w(f"  hit {row['hit']} @{row['age']}: kick {row.get('kick')} {row.get('initial_kick', row.get('initial_view')):.3e}"
                      f" {rec['class']} t_rec={rec['t_rec']} end/kick={rec['residual']:.3f}"
                      f" first raw/view/anchor/expr "
                      f"{row.get('first_raw')}/{row['first_view']}/{row['first_anchor']}/{row['first_expr']}"
                      f" end raw/view/anchor {row.get('end_raw', float('nan')):.3e}"
                      f"/{row['end_view']:.3e}/{row['end_anchor']:.3e}"
                      f" live {row['exposed_live']} vs plain {row['plain_live']}"
                      f" attr {row['exposed_attractors']}/{row['plain_attractors']}"
                      f" cryst {row['exposed_crystals']}/{row['plain_crystals']}"
                      f" weights_same={row['exposed_weights'] == row['plain_weights']}"
                      f" sat {row['exposed_sat']:.3f} vs plain {row['plain_sat']:.3f}")
        w("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return "\n".join(lines)


def _msd_at(block, lag):
    lags = block["lags"]
    if lag not in lags:
        return float("nan")
    return float(block["msd"][lags.index(lag)])


def save_scratch(scratch, res):
    tr = res["plain"]["trace"]
    seed = res["seed"]
    np.savez_compressed(
        scratch / f"seed{seed}_trace.npz",
        raw=tr.raw, view=tr.view, anchor=tr.anchor, short=tr.short, mid=tr.mid,
        long=tr.long, expr=tr.expr, field_coh=tr.field_coh, watcher=tr.watcher,
        eff_lr=tr.eff_lr, sat=tr.sat, sat99=tr.sat99, view_gain=tr.view_gain,
        raw_norm=tr.raw_norm, expr_norm=tr.expr_norm, live=tr.live, births=tr.births,
        ever=tr.ever, attractors=tr.attractors, crystals=tr.crystals, rhythm=tr.rhythm,
        boredom=tr.boredom,
    )
    # Fork curves are small. Keep them next to the trace so the report is replottable.
    blob = {"verify": res["verify"], "ages": res.get("ages", [])}
    if res["nudges"]:
        n = dict(res["nudges"])
        n["d_field"] = n["d_field"].tolist()
        n["d_anchor"] = n["d_anchor"].tolist()
        blob["nudges"] = n
    fork_s = {}
    for age, pair in res["forks"].items():
        if pair is None:
            fork_s[age] = None
            continue
        fork_s[age] = {}
        for which, f in pair.items():
            fork_s[age][which] = {
                "immediate": f["immediate"],
                "rhythm_mismatch": f["rhythm_mismatch"],
                "eff_lr_fork": f["fork_eff_lr_mean"],
                "eff_lr_plain": f["plain_eff_lr_mean"],
                "streams": {s: {k: f[s][k] for k in ("first", "recovery", "end", "peak")}
                            for s in ("raw", "view", "anchor", "expr")},
                "series": {s: f["series"][s].tolist() for s in f["series"]},
            }
    blob["forks"] = fork_s
    if res["repeat"]:
        blob["repeat"] = {}
        blocks = res["repeat"].items() if isinstance(res["repeat"], dict) else [("field", res["repeat"])]
        for label, rows in blocks:
            blob["repeat"][label] = []
            for row in rows:
                r = dict(row)
                r["series_kick"] = np.asarray(r["series_kick"]).tolist()
                blob["repeat"][label].append(r)
    (scratch / f"seed{seed}_forks.pkl").write_bytes(pickle.dumps(blob, protocol=pickle.HIGHEST_PROTOCOL))


def save_summary(path, results):
    """Compressed curves and scalars. Not the raw vectors."""
    payload = {}
    for res in results:
        s = f"s{res['seed']}_"
        tr = res["plain"]["trace"]
        for name in ("field_coh", "watcher", "eff_lr", "sat", "sat99", "view_gain",
                     "raw_norm", "expr_norm", "live", "births", "ever", "attractors",
                     "crystals", "rhythm", "boredom"):
            payload[s + name] = getattr(tr, name)
        if "shape" in res:
            for stream, blocks in res["shape"].items():
                for label, block in blocks.items():
                    payload[s + f"msd_{stream}_{label}_lag"] = np.asarray(block["lags"])
                    payload[s + f"msd_{stream}_{label}"] = np.asarray(block["msd"])
        if "lead" in res:
            for name, block in res["lead"].items():
                if not isinstance(block, dict) or "rho" not in block:
                    continue
                payload[s + f"xcorr_{name}_lag"] = np.asarray(block["lags"])
                payload[s + f"xcorr_{name}"] = np.asarray(block["rho"])
        for age, pair in res["forks"].items():
            if not pair:
                continue
            for which, f in pair.items():
                for stream, series in f["series"].items():
                    payload[s + f"fork_{which}_{age}_{stream}"] = np.asarray(series)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **payload)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_time(steps, seed):
    print("estimator self-check", flush=True)
    problems = self_check_estimators()
    if problems:
        print("FAIL")
        for p in problems:
            print(" ", p)
        return 1
    print("  diffusion ~1, drift ~2, constant frozen, AR tau, xcorr lag: OK", flush=True)
    # Confirm effective_lr is exactly what witness.update computes, on one step.
    print(f"timing seed {seed}, {steps} steps", flush=True)
    sids, weights = workload_sources()
    with determinism.deterministic(seed):
        t0 = time.perf_counter()
        gen, cycle, gov, ve, ledger, consumer, report, pretrained = build_all_on()
        print(f"  build_all_on {time.perf_counter() - t0:.1f}s  pretrained={pretrained}", flush=True)
        seen = {}
        orig = cycle.witness.update

        def wrap(vec, coherence, field_energy=0.0):
            seen["lr"] = float(np.clip(coherence ** 2, 0.01, 1.0))
            seen["coh"] = float(coherence)
            return orig(vec, coherence, field_energy=field_energy)

        cycle.witness.update = wrap
        pick = random.Random(seed)
        state, src, toks, _ = _step(cycle, pick, sids, weights)
        cycle.witness.update = orig
        recon = float(np.clip(state.coherence ** 2, 0.01, 1.0))
        ok = abs(seen.get("lr", -1) - recon) == 0.0 and seen.get("coh") == state.coherence
        print(f"  effective_lr reconstruction {'OK' if ok else 'FAIL'}: "
              f"inside update {seen.get('lr')} vs clip(state.coherence^2) {recon}", flush=True)
        if not ok:
            return 1
        # The wrapped step consumed one input. Time the rest, and bit-exact a fork
        # from a snapshot taken partway, compared against this same run.
        remain = steps - 1
        tr = Trace(steps, cycle.field.dim)
        record_step(tr, 0, cycle, ve, state, src, toks, 0)
        snap_at = min(80, steps // 2)
        snap = None
        t_step = time.perf_counter()
        buckets = []
        bucket_t = t_step
        for i in range(1, steps):
            state, src, toks, boredom = _step(cycle, pick, sids, weights)
            record_step(tr, i, cycle, ve, state, src, toks, boredom)
            if (i + 1) == snap_at:
                tr.weights_at[snap_at] = weight_digest(gen)
                tr.values_at[snap_at] = value_digest(ve)
                # The verify compares the horizon END. Mark it too, below.
                snap = capture(cycle, pick)
            if (i + 1) % 100 == 0:
                now = time.perf_counter()
                buckets.append(((i + 1), (now - bucket_t) / 100.0))
                bucket_t = now
        step_s = time.perf_counter() - t_step
        horizon = min(40, steps - snap_at)
        # Vector equality is the check. Weight hashes are only compared when the
        # plain run stored one, which this short timing path does not do at the
        # horizon end.
        v = verify_unperturbed(snap, tr, snap_at, horizon, sids, weights)
        print(f"  bit-exact unperturbed fork @{snap_at} for {horizon} steps: "
              f"{'OK' if v['ok'] else 'FAIL'} {v['mismatches'][:4]}", flush=True)
        per = step_s / max(remain, 1)
        print(f"  {remain} steps in {step_s:.1f}s  ({per * 1e3:.2f} ms/step average)", flush=True)
        if buckets:
            print(f"  first 100-step bucket {buckets[0][1] * 1e3:.2f} ms/step at step {buckets[0][0]}",
                  flush=True)
            print(f"  last  100-step bucket {buckets[-1][1] * 1e3:.2f} ms/step at step {buckets[-1][0]}",
                  flush=True)
            # If per-step cost grows linearly with step count, total time is quadratic.
            b0, r0 = buckets[0]
            b1, r1 = buckets[-1]
            if b1 != b0 and r1 > r0:
                slope = (r1 - r0) / (b1 - b0)          # seconds per step, per step of age
                base = r0 - slope * b0
                def total(n):
                    # integrate max(base, 0) + slope*t from 1..n, but base may be ~0
                    return sum(max(1e-6, base + slope * t) for t in range(1, n + 1, 50)) * 50
                # The sum above is a coarse integral. Do it properly:
                def total_quad(n):
                    # per-step ≈ base + slope * t, t=1..n
                    return max(0.0, base) * n + slope * n * (n + 1) / 2.0
                print(f"  extrapolated (cost growing with age): "
                      f"5k {total_quad(5000)/60:.1f} min, "
                      f"10k {total_quad(10000)/60:.1f} min, "
                      f"20k {total_quad(20000)/60:.1f} min   "
                      f"[plus build {time.perf_counter() - t0 - step_s:.0f}s, once per seed]",
                      flush=True)
                print(f"  per 1k steps at the START ~ {buckets[0][1] * 1000:.1f}s; "
                      f"at step {buckets[-1][0]} ~ {buckets[-1][1] * 1000:.1f}s",
                      flush=True)
            else:
                print(f"  per 1k steps ~ {per * 1000:.1f}s (no clear age slope yet)", flush=True)
                print(f"  flat extrapolation: 20k ~ {per * 20000 / 60:.1f} min plus build", flush=True)
        return 0 if v["ok"] else 1


def cmd_run(steps, seeds, ages, horizon, repeat_spacing, repeat_hits, scratch, summary):
    problems = self_check_estimators()
    if problems:
        print("estimator self-check FAIL")
        for p in problems:
            print(" ", p)
        return 1
    scratch.mkdir(parents=True, exist_ok=True)
    print(f"scratch: {scratch}", flush=True)
    results = []
    for seed in seeds:
        res = run_seed(seed, steps, ages, horizon, repeat_spacing, repeat_hits,
                       progress=True, checkpoint_dir=scratch)
        save_scratch(scratch, res)
        results.append(res)
        text = write_report(scratch / f"seed{seed}_report.txt", [res])
        print(text, flush=True)
    write_report(scratch / "report.txt", results)
    if summary:
        save_summary(Path(summary), results)
        print(f"summary: {summary}", flush=True)
    failed = [a for res in results for a, v in res["verify"].items() if not v["ok"]]
    if failed:
        print(f"BIT-EXACT VERIFY FAILED at ages {failed}", flush=True)
        return 1
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description="H0 timescale probe (read-only)")
    sub = p.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("time", help="cost, estimator check, one bit-exact fork")
    t.add_argument("--steps", type=int, default=400)
    t.add_argument("--seed", type=int, default=42)

    r = sub.add_parser("run", help="long run plus forks")
    r.add_argument("--steps", type=int, default=20000)
    r.add_argument("--seeds", type=str, default="42,43")
    r.add_argument("--ages", type=str, default="500,2000,5000,10000,15000")
    r.add_argument("--horizon", type=int, default=400)
    r.add_argument("--repeat-spacing", type=int, default=500)
    r.add_argument("--repeat-hits", type=int, default=6)
    r.add_argument("--scratch", type=str, default="")
    r.add_argument("--summary", type=str, default="")

    args = p.parse_args(argv)
    if args.cmd == "time":
        return cmd_time(args.steps, args.seed)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    scratch = Path(args.scratch) if args.scratch else REPO / "scratch" / "h0" / stamp
    summary = args.summary
    if summary == "auto":
        summary = str(REPO / "docs" / "findings" / "data" / "2026-10-15-h0-summary.npz")
    seeds = [int(s) for s in args.seeds.split(",") if s.strip()]
    ages = [int(s) for s in args.ages.split(",") if s.strip()]
    return cmd_run(args.steps, seeds, ages, args.horizon, args.repeat_spacing,
                   args.repeat_hits, scratch, summary)


if __name__ == "__main__":
    sys.exit(main())
