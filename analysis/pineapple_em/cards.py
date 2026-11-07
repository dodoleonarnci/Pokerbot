RANKS = "23456789TJQKA"
SUITS = "cdhs"

HIGH_CARD, PAIR, TWO_PAIR, TRIPS, STRAIGHT, FLUSH, FULL_HOUSE, QUADS, STRAIGHT_FLUSH = range(9)

AIR, WEAK_DRAW, STRONG_DRAW, WEAK_PAIR, TOP_PAIR, STRONG = range(6)
BUCKET_NAMES = ("air", "weak draw", "strong draw", "weak pair", "top pair", "strong")
N_BUCKETS = len(BUCKET_NAMES)


def card_name(card):
    return RANKS[card >> 2] + SUITS[card & 3]


def parse_card(text):
    return RANKS.index(text[0]) * 4 + SUITS.index(text[1])


def _straight_high_of(mask):
    extended = (mask << 1) | ((mask >> 12) & 1)
    for top in range(13, 3, -1):
        window = 0b11111 << (top - 4)
        if extended & window == window:
            return top - 1
    return -1


STRAIGHT_HIGH = [_straight_high_of(m) for m in range(1 << 13)]
STRAIGHT_COMPLETERS = [
    0 if STRAIGHT_HIGH[m] >= 0 else sum(1 << x for x in range(13) if STRAIGHT_HIGH[m | (1 << x)] >= 0)
    for m in range(1 << 13)
]


def _ranks_desc(mask, limit):
    found = []
    rank = 12
    while rank >= 0 and len(found) < limit:
        if mask >> rank & 1:
            found.append(rank)
        rank -= 1
    return found


def _pack(category, ranks):
    value = category
    for i in range(5):
        value = value * 16 + (ranks[i] + 1 if i < len(ranks) else 0)
    return value


def evaluate(cards):
    counts = [0] * 13
    suit_masks = [0, 0, 0, 0]
    for card in cards:
        counts[card >> 2] += 1
        suit_masks[card & 3] |= 1 << (card >> 2)
    rank_mask = suit_masks[0] | suit_masks[1] | suit_masks[2] | suit_masks[3]
    flush_mask = next((m for m in suit_masks if m.bit_count() >= 5), 0)
    if flush_mask and STRAIGHT_HIGH[flush_mask] >= 0:
        return _pack(STRAIGHT_FLUSH, [STRAIGHT_HIGH[flush_mask]])
    quads = [r for r in range(12, -1, -1) if counts[r] == 4]
    trips = [r for r in range(12, -1, -1) if counts[r] == 3]
    pairs = [r for r in range(12, -1, -1) if counts[r] == 2]
    if quads:
        return _pack(QUADS, [quads[0]] + _ranks_desc(rank_mask & ~(1 << quads[0]), 1))
    if trips and (len(trips) > 1 or pairs):
        return _pack(FULL_HOUSE, [trips[0], max(trips[1:] + pairs)])
    if flush_mask:
        return _pack(FLUSH, _ranks_desc(flush_mask, 5))
    if STRAIGHT_HIGH[rank_mask] >= 0:
        return _pack(STRAIGHT, [STRAIGHT_HIGH[rank_mask]])
    if trips:
        return _pack(TRIPS, [trips[0]] + _ranks_desc(rank_mask & ~(1 << trips[0]), 2))
    if len(pairs) >= 2:
        rest = rank_mask & ~(1 << pairs[0]) & ~(1 << pairs[1])
        return _pack(TWO_PAIR, pairs[:2] + _ranks_desc(rest, 1))
    if pairs:
        return _pack(PAIR, [pairs[0]] + _ranks_desc(rank_mask & ~(1 << pairs[0]), 3))
    return _pack(HIGH_CARD, _ranks_desc(rank_mask, 5))


class BoardView:
    __slots__ = ("size", "rank_counts", "suit_counts", "rank_mask", "top", "max_count",
                 "completers", "is_straight")

    def __init__(self, board):
        self.size = len(board)
        self.rank_counts = [0] * 13
        self.suit_counts = [0] * 4
        for card in board:
            self.rank_counts[card >> 2] += 1
            self.suit_counts[card & 3] += 1
        self.rank_mask = sum(1 << r for r in range(13) if self.rank_counts[r])
        self.top = max(card >> 2 for card in board)
        self.max_count = max(self.rank_counts)
        self.completers = STRAIGHT_COMPLETERS[self.rank_mask]
        self.is_straight = STRAIGHT_HIGH[self.rank_mask] >= 0


def bucket(first, second, view):
    r1, r2 = first >> 2, second >> 2
    s1, s2 = first & 3, second & 3
    c1, c2 = view.rank_counts[r1], view.rank_counts[r2]
    pocket = r1 == r2
    if pocket:
        if c1 or view.max_count >= 3:
            return STRONG
    elif c1 >= 2 or c2 >= 2 or (c1 and c2):
        return STRONG
    suited = s1 == s2
    flush_count = max(view.suit_counts[s1] + 1 + suited, view.suit_counts[s2] + 1 + suited)
    if flush_count >= 5:
        return STRONG
    mask = view.rank_mask | (1 << r1) | (1 << r2)
    if not view.is_straight and STRAIGHT_HIGH[mask] >= 0:
        return STRONG
    if (c1 and r1 == view.top) or (c2 and r2 == view.top) or (pocket and r1 > view.top):
        return TOP_PAIR
    if c1 or c2 or pocket:
        return WEAK_PAIR
    if view.size < 5:
        if flush_count == 4:
            return STRONG_DRAW
        outs = (STRAIGHT_COMPLETERS[mask] & ~view.completers).bit_count()
        if outs >= 2:
            return STRONG_DRAW
        if outs == 1 or (r1 > view.top and r2 > view.top):
            return WEAK_DRAW
    return AIR


def preflop_score(first, second):
    high, low = max(first >> 2, second >> 2), min(first >> 2, second >> 2)
    score = (high + 2) + (low + 2) / 2
    if high == low:
        score += 10 + high / 2
    if first & 3 == second & 3:
        score += 2
    gap = high - low
    if gap == 1:
        score += 2
    elif gap == 2:
        score += 1
    return score


def best_two_score(cards):
    a, b, c = cards
    return max(preflop_score(a, b), preflop_score(a, c), preflop_score(b, c))
