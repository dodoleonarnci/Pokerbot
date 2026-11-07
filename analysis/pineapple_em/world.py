"""A heads-up postflop stand-in for the Bay Area variant with a known population policy."""
import random
from dataclasses import dataclass

import numpy as np

from .cards import BoardView, best_two_score, bucket, evaluate
from .em import Observation

RAISER, CALLER = 0, 1
N_LINES = 2

A_OPEN, N_VS_CHECK, N_VS_SMALL, N_VS_BIG, A_VS_SMALL, A_VS_BIG = range(6)
NODE_TYPES = 6
N_NODES = 3 * NODE_TYPES
CHECK, BET_SMALL, BET_BIG = 0, 1, 2
FOLD, CALL = 0, 1
N_ACTIONS = 3
BET_SIZE = {BET_SMALL: 1 / 3, BET_BIG: 1.0}


def node_id(street, node_type):
    return street * NODE_TYPES + node_type


_OPEN = (
    [[.45, .40, .15], [.45, .40, .15], [.30, .35, .35], [.65, .30, .05], [.25, .55, .20], [.20, .30, .50]],
    [[.65, .20, .15], [.60, .25, .15], [.40, .25, .35], [.70, .25, .05], [.35, .45, .20], [.20, .30, .50]],
    [[.70, .10, .20], [.70, .10, .20], [.70, .10, .20], [.85, .12, .03], [.45, .45, .10], [.15, .25, .60]],
)
_STAB = (
    [[.65, .30, .05], [.60, .30, .10], [.45, .30, .25], [.70, .25, .05], [.35, .50, .15], [.30, .30, .40]],
    [[.70, .20, .10], [.65, .25, .10], [.50, .25, .25], [.75, .20, .05], [.40, .45, .15], [.30, .30, .40]],
    [[.75, .05, .20], [.75, .05, .20], [.75, .05, .20], [.85, .12, .03], [.50, .40, .10], [.20, .25, .55]],
)
_VS_SMALL = (
    [[.75, .25], [.55, .45], [.15, .85], [.35, .65], [.10, .90], [.02, .98]],
    [[.80, .20], [.60, .40], [.20, .80], [.45, .55], [.15, .85], [.02, .98]],
    [[.90, .10], [.90, .10], [.90, .10], [.55, .45], [.20, .80], [.02, .98]],
)
_VS_BIG = (
    [[.90, .10], [.75, .25], [.30, .70], [.60, .40], [.25, .75], [.05, .95]],
    [[.92, .08], [.80, .20], [.35, .65], [.70, .30], [.30, .70], [.05, .95]],
    [[.97, .03], [.97, .03], [.97, .03], [.80, .20], [.40, .60], [.05, .95]],
)


def _true_policy():
    policy = np.zeros((N_NODES, 6, N_ACTIONS))
    for street in range(3):
        for node_type, table in ((A_OPEN, _OPEN), (N_VS_CHECK, _STAB), (N_VS_SMALL, _VS_SMALL),
                                 (N_VS_BIG, _VS_BIG), (A_VS_SMALL, _VS_SMALL), (A_VS_BIG, _VS_BIG)):
            rows = np.array(table[street])
            policy[node_id(street, node_type), :, :rows.shape[1]] = rows
    return policy


TRUE_POLICY = _true_policy()


def _barreling_policy():
    policy = TRUE_POLICY.copy()
    for street in (1, 2):
        for weak in (0, 1, 2):
            policy[node_id(street, A_OPEN), weak] = [.35, .05, .60]
            policy[node_id(street, A_VS_SMALL), weak, :2] = [.97, .03]
            policy[node_id(street, A_VS_BIG), weak, :2] = [.97, .03]
        policy[node_id(street, A_OPEN), 5] = [.15, .15, .70]
        policy[node_id(street, N_VS_SMALL), 3, :2] = [.60, .40]
        policy[node_id(street, N_VS_BIG), 3, :2] = [.80, .20]
        policy[node_id(street, N_VS_BIG), 4, :2] = [.55, .45]
    return policy


WORLDS = {"base": TRUE_POLICY, "barreling": _barreling_policy()}


def _thresholds(seed=7, samples=20000):
    rng = random.Random(seed)
    scores = sorted(best_two_score(rng.sample(range(52), 3)) for _ in range(samples))
    return scores[int(0.60 * samples)], scores[int(0.40 * samples)]


