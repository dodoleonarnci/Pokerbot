"""M3: hand ranking. Replace score7 with the kit's evaluator if it is fast enough.

Cards are ints 0-51: rank * 4 + suit. A larger score is a stronger hand.
"""
from itertools import combinations_with_replacement

RANKS = "23456789TJQKA"
SUITS = "cdhs"
CARD = {r + s: i * 4 + j for i, r in enumerate(RANKS) for j, s in enumerate(SUITS)}

STRAIGHT = [-1] * 8192
for _mask in range(8192):
    for _high in range(12, 3, -1):
        _pattern = 0b11111 << (_high - 4)
        if _mask & _pattern == _pattern:
            STRAIGHT[_mask] = _high
            break
    else:
        if _mask & 0b1000000001111 == 0b1000000001111:
            STRAIGHT[_mask] = 3

CATEGORY_SHIFT = 20
FLUSH = 5


def _pack(category, *ranks):
    value = 0
    for i in range(5):
        value = value * 13 + (ranks[i] if i < len(ranks) else 0)
    return (category << CATEGORY_SHIFT) | value


def _top(mask, count, skip=()):
    found = []
    for rank in range(12, -1, -1):
        if mask >> rank & 1 and rank not in skip:
            found.append(rank)
            if len(found) == count:
                break
    return found


def score7(cards):
    """Score five to seven cards. Used once per decision, plus offline."""
    counts = [0] * 13
    suits = [0, 0, 0, 0]
    for c in cards:
        rank = c >> 2
        counts[rank] += 1
        suits[c & 3] |= 1 << rank
    mask = suits[0] | suits[1] | suits[2] | suits[3]

    flush = 0
    for suit_mask in suits:
        if suit_mask.bit_count() >= 5:
            flush = suit_mask
            if STRAIGHT[suit_mask] >= 0:
                return _pack(8, STRAIGHT[suit_mask])

    quads, trips, pairs = -1, [], []
    for rank in range(12, -1, -1):
        n = counts[rank]
        if n == 4:
            quads = rank
        elif n == 3:
            trips.append(rank)
        elif n == 2:
            pairs.append(rank)

    if quads >= 0:
        return _pack(7, quads, *_top(mask, 1, (quads,)))
    if trips and (len(trips) > 1 or pairs):
        return _pack(6, trips[0], max(trips[1:] + pairs))
    if flush:
        return _pack(5, *_top(flush, 5))
    if STRAIGHT[mask] >= 0:
        return _pack(4, STRAIGHT[mask])
    if trips:
        return _pack(3, trips[0], *_top(mask, 2, (trips[0],)))
    if len(pairs) >= 2:
        return _pack(2, pairs[0], pairs[1], *_top(mask, 1, (pairs[0], pairs[1])))
    if pairs:
        return _pack(1, pairs[0], *_top(mask, 3, (pairs[0],)))
    return _pack(0, *_top(mask, 5))


# ---- Starting-hand classes -------------------------------------------------------
CLASSES = []  # (high rank, low rank, kind): kind 0 pair, 1 suited, 2 offsuit
for _high in range(12, -1, -1):
    for _low in range(_high, -1, -1):
        if _high == _low:
            CLASSES.append((_high, _low, 0))
        else:
            CLASSES.append((_high, _low, 1))
            CLASSES.append((_high, _low, 2))

CLASS_ID = {info: i for i, info in enumerate(CLASSES)}
CLASS_COMBOS = [6 if k == 0 else 4 if k == 1 else 12 for _, _, k in CLASSES]
PAIR_INDEX = [h * (h + 1) // 2 + l for h, l, _ in CLASSES]  # 91 rank pairs
RANK_PAIRS = 91
N_CLASSES = len(CLASSES)

_CLASS_OF = [[0] * 52 for _ in range(52)]
for _a in range(52):
    for _b in range(52):
        if _a == _b:
            continue
        _ra, _rb = _a >> 2, _b >> 2
        _hi, _lo = max(_ra, _rb), min(_ra, _rb)
        _kind = 0 if _ra == _rb else 1 if _a & 3 == _b & 3 else 2
        _CLASS_OF[_a][_b] = CLASS_ID[(_hi, _lo, _kind)]


def class_of(a, b):
    return _CLASS_OF[a][b]


def class_label(index):
    high, low, kind = CLASSES[index]
    return RANKS[high] + RANKS[low] + ("" if kind == 0 else "s" if kind == 1 else "o")


def class_combos(index):
    high, low, kind = CLASSES[index]
    if kind == 0:
        return [(high * 4 + s, high * 4 + t) for s in range(4) for t in range(s + 1, 4)]
    if kind == 1:
        return [(high * 4 + s, low * 4 + s) for s in range(4)]
    return [(high * 4 + s, low * 4 + t) for s in range(4) for t in range(4) if s != t]


# ---- Board rank multisets, for the precomputed rank table --------------------------
def board_keys():
    """Every board rank multiset for 3, 4 and 5 cards, in a fixed order."""
    keys = []
    for size in (3, 4, 5):
        for ranks in combinations_with_replacement(range(13), size):
            if max(ranks.count(r) for r in set(ranks)) <= 4:
                keys.append(ranks)
    return keys


def nonflush_score(ranks):
    """Score a rank multiset with suits dealt so that no flush is possible."""
    cards = [rank * 4 + i % 4 for i, rank in enumerate(sorted(ranks))]
    return score7(cards)
