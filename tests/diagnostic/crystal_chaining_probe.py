"""
tests/diagnostic/crystal_chaining_probe.py

Does the pretrained crystal store stay at 2-3 because a merge walks the
center and chains later offers in, or because the offers already sit in
that many balls of radius 0.92?

Informational. Exit 0. Not in run_all_tests.sh. Changes no constant.
The recording boot is prod_pretrain from why_allow_crystals_probe:
build_engine, 8-epoch corpus pretrain, eval, post-fork flags left on,
dream channel off (it is built in main(), not in build_engine), Resonance
Family, seeds 42, 43, 44, 500 steps. CPU, 2 threads.

Pre-declared, before the recording run (2026-10-31). The block below is
not edited after the offers are recorded.

CHAINING. The store chains if either of these is true on the recorded
waking offers of a seed:
  (1) Within-crystal split. An online crystal with two or more members
      contains a pair whose cosine is below 0.92. Membership was "near
      the center", and the crystal holds points the threshold would keep
      apart.
  (2) Order move. Replaying those offers through
      CrystalStore.maybe_crystallize (no field, no generator) does not
      give the same final count on every pre-declared order.

DRIFT, named separately. Copilot's mechanism is not implied by (1) or (2):
  (3) Drift chain. The stored center moves. The largest L2 between a
      crystal's vector and the vector it was formed with, measured after
      every assignment, is above 1e-5, AND some member of that crystal
      has cosine below 0.92 to the formation vector.

Hub covering is (1) without (3): a frozen center's ball contains a pair
below 0.92. The ball did not walk.

Across seeds, chaining is called if any seed shows (1) or (2). Drift is
called if any seed shows (3). Per-seed numbers are kept either way.

FROZEN CENTERS. A fresh CrystalStore replays the waking offers in arrival
order. This matches the online assignment if centers never moved, because
that replay is the store's own rule. "Later offers still merge" means
this replay's labels equal the online labels.

PAIRWISE GRAPH. Edge when cosine >= 0.92, scored as CrystalStore._score_all
scores: divide by L2 norm + 1e-8, then dot, on the offer vectors.
Connected components are the single-link clusters. Fewer components than
the online count means the threshold graph chains across crystals the
store kept apart.

COMPLETE LINK. Agglomerative. Start from one cluster per offer. Repeatedly
merge the two clusters whose minimum cross-pair cosine is highest, but
only when that minimum is >= 0.92. Ties break toward the smaller cluster
id, then the other id. Ids start as arrival indices; a merge keeps the
smaller id (the higher id is dropped). Every pair inside a finished
cluster is >= 0.92. A larger complete-link count than the online count
means the store grouped points this rule would not.

ORDERS, fixed:
  arrival; reverse;
  increasing cosine-distance from the mean of the offer set; decreasing;
  increasing projection on the first right singular vector of the
  mean-centred offers, as np.linalg.svd returns it; decreasing;
  24 shuffles, numpy Generator seeds 0 through 23
  (np.random.default_rng(s).permutation).
  Distance ties and projection ties break toward the lower arrival index.

THRESHOLD GRID, fixed:
  0.80, 0.85, 0.88, 0.90, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.98.
  The call uses the arrival-order real-merge count.
  A seed is on a plateau if that count is the same at 0.90, 0.91, 0.92,
  0.93 and 0.94. A seed is a knife edge if the count at 0.91 differs from
  the count at 0.93. The boot is a plateau only if every seed is. The boot
  is a knife edge if any seed is. Otherwise neither, and the grid stands.

CENTROID. Per online crystal: stored-center cosine between the final
stored vector and the formation vector; member-centroid cosine between
the normalized mean of the member vectors and the formation vector.
Travel is 1 minus that cosine. Lowest within-member cosine is the minimum
pairwise cosine, undefined for a crystal of one. Also report the fraction
of within-crystal pairs below 0.92.

ANISOTROPY. Two transforms of the waking offers, then the same
arrival-order real merge, the component count, and the complete-link
count, at 0.92:
  mean-centred: subtract the offer mean, L2-renormalize each row;
  dominant component removed: mean-centre, subtract the projection onto
  the first right singular vector, renormalize.
  A row whose residual norm is below 1e-8 is dropped. If any row is
  dropped, that transform does not get a call.
  Manufactures, if no row was dropped and every seed's arrival-order
  count at least doubles on that transform. Partial, if at least one
  seed doubles and not every seed. Does not, if no seed doubles.
  The fraction of centered variance on the first component is reported.
  That component is large when the fraction is above one half.

IDENTITY. The live store's merge threshold must round to 0.92 at 4
decimals. The prior finding's crystal counts were 2 / 2 / 3, its strict
allow rates 0.550 / 0.602 / 0.560, and its waking passer counts
265 / 276 / 279. Passers there exclude the offer that formed the first
crystal, so this probe's waking-clearer counts are 266 / 277 / 280 when
the runs are the same.
  MATCH: crystals, allow rates and clearer counts all agree.
  CLOSE: crystals and allow rates agree, clearer counts do not.
  MISS: crystals or allow rates disagree.
  The chaining, drift, plateau and anisotropy calls are made only on
  MATCH. CLOSE reports the numbers and names the discrepancy as a threat.
  MISS makes no call.

REPLAY INTEGRITY. On the online labels, an offer presented to a non-empty
store is a merge if and only if its recorded best cosine is >= 0.92, and
a formation otherwise. The first offer is a formation and has no cosine.
Arrival-order replay through CrystalStore must reproduce the online
labels. If either check fails, no call is made on that recording.

CONTROL. A three-vector toy, angles 0 / 18 / 36 degrees, so consecutive
cosines are cos(18 deg) and the ends are cos(36 deg). It must, before
the offers are interpreted: have one connected component at 0.92;
complete-link count 2; real-merge count 2 in order (0, 1, 2) and count 1
in order (1, 0, 2); the count-1 crystal must contain a pair below 0.92;
the stored center must not move (max L2 == 0) on either order. If the
toy fails, the analysis code is wrong and no call is made on the offers.

Run:
  python -m tests.diagnostic.crystal_chaining_probe --toy
  python -m tests.diagnostic.crystal_chaining_probe --record
  python -m tests.diagnostic.crystal_chaining_probe --analyse
"""
from __future__ import annotations

