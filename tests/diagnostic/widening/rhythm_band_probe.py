"""
tests/diagnostic/widening/rhythm_band_probe.py

Widening plan step 4, part B. The rhythm bands are one co-tuned set.
FIELD_DIM stays 128. Bands other than the F9 defaults apply only when
the field is wider than that, and only after this probe's placement
rule says so. This file does not edit the constants. It measures.

Pre-declared before any pin or free-run arm. Do not edit this block
to fit a result.

Occupancy restored — canonical, settled half, steps 261 through 500,
energy-classified rhythm. Boredom's override does not count as explore.
The 128 target is the census youth replay, not a number from this probe:

  seeds 42 / 43 / 44 late explore counts 51, 62, 82 out of 240
    fractions 0.2125, 0.258333, 0.341667
    mean 0.270833, span 0.129167
  late reflect counts 189, 178, 158
  late dream 0, late stabilize 0

SUCCESS at width W, on one seed set (the fitting seeds, and again on
the held-out seeds):

  - mean late explore fraction is inside [0.141667, 0.400000]
  - every seed's late explore count is > 0
  - every seed's late dream count is <= 2
  - every seed's late stabilize count is 0
  - every seed's late reflect count is greater than its late explore count

WIDE must stay a reflect home. The census wide 128 settled explore
counts are 0, 0, 9. On wide, same settled half, every seed:

  - late explore fraction <= 0.15
  - late reflect fraction >= 0.85
  - late dream count <= 2
  - late stabilize count is 0

The 128 control (no threshold override, both workloads, seeds 42-44)
must reproduce the canonical late counts exactly, and must itself pass
the wide bar. If the control misses, stop. The bands are not the cause.

Held-out seeds are 45 and 46. They are not used to place bands. If the
fitting seeds pass and a held-out seed fails, the set does not ship.

Placement is the F9 constraint set, not a search on occupancy.

  A pinned run forces field.current_rhythm to one band and sets the
  boredom override threshold to 2 so the pin is that band's behavior.
  Canonical workload, seeds 42-44, 400 steps. The equilibrium is the
  mean field energy over steps 301-400. Drift is the mean of steps
  351-400 minus the mean of steps 301-350. Absolute drift above 2% of
  the level means that window is not an equilibrium.

  Degraded stabilize forces every non-blocking decision to
  ALLOW_WEAKENED at the live weakened_strength_factor. Blocking
  decisions are left alone. That equilibrium is the one the stabilize
  threshold has to sit below.

  Calibration gate at dim 128, seed-mean equilibrium. Outside this,
  the pin is the wrong instrument and nothing ships:
    stabilize full      [30, 45]
    stabilize degraded  [8, 20]
    dream               [160, 240]
    reflect             [270, 320]
    explore             [280, 330]
  Dim 64 is reported (F9 said 64 and 128 agree). It is not a fit point
  and it does not retune the defaults.

  Integers, the precision of 5 / 150 / 300. From the seed-mean
  equilibria at that width:
    stabilize stays 5. If the degraded equilibrium is not above 5,
    the constraint cannot be met and nothing ships.
    dream cut = round(0.75 * dream equilibrium), and strictly below
    that equilibrium and strictly above 5. 0.75 is 150/200.
    explore edge = ceil(explore equilibrium), so it sits at or above
    it. The edge must also be strictly above the reflect equilibrium
    so the reflect band contains its own equilibrium. If ceil(explore)
    is not above reflect, the edge is floor(reflect) + 1.
  If those cannot be satisfied together, nothing ships.
  The same formula on the published F9 numbers (degraded 13, dream 200,
  reflect 293, explore 298) must land within 15 of 300 and within 30
  of 150. Production dim 128 keeps 5 / 150 / 300 even when the formula
  would name a neighbor.

Rule or table, decided by decide() from the pin files:

  Ratios are dream_cut / 150 and explore_edge / 300.
  Fit widths are 256 and 768. Holdout width is 512, pinned on the
  same seeds and not used to choose. Candidates are one shared f for
  both ratios: 1; sqrt(128/d); 128/d; sqrt(d/128); and
  1 + a * ln(d/128) with a fit by least squares on the four ratios.
  A candidate fits a width when both of its predicted integers fall
  inside the min and max of the per-seed placements at that width.
  It ships only if it fits 256 and 768 and predicts 512 inside that
  width's per-seed range. Otherwise the data supports a per-width
  table of the placed integers at 256 and at 768, and no other wide
  dim is invented: if the 512 placement lies between the 256 and 768
  placements on both cuts, dims in (128, 512] use the 256 set and
  dims above 512 use the 768 set; if it does not, only exactly 256
  and exactly 768 are retuned.

There is no second placement. If the placed set misses the occupancy
signature on seeds 42-44, that is the result. Do not walk the
thresholds toward the free-run mean.

    python -m tests.diagnostic.widening.rhythm_band_probe --check
    python -m tests.diagnostic.widening.rhythm_band_probe --batch-pin \\
        docs/findings/data/2026-10-31-rhythm-bands/pins --jobs 2
    python -m tests.diagnostic.widening.rhythm_band_probe --decide \\
        docs/findings/data/2026-10-31-rhythm-bands/pins
"""

