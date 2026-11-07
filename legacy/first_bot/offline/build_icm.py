#!/usr/bin/env python3
"""M6 offline: ICM jam/fold charts by fictitious play over hand classes.

Simplifications, all approximate: stacks are equal, only one caller reaches showdown,
and blinds are dead money of 1.5 big blinds. With --pool it re-solves as a best
response to Table C's observed calling ranges (M8 step 4).
Uses numpy, which is fine because this never runs inside the bot.
"""
import json
import os
import pathlib
import sys
from array import array

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bot.evaluator import CLASS_COMBOS, N_CLASSES  # noqa: E402
from bot.icm import icm_values  # noqa: E402
from bot.params import PARAMS, PAYOUTS, TABLE_SIZE  # noqa: E402

DATA = pathlib.Path(os.environ.get("FIRST_BOT_DATA", ROOT / "data"))
ITERATIONS = 200


def payout_outcomes(players, depth):
    """ICM values for a shover's outcomes, with equal stacks elsewhere."""
    others = [float(depth)] * (players - 1)
    pay = list(PAYOUTS[:players])

    def value(mine, rest):
        stacks = [mine] + rest
        return icm_values(stacks, pay)[0]

    fold = value(depth, others)
    steal = value(depth + 1.5, [max(0.01, s - 1.5 / (players - 1)) for s in others])
    win = value(2 * depth + 1.5, others[1:]) if players > 2 else PAYOUTS[0]
    lose = PAYOUTS[players - 1]
    return fold, steal, win, lose


def call_outcomes(players, depth):
    others = [float(depth)] * (players - 2)
    pay = list(PAYOUTS[:players])
    fold = icm_values([depth, depth + 1.5] + others, pay)[0] if players >= 2 else 0
    win = icm_values([2 * depth + 1.5] + others, pay[:max(1, players - 1)])[0]
    return fold, win, PAYOUTS[players - 1]


def _top_mask(matrix, weights, percent):
    """Call frequencies for the top percent% of hands, ordered by overall equity."""
    strength = matrix @ weights / weights.sum()
    order = np.argsort(-strength)
    mask = np.zeros(N_CLASSES)
    count = 0.0
    for index in order:
        if count >= 13.26 * percent:
            break
        mask[index] = 1.0
        count += CLASS_COMBOS[index]
    return mask


def solve_cell(players, behind, depth, matrix, weights, pool_call=None, pool_jam=None):
    jam = np.ones(N_CLASSES) * 0.5
    call = np.ones(N_CLASSES) * 0.2
    if pool_call is not None:
        call = _top_mask(matrix, weights, pool_call)
    if pool_jam is not None:
        jam = _top_mask(matrix, weights, pool_jam)
    fold_u, steal_u, win_u, lose_u = payout_outcomes(players, depth)
    call_fold_u, call_win_u, call_lose_u = call_outcomes(players, depth)

    iterations = 1 if pool_call is not None else ITERATIONS
    for step in range(1, iterations + 1):
        call_rate = (call * weights).sum() / weights.sum()
        any_call = 1 - (1 - call_rate) ** behind
        denominator = (call * weights).sum()
        versus_call = matrix @ (call * weights) / denominator if denominator > 0 else np.full(N_CLASSES, 0.5)
        jam_ev = (1 - any_call) * steal_u + any_call * (versus_call * win_u + (1 - versus_call) * lose_u)
        best_jam = (jam_ev > fold_u).astype(float)

        denominator = (jam * weights).sum()
        versus_jam = matrix @ (jam * weights) / denominator if denominator > 0 else np.full(N_CLASSES, 0.5)
        call_ev = versus_jam * call_win_u + (1 - versus_jam) * call_lose_u
        best_call = (call_ev > call_fold_u).astype(float)

        if pool_call is not None:
            jam = best_jam
        else:
            jam += (best_jam - jam) / (step + 1)
        if pool_jam is not None or pool_call is None:
            call = best_call if pool_jam is not None else call + (best_call - call) / (step + 1)
    return jam >= 0.5, call >= 0.5


def pack(mask):
    size = N_CLASSES // 8 + 1
    packed = bytearray(size)
    for index, on in enumerate(mask):
        if on:
            packed[index >> 3] |= 1 << (index & 7)
    return bytes(packed)


def pool_rates(players, depth_label):
    """Table C widths for call-vs-jam and jam, or (None, None)."""
    try:
        with open(DATA / "pool_tables.json") as f:
            c = json.load(f)["c"]
    except (OSError, ValueError, KeyError):
        return None, None
    crowd = "8-6" if players >= 6 else "5-3" if players >= 3 else "2"
    call = c.get(f"call-vs-jam|{depth_label}|{crowd}") or c.get("call-vs-jam")
    jam = c.get(f"jam|{depth_label}|{crowd}") or c.get("jam")
    return (100 * call[1] if call else None), (100 * jam[1] if jam else None)


def main(use_pool=False):
    matrix_raw = array("f")
    matrix_raw.frombytes((DATA / "class_matrix.bin").read_bytes())
    matrix = np.array(matrix_raw, dtype=float).reshape(N_CLASSES, N_CLASSES)
    weights = np.array(CLASS_COMBOS, dtype=float)
    out = bytearray()
    cells = jam_total = 0
    for players in range(2, TABLE_SIZE + 1):
        for behind in range(1, players):
            for depth in range(1, PARAMS["JAM_BB"] + 1):
                pool_call, pool_jam = (None, None)
                if use_pool:
                    pool_call, pool_jam = pool_rates(players, "short")
                jam, call = solve_cell(players, behind, depth, matrix, weights, pool_call, pool_jam)
                out += pack(jam) + pack(call)
                cells += 1
                jam_total += (jam * weights).sum() / 13.26
    (DATA / "icm_charts.bin").write_bytes(bytes(out))
    print(f"{cells} cells, average jam range {jam_total / cells:.1f}%, {len(out)} bytes")


if __name__ == "__main__":
    main("--pool" in sys.argv)