import argparse
import gzip
import io
import json
import sys
from pathlib import Path

import numpy as np

from substrate.memory_crystals import CrystalStore

ROOT = Path(__file__).resolve().parents[2]
OFFERS_PATH = ROOT / "docs" / "findings" / "data" / "2026-10-31-crystal-chaining-offers.npz.gz"
ANALYSIS_PATH = ROOT / "docs" / "findings" / "data" / "2026-10-31-crystal-chaining-analysis.json"

SEEDS = (42, 43, 44)
STEPS = 500
# Prior finding, prod_pretrain, 500 steps. Passers exclude the first formation.
EXPECT_CRYSTALS = {42: 2, 43: 2, 44: 3}
EXPECT_ALLOW = {42: 0.550, 43: 0.602, 44: 0.560}
EXPECT_CLEARERS = {42: 266, 43: 277, 44: 280}
GRID = (0.80, 0.85, 0.88, 0.90, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.98)
PLATEAU_BAND = (0.90, 0.91, 0.92, 0.93, 0.94)
MERGE = 0.92
SHUFFLE_SEEDS = tuple(range(24))


def pair_sim(vecs: np.ndarray) -> np.ndarray:
    """Cosine the way CrystalStore._score_all computes it."""
    x = np.asarray(vecs, dtype=np.float64)
    u = x / (np.linalg.norm(x, axis=1, keepdims=True) + 1e-8)
    return u @ u.T


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    return float(
        (a / (np.linalg.norm(a) + 1e-8)) @ (b / (np.linalg.norm(b) + 1e-8))
    )


def replay(vecs, coh, press, rel, threshold: float):
    """Real merge rule. Gate values are the ones the offer cleared with."""
    store = CrystalStore(merge_threshold=float(threshold))
    labels = np.empty(len(vecs), dtype=np.int32)
    formed_at = {}
    max_l2 = {}
    id_map = {}
    for i, v in enumerate(vecs):
        out = store.maybe_crystallize(
            np.asarray(v, dtype=np.float64),
            float(coh[i]),
            float(press[i]),
            float(rel[i]),
        )
        if out is None:
            labels[i] = -1
            continue
        if id(out) not in id_map:
            cid = len(id_map)
            id_map[id(out)] = cid
            formed_at[cid] = out.vector.copy()
            max_l2[cid] = 0.0
        cid = id_map[id(out)]
        delta = float(np.linalg.norm(
            out.vector.astype(np.float64) - formed_at[cid].astype(np.float64)
        ))
        if delta > max_l2[cid]:
            max_l2[cid] = delta
        labels[i] = cid
    return labels, len(store.crystals), max_l2


def component_count(sim: np.ndarray, threshold: float) -> int:
    n = sim.shape[0]
    parent = np.arange(n)

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = int(parent[x])
        return x

    iu = np.triu_indices(n, k=1)
    take = sim[iu] >= threshold
    for a, b in zip(iu[0][take], iu[1][take]):
        ra, rb = find(int(a)), find(int(b))
        if ra != rb:
            parent[rb] = ra
    return len({find(i) for i in range(n)})


