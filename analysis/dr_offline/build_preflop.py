import itertools, json, random, sys
from multiprocessing import Pool
import eval7

RANKS = "23456789TJQKA"
SUITS = "shdc"
DECK = [r + s for r in RANKS for s in SUITS]
CARD = {c: eval7.Card(c) for c in DECK}


def hand_key(cards):
    cs = sorted(cards, key=lambda c: RANKS.index(c[0]), reverse=True)
    suit_map = {}
    pattern = []
    for c in cs:
        suit_map.setdefault(c[1], len(suit_map))
        pattern.append(suit_map[c[1]])
    ranks = "".join(c[0] for c in cs)
    # canonical suit pattern independent of order among equal ranks
    groups = {}
    for c in cs:
        groups.setdefault(c[1], []).append(c[0])
    shape = sorted(("".join(v) for v in groups.values()), key=lambda s: (-len(s), s))
    return ranks + ":" + "|".join(shape)


def best_keep(hole, flop):
    best, best_pair = -1, None
    for pair in itertools.combinations(hole, 2):
        v = eval7.evaluate(list(pair) + flop)
        if v > best:
            best, best_pair = v, pair
    return list(best_pair)


def equity(args):
    key, cards, opp_pool, trials, seed = args
    rng = random.Random(seed)
    hero = [CARD[c] for c in cards]
    dead = set(cards)
    rest = [CARD[c] for c in DECK if c not in dead]
    score = 0.0
    for _ in range(trials):
        if opp_pool is None:
            sample = rng.sample(rest, 8)
            opp, board = sample[:3], sample[3:]
        else:
            while True:
                combo = opp_pool[rng.randrange(len(opp_pool))]
                if not (set(combo) & dead):
                    break
            opp = [CARD[c] for c in combo]
            taken = set(combo) | dead
            board = rng.sample([CARD[c] for c in DECK if c not in taken], 5)
        flop = board[:3]
        h = eval7.evaluate(best_keep(hero, flop) + board)
        o = eval7.evaluate(best_keep(opp, flop) + board)
        score += 1.0 if h > o else 0.5 if h == o else 0.0
    return key, score / trials


def representatives():
    reps = {}
    for combo in itertools.combinations(DECK, 3):
        reps.setdefault(hand_key(combo), combo)
    return reps


if __name__ == "__main__":
    trials = int(sys.argv[1])
    reps = representatives()
    print(len(reps), "classes", flush=True)
    with Pool() as pool:
        vs_random = dict(pool.map(equity, [(k, c, None, trials, i) for i, (k, c) in enumerate(reps.items())]))
    order = sorted(vs_random, key=vs_random.get)
    weights = {}
    counts = {}
    for combo in itertools.combinations(DECK, 3):
        counts[hand_key(combo)] = counts.get(hand_key(combo), 0) + 1
    total = sum(counts.values())
    cum, percentile = 0, {}
    for k in order:
        percentile[k] = (cum + counts[k] / 2) / total
        cum += counts[k]
    top = [c for c in itertools.combinations(DECK, 3) if percentile[hand_key(c)] >= 0.80]
    with Pool() as pool:
        vs_top = dict(pool.map(equity, [(k, c, top, trials // 2, 10_000 + i) for i, (k, c) in enumerate(reps.items())]))
    table = {k: [round(percentile[k], 4), round(vs_random[k], 4), round(vs_top[k], 4)] for k in reps}
    json.dump(table, open("preflop3.json", "w"), separators=(",", ":"))
    best = sorted(table.items(), key=lambda kv: -kv[1][0])
    print("top:", best[:8])
    print("bottom:", best[-5:])