from __future__ import annotations

import os

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
import subprocess
import sys
from pathlib import Path

import numpy as np

logging.disable(logging.CRITICAL)

import torch  # noqa: E402

torch.set_num_threads(int(os.environ.get("OMP_NUM_THREADS", "2")))
try:
    torch.set_num_interop_threads(1)
except RuntimeError:
    pass

from agents.selfhood_governance import GovernanceDecision  # noqa: E402
from loop.recursion1188 import CONFIG, build_engine  # noqa: E402
from substrate import determinism  # noqa: E402
from substrate.dims import FIELD_DIM  # noqa: E402
from substrate.resonance_field import ResonanceField  # noqa: E402
from tests.workloads import load_named  # noqa: E402

PIN_STEPS = 400
EQ_LO = 300          # steps 301-400, 0-based slice start
EQ_MID = 350
DRIFT_FRAC = 0.02
DREAM_RATIO = 150.0 / 200.0
BLOCKING = (
    GovernanceDecision.QUARANTINE,
    GovernanceDecision.REJECT,
    GovernanceDecision.SACRED_SHIELD,
)
CALIBRATION = {
    "stabilize": (30.0, 45.0),
    "degraded": (8.0, 20.0),
    "dream": (160.0, 240.0),
    "reflect": (270.0, 320.0),
    "explore": (280.0, 330.0),
}
FIT_WIDTHS = (256, 768)
HOLDOUT_WIDTH = 512
PIN_WIDTHS = (64, 128, 256, 512, 768)
PIN_SEEDS = (42, 43, 44)
# Canonical late counts the 128 control has to reproduce.
CANON_128_LATE = {
    42: {"stabilize": 0, "dream": 0, "reflect": 189, "explore": 51},
    43: {"stabilize": 0, "dream": 0, "reflect": 178, "explore": 62},
    44: {"stabilize": 0, "dream": 0, "reflect": 158, "explore": 82},
}
EXPLORE_MEAN = 0.270833
EXPLORE_SPAN = 0.129167


def place_from_eqs(degraded, dream_eq, reflect_eq, explore_eq):
    """F9 placement. Returns (thresholds, error). error is None on success.

    stabilize is the published 5, not a scaled number. The other two
    cuts are integers placed against the equilibria.
    """
    stabilize = 5.0
    if not (float(degraded) > stabilize):
        return None, "degraded equilibrium is not above 5"
    dream = int(round(DREAM_RATIO * float(dream_eq)))
    if dream >= float(dream_eq):
        dream = int(math.floor(float(dream_eq) - 1e-9))
    if dream <= stabilize:
        return None, "dream cut collapsed onto stabilize"
    edge = int(math.ceil(float(explore_eq) - 1e-9))
    if edge <= float(reflect_eq):
        edge = int(math.floor(float(reflect_eq))) + 1
    if not (dream < float(reflect_eq) < edge):
        return None, "reflect equilibrium is not inside the reflect band"
    if edge < float(explore_eq) - 1e-9:
        return None, "explore edge fell below the explore equilibrium"
    return {
        "stabilize": stabilize,
        "dream": float(dream),
        "reflect": float(edge),
    }, None


def _quant(xs, q):
    if not xs:
        return None
    return float(np.quantile(np.asarray(xs, dtype=float), q))


def _pin_names():
    return (
        ("stabilize", False),
        ("degraded", True),
        ("dream", False),
        ("reflect", False),
        ("explore", False),
    )