def complete_link_count(sim: np.ndarray, threshold: float) -> int:
    """Agglomerative complete link. Tie = first max in row-major order, which
    is the smaller id, then the other id, and the merge keeps the smaller id.
    """
    n = sim.shape[0]
    link = np.array(sim, dtype=np.float64, copy=True)
    np.fill_diagonal(link, -np.inf)
    alive = np.ones(n, dtype=bool)
    n_clusters = n
    while n_clusters > 1:
        masked = link.copy()
        dead = ~alive
        masked[dead, :] = -np.inf
        masked[:, dead] = -np.inf
        flat = int(np.argmax(masked))
        i, j = divmod(flat, n)
        if i > j:
            i, j = j, i
        m = float(masked[i, j])
        if (not np.isfinite(m)) or m < threshold:
            break
        both = np.minimum(link[i], link[j])
        both[i] = -np.inf
        both[j] = -np.inf
        link[i, :] = both
        link[:, i] = both
        link[j, :] = -np.inf
        link[:, j] = -np.inf
        alive[j] = False
        n_clusters -= 1
    return int(n_clusters)


def _toy_vectors() -> np.ndarray:
    deg = np.deg2rad(np.array([0.0, 18.0, 36.0]))
    return np.stack([np.cos(deg), np.sin(deg)], axis=1)


def run_toy() -> dict:
    vecs = _toy_vectors()
    sim = pair_sim(vecs)
    gates = np.ones(3)
    lab_abc, n_abc, l2_abc = replay(vecs, gates, gates, gates, MERGE)
    order = np.array([1, 0, 2])
    lab_bac, n_bac, l2_bac = replay(vecs[order], gates, gates, gates, MERGE)
    # Members of the single crystal in BAC order, mapped back to angles.
    split = bool(n_bac == 1 and float(sim[0, 2]) < MERGE)
    ok = (
        component_count(sim, MERGE) == 1
        and complete_link_count(sim, MERGE) == 2
        and n_abc == 2
        and n_bac == 1
        and split
        and max(l2_abc.values(), default=0.0) == 0.0
        and max(l2_bac.values(), default=0.0) == 0.0
        and int((lab_abc < 0).sum()) == 0
        and int((lab_bac < 0).sum()) == 0
    )
    return {
        "ok": ok,
        "cos_0_18": round(float(sim[0, 1]), 6),
        "cos_18_36": round(float(sim[1, 2]), 6),
        "cos_0_36": round(float(sim[0, 2]), 6),
        "components": component_count(sim, MERGE),
        "complete_link": complete_link_count(sim, MERGE),
        "replay_abc": n_abc,
        "replay_bac": n_bac,
        "max_l2_abc": max(l2_abc.values(), default=0.0),
        "max_l2_bac": max(l2_bac.values(), default=0.0),
    }


def orders_for(vecs: np.ndarray) -> dict:
    n = len(vecs)
    idx = np.arange(n)
    mean = vecs.mean(axis=0)
    cos_mean = pair_sim(np.vstack([vecs, mean[None, :]]))[:-1, -1]
    # Increasing distance = decreasing cosine to the mean.
    near = np.lexsort((idx, -cos_mean))
    far = np.lexsort((idx, cos_mean))
    centered = vecs - mean
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    proj = centered @ vt[0]
    pc_up = np.lexsort((idx, proj))
    pc_down = np.lexsort((idx, -proj))
    out = {
        "arrival": idx,
        "reverse": idx[::-1].copy(),
        "near_mean_first": near,
        "far_mean_first": far,
        "pc1_increasing": pc_up,
        "pc1_decreasing": pc_down,
    }
    for s in SHUFFLE_SEEDS:
        out[f"shuffle_{s}"] = np.random.default_rng(s).permutation(n)
    return out


def mean_center(vecs: np.ndarray):
    xc = np.asarray(vecs, dtype=np.float64)
    xc = xc - xc.mean(axis=0)
    norms = np.linalg.norm(xc, axis=1)
    keep = norms >= 1e-8
    out = np.zeros_like(xc)
    out[keep] = xc[keep] / norms[keep, None]
    return out, int((~keep).sum())