RAISER_THRESHOLD, CALLER_THRESHOLD = _thresholds()


@dataclass
class Seat:
    dealt: tuple
    discard: int
    exposed: int
    hidden: int
    smart: bool


@dataclass
class Hand:
    seats: tuple
    board: tuple
    board_seen: int
    events: list
    showdown: bool


class BayAreaWorld:
    def __init__(self, seed, smart_share=0.6, loose=0.08, policy=TRUE_POLICY):
        self.rng = random.Random(seed)
        self.smart_share = smart_share
        self.loose = loose
        self.policy = policy

    def _plays(self, cards, threshold):
        return best_two_score(cards) >= threshold or self.rng.random() < self.loose

    def _smart_select(self, cards, flop):
        rng = self.rng
        view = BoardView(flop)
        options = []
        for drop in range(3):
            kept = [cards[i] for i in range(3) if i != drop]
            options.append(((bucket(kept[0], kept[1], view), evaluate(kept + list(flop))), drop, kept))
        _, drop, (a, b) = max(options) if rng.random() < 0.9 else rng.choice(options)
        board_ranks = {card >> 2 for card in flop}
        a_hits, b_hits = (a >> 2) in board_ranks, (b >> 2) in board_ranks
        if a_hits != b_hits:
            quiet = b if a_hits else a
        elif a >> 2 != b >> 2:
            quiet = a if a >> 2 < b >> 2 else b
        else:
            quiet = a if rng.random() < 0.5 else b
        exposed = quiet if rng.random() < 0.8 else (b if quiet == a else a)
        return cards[drop], exposed, b if exposed == a else a

    def _select(self, cards, flop):
        if self.rng.random() < self.smart_share:
            return Seat(tuple(cards), *self._smart_select(cards, flop), True)
        return Seat(tuple(cards), cards[2], cards[0], cards[1], False)

    def _act(self, node, strength):
        probs = self.policy[node, strength]
        u = self.rng.random()
        for action, p in enumerate(probs):
            u -= p
            if u < 0:
                return action
        return int(np.flatnonzero(probs)[-1])

    def hand(self):
        rng = self.rng
        while True:
            deck = list(range(52))
            rng.shuffle(deck)
            if self._plays(deck[0:3], RAISER_THRESHOLD) and self._plays(deck[3:6], CALLER_THRESHOLD):
                break
        board = tuple(deck[6:11])
        seats = (self._select(deck[0:3], board[:3]), self._select(deck[3:6], board[:3]))
        events = []
        for street in range(3):
            view = BoardView(board[:3 + street])
            strengths = [bucket(s.exposed, s.hidden, view) for s in seats]
            if self._street(street, strengths, events):
                return Hand(seats, board, 3 + street, events, False)
        return Hand(seats, board, 5, events, True)

    def _street(self, street, strengths, events):
        def play(role, node_type):
            node = node_id(street, node_type)
            action = self._act(node, strengths[role])
            events.append((role, node, action, street))
            return action

        first = play(RAISER, A_OPEN)
        if first == CHECK:
            second = play(CALLER, N_VS_CHECK)
            if second == CHECK:
                return False
            return play(RAISER, A_VS_SMALL if second == BET_SMALL else A_VS_BIG) == FOLD
        return play(CALLER, N_VS_SMALL if first == BET_SMALL else N_VS_BIG) == FOLD


def observations(hands, visibility="realistic"):
    """One Observation per player per hand, as an outside observer of the history sees it.

    visibility: "realistic" (hidden card known only after showdown), "full" (always known),
    or "showdown" (keep only hands that reached showdown, the naive sample).
    """
    for hand in hands:
        if visibility == "showdown" and not hand.showdown:
            continue
        for role in (RAISER, CALLER):
            seat, other = hand.seats[role], hand.seats[1 - role]
            blocked = {other.exposed, other.hidden} if hand.showdown else {other.exposed}
            known = visibility == "full" or hand.showdown
            yield Observation(
                line=role, exposed=seat.exposed, board=hand.board[:hand.board_seen],
                blocked=frozenset(blocked),
                decisions=tuple((n, a, s) for r, n, a, s in hand.events if r == role),
                hidden=seat.hidden if known else None)
