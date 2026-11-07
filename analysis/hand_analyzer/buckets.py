"""Variant-specific hand classes. Swap this file (and generate.py's policy) for another variant.

Target variant: 3 hole cards preflop; on the flop each live player discards one and shows one of
the two kept cards; 2 hole cards + board afterwards. Standard library only, so a bot can import it.
"""

from functools import lru_cache
from itertools import permutations

RANKS = "23456789TJQKA"
R = {c: i + 2 for i, c in enumerate(RANKS)}
SUITS = "shdc"
SUIT = {c: i for i, c in enumerate(SUITS)}
_PERMS = tuple(permutations(range(4)))

STRENGTHS = ("air", "draw", "weak", "top", "strong")
STRENGTH_ORDER = {name: i for i, name in enumerate(STRENGTHS)}
PUB_BUCKETS = ("P", "F", "S", "H", "B")

_CLASS3: dict = {}


def class3(cards) -> str:
    """Suit-merged 3-card class (1,755 classes): the minimum sorted (rank, suit) over 24 relabelings."""
    key = tuple(cards)
    found = _CLASS3.get(key)
    if found is None:
        raw = [(R[c[0]], SUIT[c[1]]) for c in key]
        best = min(tuple(sorted((r, p[s]) for r, s in raw)) for p in _PERMS)
        found = "".join(RANKS[r - 2] + "abcd"[s] for r, s in best)
        _CLASS3[key] = found
    return found


def _bit(rank: int) -> int:
    return (1 << rank) | (2 if rank == 14 else 0)  # An ace also plays low, as bit 1.


_STRAIGHTS = tuple((high, 0b11111 << (high - 4)) for high in range(14, 4, -1))
_OESD = tuple(0b1111 << low for low in range(2, 11))  # 2345 .. TJQK: both ends can complete.


def _straight_high(mask: int) -> int:
    for high, pattern in _STRAIGHTS:
        if mask & pattern == pattern:
            return high
    return 0


@lru_cache(maxsize=400_000)
def _strength(a: str, b: str, board: tuple) -> str:
    ra, rb, sa, sb = R[a[0]], R[b[0]], a[1], b[1]
    ranks = [R[c[0]] for c in board]
    suits = [c[1] for c in board]
    top = max(ranks)
    counts = {r: ranks.count(r) for r in ranks}
    board_paired = any(n >= 2 for n in counts.values())
    for suit in {sa, sb}:
        if suits.count(suit) + (sa == suit) + (sb == suit) >= 5:
            return "strong"
    board_mask = 0
    for r in ranks:
        board_mask |= _bit(r)
    all_mask = board_mask | _bit(ra) | _bit(rb)
    if _straight_high(all_mask) > _straight_high(board_mask):
        return "strong"
    if ra == rb:
        if ra in counts or board_paired:
            return "strong"  # A set, or two pair using the pocket pair.
        if ra > top:
            return "top"  # Overpair.
        return "weak"
    ha, hb = counts.get(ra, 0), counts.get(rb, 0)
    if ha >= 2 or hb >= 2 or (ha and hb):
        return "strong"  # Trips or better, or two pair with both hole cards.
    if ha or hb:
        if board_paired:
            return "strong"  # Two pair using one hole card.
        return "top" if (ra if ha else rb) == top else "weak"
    if len(board) < 5:
        for suit in {sa, sb}:
            if suits.count(suit) + (sa == suit) + (sb == suit) == 4:
                return "draw"
        hole = _bit(ra) | _bit(rb)
        for pattern in _OESD:
            if all_mask & pattern == pattern and hole & pattern:
                return "draw"
    return "air"


def strength_class(kept2, board) -> str:
    """air, draw, weak, top or strong for the two kept cards on this board."""
    return _strength(kept2[0], kept2[1], tuple(board))


@lru_cache(maxsize=100_000)
def _pub(shown: str, flop: tuple) -> str:
    rank = R[shown[0]]
    ranks = [R[c[0]] for c in flop]
    if rank in ranks:
        return "P"
    if sum(c[1] == shown[1] for c in flop) >= 2:
        return "F"
    distinct = set(ranks) | {rank}
    if 14 in distinct:
        distinct.add(1)
    for low in range(1, 11):
        if sum(low <= r <= low + 4 for r in distinct) >= 3:
            return "S"
    return "H" if rank > max(ranks) else "B"


def pub_bucket(shown: str, flop) -> str:
    """Public bucket of the shown card, fixed from the flop: P, F, S, H or B (first match wins)."""
    return _pub(shown, tuple(flop[:3]))


def pairs_board(card: str, flop) -> bool:
    return any(c[0] == card[0] for c in flop[:3])
