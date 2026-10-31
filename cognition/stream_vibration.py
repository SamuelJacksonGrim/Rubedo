"""
cognition/stream_vibration.py — observe-only vibration gauge on a vector stream.

The maturity target (Samuel, 2026-10-19): the expression stream should carry
"a resonance. A pulse, a rhythm, and a sustainable frequency." H0 found
today's stream is white jitter in a fixed cone — MSD flat from lag 1 to 512,
nothing repeats. This gauge is the instrument that can tell those two apart,
and can tell a real vibration from the Ouroboros wearing a rhythm (a rigid
closed loop).

Read on the EXPRESSION stream, never on the resonance field. The field's
decay is a heavy integrator that would smooth a pulse away by construction
(the same locus invariant as StreamMetastabilityMonitor). The tap in the
cycle is `_last_expressed` (post-reflection, what H0 recorded), not the
pre-loop stage-C metastability monitor.

Reads, each from a bounded window of unit directions:
  - power spectrum of the stream projected on its leading PCA axes
  - spectral flatness (Wiener entropy: white ≈ 1, a tone well below)
  - a dominant frequency and whether it holds across the two halves
  - MSD vs lag (white = flat; a vibration dips at multiples of its period)
  - leftover variance after subtracting the mean cycle, and the distance
    from one cycle to the next — so lock-in cannot pass for maturity

It is an OPTIONAL instrument (default-on as a pure observer): a bounded
ring, lazy recompute off the hot path, a terminal sink like dilation_factor
and StreamMetastabilityMonitor. It must never feed the cognitive or
governance loop. No randomness; SVD and rFFT are deterministic.
"""

from __future__ import annotations

import logging
import math
from collections import deque
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Sequence, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# MSD lags used by H0. Cap at window/2 at read time.
_LAGS = (1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512)

# Classification floors. Tuned so the three synthetic controls in
# tests.smoke.stream_vibration_smoke separate; the live stream is not
# forced into a label if it sits between them.
_SF_WHITE = 0.40          # spectral flatness at/above this, no stable peak → white
_PROMINENCE = 5.0         # FFT peak / median; reported, not the period source
_ACORR_PEAK = 0.40        # first autocorrelation local max at/above this → a period
_RESID_LOCK = 0.06        # leftover variance below this, with a stable peak → lock-in
_MIN_SAMPLES = 32


