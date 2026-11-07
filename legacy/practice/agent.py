"""Your practice agent. Edit act(), then run:

    python3.12 play.py agent.py min_raiser caller maniac --hands 2000

Actions: "fold", "check", "call" or ("raise", total_street_bet).
An illegal action or an exception counts as a failed decision: check if free, else fold.

state keys: seat, button, street, hole, board, pot, to_call, can_raise,
min_raise_to, max_raise_to, stacks, bets, folded, big_blind, history.
"""
from engine import RANKS, best_hand


def act(state):
    to_call = state["to_call"]
    pot = state["pot"]

    if state["street"] == "preflop":
        high, low = sorted((RANKS.index(c[0]) for c in state["hole"]), reverse=True)
        strong = high == low or high >= RANKS.index("Q") and low >= RANKS.index("T")
        if strong and state["can_raise"]:
            target = 3 * state["big_blind"]
            return ("raise", max(state["min_raise_to"], min(target, state["max_raise_to"])))
        if to_call == 0:
            return "check"
        return "call" if strong or to_call <= state["big_blind"] else "fold"

    category = best_hand(state["hole"] + state["board"])[0]
    if category >= 2 and state["can_raise"]:
        target = state["bets"][state["seat"]] + to_call + pot // 2
        return ("raise", max(state["min_raise_to"], min(target, state["max_raise_to"])))
    if to_call == 0:
        return "check"
    return "call" if category >= 1 and to_call <= pot // 2 else "fold"
