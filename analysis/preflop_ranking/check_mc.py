"""Independently re-deal hands in Python with eval7 and compare with ranking.csv.

Shares only the keep table with eq.c: the deal, keep lookup and showdown are all rewritten here.
"""
import csv
import itertools
import math
import random
import sys

import eval7
import numpy as np

RANKS, SUITS = "23456789TJQKA", "cdhs"
CARD = [eval7.Card(r + s) for r in RANKS for s in SUITS]
tab = np.fromfile("keep_equity.bin", dtype=np.float32).reshape(1755, 1326)
hole = {}
for i, (a, b) in enumerate(itertools.combinations(range(52), 2)):
    hole[(a, b)] = hole[(b, a)] = i
flops = list(itertools.combinations(range(52), 3))
ids = {f: i for i, f in enumerate(flops)}
perms = list(itertools.permutations(range(4)))
canon, class_of, perm_of = {}, {}, {}
for f in flops:
    best, bp = min(((ids[tuple(sorted((c & ~3) | p[c & 3] for c in f))], p) for p in perms), key=lambda x: x[0])
    canon.setdefault(best, len(canon))
    class_of[f], perm_of[f] = canon[best], bp


def keep(cards, flop):
    f = tuple(sorted(flop))
    row, p = tab[class_of[f]], perm_of[f]
    return max(itertools.combinations(cards, 2),
               key=lambda k: row[hole[((k[0] & ~3) | p[k[0] & 3], (k[1] & ~3) | p[k[1] & 3])]])


def parse(text):
    return [RANKS.index(c[0]) * 4 + SUITS.index(c[1]) for c in text.split()]


def main(trials):
    rows = list(csv.DictReader(open("ranking.csv")))
    picks = [rows[i] for i in (0, 50, 300, 877, 1400, 1754)]
    rng = random.Random(99)
    worst = 0.0
    for row in picks:
        hero = parse(row["example"])
        deck = [c for c in range(52) if c not in hero]
        pts = 0
        for _ in range(trials):
            s = rng.sample(deck, 8)
            opp, board = s[:3], s[3:]
            mine = eval7.evaluate([CARD[c] for c in list(keep(hero, board[:3])) + board])
            theirs = eval7.evaluate([CARD[c] for c in list(keep(opp, board[:3])) + board])
            pts += 2 if mine > theirs else 1 if mine == theirs else 0
        got, want = pts / (2 * trials), float(row["equity_vs_random"])
        z = (got - want) / math.sqrt(max(got * (1 - got), 1e-9) / trials)
        worst = max(worst, abs(z))
        print(f"#{row['rank']:>4} {row['hand_key']:14s} csv {want:.4f}  python {got:.4f}  z={z:+.2f}")
    print(f"largest |z| = {worst:.2f}")
    return worst < 3.5


if __name__ == "__main__":
    sys.exit(0 if main(int(sys.argv[1])) else 1)
