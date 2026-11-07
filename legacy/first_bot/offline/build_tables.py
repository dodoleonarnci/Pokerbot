#!/usr/bin/env python3
"""M3 and M4 offline build. Writes the data files that the bot loads at import.

With the kit available, the simulation here should use the kit's own engine and
evaluator, as the spec requires. Run from the first_bot folder.
"""
import json
import pathlib
import random
import sys
import time
from array import array
from multiprocessing import Pool

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bot.evaluator import (CLASSES, CLASS_COMBOS, RANK_PAIRS, board_keys, class_combos,  # noqa: E402
                           class_label, nonflush_score, score7)
from bot.features import hand_key  # noqa: E402

DATA = ROOT / "data"
MATCHUP_SAMPLES = 1000
OPPONENT_SAMPLES = 3000
POSTFLOP_DEALS = 400000
N = len(CLASSES)


def rank_table():
    """Non-flush score of each of the 91 rank pairs on each board rank multiset."""
    values = array("i")
    for board in board_keys():
        for high in range(13):
            for low in range(high + 1):
                ranks = list(board) + [high, low]
                if max(ranks.count(r) for r in set(ranks)) > 4:
                    values.append(-1)
                else:
                    values.append(nonflush_score(ranks))
    assert len(values) == len(board_keys()) * RANK_PAIRS
    return values


def _matchups(args):
    a, seed = args
    rng = random.Random(seed)
    combos_a = class_combos(a)
    row = []
    for b in range(a, N):
        combos_b = class_combos(b)
        wins = 0.0
        done = 0
        while done < MATCHUP_SAMPLES:
            ha, hb = rng.choice(combos_a), rng.choice(combos_b)
            if set(ha) & set(hb):
                # Some class pairs cannot be drawn without overlap on most tries.
                done += 0.02
                continue
            used = set(ha) | set(hb)
            board = []
            while len(board) < 5:
                c = rng.randrange(52)
                if c not in used and c not in board:
                    board.append(c)
            x, y = score7(board + list(ha)), score7(board + list(hb))
            wins += 1.0 if x > y else 0.5 if x == y else 0.0
            done += 1
        row.append(wins / done if done else 0.5)
    return a, row


def _versus_field(args):
    a, seed = args
    rng = random.Random(seed)
    combos = class_combos(a)
    wins = [0.0] * 8
    for _ in range(OPPONENT_SAMPLES):
        hero = rng.choice(combos)
        deck = [c for c in range(52) if c not in hero]
        cards = rng.sample(deck, 5 + 14)
        board, rest = cards[:5], cards[5:]
        mine = score7(board + list(hero))
        best, ties = 0, 0
        for opp in range(1, 8):
            s = score7(board + rest[(opp - 1) * 2:(opp - 1) * 2 + 2])
            if s > best:
                best, ties = s, 1
            elif s == best:
                ties += 1
            if mine > best:
                wins[opp] += 1.0
            elif mine == best:
                wins[opp] += 1.0 / (ties + 1)
    return a, [w / OPPONENT_SAMPLES for w in wins[1:]]


def _postflop(seed):
    rng = random.Random(seed)
    totals = {}
    for _ in range(POSTFLOP_DEALS // 2):
        cards = rng.sample(range(52), 21)
        hero, full_board, rest = cards[:2], cards[2:7], cards[7:]
        mine = score7(full_board + hero)
        best = 0
        results = []
        for opp in range(7):
            best = max(best, score7(full_board + rest[opp * 2:opp * 2 + 2]))
            results.append(mine > best)
        for street_cards in (3, 4):
            key = hand_key(hero, full_board[:street_cards])
            row = totals.setdefault(key, [0] * 8)
            row[0] += 1
            for opp, won in enumerate(results):
                row[opp + 1] += won
    return totals


def main():
    start = time.time()
    DATA.mkdir(exist_ok=True)
    (DATA / "rank_table.bin").write_bytes(rank_table().tobytes())
    print(f"rank table done {time.time() - start:.0f}s", flush=True)

    with Pool(2) as pool:
        matrix = [[0.5] * N for _ in range(N)]
        for a, row in pool.imap_unordered(_matchups, [(a, 1000 + a) for a in range(N)]):
            for offset, value in enumerate(row):
                matrix[a][a + offset] = value
                matrix[a + offset][a] = 1 - value
        print(f"class matchups done {time.time() - start:.0f}s", flush=True)

        field = [None] * N
        for a, row in pool.imap_unordered(_versus_field, [(a, 5000 + a) for a in range(N)]):
            field[a] = row
        print(f"versus field done {time.time() - start:.0f}s", flush=True)

        postflop = {}
        for totals in pool.imap_unordered(_postflop, [91, 92]):
            for key, row in totals.items():
                old = postflop.setdefault(key, [0] * 8)
                for i, value in enumerate(row):
                    old[i] += value
        print(f"postflop table done {time.time() - start:.0f}s", flush=True)

    flat = array("f", (matrix[a][b] for a in range(N) for b in range(N)))
    (DATA / "class_matrix.bin").write_bytes(flat.tobytes())

    # Order classes by equity against a typical opening range: the top 25% by raw equity.
    raw = sorted(range(N), key=lambda a: field[a][0], reverse=True)
    typical, count = [], 0
    for a in raw:
        if count >= 0.25 * 1326:
            break
        typical.append(a)
        count += CLASS_COMBOS[a]
    weight = sum(CLASS_COMBOS[b] for b in typical)
    versus_typical = [
        sum(matrix[a][b] * CLASS_COMBOS[b] for b in typical) / weight for a in range(N)
    ]
    order = sorted(range(N), key=lambda a: versus_typical[a], reverse=True)

    # Equity of each class against the top X% of hands, X from 1 to 100.
    versus_top = array("f")
    for a in range(N):
        total, combos, position = 0.0, 0, 0
        for percent in range(1, 101):
            target = 13.26 * percent
            while position < N and (combos < target or combos == 0):
                b = order[position]
                total += matrix[a][b] * CLASS_COMBOS[b]
                combos += CLASS_COMBOS[b]
                position += 1
            versus_top.append(total / combos)
    (DATA / "versus_top.bin").write_bytes(versus_top.tobytes())

    with open(DATA / "preflop.json", "w") as f:
        json.dump({
            "order": order,
            "labels": [class_label(a) for a in order],
            "field": field,
        }, f)
    with open(DATA / "postflop_keys.json", "w") as f:
        json.dump({k: [row[0]] + [round(x / row[0], 4) for x in row[1:]]
                   for k, row in postflop.items() if row[0] >= 50}, f)
    print(f"all done {time.time() - start:.0f}s")


if __name__ == "__main__":
    main()