def run_pin(dim, seed, rhythm, degraded, steps=PIN_STEPS):
    if dim % 4 != 0 or dim % 2 != 0:
        raise SystemExit(f"dim {dim} is not usable (heads=4, even PE)")
    cfg = dict(CONFIG)
    cfg["dim"] = int(dim)
    cfg["pretrain_on_corpus"] = False
    cfg["session_persistence"] = False
    cfg["log_interval"] = 10 ** 9
    sources, weights = load_named("canonical")
    energy = []
    forced = already = blocked = decisions = 0
    pin_name = "stabilize" if rhythm == "degraded" else rhythm

    with determinism.deterministic(seed):
        gen, cycle, gov, _ve = build_engine(cfg)
        if "cuda" in str(gen.device).lower():
            raise SystemExit(f"refusing GPU device {gen.device}")
        if getattr(cycle, "dreamer", None) is not None:
            cycle.dreamer._rng = np.random.default_rng(seed)
        cycle.field.current_rhythm = lambda name=pin_name: name
        # Boredom must not rewrite the pin into explore's injection.
        cycle.config["boredom_override_threshold"] = 2.0
        if degraded:
            factor = float(gov.config.get("weakened_strength_factor", 0.40))
            orig = gov.arbitrate

            def arbitrate(*a, **k):
                nonlocal forced, already, blocked, decisions
                dec, strength = orig(*a, **k)
                decisions += 1
                if dec == GovernanceDecision.ALLOW_WEAKENED:
                    already += 1
                if dec in BLOCKING:
                    blocked += 1
                    return dec, strength
                forced += 1
                return GovernanceDecision.ALLOW_WEAKENED, factor

            gov.arbitrate = arbitrate
        sids = list(sources.keys())
        wts = [weights[s] for s in sids]
        pick = random.Random(seed)
        for i in range(1, steps + 1):
            src = pick.choices(sids, weights=wts)[0]
            tokens = pick.choice(sources[src])
            state = cycle.step(tokens, source_id=src, origin_type="internal")
            energy.append(float(state.field_energy))
            if i % 100 == 0 or i == steps:
                print(
                    f"pin dim={dim} seed={seed} {rhythm} step={i}/{steps} "
                    f"E={energy[-1]:.1f}",
                    flush=True,
                )
        boredom = int(cycle._boredom_overrides)

    window = energy[EQ_LO:steps]
    first = energy[EQ_LO:EQ_MID]
    second = energy[EQ_MID:steps]
    eq = float(sum(window) / len(window))
    drift = float(sum(second) / len(second) - sum(first) / len(first))
    return {
        "schema": 1,
        "kind": "pin",
        "dim": int(dim),
        "seed": int(seed),
        "rhythm": rhythm,
        "degraded": bool(degraded),
        "steps": int(steps),
        "eq_lo_step": EQ_LO + 1,
        "eq_mean": round(eq, 6),
        "eq_drift": round(drift, 6),
        "not_basin": abs(drift) > DRIFT_FRAC * max(abs(eq), 1.0),
        "eq_p10": round(_quant(window, 0.10), 6),
        "eq_p50": round(_quant(window, 0.50), 6),
        "eq_p90": round(_quant(window, 0.90), 6),
        "boredom_overrides": boredom,
        "decisions": int(decisions),
        "weakened_already": int(already),
        "weakened_forced": int(forced),
        "blocked": int(blocked),
        "field_dim_constant": int(FIELD_DIM),
        "device": str(gen.device),
        "thresholds": dict(cycle.field.thresholds),
    }


def _pin_path(out_dir, dim, seed, rhythm):
    return Path(out_dir) / f"pin-d{dim}-s{seed}-{rhythm}.json"


def _load_pins(out_dir):
    pins = []
    for path in sorted(Path(out_dir).glob("pin-d*-s*-*.json")):
        pins.append(json.loads(path.read_text(encoding="utf-8")))
    return pins


def _group_eq(pins):
    """dim -> rhythm -> seed -> eq_mean, plus not_basin if any seed drifted."""
    out = {}
    for arm in pins:
        slot = out.setdefault(int(arm["dim"]), {}).setdefault(arm["rhythm"], {})
        slot[int(arm["seed"])] = arm
    return out


