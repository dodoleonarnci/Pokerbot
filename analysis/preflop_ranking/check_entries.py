"""Recompute random keep-table entries by full enumeration with eval7; they must match exactly."""
import itertools, random, sys
import eval7
import numpy as np

CARD = [eval7.Card(r + s) for r in "23456789TJQKA" for s in "cdhs"]
tab = np.fromfile("keep_equity.bin", dtype=np.float32).reshape(1755, 1326)
hole = {p: i for i, p in enumerate(itertools.combinations(range(52), 2))}
flops = list(itertools.combinations(range(52), 3))
ids = {f: i for i, f in enumerate(flops)}
perms = list(itertools.permutations(range(4)))
canon = {}
for f in flops:
    best = min(ids[tuple(sorted((c & ~3) | p[c & 3] for c in f))] for p in perms)
    canon.setdefault(best, len(canon))
reps = {v: flops[k] for k, v in canon.items()}

rng = random.Random(7)
worst = 0.0
for _ in range(int(sys.argv[1])):
    cls = rng.randrange(1755)
    flop = reps[cls]
    live = [c for c in range(52) if c not in flop]
    a, b = sorted(rng.sample(live, 2))
    rest = [c for c in live if c not in (a, b)]
    pts = n = 0
    for t, r in itertools.combinations(rest, 2):
        board = [CARD[c] for c in flop + (t, r)]
        mine = eval7.evaluate(board + [CARD[a], CARD[b]])
        opp_live = [c for c in rest if c not in (t, r)]
        for x, y in itertools.combinations(opp_live, 2):
            v = eval7.evaluate(board + [CARD[x], CARD[y]])
            pts += 2 if mine > v else 1 if mine == v else 0
            n += 2
    got, want = float(tab[cls, hole[(a, b)]]), pts / n
    worst = max(worst, abs(got - want))
    print(f"class {cls:4d} keep {a:2d},{b:2d}  table {got:.6f}  eval7 {want:.6f}")
print(f"worst difference {worst:.2e}")
sys.exit(0 if worst < 1e-6 else 1)