def _unit_rows(X: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(X, axis=1, keepdims=True)
    return X / np.maximum(n, 1e-15)


def _hann(n: int) -> np.ndarray:
    if n <= 1:
        return np.ones(n, dtype=float)
    return 0.5 - 0.5 * np.cos(2.0 * np.pi * np.arange(n) / (n - 1))


def _msd_curve(X: np.ndarray, lags: Sequence[int]) -> List[float]:
    T = len(X)
    out: List[float] = []
    for lag in lags:
        if lag <= 0 or lag >= T:
            out.append(float("nan"))
            continue
        d = X[lag:] - X[:-lag]
        out.append(float(np.mean(np.sum(d * d, axis=1))))
    return out


def _spectrum(scores: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Mean power spectrum across columns of `scores`, Hann-windowed.

    Returns (freqs_cycles_per_step, power) including the DC bin.
    """
    T, k = scores.shape
    w = _hann(T)
    powers = []
    for i in range(k):
        spec = np.fft.rfft(scores[:, i] * w)
        powers.append(spec.real * spec.real + spec.imag * spec.imag)
    P = np.mean(np.stack(powers, axis=0), axis=0)
    freqs = np.fft.rfftfreq(T)
    return freqs, P


def _peak(freqs: np.ndarray, power: np.ndarray) -> Tuple[float, float, float]:
    """Dominant AC bin: frequency, period (steps), prominence (peak/median)."""
    if len(power) < 2:
        return float("nan"), float("nan"), float("nan")
    P = np.maximum(power[1:], 1e-30)
    f = freqs[1:]
    i = int(np.argmax(P))
    freq = float(f[i])
    period = (1.0 / freq) if freq > 1e-12 else float("nan")
    prominence = float(P[i] / (float(np.median(P)) + 1e-30))
    return freq, period, prominence


def _flatness(power: np.ndarray) -> float:
    """Wiener spectral flatness of the AC bins. White → ~1; a tone → ~0."""
    if len(power) < 2:
        return float("nan")
    P = np.maximum(power[1:], 1e-30)
    return float(np.exp(np.mean(np.log(P))) / np.mean(P))


def acorr_period(U: np.ndarray, min_lag: int = 2) -> Tuple[float, float]:
    """Period of a unit-vector stream from the first autocorrelation peak.

    FFT peak-picking prefers harmonics; a discrete repeating loop is exactly
    period-K in the vectors themselves, so the first lag where the
    mean-centered cosine autocorrelation locally maxes is the fundamental.
    White has no peak (max ρ after lag 1 is noise ~ 1/sqrt(T)). Returns
    (period_steps, peak_rho); both nan when no peak clears `_ACORR_PEAK`.
    """
    T = len(U)
    Y = U - U.mean(axis=0, keepdims=True)
    var = float(np.mean(np.sum(Y * Y, axis=1)))
    if T < min_lag + 3 or var < 1e-18:
        return float("nan"), float("nan")
    max_lag = max(min_lag + 2, T // 3)
    rho = np.empty(max_lag)
    for lag in range(1, max_lag + 1):
        rho[lag - 1] = float(np.mean(np.sum(Y[lag:] * Y[:-lag], axis=1)) / var)
    for lag in range(min_lag, max_lag - 1):
        r = float(rho[lag - 1])
        if r >= _ACORR_PEAK and r >= float(rho[lag - 2]) and r >= float(rho[lag]):
            return float(lag), r
    return float("nan"), float("nan")


def _periodic_residual(X: np.ndarray, period: float) -> Tuple[float, float]:
    """Leftover variance and cycle-to-cycle L2 after subtracting the mean cycle.

    residual_frac is var(X - mean_cycle) / var(X) on the folded prefix.
    cycle_distance is the mean Euclidean distance between consecutive
    flattened cycles (0 for a rigid loop).
    """
    T = len(X)
    if not np.isfinite(period):
        return float("nan"), float("nan")
    P = int(round(period))
    if P < 2 or P > T // 2:
        return float("nan"), float("nan")
    n = T // P
    if n < 2:
        return float("nan"), float("nan")
    cycles = X[: n * P].reshape(n, P, X.shape[1])
    mean_cycle = cycles.mean(axis=0)
    resid = cycles - mean_cycle
    var = float(np.var(cycles))
    var_r = float(np.var(resid))
    residual_frac = (var_r / var) if var > 1e-18 else 0.0
    diffs = cycles[1:] - cycles[:-1]
    cycle_distance = float(np.mean(np.sqrt(np.sum(diffs * diffs, axis=(1, 2)))))
    return residual_frac, cycle_distance


def _cone_deg(U: np.ndarray) -> float:
    """Mean angle from the mean direction, in degrees."""
    mu = U.mean(axis=0)
    n = float(np.linalg.norm(mu))
    if n < 1e-15:
        return float("nan")
    coss = np.clip(U @ (mu / n), -1.0, 1.0)
    return float(np.mean(np.arccos(coss)) * (180.0 / math.pi))


def classify(
    spectral_flatness: float,
    has_dominant: bool,
    dominant_holds: bool,
    residual_frac: float,
) -> str:
    """Map the reads onto white / vibration / lock-in.

    A vibration is a stable peak with leftover variation from cycle to cycle.
    A lock-in is a stable peak whose leftover is gone — the same outputs
    repeating. White is a flat spectrum with no peak that holds. Anything
    else is `unknown` (do not force a label on a live stream that sits
    between the controls).
    """
    peaked = bool(has_dominant and dominant_holds)
    if peaked and np.isfinite(residual_frac) and residual_frac < _RESID_LOCK:
        return "lock-in"
    if peaked:
        return "vibration"
    if np.isfinite(spectral_flatness) and spectral_flatness >= _SF_WHITE:
        return "white"
    return "unknown"


@dataclass
class VibrationReport:
    """One read of the vibration gauge. Frozen snapshot; never written back."""

    samples: int = 0
    window: int = 0
    seen: int = 0
    n_axes: int = 0
    explained_var: float = float("nan")
    spectral_flatness: float = float("nan")
    dominant_freq: float = float("nan")
    dominant_period: float = float("nan")
    dominant_prominence: float = float("nan")
    acorr_peak: float = float("nan")
    has_dominant: bool = False
    dominant_holds: bool = False
    msd_lags: Tuple[int, ...] = ()
    msd: Tuple[float, ...] = ()
    msd_lag1: float = float("nan")
    msd_at_period: float = float("nan")
    msd_period_ratio: float = float("nan")
    msd_cv: float = float("nan")
    residual_frac: float = float("nan")
    cycle_distance: float = float("nan")
    cone_deg: float = float("nan")
    label: str = "insufficient"
    notes: str = "no samples yet"
    extra: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "samples": self.samples,
            "window": self.window,
            "seen": self.seen,
            "n_axes": self.n_axes,
            "explained_var": self.explained_var,
            "spectral_flatness": self.spectral_flatness,
            "dominant_freq": self.dominant_freq,
            "dominant_period": self.dominant_period,
            "dominant_prominence": self.dominant_prominence,
            "acorr_peak": self.acorr_peak,
            "has_dominant": self.has_dominant,
            "dominant_holds": self.dominant_holds,
            "msd_lags": list(self.msd_lags),
            "msd": list(self.msd),
            "msd_lag1": self.msd_lag1,
            "msd_at_period": self.msd_at_period,
            "msd_period_ratio": self.msd_period_ratio,
            "msd_cv": self.msd_cv,
            "residual_frac": self.residual_frac,
            "cycle_distance": self.cycle_distance,
            "cone_deg": self.cone_deg,
            "label": self.label,
            "notes": self.notes,
        }

    def snapshot(self) -> dict:
        """Compact status card (cycle.status() / the board)."""
        return {
            "label": self.label,
            "spectral_flatness": self.spectral_flatness,
            "dominant_period": self.dominant_period,
            "dominant_holds": self.dominant_holds,
            "residual_frac": self.residual_frac,
            "cycle_distance": self.cycle_distance,
            "cone_deg": self.cone_deg,
            "msd_period_ratio": self.msd_period_ratio,
            "explained_var": self.explained_var,
            "samples": self.samples,
            "window": self.window,
            "seen": self.seen,
        }


def analyze(
    vectors: Iterable[np.ndarray],
    n_axes: int = 3,
    window: Optional[int] = None,
    seen: Optional[int] = None,
) -> VibrationReport:
    """Offline read over a finite list of vectors. The online gauge calls this."""
    stacked = [np.asarray(v, dtype=float).ravel() for v in vectors]
    T = len(stacked)
    win = int(window) if window is not None else T
    seen_n = int(seen) if seen is not None else T
    if T < _MIN_SAMPLES:
        return VibrationReport(
            samples=T, window=win, seen=seen_n,
            label="insufficient",
            notes=f"need >= {_MIN_SAMPLES} samples, have {T}",
        )
    X = _unit_rows(np.stack(stacked, axis=0))
    cone = _cone_deg(X)

    Xc = X - X.mean(axis=0, keepdims=True)
    try:
        U, S, _Vt = np.linalg.svd(Xc, full_matrices=False)
    except np.linalg.LinAlgError as exc:
        return VibrationReport(
            samples=T, window=win, seen=seen_n, cone_deg=cone,
            label="unknown", notes=f"svd failed: {exc}",
        )
    rank = int(np.count_nonzero(S > 1e-12))
    k = int(min(max(1, n_axes), U.shape[1], max(1, rank)))
    scores = U[:, :k] * S[:k]
    explained = float(np.sum(S[:k] ** 2) / (np.sum(S ** 2) + 1e-30))

    freqs, power = _spectrum(scores)
    sf = _flatness(power)
    fft_f, fft_period, prominence = _peak(freqs, power)
    # Period from the vector autocorrelation (fundamental), not the FFT
    # peak (which prefers harmonics on a discrete loop).
    period, acorr_pk = acorr_period(X)
    has_dominant = bool(np.isfinite(period) and period >= 2.0 and acorr_pk >= _ACORR_PEAK)
    dom_f = (1.0 / period) if has_dominant else float("nan")

    holds = False
    if has_dominant and T >= 64:
        mid = T // 2
        p1, r1 = acorr_period(X[:mid])
        p2, r2 = acorr_period(X[mid:])
        slack = max(1.0, 0.1 * period)
        holds = bool(
            np.isfinite(p1) and np.isfinite(p2)
            and r1 >= _ACORR_PEAK * 0.75 and r2 >= _ACORR_PEAK * 0.75
            and abs(p1 - period) <= slack and abs(p2 - period) <= slack
        )

    lags = [L for L in _LAGS if L < T]
    msd = _msd_curve(X, lags)
    msd_lag1 = msd[0] if lags and lags[0] == 1 else float("nan")
    msd_at_p = float("nan")
    if has_dominant and np.isfinite(period):
        P_int = int(round(period))
        if 2 <= P_int < T:
            d = X[P_int:] - X[:-P_int]
            msd_at_p = float(np.mean(np.sum(d * d, axis=1)))
    ratio = (
        msd_at_p / msd_lag1
        if np.isfinite(msd_at_p) and np.isfinite(msd_lag1) and msd_lag1 > 1e-18
        else float("nan")
    )
    finite = [m for m in msd if np.isfinite(m)]
    msd_cv = (
        float(np.std(finite) / (np.mean(finite) + 1e-30)) if finite else float("nan")
    )

    residual_frac, cycle_distance = (
        _periodic_residual(X, period) if has_dominant else (float("nan"), float("nan"))
    )
    label = classify(sf, has_dominant, holds, residual_frac)
    notes = (
        f"sf={sf:.3f} period={period:.2f} holds={holds} "
        f"resid={residual_frac:.3f} cone={cone:.1f}deg"
    )
    return VibrationReport(
        samples=T, window=win, seen=seen_n, n_axes=k,
        explained_var=explained,
        spectral_flatness=sf,
        dominant_freq=dom_f,
        dominant_period=period,
        dominant_prominence=prominence,
        acorr_peak=acorr_pk,
        has_dominant=has_dominant,
        dominant_holds=holds,
        msd_lags=tuple(lags),
        msd=tuple(msd),
        msd_lag1=msd_lag1,
        msd_at_period=msd_at_p,
        msd_period_ratio=ratio,
        msd_cv=msd_cv,
        residual_frac=residual_frac,
        cycle_distance=cycle_distance,
        cone_deg=cone,
        label=label,
        notes=notes,
        extra={"fft_freq": fft_f, "fft_period": fft_period},
    )


def synthetic_stream(
    kind: str,
    n: int,
    dim: int,
    rng: np.random.Generator,
    period: int = 16,
) -> np.ndarray:
    """The three controls the gauge has to tell apart.

    `kind`:
      white      — i.i.d. unit vectors (no pulse)
      vibration  — period-`period` orbit in a plane plus isotropic noise
                   (a pulse with variation riding on it)
      lock-in    — a rigid repeating loop of `period` distinct unit vectors
                   (the Ouroboros wearing a rhythm)

    `rng` is passed in (no draw inside this module). Tests seed it.
    """
    if n < 1 or dim < 2:
        raise ValueError("n >= 1 and dim >= 2")
    if kind == "white":
        X = rng.normal(size=(n, dim))
        return _unit_rows(X)
    if kind == "vibration":
        a = np.zeros(dim); a[0] = 1.0
        b = np.zeros(dim); b[1] = 1.0
        t = np.arange(n)
        omega = 2.0 * math.pi / float(period)
        sig = np.outer(np.cos(omega * t), a) + np.outer(np.sin(omega * t), b)
        return _unit_rows(sig + 0.06 * rng.normal(size=(n, dim)))
    if kind == "lock-in":
        basis = _unit_rows(rng.normal(size=(period, dim)))
        return np.stack([basis[i % period] for i in range(n)], axis=0)
    raise ValueError("kind must be white, vibration, or lock-in")


class StreamVibrationGauge:
    """Sliding-window vibration read over a vector stream (expression).

    Parameters
    ----------
    window : int
        Ring-buffer size. 512 matches the lag H0 used to call the MSD flat.
    interval : int
        Recompute cadence. The report is refreshed every `interval`
        observations so the per-step cost is an O(1) copy + append.
    min_samples : int
        Defer the first recompute until the ring holds at least this many.
    n_axes : int
        Leading PCA axes whose power spectrum is averaged.
    """

    def __init__(
        self,
        window: int = 512,
        interval: int = 32,
        min_samples: int = 64,
        n_axes: int = 3,
    ):
        if window < _MIN_SAMPLES:
            raise ValueError(f"window must be >= {_MIN_SAMPLES}")
        self.window = int(window)
        self.interval = max(1, int(interval))
        self.min_samples = max(_MIN_SAMPLES, min(int(min_samples), self.window))
        self.n_axes = max(1, int(n_axes))
        self._vecs: deque = deque(maxlen=self.window)
        self._seen: int = 0
        self._report: VibrationReport = VibrationReport(
            window=self.window, notes="no samples yet",
        )

    def observe(self, vec: np.ndarray) -> None:
        """Record one vector. O(1) copy + append; recompute is lazy."""
        v = np.asarray(vec, dtype=float).copy()
        self._vecs.append(v)
        self._seen += 1
        if len(self._vecs) >= self.min_samples and self._seen % self.interval == 0:
            self._recompute()

    def _recompute(self) -> None:
        self._report = analyze(
            self._vecs, n_axes=self.n_axes,
            window=self.window, seen=self._seen,
        )
        logger.debug("vibration recompute: %s", self._report.notes)

    def compute_now(self) -> VibrationReport:
        """Force an immediate recompute over the current window."""
        if len(self._vecs) >= _MIN_SAMPLES:
            self._recompute()
        return self._report

    @property
    def report(self) -> VibrationReport:
        """Cached report (up to `interval` steps stale)."""
        return self._report

    def snapshot(self) -> dict:
        snap = self._report.snapshot()
        snap["samples"] = len(self._vecs)
        snap["window"] = self.window
        snap["seen"] = self._seen
        return snap