def remove_pc1(vecs: np.ndarray):
    x = np.asarray(vecs, dtype=np.float64)
    xc = x - x.mean(axis=0)
    _, s, vt = np.linalg.svd(xc, full_matrices=False)
    var = s ** 2
    frac = float(var[0] / var.sum()) if float(var.sum()) > 0 else 0.0
    resid = xc - np.outer(xc @ vt[0], vt[0])
    norms = np.linalg.norm(resid, axis=1)
    keep = norms >= 1e-8
    out = np.zeros_like(resid)
    out[keep] = resid[keep] / norms[keep, None]
    return out, frac, int((~keep).sum())


def _round(x, n=6):
    if x is None:
        return None
    return round(float(x), n)


def crystal_geometry(vecs, labels, formation, final, max_l2) -> list:
    sim = pair_sim(vecs)
    rows = []
    for cid in range(int(labels.max()) + 1 if len(labels) else 0):
        members = np.where(labels == cid)[0]
        n = int(len(members))
        if n >= 2:
            sub = sim[np.ix_(members, members)]
            iu = np.triu_indices(n, k=1)
            pairs = sub[iu]
            min_pair = float(pairs.min())
            n_pairs = int(len(pairs))
            n_below = int((pairs < MERGE).sum())
        else:
            min_pair = None
            n_pairs = 0
            n_below = 0
        pin = formation[cid]
        to_pin = np.array([cosine(vecs[i], pin) for i in members])
        centroid = vecs[members].mean(axis=0)
        rows.append({
            "crystal": cid,
            "n": n,
            "min_pair": _round(min_pair),
            "n_pairs": n_pairs,
            "n_pairs_below_0_92": n_below,
            "min_to_pin": _round(float(to_pin.min()) if n else None),
            "stored_center_l2": _round(max_l2.get(cid, 0.0), 8),
            "stored_center_cosine": _round(cosine(final[cid], pin)),
            "centroid_cosine": _round(cosine(centroid, pin)),
            "centroid_travel": _round(1.0 - cosine(centroid, pin)),
        })
    return rows


def sweep(vecs, coh, press, rel) -> list:
    sim = pair_sim(vecs)
    rows = []
    for t in GRID:
        _, n, _ = replay(vecs, coh, press, rel, t)
        rows.append({
            "threshold": t,
            "replay": n,
            "components": component_count(sim, t),
            "complete_link": complete_link_count(sim, t),
        })
    return rows


def transform_counts(vecs, coh, press, rel, dropped: int) -> dict:
    if dropped or len(vecs) == 0:
        return {"dropped": dropped, "called": False}
    sim = pair_sim(vecs)
    _, n, _ = replay(vecs, coh, press, rel, MERGE)
    return {
        "dropped": 0,
        "called": True,
        "replay": n,
        "components": component_count(sim, MERGE),
        "complete_link": complete_link_count(sim, MERGE),
    }


