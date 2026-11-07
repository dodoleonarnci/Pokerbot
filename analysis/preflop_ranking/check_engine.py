"""Check the C evaluator against eval7, and the keep table against known hold'em equities."""
import random
import subprocess
import sys

import eval7
import numpy as np

RANKS, SUITS = "23456789TJQKA", "cdhs"
CARD = [eval7.Card(r + s) for r in RANKS for s in SUITS]


def check_evaluator(n=2_000_000):
    rng = random.Random(1)
    hands = [rng.sample(range(52), 7) for _ in range(n)]
    # Force rarer categories: many hands drawn from one suit or few ranks.
    for _ in range(n // 4):
        pool = rng.sample(range(13), 4)
        cards = [r * 4 + s for r in pool for s in range(4)]
        hands.append(rng.sample(cards, 7))
    for _ in range(n // 4):
        suit = rng.randrange(4)
        cards = [r * 4 + suit for r in range(13)] + rng.sample(range(52), 8)
        hands.append(rng.sample(sorted(set(cards)), 7))
    text = "\n".join(" ".join(map(str, h)) for h in hands)
    mine = subprocess.run(["./eq", "check"], input=text, capture_output=True, text=True, check=True).stdout.split()
    mine = np.array(mine, dtype=np.int64)
    theirs = np.array([eval7.evaluate([CARD[c] for c in h]) for h in hands], dtype=np.int64)
    order = np.argsort(theirs, kind="stable")
    a, b = theirs[order], mine[order]
    same = a[1:] == a[:-1]
    bad_eq = int(np.sum(same & (b[1:] != b[:-1])))
    bad_ord = int(np.sum(~same & (b[1:] <= b[:-1])))
    print(f"evaluator: {len(hands):,} hands, {len(set(a.tolist())):,} distinct values, "
          f"tie mismatches {bad_eq}, order mismatches {bad_ord}")
    return bad_eq == 0 and bad_ord == 0


def combos(label):
    a, b = RANKS.index(label[0]), RANKS.index(label[1])
    if a == b:
        return [(a * 4 + s, a * 4 + t) for s in range(4) for t in range(s + 1, 4)]
    if label[2] == "s":
        return [(a * 4 + s, b * 4 + s) for s in range(4)]
    return [(a * 4 + s, b * 4 + t) for s in range(4) for t in range(4) if s != t]


def check_table(path):
    """Averaging a hold'em hand's keep equity over all flops must give its known preflop equity."""
    tab = np.fromfile(path, dtype=np.float32).reshape(1755, 1326)
    hole = {}
    n = 0
    for a in range(52):
        for b in range(a + 1, 52):
            hole[(a, b)] = hole[(b, a)] = n
            n += 1
    perms = __import__("itertools").permutations(range(4))
    perms = list(perms)
    canon, weight = {}, np.zeros(1755)
    # Rebuild classes the same way as eq.c so that any mismatch in the mapping shows up here.
    flops = list(__import__("itertools").combinations(range(52), 3))
    flop_id = {f: i for i, f in enumerate(flops)}
    cls_of, perm_of = {}, {}
    for f in flops:
        best, bp = None, None
        for p in perms:
            image = tuple(sorted((c & ~3) | p[c & 3] for c in f))
            if best is None or flop_id[image] < best:
                best, bp = flop_id[image], p
        if best not in canon:
            canon[best] = len(canon)
        cls_of[f], perm_of[f] = canon[best], bp
    known = {"AA": .8520, "KK": .8240, "AKs": .6704, "AKo": .6532, "TT": .7502,
             "22": .5033, "72o": .3460, "32o": .3232}
    ok = True
    for label, want in known.items():
        total, count = 0.0, 0
        for x, y in combos(label):
            for f in flops:
                if x in f or y in f:
                    continue
                p = perm_of[f]
                u, v = (x & ~3) | p[x & 3], (y & ~3) | p[y & 3]
                total += float(tab[cls_of[f], hole[(u, v)]])
                count += 1
        got = total / count
        flag = "ok" if abs(got - want) < 0.0005 else "MISMATCH"
        ok &= flag == "ok"
        print(f"table: {label:4s} {got:.4f}  published {want:.4f}  {flag}")
    return ok


if __name__ == "__main__":
    good = check_evaluator()
    if len(sys.argv) > 1:
        good = check_table(sys.argv[1]) and good
    sys.exit(0 if good else 1)