def _mean(xs):
    xs = list(xs)
    return float(sum(xs) / len(xs))


def _seed_placements(group, dim):
    """Per-seed placement at dim, and the placement on the seed-mean eqs."""
    g = group[dim]
    seeds = sorted(set.intersection(*(set(g[name]) for name in (
        "degraded", "dream", "reflect", "explore"))))
    per = {}
    for seed in seeds:
        placed, err = place_from_eqs(
            g["degraded"][seed]["eq_mean"],
            g["dream"][seed]["eq_mean"],
            g["reflect"][seed]["eq_mean"],
            g["explore"][seed]["eq_mean"],
        )
        per[seed] = {"thresholds": placed, "error": err}
    means = {
        name: _mean(g[name][s]["eq_mean"] for s in seeds)
        for name in ("degraded", "dream", "reflect", "explore", "stabilize")
        if name in g
    }
    placed, err = place_from_eqs(
        means["degraded"], means["dream"], means["reflect"], means["explore"],
    )
    return seeds, per, means, placed, err


def _in_range(value, bounds):
    lo, hi = bounds
    return lo <= value <= hi


def _fits(predicted, per_seed, key):
    """Predicted integer is inside the per-seed placements.

    A seed whose own equilibria could not be placed does not vote.
    Fewer than two placed seeds is not a range.
    """
    vals = []
    for row in per_seed.values():
        thr = row["thresholds"]
        if thr is None:
            continue
        vals.append(thr[key])
    if len(vals) < 2:
        return False
    return min(vals) <= predicted <= max(vals)


def _candidate_predictions(ratios_by_width):
    """Shared f. ratios_by_width[width] = (dream_ratio, edge_ratio)."""
    widths = list(FIT_WIDTHS)
    pairs = [(d, ratios_by_width[d][0]) for d in widths] + [
        (d, ratios_by_width[d][1]) for d in widths
    ]
    candidates = {
        "constant": lambda d: 1.0,
        "inv_sqrt": lambda d: math.sqrt(FIELD_DIM / d),
        "inv_dim": lambda d: FIELD_DIM / d,
        "sqrt_dim": lambda d: math.sqrt(d / FIELD_DIM),
    }
    # One shared slope on ln(d/128). Least squares through the four ratios.
    xs = [math.log(d / FIELD_DIM) for d, _r in pairs]
    ys = [r - 1.0 for _d, r in pairs]
    denom = sum(x * x for x in xs)
    slope = (sum(x * y for x, y in zip(xs, ys)) / denom) if denom else 0.0
    candidates["log_linear"] = lambda d, a=slope: 1.0 + a * math.log(d / FIELD_DIM)
    return candidates, slope


