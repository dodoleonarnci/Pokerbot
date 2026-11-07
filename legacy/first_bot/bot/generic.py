"""Generic engine: equity from the active VariantSpec against random hands, then pot odds.

Used when the variant breaks the hold'em policy's assumptions (uses_holdem_policy False) or
the policy raises. It needs only spec.parse_card, spec.equity and the practice-format state.
"""
from .params import PARAMS


def decide(practice, spec, deadline, rng):
    P = PARAMS
    hole = [spec.parse_card(c) for c in practice["hole"]]
    board = [spec.parse_card(c) for c in practice["board"]]
    me = practice["seat"]
    opponents = sum(1 for i, folded in enumerate(practice["folded"])
                    if i != me and not folded and practice["stacks"][i] + practice["bets"][i] > 0)
    equity = spec.equity(hole, board, max(1, opponents), deadline, rng, P["GENERIC_SAMPLES"])
    pot, to_call = practice["pot"], practice["to_call"]
    stack = practice["stacks"][me]
    can_raise = practice["can_raise"]
    low, high = practice["min_raise_to"], practice["max_raise_to"]
    fair = 1.0 / (max(1, opponents) + 1)

    if stack <= P["GENERIC_SHOVE_BB"] * practice["big_blind"]:
        if equity >= fair + P["GENERIC_SHOVE_EDGE"]:
            return ("raise", high) if can_raise else ("call" if to_call else "check")
        return "check" if to_call == 0 else "fold"

    if to_call > 0:
        if equity >= fair + P["GENERIC_RAISE_EDGE"] and can_raise:
            return ("raise", max(low, min(high, practice["bets"][me] + to_call + pot)))
        if equity >= to_call / (pot + to_call) + P["GENERIC_CALL_MARGIN"]:
            return "call"
        return "fold"
    if equity >= fair + P["GENERIC_BET_EDGE"] and can_raise:
        return ("raise", max(low, min(high, practice["bets"][me] + int(P["GENERIC_BET_POT"] * pot))))
    return "check"
