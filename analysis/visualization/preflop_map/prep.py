import itertools, json, sys

RANKS = "23456789TJQKA"
SUITS = "shdc"
DECK = [r + s for r in RANKS for s in SUITS]
POSITIONS = {(0, 1): "hm", (0, 2): "hl", (1, 2): "ml"}


def hand_key(cards):  # copied from ~/work/dr_offline/build_preflop.py
    cs = sorted(cards, key=lambda c: RANKS.index(c[0]), reverse=True)
    ranks = "".join(c[0] for c in cs)
    groups = {}
    for c in cs:
        groups.setdefault(c[1], []).append(c[0])
    shape = sorted(("".join(v) for v in groups.values()), key=lambda s: (-len(s), s))
    return ranks + ":" + "|".join(shape)


table = json.load(open(sys.argv[1]))
counts = {}
for combo in itertools.combinations(DECK, 3):
    k = hand_key(combo)
    counts[k] = counts.get(k, 0) + 1
assert sum(counts.values()) == 22100 and set(counts) == set(table), "key mismatch"

triples = {}
for key, (pct, eq_r, eq_t) in table.items():
    ranks, groups = key.split(":")
    sizes = sorted(len(g) for g in groups.split("|"))
    opts = []
    if sizes == [3]:
        opts = ["s"]
    elif sizes == [1, 1, 1]:
        opts = ["r"]
    else:
        pair = sorted(next(g for g in groups.split("|") if len(g) == 2))
        opts = [name for (i, j), name in POSITIONS.items() if sorted(ranks[i] + ranks[j]) == pair]
    assert opts, key
    t = triples.setdefault(ranks, {"keys": {}, "opts": {}})
    t["keys"][key] = [pct, eq_r, eq_t, counts[key]]
    for o in opts:
        t["opts"][o] = [pct, eq_r, eq_t, counts[key]]

rows = []
for ranks, t in triples.items():
    total = sum(v[3] for v in t["keys"].values())
    avg = [round(sum(v[m] * v[3] for v in t["keys"].values()) / total, 4) for m in range(3)] + [total]
    t["opts"]["avg"] = avg
    rows.append([RANKS.index(ranks[0]), RANKS.index(ranks[1]), RANKS.index(ranks[2]), t["opts"]])
rows.sort()
out = json.dumps(rows, separators=(",", ":"))
open(sys.argv[2], "w").write(out)
print(len(rows), "rank triples;", sum(len(t["keys"]) for t in triples.values()), "keys;", len(out), "bytes")
for m, name in enumerate(("percentile", "eq_random", "eq_top20")):
    vals = [v[m] for t in triples.values() for v in t["keys"].values()]
    print(name, min(vals), max(vals))
print("example", [r for r in rows if r[:3] == [11, 11, 2]])
