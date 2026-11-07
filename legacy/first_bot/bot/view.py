"""M2: turn the kit's state into a fixed View. A new kit interface changes only this file.

The field names read here come from the practice engine and are provisional.
"""
from .variant import ACTIVE


class View:
    __slots__ = ("seat", "button", "street", "hole", "board", "pot", "to_call", "can_raise",
                 "min_raise", "max_raise", "stacks", "bets", "folded", "bb", "sb", "history",
                 "hand_number", "hands_remaining", "players_left", "seat_ids", "players")


def make_view(state):
    v = View()
    v.seat = state["seat"]
    v.button = state["button"]
    v.street = state["street"]
    v.hole = [ACTIVE.parse_card(c) for c in state["hole"]]
    v.board = [ACTIVE.parse_card(c) for c in state["board"]]
    v.pot = state["pot"]
    v.to_call = state["to_call"]
    v.can_raise = state["can_raise"]
    v.min_raise = state["min_raise_to"]
    v.max_raise = state["max_raise_to"]
    v.stacks = state["stacks"]
    v.bets = state["bets"]
    v.folded = state["folded"]
    v.bb = state["big_blind"]
    v.sb = state.get("small_blind", state["big_blind"] // 2)
    v.history = state["history"]
    v.hand_number = state.get("hand_number", 0)
    v.hands_remaining = state.get("hands_remaining", 100)
    v.players = len(state["stacks"])
    v.players_left = state.get("players_left", v.players)
    v.seat_ids = state.get("seat_ids") or list(range(v.players))
    return v
