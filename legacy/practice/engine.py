"""Small no-limit Texas hold'em engine for practice. Standard library only.

This is NOT the tournament engine or SDK. The agent interface here is a stand-in.
"""
import time
from collections import Counter
from itertools import combinations

RANKS = "23456789TJQKA"
SUITS = "cdhs"
DECK = [r + s for r in RANKS for s in SUITS]
STREETS = ("preflop", "flop", "turn", "river")


def eval5(cards):
    """Rank five cards like 'As'. A larger tuple is a stronger hand."""
    ranks = sorted((RANKS.index(c[0]) for c in cards), reverse=True)
    counts = Counter(ranks)
    grouped = sorted(counts, key=lambda r: (counts[r], r), reverse=True)
    shape = sorted(counts.values(), reverse=True)
    flush = len({c[1] for c in cards}) == 1

    straight_high = None
    if len(counts) == 5:
        if ranks[0] - ranks[4] == 4:
            straight_high = ranks[0]
        elif ranks == [12, 3, 2, 1, 0]:  # A-2-3-4-5
            straight_high = 3

    if straight_high is not None and flush:
        return (8, straight_high)
    if shape == [4, 1]:
        return (7, *grouped)
    if shape == [3, 2]:
        return (6, *grouped)
    if flush:
        return (5, *ranks)
    if straight_high is not None:
        return (4, straight_high)
    if shape == [3, 1, 1]:
        return (3, *grouped)
    if shape == [2, 2, 1]:
        return (2, *grouped)
    if shape == [2, 1, 1, 1]:
        return (1, *grouped)
    return (0, *ranks)


def best_hand(cards):
    """Best five-card rank from five to seven cards."""
    return max(eval5(c) for c in combinations(cards, 5))


def side_pots(contrib, folded):
    """Split contributions into [[amount, eligible seats], ...].

    An uncalled excess forms a layer only its owner can win, which refunds it.
    """
    pots, prev = [], 0
    for level in sorted({c for c in contrib if c > 0}):
        amount = sum(min(c, level) - min(c, prev) for c in contrib)
        eligible = [i for i, c in enumerate(contrib) if c >= level and not folded[i]]
        if pots and (not eligible or eligible == pots[-1][1]):
            pots[-1][0] += amount
        else:
            pots.append([amount, eligible])
        prev = level
    return pots


