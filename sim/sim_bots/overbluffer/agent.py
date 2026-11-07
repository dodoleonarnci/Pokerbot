"""Practice opponent: bets the pot with anything when checked to, calls only with a pair."""
import random

import poker_agent_sdk
from poker_agent_sdk import Action

RANKS = "23456789TJQKA"


def ranks(cards):
    return [RANKS.index(c[0]) for c in cards]


def has_pair(state):
    hole, board = ranks(state.cards), ranks(state.board)
    return any(r in board for r in hole) or len(set(hole)) < len(hole)


def bet(state, fraction):
    option = state.can("raise")
    if option is None:
        return None
    return Action.raise_to(max(option.min_amount, min(option.max_amount, int(state.pot * fraction))))


class Agent(poker_agent_sdk.Agent):
    def act(self, state, memory):
        if state.phase != "betting":
            first = state.legal_actions[0]
            return Action(first.kind, first.min_amount), memory
        if not state.board:
            if state.can("check"):
                return Action.check(), memory
            playable = max(ranks(state.cards)) >= 8 or len(set(ranks(state.cards))) < 3
            if playable and state.to_call <= state.pot:
                return Action.call(), memory
            return Action.fold(), memory
        if state.can("check"):
            action = bet(state, 1.0) if random.random() < 0.75 else None
            return action or Action.check(), memory
        if has_pair(state) or random.random() < 0.15:
            return Action.call(), memory
        return Action.fold(), memory