def analyse_seed(seed: int, pack: dict) -> dict:
    wake = pack["wake"].astype(bool)
    # Primary set is waking clearers, in the order the store saw them.
    vecs = pack["vec"][wake]
    coh = pack["coh"][wake]
    press = pack["press"][wake]
    rel = pack["rel"][wake]
    online = pack["crystal"][wake].astype(np.int32)
    best = pack["best_cos"][wake]
    formed = pack["formed"][wake].astype(bool)
    sim = pair_sim(vecs)
    lab, n_replay, _ = replay(vecs, coh, press, rel, MERGE)
    integrity = True
    if len(vecs):
        if not (bool(formed[0]) and int(online[0]) == 0):
            integrity = False
        if not np.isnan(best[0]):
            integrity = False
        for i in range(1, len(vecs)):
            merged = (not formed[i]) and best[i] >= MERGE
            new = formed[i] and best[i] < MERGE
            if not (merged or new):
                integrity = False
                break
    labels_match = bool(np.array_equal(lab, online) and n_replay == int(online.max()) + 1) if len(online) else True
    if int((lab < 0).sum()):
        labels_match = False

    named = orders_for(vecs)
    order_counts = {}
    for name, perm in named.items():
        _, n, l2 = replay(vecs[perm], coh[perm], press[perm], rel[perm], MERGE)
        order_counts[name] = {"n": n, "max_l2": max(l2.values(), default=0.0)}
    counts = [v["n"] for v in order_counts.values()]
    distinct = sorted(set(counts))

    grid = sweep(vecs, coh, press, rel)
    by_t = {row["threshold"]: row["replay"] for row in grid}
    plateau = len({by_t[t] for t in PLATEAU_BAND}) == 1
    knife = by_t[0.91] != by_t[0.93]

    geom = crystal_geometry(
        vecs, online, pack["formation"], pack["final"], pack["max_l2"],
    )
    wake_steps = pack["step"][wake]
    for g in geom:
        members = np.where(online == g["crystal"])[0]
        founders = members[formed[members]] if len(members) else members
        g["form_step"] = int(wake_steps[founders[0]]) if len(founders) else None
    # The call uses the unrounded pairs. The printed min is rounded.
    split = False
    for cid in range(int(online.max()) + 1 if len(online) else 0):
        members = np.where(online == cid)[0]
        if len(members) < 2:
            continue
        sub = sim[np.ix_(members, members)]
        iu = np.triu_indices(len(members), k=1)
        if float(sub[iu].min()) < MERGE:
            split = True
            break
    drift = any(
        g["stored_center_l2"] is not None and g["stored_center_l2"] > 1e-5
        and g["min_to_pin"] is not None and g["min_to_pin"] < MERGE
        for g in geom
    )
    # stored_center_l2 in geom is rounded to 1e-8. The call uses the raw max.
    raw_drift = False
    for cid, raw in pack["max_l2"].items():
        members = np.where(online == cid)[0]
        if raw > 1e-5 and len(members):
            pin = pack["formation"][cid]
            if min(cosine(vecs[i], pin) for i in members) < MERGE:
                raw_drift = True

    mc_vecs, mc_drop = mean_center(vecs)
    pc_vecs, pc_frac, pc_drop = remove_pc1(vecs)
    mc = transform_counts(mc_vecs[np.linalg.norm(mc_vecs, axis=1) > 0] if mc_drop else mc_vecs,
                          coh, press, rel, mc_drop)
    # Keep every row when nothing was dropped. A dropped row must not be
    # replayed against a gate list of a different length.
    if mc_drop:
        mc = {"dropped": mc_drop, "called": False}
    pc = transform_counts(pc_vecs, coh, press, rel, pc_drop)

    allow = round(float(pack["allow_rate"]), 4)
    n_clear = int(wake.sum())
    n_crystals = int(pack["crystals_end"])
    identity = "MISS"
    if n_crystals == EXPECT_CRYSTALS[seed] and allow == EXPECT_ALLOW[seed]:
        identity = "MATCH" if n_clear == EXPECT_CLEARERS[seed] else "CLOSE"

    shuffle_counts = [order_counts[f"shuffle_{s}"]["n"] for s in SHUFFLE_SEEDS]
    return {
        "seed": seed,
        "identity": identity,
        "allow_rate": allow,
        "crystals_end": n_crystals,
        "wake_clearers": n_clear,
        "dream_clearers": int((~wake).sum()) if len(pack["wake"]) else 0,
        "wake_reject": pack["wake_reject"],
        "merge_threshold": pack["merge_threshold"],
        "integrity_ok": bool(integrity),
        "replay_matches_online": bool(labels_match),
        "calls_allowed": bool(identity == "MATCH" and integrity and labels_match),
        "online_count": n_crystals,
        "components": component_count(sim, MERGE) if len(vecs) else 0,
        "complete_link": complete_link_count(sim, MERGE) if len(vecs) else 0,
        "order_min": min(counts) if counts else None,
        "order_max": max(counts) if counts else None,
        "order_distinct": distinct,
        "order_counts": {k: v["n"] for k, v in order_counts.items()},
        "shuffle_min": min(shuffle_counts) if shuffle_counts else None,
        "shuffle_max": max(shuffle_counts) if shuffle_counts else None,
        "any_replay_center_moved": any(v["max_l2"] > 1e-5 for v in order_counts.values()),
        "plateau": plateau,
        "knife": knife,
        "grid": grid,
        "within_crystal_split": bool(split),
        "drift_chain": bool(raw_drift),
        "crystals": geom,
        "pc1_variance_fraction": round(pc_frac, 4),
        "pc1_large": bool(pc_frac > 0.5),
        "mean_centred": mc,
        "pc1_removed": pc,
    }


def _calls(rows: list) -> dict:
    allowed = [r for r in rows if r["calls_allowed"]]
    if len(allowed) != len(rows) or not rows:
        return {
            "made": False,
            "reason": "identity, integrity or replay match failed",
        }
    chaining = any(r["within_crystal_split"] or len(r["order_distinct"]) > 1 for r in allowed)
    drift = any(r["drift_chain"] for r in allowed)
    plateau = all(r["plateau"] for r in allowed)
    knife = any(r["knife"] for r in allowed)

    def anisotropy(key):
        arms = [r[key] for r in allowed]
        if any(not a.get("called") for a in arms):
            return "not_called"
        doubled = [
            a["replay"] >= 2 * r["online_count"]
            for r, a in zip(allowed, arms)
        ]
        if all(doubled):
            return "manufactures"
        if any(doubled):
            return "partial"
        return "does_not"

    return {
        "made": True,
        "chaining": chaining,
        "drift_chain": drift,
        "within_crystal_split": any(r["within_crystal_split"] for r in allowed),
        "order_move": any(len(r["order_distinct"]) > 1 for r in allowed),
        "plateau": plateau,
        "knife_edge": knife,
        "threshold_call": "plateau" if plateau else ("knife_edge" if knife else "neither"),
        "mean_centred": anisotropy("mean_centred"),
        "pc1_removed": anisotropy("pc1_removed"),
    }


