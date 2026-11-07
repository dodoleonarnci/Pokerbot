"""Rank all 1,755 Bay Area starting hands. Usage: build.py TRIALS_RANDOM TRIALS_TOP

Writes ranking.csv (strongest first) and preflop3.json, whose keys and
[percentile, vs_random, vs_top20] values match dr_offline/preflop3.json.
"""
import csv
import itertools
import json
import subprocess
import sys

RANKS = "23456789TJQKA"
SUITS = "cdhs"
TOP_SHARE = 0.20


def name(card):
    return RANKS[card >> 2] + SUITS[card & 3]


def hand_key(cards):
    """Same key as dr_offline/build_preflop.py: ranks high to low, then the suit groups."""
    cs = sorted((name(c) for c in cards), key=lambda c: RANKS.index(c[0]), reverse=True)
    groups = {}
    for c in cs:
        groups.setdefault(c[1], []).append(c[0])
    shape = sorted(("".join(v) for v in groups.values()), key=lambda s: (-len(s), s))
    return "".join(c[0] for c in cs) + ":" + "|".join(shape)


def suit_label(key):
    ranks, shape = key.split(":")
    sizes = sorted(len(g) for g in shape.split("|"))
    if sizes == [3]:
        return "suited"
    if sizes == [1, 1, 1]:
        return "rainbow"
    return "two-tone"


def run_mc(reps_path, out, trials, pool=None):
    cmd = ["./eq", "mc", "keep_equity.bin", reps_path, out, str(trials)] + ([pool] if pool else [])
    subprocess.run(cmd, check=True)
    rows = {}
    for line in open(out):
        a, b, c, eq, d0, d1, d2 = line.split()
        rows[(int(a), int(b), int(c))] = (float(eq), float(d0), float(d1), float(d2))
    return rows


def main():
    trials_random, trials_top = int(sys.argv[1]), int(sys.argv[2])
    members = {}
    for combo in itertools.combinations(range(52), 3):
        members.setdefault(hand_key(combo), []).append(combo)
    assert len(members) == 1755 and sum(map(len, members.values())) == 22100
    reps = {k: v[0] for k, v in members.items()}
    with open("reps.txt", "w") as f:
        for r in reps.values():
            print(*r, file=f)

    random_rows = run_mc("reps.txt", "mc_random.txt", trials_random)
    vs_random = {k: random_rows[r][0] for k, r in reps.items()}
    order = sorted(vs_random, key=vs_random.get)
    total = 22100
    cum, percentile, top_pool = 0, {}, []
    for k in order:
        n = len(members[k])
        percentile[k] = (cum + n / 2) / total
        cum += n
        if percentile[k] >= 1 - TOP_SHARE:
            top_pool += members[k]
    with open("top_pool.txt", "w") as f:
        for c in top_pool:
            print(*c, file=f)
    top_rows = run_mc("reps.txt", "mc_top.txt", trials_top, "top_pool.txt")
    vs_top = {k: top_rows[r][0] for k, r in reps.items()}

    mean = sum(vs_random[k] * len(members[k]) for k in reps) / total
    print(f"combo-weighted mean vs random: {mean:.5f} (must be 0.5)")
    print(f"top pool: {len(top_pool)} combos, {len(top_pool) / total:.1%}")

    with open("ranking.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["rank", "hand_key", "example", "suits", "combos", "equity_vs_random",
                    "percentile", "equity_vs_top20"])
        for i, k in enumerate(reversed(order), 1):
            w.writerow([i, k, " ".join(name(c) for c in sorted(reps[k], reverse=True)), suit_label(k),
                        len(members[k]), f"{vs_random[k]:.4f}", f"{percentile[k]:.4f}", f"{vs_top[k]:.4f}"])
    table = {k: [round(percentile[k], 4), round(vs_random[k], 4), round(vs_top[k], 4)] for k in reps}
    json.dump(table, open("preflop3.json", "w"), separators=(",", ":"))


if __name__ == "__main__":
    main()