def decide(out_dir):
    pins = _load_pins(out_dir)
    group = _group_eq(pins)
    report = {"ship": False, "reason": "", "form": "none", "calibration": {}}
    missing = [d for d in PIN_WIDTHS if d not in group]
    if missing:
        report["reason"] = f"missing pin widths {missing}"
        return report
    # Contaminated pin: boredom rewrote the band.
    dirty = [
        f"d{a['dim']} s{a['seed']} {a['rhythm']}"
        for a in pins if a.get("boredom_overrides")
    ]
    if dirty:
        report["reason"] = f"boredom overrode a pin: {dirty}"
        return report

    cal = {}
    for name, bounds in CALIBRATION.items():
        arms = group[128][name]
        mean = _mean(a["eq_mean"] for a in arms.values())
        drifted = [s for s, a in arms.items() if a["not_basin"]]
        cal[name] = {
            "mean": round(mean, 6),
            "bounds": list(bounds),
            "inside": _in_range(mean, bounds),
            "drifted_seeds": drifted,
            "per_seed": {str(s): a["eq_mean"] for s, a in sorted(arms.items())},
        }
    report["calibration"] = cal
    if not all(row["inside"] for row in cal.values()):
        report["reason"] = "dim 128 pinned equilibria are outside the F9 calibration gate"
        return report
    if any(row["drifted_seeds"] for row in cal.values()):
        report["reason"] = "dim 128 pinned window drifted; not an equilibrium"
        return report

    published, pub_err = place_from_eqs(13.0, 200.0, 293.0, 298.0)
    report["formula_on_published_f9"] = {"thresholds": published, "error": pub_err}
    if pub_err or abs(published["reflect"] - 300.0) > 15 or abs(published["dream"] - 150.0) > 30:
        report["reason"] = "placement formula does not reproduce the F9 shape"
        return report

    per_width = {}
    for dim in PIN_WIDTHS:
        seeds, per, means, placed, err = _seed_placements(group, dim)
        drifted = {
            name: [s for s, a in group[dim][name].items() if a["not_basin"]]
            for name in group[dim]
        }
        per_width[str(dim)] = {
            "seeds": seeds,
            "eq_mean": {k: round(v, 6) for k, v in means.items()},
            "placed": placed,
            "error": err,
            "per_seed": {
                str(s): row for s, row in per.items()
            },
            "drifted": {k: v for k, v in drifted.items() if v},
        }
    report["per_width"] = per_width
    for dim in FIT_WIDTHS:
        row = per_width[str(dim)]
        if row["error"] or row["drifted"]:
            report["reason"] = f"dim {dim} cannot be placed ({row['error'] or row['drifted']})"
            return report
    hold = per_width[str(HOLDOUT_WIDTH)]
    if hold["error"] or hold["drifted"]:
        report["reason"] = f"holdout dim {HOLDOUT_WIDTH} cannot be placed ({hold['error'] or hold['drifted']})"
        return report

    ratios = {}
    for dim in FIT_WIDTHS + (HOLDOUT_WIDTH,):
        placed = per_width[str(dim)]["placed"]
        ratios[dim] = (placed["dream"] / 150.0, placed["reflect"] / 300.0)
    candidates, slope = _candidate_predictions(ratios)
    tested = {}
    winner = None
    for name, fn in candidates.items():
        ok = True
        detail = {}
        for dim in FIT_WIDTHS + (HOLDOUT_WIDTH,):
            pred_dream = int(round(150.0 * fn(dim)))
            pred_edge = int(round(300.0 * fn(dim)))
            per = {
                int(s): row for s, row in per_width[str(dim)]["per_seed"].items()
            }
            dream_ok = _fits(pred_dream, per, "dream")
            edge_ok = _fits(pred_edge, per, "reflect")
            detail[str(dim)] = {
                "dream": pred_dream, "reflect": pred_edge,
                "dream_ok": dream_ok, "edge_ok": edge_ok,
            }
            if dim in FIT_WIDTHS or dim == HOLDOUT_WIDTH:
                if not (dream_ok and edge_ok):
                    ok = False
        tested[name] = {"fits_all_declared": ok, "detail": detail}
        if ok and winner is None:
            winner = name
    report["candidates"] = tested
    report["log_linear_slope"] = slope
    report["ratios"] = {
        str(d): {"dream": ratios[d][0], "reflect": ratios[d][1]} for d in ratios
    }

    bands = {str(d): per_width[str(d)]["placed"] for d in FIT_WIDTHS}
    if winner is not None:
        fn = candidates[winner]
        shipped = {
            str(dim): {
                "stabilize": 5.0,
                "dream": float(int(round(150.0 * fn(dim)))),
                "reflect": float(int(round(300.0 * fn(dim)))),
            }
            for dim in FIT_WIDTHS
        }
        report["ship"] = True
        report["form"] = "rule"
        report["rule"] = winner
        report["bands"] = bands
        report["shipped"] = shipped
        report["reason"] = f"shared scale {winner} fits 256, 768 and predicts 512"
        return report

    # Table. The 512 placement has to lie between the two measured sets
    # on both cuts before any other wide dim inherits a neighbor.
    p256 = bands["256"]
    p768 = bands["768"]
    p512 = per_width[str(HOLDOUT_WIDTH)]["placed"]
    between = True
    for key in ("dream", "reflect"):
        lo, hi = sorted((p256[key], p768[key]))
        if not (lo <= p512[key] <= hi):
            between = False
    report["ship"] = True
    report["form"] = "table"
    report["bands"] = bands
    report["shipped"] = bands
    report["holdout_between"] = between
    report["holdout_placed"] = p512
    if between:
        report["reason"] = (
            "no shared scale fits; table at 256 and 768, "
            "and 512 lies between them so neighbors may use the nearer measured set"
        )
    else:
        report["reason"] = (
            "no shared scale fits, and 512 is not between 256 and 768; "
            "only exactly those two widths are retuned"
        )
    return report


