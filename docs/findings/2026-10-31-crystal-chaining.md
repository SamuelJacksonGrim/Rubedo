# The crystal center does not walk. The 2–3 count is a shared direction, with a one-crystal wobble

- **Date:** 2026-10-31
- **Substrate:** live store, offers recorded once, geometry offline. Pretrained main boot (`build_engine`, 8-epoch corpus pretrain, eval, post-fork flags left on, dream channel off). Resonance Family, internal origin, seeds 42, 43, 44, 500 steps. CPU, CUDA hidden, 2 threads. Recorded on `86d5351`, before `5241a8c` restored the witness and stood the rhythm behaviours down on a refused step. The crystal call on an allowed step was not what that commit changed.
- **Probe:** `tests/diagnostic/crystal_chaining_probe.py`
- **Status:** standing
- **Depends on:** `2026-10-31-why-allow-rate-and-crystal-count` (the 2/2/3 count, and the open question this one sharpens)

## Question

Copilot's review of the crystal-count finding: if a merge moves the center, the store can chain. A absorbs B, the center drifts, then it is close enough to absorb C, though A and C are below 0.92. The final count would be small even if the offers spanned several threshold-separated regions. So "the cone holds 2–3 directions" might be manufactured by an updating, order-dependent merge rather than discovered.

The same review asked whether a tiny store is real consolidation or a large shared component in every vector.

## Pre-declared signatures

Written in the probe, and printed into the recording log, before the first seed. Not edited after the offers were recorded.

Chaining, if either is true on a seed's waking offers:

- Within-crystal split. An online crystal with two or more members contains a pair below cosine 0.92.
- Order move. Replaying those offers through `CrystalStore.maybe_crystallize` does not give the same final count on every fixed order: arrival, reverse, near-the-mean first, far-the-mean first, both directions of the first principal component, and 24 shuffles from numpy Generator seeds 0 through 23.

The boot chains if any seed does either.

Drift, named separately, and not implied by those two. The stored center moves: the largest L2 from the formation vector, measured after every assignment, is above 1e-5, and some member of that crystal is below 0.92 of the formation vector. Hub covering is a split without drift. The center stayed put and the ball still holds a pair the threshold would separate.

Frozen centers. A fresh `CrystalStore` replays the waking offers in arrival order. Later offers still merged against unmoved centers if that replay's labels equal the online labels.

Pairwise graph. An edge at cosine ≥ 0.92, scored as `_score_all` scores (L2 norm + 1e-8, then a dot). Connected components are the single-link clusters. Complete link merges two clusters only when every cross pair is ≥ 0.92; ties keep the smaller arrival id.

Threshold grid, fixed: 0.80, 0.85, 0.88, 0.90, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.98. The call uses the arrival-order real-merge count. A seed is on a plateau if that count is the same at 0.90, 0.91, 0.92, 0.93 and 0.94. A seed is a knife edge if the count at 0.91 differs from the count at 0.93. The boot is a plateau only if every seed is, and a knife edge if any seed is. Otherwise neither.

Anisotropy. Mean-centre the offers and renormalize. Separately, mean-centre, remove the first principal component, renormalize. Each transform's arrival-order count manufactures the small count if every seed at least doubles, partial if some do, and does not if none do. A row with residual norm below 1e-8 would drop that transform's call. The first component is large when it holds more than half the centered variance.

