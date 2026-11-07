"""Practice stand-in for the kit's simulator: one 8-bot sit-and-go.

Blinds, payouts and tie handling are assumptions from bot/params.py.
"""
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / "practice"))

from engine import Hand  # noqa: E402

from bot.icm import icm_values  # noqa: E402
from bot.params import (BLIND_LEVELS, HANDS_PER_LEVEL, MAX_HANDS, PAYOUTS,  # noqa: E402
                        STARTING_STACK)


def run_table(agents, rng, limits=None, log=None, starting=STARTING_STACK, max_hands=MAX_HANDS):
    """Play one table. Returns result dict; agents are callables, one per player."""
    n = len(agents)
    stacks = [starting] * n
    points = [0.0] * n
    place = n
    button = rng.randrange(n)
    failures, timeouts = [0] * n, [0] * n
    hand_no = 0
    while hand_no < max_hands:
        alive = [i for i in range(n) if stacks[i] > 0]
        if len(alive) < 2:
            break
        level = min(hand_no // HANDS_PER_LEVEL, len(BLIND_LEVELS) - 1)
        sb, bb = BLIND_LEVELS[level]
        while stacks[button] <= 0:
            button = (button + 1) % n
        button_index = alive.index(button)
        extras = {
            "hand_number": hand_no,
            "hands_remaining": max_hands - hand_no,
            "players_left": len(alive),
            "seat_ids": alive,
            "payouts": PAYOUTS,
        }
        seat_limits = {alive.index(i): limits[i] for i in (limits or {}) if i in alive}
        hand = Hand([agents[i] for i in alive], [stacks[i] for i in alive],
                    button_index, sb, bb, rng, extras=extras, limits=seat_limits)
        before = [stacks[i] for i in alive]
        result = hand.play()
        for index, seat in enumerate(alive):
            stacks[seat] = result[index]
            failures[seat] += hand.failures[index]
            timeouts[seat] += hand.timeouts[index]
        if log is not None:
            log.append({
                "hand": hand_no, "button": button_index, "sb": sb, "bb": bb,
                "seats": alive, "stacks": before, "holes": hand.holes,
                "board": hand.board, "history": hand.history, "after": result,
                "players_left": len(alive), "hands_remaining": max_hands - hand_no,
            })
        # Players busted this hand take the lowest open places; a bigger start ranks higher.
        busted = sorted((alive[i] for i in range(len(alive)) if result[i] == 0),
                        key=lambda seat: before[alive.index(seat)])
        groups = {}
        for seat in busted:
            groups.setdefault(before[alive.index(seat)], []).append(seat)
        for stack in sorted(groups):
            group = groups[stack]
            share = sum(PAYOUTS[place - 1 - k] for k in range(len(group))) / len(group)
            for seat in group:
                points[seat] = share
            place -= len(group)
        button = (button + 1) % n
        hand_no += 1

    survivors = [i for i in range(n) if stacks[i] > 0]
    if len(survivors) == 1:
        points[survivors[0]] = PAYOUTS[0]
    elif survivors:  # hand cap: split the remaining places by ICM
        values = icm_values([stacks[i] for i in survivors], PAYOUTS[:len(survivors)])
        for seat, value in zip(survivors, values):
            points[seat] = value
    return {"points": points, "hands": hand_no, "failures": failures,
            "timeouts": timeouts, "stacks": stacks}


def seed_rng(seed):
    return random.Random(seed)