def late_counts(arm):
    early = arm["youth"]["early"]
    full = arm["youth"]["full"]
    late_steps = int(full["steps"]) - int(early["steps"])
    counts = {
        name: int(full[name]) - int(early[name])
        for name in ("stabilize", "dream", "reflect", "explore")
    }
    return late_steps, counts


def occupancy_ok(workload, counts, late_steps):
    if counts["dream"] > 2 or counts["stabilize"] != 0:
        return False
    if workload == "canonical":
        explore = counts["explore"] / late_steps
        # The mean test is across seeds. Per seed: explore happened,
        # and reflect is still the larger band.
        return counts["explore"] > 0 and counts["reflect"] > counts["explore"] and explore <= 1
    explore = counts["explore"] / late_steps
    reflect = counts["reflect"] / late_steps
    return explore <= 0.15 and reflect >= 0.85


def canonical_mean_ok(fractions):
    mean = sum(fractions) / len(fractions)
    return abs(mean - EXPLORE_MEAN) <= EXPLORE_SPAN


def _batch_pin(out_dir, jobs):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    pending = []
    for dim in PIN_WIDTHS:
        for seed in PIN_SEEDS:
            for rhythm, _degraded in _pin_names():
                path = _pin_path(out, dim, seed, rhythm)
                if path.is_file():
                    try:
                        got = json.loads(path.read_text(encoding="utf-8"))
                        if got.get("kind") == "pin" and got.get("steps") == PIN_STEPS:
                            print(f"skip {path.name}", flush=True)
                            continue
                    except json.JSONDecodeError:
                        pass
                pending.append({"dim": dim, "seed": seed, "rhythm": rhythm})
    n = max(1, int(jobs))
    print(f"batch-pin {len(pending)} arms, {n} workers", flush=True)
    if not pending:
        return 0
    lists = [pending[i::n] for i in range(n)]
    procs = []
    for i, chunk in enumerate(lists):
        if not chunk:
            continue
        list_path = out / f"_worker-{i}.json"
        list_path.write_text(json.dumps({
            "out": str(out), "arms": chunk,
        }), encoding="utf-8")
        procs.append(subprocess.Popen([
            sys.executable, "-m", "tests.diagnostic.widening.rhythm_band_probe",
            "--run-list", str(list_path),
        ]))
    failed = [p.wait() for p in procs]
    failed = [c for c in failed if c != 0]
    if failed:
        print(f"batch-pin failed, worker exits {failed}", flush=True)
        return 1
    print("batch-pin done", flush=True)
    return 0


def _run_listed(list_path):
    payload = json.loads(Path(list_path).read_text(encoding="utf-8"))
    out = Path(payload["out"])
    degraded_of = {name: flag for name, flag in _pin_names()}
    for job in payload["arms"]:
        rhythm = job["rhythm"]
        arm = run_pin(job["dim"], job["seed"], rhythm, degraded_of[rhythm])
        path = _pin_path(out, job["dim"], job["seed"], rhythm)
        path.write_text(json.dumps(arm, indent=2, sort_keys=True), encoding="utf-8")
        print(
            f"WROTE {path.name} eq={arm['eq_mean']} drift={arm['eq_drift']} "
            f"not_basin={arm['not_basin']}",
            flush=True,
        )
    return 0


def _free_jobs(placement, out_dir):
    """128 controls, then the shipped bands at 256 and 768.

    Seeds 42-44 place nothing here; they are the occupancy check on the
    set the pins already placed. Seeds 45 and 46 are held out.
    """
    shipped = placement["shipped"]
    jobs = []
    for workload in ("canonical", "wide"):
        for seed in PIN_SEEDS:
            jobs.append({
                "workload": workload, "dim": 128, "seed": seed,
                "steps": 500, "thresholds": None, "out": out_dir,
                "role": "control",
            })
        for dim in FIT_WIDTHS:
            for seed in (42, 43, 44, 45, 46):
                jobs.append({
                    "workload": workload, "dim": dim, "seed": seed,
                    "steps": 500, "thresholds": shipped[str(dim)],
                    "out": out_dir,
                    "role": "fit" if seed in PIN_SEEDS else "heldout",
                })
    return jobs


