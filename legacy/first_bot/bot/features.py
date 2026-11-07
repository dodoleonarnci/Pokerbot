"""Cheap postflop features: draw outs, made-hand class and board texture."""
from .evaluator import CATEGORY_SHIFT, STRAIGHT, score7


def count_outs(hole, board):
    """Flush and straight outs that use a hole card. Run on the flop and turn."""
    suits = [0, 0, 0, 0]
    ranks_all = [0] * 13
    board_mask = 0
    for c in board:
        suits[c & 3] += 1
        ranks_all[c >> 2] += 1
        board_mask |= 1 << (c >> 2)
    mask = board_mask
    for c in hole:
        ranks_all[c >> 2] += 1
        mask |= 1 << (c >> 2)

    outs = 0
    flush_suit = -1
    for c in hole:
        s = c & 3
        held = suits[s] + (hole[0] & 3 == s) + (hole[1] & 3 == s)
        if held == 4:
            flush_suit = s
            break
    if flush_suit >= 0:
        outs += 9

    if STRAIGHT[mask] < 0:
        for rank in range(13):
            bit = 1 << rank
            if mask & bit:
                continue
            # The straight must not already be on the board plus this card alone.
            if STRAIGHT[mask | bit] >= 0 and STRAIGHT[board_mask | bit] < 0:
                outs += 4 - (1 if flush_suit >= 0 else 0)
    return outs


def ppot(outs, street):
    """Chance of improving, from outs. Spec S1."""
    if street == "turn":
        return outs / 46
    if street == "flop":
        return min(0.04 * outs, 0.6)
    return 0.0


def texture(board):
    ranks = sorted(c >> 2 for c in board)
    suit_counts = [0, 0, 0, 0]
    for c in board:
        suit_counts[c & 3] += 1
    if max(suit_counts) >= 3:
        return "s"  # flush possible
    if len(set(ranks)) < len(ranks):
        return "p"  # paired
    if ranks[-1] - ranks[0] <= 6:
        return "c"  # connected
    return "d"  # dry


def made_class(hole, board):
    score = score7(list(hole) + list(board))
    category = score >> CATEGORY_SHIFT
    if category >= 3:
        return str(category)
    if category == 2:
        return "2"
    if category == 1:
        top_board = max(c >> 2 for c in board)
        pair = (score & ((1 << CATEGORY_SHIFT) - 1)) // 13 ** 4
        if pair > top_board:
            return "over"
        if pair == top_board:
            return "top"
        return "mid"
    return "0"


def hand_key(hole, board):
    outs = count_outs(hole, board)
    bucket = 0 if outs < 4 else 4 if outs < 8 else 8 if outs < 12 else 12
    return f"{len(board)}|{made_class(hole, board)}|{bucket}|{texture(board)}"
