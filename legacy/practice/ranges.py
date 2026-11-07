"""Preflop ranges as percentages of all starting combos. Edit the tables to tune them.

Each band runs from the top of the stronger action down to this percentage: a hand
in the top THREEBET% raises, and a hand between THREEBET% and FLAT% calls.
"""
from functools import lru_cache

from engine import RANKS
from preflop_order import ORDER

OPEN = {"EP": 15, "HJ": 22, "CO": 30, "BTN": 45, "SB": 40, "BB": 20, "HU_BTN": 85, "HU_BB": 30}
FLAT = {"EP": 10, "HJ": 12, "CO": 15, "BTN": 20, "SB": 12, "BB": 40, "HU_BTN": 40, "HU_BB": 60}
THREEBET = {"EP": 5, "HJ": 5, "CO": 6, "BTN": 7, "SB": 7, "BB": 7, "HU_BTN": 15, "HU_BB": 12}
CALL_3BET = {"EP": 8, "HJ": 8, "CO": 9, "BTN": 10, "SB": 8, "BB": 8, "HU_BTN": 25, "HU_BB": 25}
FOURBET = {"EP": 3, "HJ": 3, "CO": 3, "BTN": 3, "SB": 3, "BB": 3, "HU_BTN": 6, "HU_BB": 6}
JAM = {"EP": 2, "HJ": 2, "CO": 2, "BTN": 2, "SB": 2, "BB": 2, "HU_BTN": 4, "HU_BB": 4}
LIMP = 40  # how wide we assume an opponent limps; the bot itself never limps


def position(seat, button, players):
    distance = (seat - button) % players
    if players == 2:
        return "HU_BTN" if distance == 0 else "HU_BB"
    if distance == 0:
        return "BTN"
    if distance == 1:
        return "SB"
    if distance == 2:
        return "BB"
    if distance == players - 1:
        return "CO"
    return "HJ" if distance == players - 2 else "EP"


def combos_of(label):
    a, b = RANKS.index(label[0]), RANKS.index(label[1])
    if a == b:
        return [(a * 4 + s, a * 4 + t) for s in range(4) for t in range(s + 1, 4)]
    if label[2] == "s":
        pairs = ((a * 4 + s, b * 4 + s) for s in range(4))
    else:
        pairs = ((a * 4 + s, b * 4 + t) for s in range(4) for t in range(4) if s != t)
    return [tuple(sorted(p)) for p in pairs]


def label_of(hole):
    a, b = sorted(hole, key=lambda c: c >> 2, reverse=True)
    high, low = RANKS[a >> 2], RANKS[b >> 2]
    if high == low:
        return high + low
    return high + low + ("s" if a & 3 == b & 3 else "o")


_PERCENTILE = {}
_count = 0
for _label in ORDER:
    _count += len(combos_of(_label))
    _PERCENTILE[_label] = 100 * _count / 1326


def percentile(hole):
    """Lower is stronger: AA is about 0.5, and the weakest hand is 100."""
    return _PERCENTILE[label_of(hole)]


@lru_cache(maxsize=None)
def band(low, high):
    """Combos stronger than high% and not stronger than low%, as a sorted list."""
    return sorted(
        c for label in ORDER if low < _PERCENTILE[label] <= high for c in combos_of(label)
    )


def top(percent):
    return band(0, percent)