Identity, required before any call. Crystals 2/2/3, strict allow 0.550/0.602/0.560, waking clearers 266/277/280 (the prior finding's passer counts plus the first formation). Replay of the arrival order must reproduce the online labels, and an offer presented to a non-empty store must be a merge exactly when its recorded best cosine is ≥ 0.92. A three-vector toy (angles 0/18/36 degrees) must show the split, the order move, one component, complete-link 2, and an unmoved center, or the analysis is wrong and no call is made.

No constant was changed. `merge_threshold` stayed 0.92 in the source. The sweep built throwaway stores.

## Result (observed)

Identity matched on all three seeds. Allow rates 0.550 / 0.602 / 0.560. Waking clearers 266 / 277 / 280. Dream clearers 0. Rejects, first gate only, coherence / stability / relation: 55 / 172 / 7, 64 / 151 / 8, 92 / 124 / 4. Same figures as the prior finding. The live store's merge threshold was 0.92. The toy passed: one component, complete-link 2, real-merge counts 2 and 1, stored-center L2 0. Arrival-order replay reproduced the online labels on every seed. No center moved on any replay order either.

The store's vector does not change on a merge. Measured stored-center L2 is 0 on every crystal, and the stored vector's cosine to the formation vector is 1. Every member is at least 0.92 from its own pin. The weakest member-to-pin cosines are 0.983 and 0.928 (seed 42), 0.990 and 0.946 (seed 43), 0.941, 0.975 and 0.938 (seed 44).

| Seed | Online | Components | Complete link | Order counts | Split | Drift |
|---|---|---|---|---|---|---|
| 42 | 2 | 2 | 2 | 2 on all 30 orders | no | no |
| 43 | 2 | 2 | 3 | 2 or 3 (6 of 30 orders give 3) | yes | no |
| 44 | 3 | 2 | 4 | 2 or 3 (19 of 30 give 2; arrival gives 3) | yes | no |

Crystals, formation step, size, lowest pair, pairs below 0.92, centroid cosine to the pin:

- Seed 42. Step 101, size 2, lowest pair 0.983, none below. Step 237, size 264, lowest pair 0.928, none of 34,716 pairs below. Centroid cosines 0.996 and 0.954.
- Seed 43. Step 15, size 2, lowest pair 0.990, none below. Step 226, size 275, lowest pair 0.912, 168 of 37,675 pairs below. Centroid cosines 0.998 and 0.990. The pin still covers every member (weakest 0.946).
- Seed 44. Step 2, size 9, lowest pair 0.937, none below. Step 191, size 3, lowest pair 0.961, none below. Step 233, size 268, lowest pair 0.918, 3 of 35,778 pairs below. Centroid cosines 0.984, 0.994 and 0.986.

Pins of different crystals, and cross pairs at or above 0.92:

- Seed 42. Pins at 0.776. No cross pair reaches 0.92.
- Seed 43. Pins at 0.808. No cross pair reaches 0.92.
- Seed 44. Pins at 0.919, 0.764 and 0.776. Crystals 0 and 1, the two small ones, have 22 of 27 cross pairs at or above 0.92 (max 0.993). Nothing else crosses.

Arrival-order real-merge count across the grid:

| Threshold | 42 | 43 | 44 |
|---|---|---|---|
| 0.80 | 2 | 2 | 2 |
| 0.85, 0.88, 0.90 | 2 | 2 | 2 |
| 0.91 | 2 | 2 | 3 |
| 0.92 | 2 | 2 | 3 |
| 0.93 | 3 | 2 | 3 |
| 0.94 | 3 | 2 | 4 |
| 0.95 | 3 | 3 | 6 |
| 0.96 | 4 | 4 | 6 |
| 0.98 | 5 | 5 | 9 |

Seed 42 is not on the plateau band: 2, 2, 2, 3, 3. It is a knife edge, 2 at 0.91 against 3 at 0.93. Two members of its big crystal sit between 0.928 and 0.93 of the pin. Seed 43 is on the plateau: the replay count is 2 from 0.90 through 0.94, and no member is below 0.946 of its pin. Seed 44 is neither: 2, 3, 3, 3, 4 across the band, and 0.91 equals 0.93. Connected components stay at 2 from 0.85 through 0.94 on every seed. The boot call is knife edge, because one seed is.

Mean-centred offers, then the first component removed. No row was dropped.

| Seed | PC1 fraction | Mean-centre replay / components / complete | PC1 removed replay / components / complete |
|---|---|---|---|
| 42 | 0.529 | 18 / 5 / 28 | 156 / 132 / 169 |
| 43 | 0.474 | 18 / 8 / 26 | 87 / 73 / 98 |
| 44 | 0.473 | 27 / 8 / 38 | 35 / 18 / 51 |

Both transforms at least double every seed. The first component is large, by the declared half, on seed 42 only.

## Interpretation

The calls that were pre-declared, and that the identity match allows:

- Drift chain: no.
- Chaining: yes. Seeds 43 and 44 have a within-crystal pair below 0.92, and their real-merge count moves between 2 and 3 with order. Seed 42 does neither.
- Threshold: knife edge, not a plateau.
- Anisotropy: both the mean-centred offers and the offers with the first component removed manufacture the small count.

Copilot's mechanism is not this store. `MemoryCrystal.reinforce` updates stability, usage and the activation count. It does not write the vector. The measurement agrees: after every assignment the stored center is the formation vector, and a replay that never moves a center assigns every offer the way the live store did. Nothing was absorbed that the original pin would have refused. The member centroids stay inside the formation ball too. The worst centroid cosine is 0.954, on seed 42's big crystal. A center updated to the mean of its members would still sit well above 0.92 of the pin. The ball did not walk into a new region.

What did fire is thinner than the review's picture. The pairs below 0.92 are a rim: 168 of 37,675 on seed 43 (lowest 0.912), and 3 of 35,778 on seed 44 (lowest 0.918). Complete link, which refuses any such pair, raises the counts from 2/2/3 to 2/3/4. One extra cluster on two seeds, and none on the third. Order does the same size of thing. Six of thirty orders give seed 43 a third crystal. Nineteen of thirty give seed 44 two crystals instead of the arrival order's three, because that seed's two small pins sit at 0.919 and 22 of their 27 cross pairs clear 0.92. A center that had landed in the overlap would have covered both. The arrival order did not. The count moves by one crystal. It does not move from a dozen regions down to two.

The pairwise graph is the direct answer to "several threshold-separated regions." At 0.92 there are two components on every seed, and there are still two from 0.85 through 0.94. Seeds 42 and 43 have no edge between their crystals at all (pins at 0.776 and 0.808). The offers do not span a chain of regions that only the merge rule glued together. They span two regions, and the store's 2 or 3 is those two, plus, on seed 44, a second pin just outside 0.92 of the first.

The smallness that is manufactured is the shared direction, not the merge. Mean-centering and renormalizing, which throws away the common offset and scores the residuals, takes the arrival count from 2/2/3 to 18/18/27. Removing the first principal component as well takes it to 156/87/35, out of 266/277/280 offers. Seed 42's first component is 0.529 of the centered variance. The other two seeds sit just under the declared half, at 0.474 and 0.473, and the count still multiplies. In the cosine the store actually uses, those offers lie in two balls. A large part of why they lie there is a direction they share.

0.92 is a real step and a poor place to pretend there is a plateau. Seed 42 gains one crystal between 0.92 and 0.93, which is the two members at 0.928 of the pin, and that is enough for the pre-declared knife. It is not the radius that creates the 2–3. From 0.85 to 0.94 the replay count stays in 2–4, and the component count stays at 2. At 0.98 the counts are 5, 5 and 9, still not the cold cone's 12–15. Lowering 0.92 would not reveal hidden regions. Raising it by a few hundredths peels one crystal off a rim. For "same direction as this pin," 0.92 is about where this cone's own weakest member already sits (0.928, 0.946, 0.938). It is a radius of the data, not a knife that invented the data. It was not changed.

## Threats / confounds

- One recording. The geometry was computed offline from that file, not from a second boot.
- The window is 500 steps. The prior finding already showed the count flat from step 250 through 3,000, with every later step a merge. Those later offers were not in this file. A later offer could only join a crystal by clearing 0.92 of a frozen pin, so it could lower a within-crystal pair. It could not create a new crystal unless it missed every pin.
- Recorded on `86d5351`. `5241a8c` restores the witness anchor on a refused step and stands explore, reflect and the dreamer down. The crystal call on an allowed step is the same function. A refusal no longer moves the anchor, so a later allowed step's vector can differ. This probe was not re-run after that commit. The identity match is against the earlier boot.
- Attractor centers do move. `AttractorField.add` blends 0.9 of the old center with 0.1 of the new vector, and a later pass merges centers at 0.95. That is Copilot's update, on a different store, and this probe did not record it.
- Mean-centering and removing a component change the geometry on purpose. The call says what the count does in that geometry. It does not say the store is secretly running that geometry.
- Three seeds, one workload, the 46-token Resonance Family. Not the cold cone, not the wide room, not a conversation.
- The first component's sign is arbitrary. Both projection orders were in the order set.

## Open / next

- [ ] The cold eval cone's 12–15, under this same geometry. Components, complete link, and the count after the first component is removed. Not re-recorded here.
- [ ] Whether the attractor store, which does walk its centers, chains at 0.95. Not this probe.
- [x] Does a walking crystal center manufacture the pretrained 2–3? No. The center does not walk. → this file.
- [x] Do the offers span several regions that only an order-dependent merge glues together? No. Two components at 0.92, and order moves the count by one. → this file.
