"""Practice opponent: bets only top pair or better and folds anything weaker to a bet."""
import poker_agent_sdk
from poker_agent_sdk import Action

RANKS = "23456789TJQKA"


def ranks(cards):
    return [RANKS.index(c[0]) for c in cards]


def strong(state):
    hole, board = ranks(state.cards), ranks(state.board)
    top = max(board)
    pocket = len(hole) == 2 and hole[0] == hole[1]
    return top in hole or (pocket and hole[0] > top) or sum(r in board for r in set(hole)) >= 2


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
            hand = ranks(state.cards)
            playable = len(set(hand)) < 3 or sorted(hand)[-2] >= 10
            if playable and state.to_call <= state.pot:
                return Action.call(), memory
            return Action.fold(), memory
        if state.can("check"):
            return (bet(state, 0.5) if strong(state) else None) or Action.check(), memory
        return (Action.call() if strong(state) else Action.fold()), memory
