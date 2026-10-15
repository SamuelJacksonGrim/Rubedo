"""
data/corpus/build_witness_v1_4_0.py

Corpus 1.4.0: add the sixth rhythm, witness (the receptive pole: perceive
without transforming), to the 1.3.0 corpus. The five existing rhythms are left
byte-identical; witness rows are appended to train and holdout.

Source: the grown witness set built for the encoder work, 1,181 sequences over
170 words, authored to the same rules as the rest of this corpus
(`v19_natural_angle.jsonl` in the encoder sweep; see authoring/witness.md and
witness_core.txt). Split ~15% holdout with a fixed seed, then repaired so the
gate holds: holdout vocabulary inside train vocabulary, every train token in
>= 8 distinct contexts, no sequence shared with another rhythm.

Run once (historical record of the build, like build_extension_v1_1_0.py):
    python data/corpus/build_witness_v1_4_0.py <path to v19_natural_angle.jsonl>
"""

import collections
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRAIN, HOLD = HERE / "rhythm_train.jsonl", HERE / "rhythm_holdout.jsonl"
SEED, HOLD_FRAC, MIN_CTX = 1188, 0.15, 8


def load(p):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def main(src):
    train, hold = load(TRAIN), load(HOLD)
    assert not any(r["rhythm"] == "witness" for r in train + hold), "witness already present"
    existing = {tuple(r["tokens"]) for r in train + hold}

    seen, wit = set(), []
    for r in load(Path(src)):
        if r["rhythm"] != "witness":
            continue
        k = tuple(r["tokens"])
        if k in seen or k in existing:
            continue
        seen.add(k)
        wit.append({"tokens": list(k), "rhythm": "witness"})

    rng = random.Random(SEED)
    rng.shuffle(wit)
    n_hold = round(len(wit) * HOLD_FRAC)
    w_hold, w_train = wit[:n_hold], wit[n_hold:]

    def contexts(rows):
        c = collections.defaultdict(set)
        for r in rows:
            for t in r["tokens"]:
                c[t].add(tuple(r["tokens"]))
        return c

    # repair: move holdout rows back to train until vocab closure + context floor hold
    for _ in range(len(wit)):
        ctx = contexts(train + w_train)
        bad = [r for r in w_hold if any(len(ctx.get(t, ())) < MIN_CTX for t in r["tokens"])]
        if not bad:
            break
        w_hold.remove(bad[0])
        w_train.append(bad[0])

    ctx = contexts(train + w_train)
    thin = sorted(t for t, v in ctx.items() if len(v) < MIN_CTX)
    if thin:
        dropped = [r for r in w_train if any(t in thin for t in r["tokens"])]
        raise SystemExit(f"witness tokens under {MIN_CTX} contexts even with all rows in train: {thin[:10]} "
                         f"({len(dropped)} rows) - author more rows first")

    with open(TRAIN, "a", encoding="utf-8") as f:
        for r in w_train:
            f.write(json.dumps(r) + "\n")
    with open(HOLD, "a", encoding="utf-8") as f:
        for r in w_hold:
            f.write(json.dumps(r) + "\n")
    print(f"witness: {len(wit)} unique -> train {len(w_train)} / holdout {len(w_hold)} "
          f"({len(w_hold) / len(wit):.3f}); totals train {len(train) + len(w_train)} "
          f"holdout {len(hold) + len(w_hold)}")


if __name__ == "__main__":
    main(sys.argv[1])