def _batch_free(placement_path, out_dir, jobs):
    placement = json.loads(Path(placement_path).read_text(encoding="utf-8"))
    if not placement.get("ship"):
        print(f"not running free arms: {placement.get('reason')}", flush=True)
        return 2
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    from tests.diagnostic.widening.dial_census_probe import _arm_path
    pending = []
    for job in _free_jobs(placement, str(out)):
        path = _arm_path(out, job["workload"], job["dim"], job["seed"], job["steps"])
        if path.is_file():
            try:
                got = json.loads(path.read_text(encoding="utf-8"))
                if got.get("youth", {}).get("full") and got.get("steps") == 500:
                    print(f"skip {path.name}", flush=True)
                    continue
            except json.JSONDecodeError:
                pass
        pending.append(job)
    n = max(1, int(jobs))
    print(f"batch-free {len(pending)} arms, {n} workers", flush=True)
    if not pending:
        return score_free(out_dir)
    lists = [pending[i::n] for i in range(n)]
    procs = []
    for i, chunk in enumerate(lists):
        if not chunk:
            continue
        list_path = out / f"_free-worker-{i}.json"
        list_path.write_text(json.dumps({"arms": chunk}), encoding="utf-8")
        procs.append(subprocess.Popen([
            sys.executable, "-m", "tests.diagnostic.widening.rhythm_band_probe",
            "--run-free-list", str(list_path),
        ]))
    failed = [c for c in (p.wait() for p in procs) if c != 0]
    if failed:
        print(f"batch-free failed, worker exits {failed}", flush=True)
        return 1
    print("batch-free done", flush=True)
    return score_free(out_dir)