def load_offers(path: Path) -> dict:
    with gzip.open(path, "rb") as fh:
        blob = io.BytesIO(fh.read())
    z = np.load(blob, allow_pickle=False)
    meta = json.loads(bytes(z["meta_json"]).decode("utf-8"))
    packs = {}
    for seed in meta["seeds"]:
        p = f"s{seed}_"
        formation = z[p + "formation"]
        final = z[p + "final"]
        max_l2 = {}
        # crystal ids are 0..k-1 in formation order
        for i, value in enumerate(z[p + "max_l2"]):
            max_l2[i] = float(value)
        packs[seed] = {
            "vec": z[p + "vec"],
            "wake": z[p + "wake"],
            "step": z[p + "step"],
            "crystal": z[p + "crystal"],
            "formed": z[p + "formed"],
            "best_cos": z[p + "best_cos"],
            "coh": z[p + "coh"],
            "press": z[p + "press"],
            "rel": z[p + "rel"],
            "formation": formation,
            "final": final,
            "max_l2": max_l2,
            "allow_rate": meta["seeds_meta"][str(seed)]["allow_rate"],
            "crystals_end": meta["seeds_meta"][str(seed)]["crystals_end"],
            "wake_reject": meta["seeds_meta"][str(seed)]["wake_reject"],
            "merge_threshold": meta["seeds_meta"][str(seed)]["merge_threshold"],
        }
    z.close()
    return {"meta": meta, "packs": packs}


def save_offers(path: Path, meta: dict, packs: dict) -> None:
    arrays = {
        "meta_json": np.frombuffer(json.dumps(meta).encode("utf-8"), dtype=np.uint8).copy(),
    }
    for seed, pack in packs.items():
        p = f"s{seed}_"
        for key in ("vec", "wake", "step", "crystal", "formed", "best_cos", "coh", "press", "rel",
                    "formation", "final", "max_l2"):
            arrays[p + key] = pack[key]
    buf = io.BytesIO()
    np.savez_compressed(buf, **arrays)
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wb") as fh:
        fh.write(buf.getvalue())


def cmd_toy() -> int:
    toy = run_toy()
    print(json.dumps(toy, sort_keys=True), flush=True)
    if not toy["ok"]:
        print("TOY_FAILED", flush=True)
        return 1
    print("TOY_OK", flush=True)
    return 0


