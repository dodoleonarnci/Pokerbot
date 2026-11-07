"""Fast seven-card scoring and range-versus-range equity. Cards are ints 0-51."""
import random
import zlib
from bisect import bisect_left, bisect_right

from engine import RANKS, SUITS


def card(text):
    return RANKS.index(text[0]) * 4 + SUITS.index(text[1])


def combo(cards):
    a, b = (card(c) for c in cards)
    return (a, b) if a < b else (b, a)


ALL_COMBOS = [(a, b) for a in range(52) for b in range(a + 1, 52)]

# Highest straight card for each 13-bit rank mask, or -1.
_STRAIGHT = [-1] * 8192
for _mask in range(8192):
    for _high in range(12, 3, -1):
        _pattern = 0b11111 << (_high - 4)
        if _mask & _pattern == _pattern:
            _STRAIGHT[_mask] = _high
            break
    else:
        if _mask & 0b1000000001111 == 0b1000000001111:
            _STRAIGHT[_mask] = 3


def _pack(category, *ranks):
    value = 0
    for i in range(5):
        value = value * 13 + (ranks[i] if i < len(ranks) else 0)
    return (category << 20) | value


def _top(mask, count, skip=()):
    found = []
    for rank in range(12, -1, -1):
        if mask >> rank & 1 and rank not in skip:
            found.append(rank)
            if len(found) == count:
                break
    return found


def score7(cards):
    """Score seven cards. A larger int is stronger; categories match engine.eval5."""
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
            if _STRAIGHT[suit_mask] >= 0:
                return _pack(8, _STRAIGHT[suit_mask])

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
        second = max(trips[1:] + pairs)
        return _pack(6, trips[0], second)
    if flush:
        return _pack(5, *_top(flush, 5))
    if _STRAIGHT[mask] >= 0:
        return _pack(4, _STRAIGHT[mask])
    if trips:
        return _pack(3, trips[0], *_top(mask, 2, (trips[0],)))
    if len(pairs) >= 2:
        return _pack(2, pairs[0], pairs[1], *_top(mask, 1, (pairs[0], pairs[1])))
    if pairs:
        return _pack(1, pairs[0], *_top(mask, 3, (pairs[0],)))
    return _pack(0, *_top(mask, 5))


def runouts(board, samples):
    """Repeatable board completions, so every seat models the same runouts."""
    needed = 5 - len(board)
    if needed == 0:
        return [()]
    deck = [c for c in range(52) if c not in board]
    rng = random.Random(zlib.crc32(bytes(board)))
    if needed == 1:
        rng.shuffle(deck)
        return [(c,) for c in deck[:samples]]
    return [tuple(rng.sample(deck, needed)) for _ in range(samples)]


def rate(combos, refs, board, outs):
    """Return {combo: [equity per runout]} for combos against the refs range.

    Blockers between the two ranges are ignored for speed. This is what makes
    rating a whole range affordable.
    """
    rated = {c: [] for c in combos}
    for out in outs:
        full = list(board) + list(out)
        blocked = set(full)
        ref_scores = sorted(
            score7(full + [a, b]) for a, b in refs if a not in blocked and b not in blocked
        )
        total = len(ref_scores)
        for c in combos:
            if c[0] in blocked or c[1] in blocked:
                continue
            if not total:
                rated[c].append(0.5)
                continue
            score = score7(full + list(c))
            low = bisect_left(ref_scores, score)
            high = bisect_right(ref_scores, score, low)
            rated[c].append((low + (high - low) / 2) / total)
    return rated


def mean(values):
    return sum(values) / len(values) if values else 0.0