class Hand:
    def __init__(self, agents, stacks, button, sb, bb, rng, extras=None, limits=None):
        self.agents, self.stacks = agents, list(stacks)
        self.extras = extras or {}  # extra state fields, such as hand number
        self.limits = limits or {}  # seat -> decision time limit in seconds
        self.timeouts = [0] * len(agents)
        self.button, self.sb, self.bb = button, sb, bb
        self.n = len(agents)
        self.deck = DECK[:]
        rng.shuffle(self.deck)
        self.holes = [[self.deck.pop(), self.deck.pop()] for _ in agents]
        self.board = []
        self.folded = [False] * self.n
        self.bets = [0] * self.n
        self.contrib = [0] * self.n
        self.history = []
        self.failures = [0] * self.n
        self.street = "preflop"

    def _pay(self, seat, amount):
        amount = min(amount, self.stacks[seat])
        self.stacks[seat] -= amount
        self.bets[seat] += amount
        self.contrib[seat] += amount

    def _live(self):
        return [i for i in range(self.n) if not self.folded[i]]

    def _can_act(self):
        return [i for i in self._live() if self.stacks[i] > 0]

    def _state(self, seat, current, last_raise, can_raise):
        return {
            "seat": seat,
            "button": self.button,
            "street": self.street,
            "hole": list(self.holes[seat]),
            "board": list(self.board),
            "pot": sum(self.contrib),
            "to_call": min(current - self.bets[seat], self.stacks[seat]),
            "can_raise": can_raise,
            "min_raise_to": min(current + last_raise, self.bets[seat] + self.stacks[seat]),
            "max_raise_to": self.bets[seat] + self.stacks[seat],
            "stacks": list(self.stacks),
            "bets": list(self.bets),
            "folded": list(self.folded),
            "big_blind": self.bb,
            "history": list(self.history),
            "small_blind": self.sb,
            **self.extras,
        }

    def _decide(self, seat, state):
        """Return a legal (action, raise_to). A bad decision checks or folds."""
        try:
            limit = self.limits.get(seat)
            start = time.perf_counter()
            reply = self.agents[seat](state)
            if limit is not None and time.perf_counter() - start > limit:
                self.timeouts[seat] += 1
                return ("check" if state["to_call"] == 0 else "fold"), None
            kind = reply[0] if isinstance(reply, (tuple, list)) else reply
            if kind in ("fold", "call") or (kind == "check" and state["to_call"] == 0):
                return kind, None
            if kind == "raise" and state["can_raise"]:
                to = reply[1]
                if (isinstance(to, int) and not isinstance(to, bool)
                        and state["min_raise_to"] <= to <= state["max_raise_to"]):
                    return kind, to
        except Exception:
            pass
        self.failures[seat] += 1
        return ("check" if state["to_call"] == 0 else "fold"), None

    def _betting_round(self, first, current, last_raise):
        actors = self._can_act()
        if len(actors) <= 1 and all(self.bets[i] >= current for i in actors):
            return
        pending, acted, seat = set(actors), set(), first
        while pending and len(self._live()) > 1:
            if seat not in pending:
                seat = (seat + 1) % self.n
                continue
            others = [i for i in self._can_act() if i != seat]
            can_raise = (seat not in acted and bool(others)
                         and self.bets[seat] + self.stacks[seat] > current)
            state = self._state(seat, current, last_raise, can_raise)
            pot_before, stacks_before = sum(self.contrib), list(self.stacks)
            kind, to = self._decide(seat, state)
            pending.discard(seat)
            acted.add(seat)
            if kind == "fold":
                self.folded[seat] = True
            elif kind == "call":
                self._pay(seat, current - self.bets[seat])
            elif kind == "raise":
                size = to - current
                self._pay(seat, to - self.bets[seat])
                current = to
                if size >= last_raise:  # a full raise reopens the action
                    last_raise = size
                    acted = {seat}
                    pending = set(others)
                else:  # a short all-in only asks others to match it
                    pending |= {i for i in others if self.bets[i] < current}
            self.history.append({
                "street": self.street, "seat": seat, "action": kind, "to": to,
                "pot": pot_before, "amount": sum(self.contrib) - pot_before,
                "stacks": stacks_before,
            })
            seat = (seat + 1) % self.n

    def _award(self):
        winnings = [0] * self.n
        scores = {}
        if len(self._live()) > 1:
            scores = {i: best_hand(self.holes[i] + self.board) for i in self._live()}
        for amount, eligible in side_pots(self.contrib, self.folded):
            if len(eligible) == 1:
                winners = eligible
            else:
                top = max(scores[i] for i in eligible)
                winners = [i for i in eligible if scores[i] == top]
            share, odd = divmod(amount, len(winners))
            # Odd chips go to the first winners left of the button.
            order = sorted(winners, key=lambda i: (i - self.button - 1) % self.n)
            for k, i in enumerate(order):
                winnings[i] += share + (1 if k < odd else 0)
        for i, won in enumerate(winnings):
            self.stacks[i] += won

    def play(self):
        if self.n == 2:
            sb_seat, bb_seat = self.button, (self.button + 1) % 2
        else:
            sb_seat, bb_seat = (self.button + 1) % self.n, (self.button + 2) % self.n
        self._pay(sb_seat, self.sb)
        self._pay(bb_seat, self.bb)
        self._betting_round((bb_seat + 1) % self.n, self.bb, self.bb)
        for street, cards in (("flop", 3), ("turn", 1), ("river", 1)):
            if len(self._live()) == 1:
                break
            self.street = street
            self.board += [self.deck.pop() for _ in range(cards)]
            self.bets = [0] * self.n
            self._betting_round((self.button + 1) % self.n, 0, self.bb)
        self._award()
        return self.stacks