def cmd_record(args) -> int:
    import logging
    import os
    import random

    # This probe is a CPU read. Hide the GPU before torch is imported.
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    os.environ.setdefault("OMP_NUM_THREADS", "2")
    os.environ.setdefault("MKL_NUM_THREADS", "2")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
    logging.disable(logging.CRITICAL)

    import torch

    from loop.recursion1188 import CONFIG, build_engine
    from substrate import determinism
    from tests._common import RESONANCE_FAMILY_SOURCES, RESONANCE_FAMILY_WEIGHTS

    torch.set_num_threads(int(os.environ.get("OMP_NUM_THREADS", "2")))
    print(
        "PREDECLARED chaining = a within-crystal pair below cosine 0.92, "
        "or the real-merge count moving on the fixed order set. "
        "Drift is separate: stored-center L2 > 1e-5 and a member below 0.92 "
        "of the formation vector. Calls require identity MATCH with "
        "crystals 2/2/3, allow 0.550/0.602/0.560, clearers 266/277/280.",
        flush=True,
    )
    print(f"device check: cuda_visible={os.environ.get('CUDA_VISIBLE_DEVICES')!r} "
          f"threads={torch.get_num_threads()}", flush=True)

    seeds = [int(s) for s in args.seeds.split(",") if s.strip()]
    steps = args.steps
    all_packs = {}
    seeds_meta = {}

    for seed in seeds:
        print(f"--- record seed {seed} steps {steps}", flush=True)
        with determinism.deterministic(seed):
            cfg = dict(CONFIG)
            cfg["pretrain_on_corpus"] = True
            cfg["log_interval"] = 99999
            cfg["step_delay"] = 0
            gen, cycle, gov, _ve = build_engine(cfg)
            if getattr(cycle, "dreamer", None) is not None:
                cycle.dreamer._rng = np.random.default_rng(seed)

            store = cycle.crystal_store
            rows = {
                "vec": [], "wake": [], "step": [], "crystal": [], "formed": [],
                "best_cos": [], "coh": [], "press": [], "rel": [],
            }
            id_map = {}
            formation = {}
            max_l2 = {}
            wake_reject = {"coherence": 0, "stability": 0, "relation": 0}
            decisions = {}
            orig_mc = store.maybe_crystallize

            def maybe_crystallize(vec, composite_coherence, crystallization_pressure,
                                  long_relation, origin_tokens=None, field=None, generator=None,
                                  _orig=orig_mc, _store=store, _rows=rows, _id=id_map,
                                  _form=formation, _l2=max_l2, _rej=wake_reject):
                dream = bool(origin_tokens) and str(origin_tokens[0]).startswith("dream_")
                ok_c = composite_coherence >= _store.coherence_threshold
                ok_s = crystallization_pressure >= _store.stability_threshold
                ok_r = long_relation >= _store.relation_threshold
                if not (ok_c and ok_s and ok_r):
                    if not dream:
                        if not ok_c:
                            _rej["coherence"] += 1
                        elif not ok_s:
                            _rej["stability"] += 1
                        else:
                            _rej["relation"] += 1
                    return _orig(
                        vec, composite_coherence, crystallization_pressure, long_relation,
                        origin_tokens=origin_tokens, field=field, generator=generator,
                    )
                saved = np.asarray(vec, dtype=np.float64).copy()
                cos = None
                if _store.crystals:
                    cos = max(s for _, s in _store._score_all(vec))
                out = _orig(
                    vec, composite_coherence, crystallization_pressure, long_relation,
                    origin_tokens=origin_tokens, field=field, generator=generator,
                )
                if out is None:
                    return out
                if id(out) not in _id:
                    cid = len(_id)
                    _id[id(out)] = cid
                    _form[cid] = out.vector.copy()
                    _l2[cid] = 0.0
                cid = _id[id(out)]
                delta = float(np.linalg.norm(
                    out.vector.astype(np.float64) - _form[cid].astype(np.float64)
                ))
                if delta > _l2[cid]:
                    _l2[cid] = delta
                # This id is new to the recording iff no earlier clearer landed in it.
                formed = sum(1 for c in _rows["crystal"] if c == cid) == 0
                _rows["vec"].append(saved)
                _rows["wake"].append(0 if dream else 1)
                _rows["step"].append(int(_rows.get("_step", 0)))
                _rows["crystal"].append(cid)
                _rows["formed"].append(1 if formed else 0)
                _rows["best_cos"].append(np.nan if cos is None else float(cos))
                _rows["coh"].append(float(composite_coherence))
                _rows["press"].append(float(crystallization_pressure))
                _rows["rel"].append(float(long_relation))
                return out

            store.maybe_crystallize = maybe_crystallize
            orig_arb = gov.arbitrate

            def counted(ethical_result, trust_report, vec, tokens, source_id, _orig=orig_arb):
                dec, strength = _orig(ethical_result, trust_report, vec, tokens, source_id)
                decisions[dec.value] = decisions.get(dec.value, 0) + 1
                return dec, strength

            gov.arbitrate = counted
            random.seed(seed)
            np.random.seed(seed)
            sids = list(RESONANCE_FAMILY_SOURCES.keys())
            weights = [RESONANCE_FAMILY_WEIGHTS[s] for s in sids]
            try:
                for i in range(steps):
                    rows["_step"] = i + 1
                    src = random.choices(sids, weights=weights)[0]
                    tokens = random.choice(RESONANCE_FAMILY_SOURCES[src])
                    cycle.step(tokens, source_id=src, origin_type="internal")
            finally:
                gov.arbitrate = orig_arb
                store.maybe_crystallize = orig_mc

            k = len(formation)
            dim = next(iter(formation.values())).shape[0] if formation else 0
            formation_m = np.zeros((k, dim), dtype=np.float32)
            final_m = np.zeros_like(formation_m)
            # Final vectors keyed by object id, not by list position.
            id_of = {id(c): id_map[id(c)] for c in store.crystals if id(c) in id_map}
            for c in store.crystals:
                if id(c) not in id_of:
                    continue
                cid = id_of[id(c)]
                final_m[cid] = c.vector.astype(np.float32)
                delta = float(np.linalg.norm(
                    c.vector.astype(np.float64) - formation[cid].astype(np.float64)
                ))
                if delta > max_l2[cid]:
                    max_l2[cid] = delta
            for cid, vec in formation.items():
                formation_m[cid] = vec.astype(np.float32)

            total = sum(decisions.values()) or 1
            allow = decisions.get("allow", 0) / total
            vecs = np.stack(rows["vec"]) if rows["vec"] else np.zeros((0, 1), dtype=np.float64)
            pack = {
                "vec": vecs,
                "wake": np.asarray(rows["wake"], dtype=np.uint8),
                "step": np.asarray(rows["step"], dtype=np.int32),
                "crystal": np.asarray(rows["crystal"], dtype=np.int16),
                "formed": np.asarray(rows["formed"], dtype=np.uint8),
                "best_cos": np.asarray(rows["best_cos"], dtype=np.float64),
                "coh": np.asarray(rows["coh"], dtype=np.float64),
                "press": np.asarray(rows["press"], dtype=np.float64),
                "rel": np.asarray(rows["rel"], dtype=np.float64),
                "formation": formation_m,
                "final": final_m,
                "max_l2": np.asarray([max_l2[i] for i in range(k)], dtype=np.float64),
            }
            wake_n = int(pack["wake"].sum()) if len(pack["wake"]) else 0
            dream_n = int(len(pack["wake"]) - wake_n)
            meta_row = {
                "allow_rate": round(allow, 4),
                "decisions": decisions,
                "crystals_end": len(store.crystals),
                "wake_clearers": wake_n,
                "dream_clearers": dream_n,
                "wake_reject": wake_reject,
                "merge_threshold": float(store.merge_threshold),
                "training": bool(gen.training),
                "dim": int(cfg["dim"]),
            }
            seeds_meta[str(seed)] = meta_row
            all_packs[seed] = pack
            print(
                f"RESULT seed={seed} allow={meta_row['allow_rate']:.3f} "
                f"crystals={meta_row['crystals_end']} wake_clearers={wake_n} "
                f"dream_clearers={dream_n} reject={wake_reject} train={meta_row['training']}",
                flush=True,
            )

    meta = {
        "seeds": list(seeds),
        "steps": steps,
        "boot": "build_engine prod_pretrain",
        "seeds_meta": seeds_meta,
    }
    save_offers(OFFERS_PATH, meta, all_packs)
    print(f"WROTE {OFFERS_PATH}", flush=True)
    print("DONE_RECORD", flush=True)
    return 0