def _run_free_list(list_path):
    from tests.diagnostic.widening.dial_census_probe import run_arm, _arm_path
    payload = json.loads(Path(list_path).read_text(encoding="utf-8"))
    for job in payload["arms"]:
        arm = run_arm(
            job["dim"], job["seed"], job["workload"], job["steps"],
            thresholds=job.get("thresholds"),
        )
        path = _arm_path(job["out"], job["workload"], job["dim"], job["seed"], job["steps"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(arm, indent=2, sort_keys=True), encoding="utf-8")
        _steps, counts = late_counts(arm)
        print(
            f"WROTE {path.name} late {counts} thresholds {arm['thresholds']['rhythm']}",
            flush=True,
        )
    return 0


def score_free(out_dir):
    """The pre-declared occupancy bars. Prints one line per arm."""
    from tests.diagnostic.widening.dial_census_probe import _load_arms
    arms = _load_arms(out_dir)
    if not arms:
        print(f"no free arms in {out_dir}")
        return 1
    fails = []
    by = {}
    for arm in arms:
        by.setdefault(arm["workload"], {}).setdefault(arm["dim"], []).append(arm)
    for workload in ("canonical", "wide"):
        got = {a["seed"] for a in by.get(workload, {}).get(128, [])}
        if got != set(PIN_SEEDS):
            fails.append(f"missing {workload} 128 controls, have {sorted(got)}")
        for dim in FIT_WIDTHS:
            got = {a["seed"] for a in by.get(workload, {}).get(dim, [])}
            if got != {42, 43, 44, 45, 46}:
                fails.append(f"missing {workload} d{dim}, have {sorted(got)}")
    # Control: canonical 128 late counts, exactly.
    for arm in by.get("canonical", {}).get(128, []):
        _n, counts = late_counts(arm)
        expect = CANON_128_LATE.get(arm["seed"])
        ok = counts == expect
        print(f"  control canonical d128 s{arm['seed']} {counts} expect {expect} {'OK' if ok else 'MISS'}")
        if not ok:
            fails.append(f"canonical 128 seed {arm['seed']} late counts {counts}")
    for arm in by.get("wide", {}).get(128, []):
        n, counts = late_counts(arm)
        ok = occupancy_ok("wide", counts, n)
        print(f"  control wide d128 s{arm['seed']} {counts} {'OK' if ok else 'MISS'}")
        if not ok:
            fails.append(f"wide 128 seed {arm['seed']} fails the wide bar {counts}")
    for workload in ("canonical", "wide"):
        for dim in FIT_WIDTHS:
            group = by.get(workload, {}).get(dim, [])
            fit = [a for a in group if a["seed"] in PIN_SEEDS]
            held = [a for a in group if a["seed"] not in PIN_SEEDS]
            fit_fracs = []
            for arm in fit + held:
                n, counts = late_counts(arm)
                ok = occupancy_ok(workload, counts, n)
                role = "fit" if arm["seed"] in PIN_SEEDS else "heldout"
                print(
                    f"  {role:7s} {workload} d{dim} s{arm['seed']} {counts} "
                    f"{'OK' if ok else 'MISS'}"
                )
                if not ok:
                    fails.append(f"{workload} d{dim} s{arm['seed']} {counts}")
                if workload == "canonical" and arm["seed"] in PIN_SEEDS:
                    fit_fracs.append(counts["explore"] / n)
            if workload == "canonical" and fit_fracs:
                mean = sum(fit_fracs) / len(fit_fracs)
                ok = canonical_mean_ok(fit_fracs)
                print(f"  mean    canonical d{dim} fit-seeds explore {mean:.6f} {'OK' if ok else 'MISS'}")
                if not ok:
                    fails.append(f"canonical d{dim} fit mean explore {mean:.6f}")
            held_fracs = []
            for arm in held:
                if workload != "canonical":
                    continue
                n, counts = late_counts(arm)
                held_fracs.append(counts["explore"] / n)
            if held_fracs:
                mean = sum(held_fracs) / len(held_fracs)
                ok = canonical_mean_ok(held_fracs)
                print(f"  mean    canonical d{dim} held-out explore {mean:.6f} {'OK' if ok else 'MISS'}")
                if not ok:
                    fails.append(f"canonical d{dim} held-out mean explore {mean:.6f}")
    if fails:
        print(f"OCCUPANCY FAIL ({len(fails)})")
        for f in fails:
            print(" ", f)
        return 2
    print("OCCUPANCY PASS")
    return 0


def _check():
    fails = []
    if FIELD_DIM != 128:
        fails.append(f"FIELD_DIM is {FIELD_DIM}")
    placed, err = place_from_eqs(13.0, 200.0, 293.0, 298.0)
    print(f"  formula on published F9: {placed} err={err}")
    if err:
        fails.append(err)
    elif abs(placed["reflect"] - 300) > 15 or abs(placed["dream"] - 150) > 30:
        fails.append(f"formula missed the F9 shape: {placed}")
    elif placed["stabilize"] != 5.0:
        fails.append("stabilize moved off 5 on the published numbers")
    # Defaults at the production width are the literal F9 set.
    if ResonanceField.DEFAULT_THRESHOLDS != {
        "stabilize": 5.0, "dream": 150.0, "reflect": 300.0,
    }:
        fails.append(f"DEFAULT_THRESHOLDS changed: {ResonanceField.DEFAULT_THRESHOLDS}")
    field = ResonanceField(dim=FIELD_DIM)
    if dict(field.thresholds) != dict(ResonanceField.DEFAULT_THRESHOLDS):
        fails.append(f"dim {FIELD_DIM} thresholds {field.thresholds}")
    if fails:
        for f in fails:
            print("FAIL", f)
        return 1
    print("PASS check")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description="Pinned rhythm equilibria and the placement rule.")
    p.add_argument("--check", action="store_true")
    p.add_argument("--batch-pin", metavar="DIR")
    p.add_argument("--run-list", metavar="PATH")
    p.add_argument("--decide", metavar="DIR")
    p.add_argument("--batch-free", nargs=2, metavar=("PLACEMENT", "DIR"))
    p.add_argument("--run-free-list", metavar="PATH")
    p.add_argument("--score-free", metavar="DIR")
    p.add_argument("--jobs", type=int, default=2)
    args = p.parse_args(argv)
    if args.check:
        return _check()
    if args.run_list:
        return _run_listed(args.run_list)
    if args.batch_pin:
        return _batch_pin(args.batch_pin, args.jobs)
    if args.run_free_list:
        return _run_free_list(args.run_free_list)
    if args.batch_free:
        return _batch_free(args.batch_free[0], args.batch_free[1], args.jobs)
    if args.score_free:
        return score_free(args.score_free)
    if args.decide:
        report = decide(args.decide)
        text = json.dumps(report, indent=2)
        out = Path(args.decide).parent / "placement.json"
        out.write_text(text, encoding="utf-8")
        print(text)
        print(f"WROTE {out}")
        return 0 if report.get("ship") else 2
    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