def cmd_analyse(args) -> int:
    toy = run_toy()
    print("TOY " + json.dumps(toy, sort_keys=True), flush=True)
    if not toy["ok"]:
        print("TOY_FAILED", flush=True)
        return 1
    loaded = load_offers(Path(args.offers) if args.offers else OFFERS_PATH)
    rows = [analyse_seed(seed, loaded["packs"][seed]) for seed in loaded["meta"]["seeds"]]
    # Round-trip the complete-link count once, so a non-deterministic SVD
    # tie is not what the call sits on. The count itself is a pure function
    # of the similarity matrix.
    for row, seed in zip(rows, loaded["meta"]["seeds"]):
        pack = loaded["packs"][seed]
        vecs = pack["vec"][pack["wake"].astype(bool)]
        if len(vecs):
            sim = pair_sim(vecs)
            again = complete_link_count(sim, MERGE)
            if again != row["complete_link"]:
                row["calls_allowed"] = False
                row["complete_link_unstable"] = True
    out = {
        "toy": toy,
        "seeds": rows,
        "calls": _calls(rows),
    }
    path = Path(args.out) if args.out else ANALYSIS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"WROTE {path}", flush=True)
    print("CALLS " + json.dumps(out["calls"], sort_keys=True), flush=True)
    for row in rows:
        print(
            f"SEED {row['seed']} identity={row['identity']} "
            f"online={row['online_count']} components={row['components']} "
            f"complete={row['complete_link']} order={row['order_min']}..{row['order_max']} "
            f"split={row['within_crystal_split']} drift={row['drift_chain']} "
            f"pc1={row['pc1_variance_fraction']} "
            f"plateau={row['plateau']} knife={row['knife']}",
            flush=True,
        )
    print("DONE_ANALYSE", flush=True)
    return 0


def main(argv) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--toy", action="store_true")
    p.add_argument("--record", action="store_true")
    p.add_argument("--analyse", action="store_true")
    p.add_argument("--seeds", default="42,43,44")
    p.add_argument("--steps", type=int, default=STEPS)
    p.add_argument("--offers", default="")
    p.add_argument("--out", default="")
    args = p.parse_args(argv)
    if args.toy:
        return cmd_toy()
    if args.record:
        return cmd_record(args)
    if args.analyse:
        return cmd_analyse(args)
    p.error("one of --toy, --record, --analyse")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
