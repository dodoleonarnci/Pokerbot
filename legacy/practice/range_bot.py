"""Range-versus-range bot. Run with: python3.12 play.py range_bot.py caller min_raiser

Every player, including us, is modelled as following this same program.
"""
import math
import random

import ranges as R
from equity import ALL_COMBOS, card, combo, mean, rate, runouts

# ---- Tunable strategy numbers -------------------------------------------------
FLOP_BET = 0.33           # "small" flop bet, as a fraction of the pot
VALUE_EQUITY = {"turn": 0.55, "river": 0.50, "flop": 0.50}  # equity when called
DRAW_MIN_SHARE = 0.15     # a turn bluff must reach DRAW_HIGH_EQUITY on this share of rivers
DRAW_HIGH_EQUITY = 0.75
USE_BLOCKERS = True       # river bluffs prefer hands that block the calling range
OPEN_BB = 2.5             # open size, in big blinds
THREEBET_X, THREEBET_OOP_X, FOURBET_X = 3.0, 3.5, 2.3
JAM_AT = 0.4              # shove instead of a raise that commits this share of our stack

# ---- Speed budget -------------------------------------------------------------
MAX_REFS = 250            # opposing-range combos used when rating a range
RATE_RUNOUTS = 10         # runouts sampled when rating a range
HERO_RUNOUTS = 30         # runouts sampled for our actual hand


# ---- Formulas from the plan ---------------------------------------------------
def mdf(pot, bet):
    """Share of a range that continues: a 50% pot bet leaves the top 67%."""
    return pot / (pot + bet)


def bluff_share(pot, bet):
    """Share of the betting range that bluffs, and also the equity a call needs."""
    return bet / (pot + 2 * bet)


def geometric_bet(pot, stack, streets):
    """The 2e size: equal pot-fraction bets that get all-in over the given streets."""
    if stack <= 0:
        return 0
    fraction = (((pot + 2 * stack) / pot) ** (1 / streets) - 1) / 2
    return min(stack, max(1, round(pot * fraction)))


def bluffs_for(value_count, pot, bet):
    """Bluff combos that make bluffs B / (P + 2B) of the betting range."""
    return round(value_count * bet / (pot + bet))


def blocker_score(hand, range_combos):
    if not range_combos:
        return 0.0
    return sum(1 for c in range_combos if set(c) & set(hand)) / len(range_combos)


# ---- One hand of range tracking and decisions -----------------------------------
class HandModel:
    BOARD_SIZE = {"preflop": 0, "flop": 3, "turn": 4, "river": 5}

    def __init__(self, state):
        self.players = len(state["stacks"])
        self.button = state["button"]
        self.hero = state["seat"]
        self.hole = combo(state["hole"])
        self.live = set(range(self.players))
        self.ranges = {s: list(ALL_COMBOS) for s in range(self.players)}
        self.raises = 0
        self.preflop_aggressor = None
        self.street = "preflop"
        self.street_aggressor = None
        self.previous_aggressor = None
        self.street_actions = 0
        self.street_bet = 0
        self.board = []
        self.events = []
        self.cache = {}

    # -- range helpers
    def _rated(self, combos, refs):
        key = (hash(tuple(combos)), hash(tuple(refs)), len(self.board))
        if key not in self.cache:
            samples = RATE_RUNOUTS if len(self.board) < 5 else 1
            self.cache[key] = rate(combos, refs, self.board, runouts(self.board, samples))
        return self.cache[key]

    def _top_share(self, combos, refs, share):
        """Keep the top share of combos, rated by equity against refs."""
        if not combos:
            return []
        rated = self._rated(combos, refs)
        ordered = sorted(combos, key=lambda c: (-mean(rated[c]), c))
        return sorted(ordered[:math.ceil(share * len(ordered))])

    def _refs(self, seat):
        """Everything seat's live opponents may hold, capped for speed."""
        combined = sorted({c for s in self.live if s != seat for c in self.ranges[s]})
        if len(combined) > MAX_REFS:
            combined = sorted(random.Random(len(combined)).sample(combined, MAX_REFS))
        return combined

    def _in_position(self, seat):
        return max(self.live, key=lambda s: (s - self.button - 1) % self.players) == seat

    def _betting_range(self, seat, pot, bet):
        """Value and bluff combos that seat bets, per the aggressor formula."""
        mine, refs = self.ranges[seat], self._refs(seat)
        if not mine or pot <= 0 or bet <= 0:
            return set()
        calling = self._top_share(refs, mine, mdf(pot, bet))
        rated = self._rated(mine, calling)
        threshold = VALUE_EQUITY[self.street]
        value = {c for c in mine if mean(rated[c]) >= threshold}
        if len(self.live) > 2:  # no bluffing into several opponents
            return value

        count = bluffs_for(len(value), pot, bet)
        rest = [c for c in mine if c not in value]
        if self.street == "river":
            # A wider pool from the bottom of the range, then the best blockers within it.
            bottom = sorted(rest, key=lambda c: (mean(rated[c]), c))
            if USE_BLOCKERS:
                pool = bottom[:2 * count]
                bluffs = sorted(pool, key=lambda c: (-blocker_score(c, calling), c))[:count]
            else:
                bluffs = bottom[:count]
        else:
            # Under 50% now, but very strong on enough runouts: draws.
            def draw(c):
                seen = rated[c]
                return sum(e >= DRAW_HIGH_EQUITY for e in seen) / len(seen) if seen else 0.0

            draws = [c for c in rest if mean(rated[c]) < 0.5 and draw(c) >= DRAW_MIN_SHARE]
            bluffs = sorted(draws, key=lambda c: (-draw(c), c))[:count]
        return value | set(bluffs)

    def _program(self, seat, pot, effective_stack):
        """What seat does when no bet is pending: (bet size, combos) or (0, None)."""
        heads_up = len(self.live) == 2
        if self.street == "flop":
            if heads_up:
                if not self._in_position(seat):  # X flop OOP
                    return 0, None
                return min(effective_stack, max(1, round(FLOP_BET * pot))), set(self.ranges[seat])
            if seat != self.preflop_aggressor:
                return 0, None
            size = min(effective_stack, max(1, round(FLOP_BET * pot)))
            return size, self._betting_range(seat, pot, size)

        # No dunks: never lead first to act into last street's aggressor.
        first_to_act = self.street_actions == 0
        if (first_to_act and self.previous_aggressor is not None
                and self.previous_aggressor != seat):
            return 0, None
        streets_left = 2 if self.street == "turn" else 1
        size = geometric_bet(pot, effective_stack, streets_left)
        if size <= 0:
            return 0, None
        return size, self._betting_range(seat, pot, size)

    @staticmethod
    def _effective(stacks, seat, live):
        others = [stacks[s] for s in live if s != seat]
        return min(stacks[seat], max(others)) if others else 0

    # -- replaying the action
    def _enter_street(self, street, board):
        self.previous_aggressor = self.street_aggressor
        self.street, self.street_aggressor = street, None
        self.street_actions, self.street_bet = 0, 0
        self.board = [card(c) for c in board[:self.BOARD_SIZE[street]]]
        blocked = set(self.board)
        for s in self.ranges:
            self.ranges[s] = [c for c in self.ranges[s]
                              if c[0] not in blocked and c[1] not in blocked]

    def _preflop_event(self, event):
        seat, kind = event["seat"], event["action"]
        pos = R.position(seat, self.button, self.players)
        if kind == "raise":
            table = {0: R.OPEN, 1: R.THREEBET, 2: R.FOURBET}.get(self.raises, R.JAM)
            self.ranges[seat] = R.top(table[pos])
            self.raises += 1
            self.preflop_aggressor = self.street_aggressor = seat
        elif kind == "call":
            if self.raises == 0:
                self.ranges[seat] = R.top(R.LIMP)
            elif self.raises == 1:
                self.ranges[seat] = R.band(R.THREEBET[pos], R.FLAT[pos])
            elif self.raises == 2:
                self.ranges[seat] = R.band(R.FOURBET[pos], R.CALL_3BET[pos])
            else:
                self.ranges[seat] = R.top(R.JAM[pos])

    def _postflop_event(self, event):
        seat, kind = event["seat"], event["action"]
        if kind == "check":
            effective = self._effective(event["stacks"], seat, self.live)
            size, combos = self._program(seat, event["pot"], effective)
            if size and combos and len(combos) < len(self.ranges[seat]):
                self.ranges[seat] = [c for c in self.ranges[seat] if c not in combos]
        elif kind == "raise":
            bet = event["to"] - self.street_bet
            pot = event["pot"] + event["amount"] - bet
            whole_range = (self.street == "flop" and len(self.live) == 2
                           and self._in_position(seat))
            if not whole_range:
                combos = self._betting_range(seat, pot, bet)
                self.ranges[seat] = sorted(combos) or self._top_share(
                    self.ranges[seat], self._refs(seat), 0.15)
            self.street_bet = event["to"]
            self.street_aggressor = seat
        elif kind == "call" and event["amount"] > 0:
            pot = event["pot"] - event["amount"]
            share = mdf(pot, event["amount"]) if pot > 0 else 1.0
            self.ranges[seat] = self._top_share(self.ranges[seat], self._refs(seat), share)

    def sync(self, state):
        for event in state["history"][len(self.events):]:
            if event["street"] != self.street:
                self._enter_street(event["street"], state["board"])
            if event["action"] == "fold":
                self.live.discard(event["seat"])
            elif self.street == "preflop":
                self._preflop_event(event)
            else:
                self._postflop_event(event)
            self.street_actions += 1
            self.events.append(event)
        if state["street"] != self.street:
            self._enter_street(state["street"], state["board"])

    # -- decisions
    def _hero_equity(self):
        """Equity of our exact hand, multiplied across live opponents."""
        total = 1.0
        outs = runouts(self.board, HERO_RUNOUTS)
        for seat in self.live - {self.hero}:
            refs = [c for c in self.ranges[seat] if not set(c) & set(self.hole)]
            rated = rate([self.hole], refs, self.board, outs)
            total *= mean(rated[self.hole])
        return total

    def _raise_or(self, state, target, otherwise):
        if not state["can_raise"]:
            return otherwise
        if target >= JAM_AT * state["max_raise_to"]:
            target = state["max_raise_to"]
        return ("raise", max(state["min_raise_to"], min(int(target), state["max_raise_to"])))

    def _preflop_decision(self, state):
        seat, bb = self.hero, state["big_blind"]
        pos = R.position(seat, self.button, self.players)
        strength = R.percentile(self.hole)
        free = state["to_call"] == 0
        passive = "check" if free else "call"
        give_up = "check" if free else "fold"
        current = max(state["bets"])

        if self.raises == 0:
            if strength <= R.OPEN[pos]:
                return self._raise_or(state, OPEN_BB * bb, passive)
            return give_up
        if self.raises == 1:
            if strength <= R.THREEBET[pos]:
                ip = self._in_position(seat)
                return self._raise_or(
                    state, current * (THREEBET_X if ip else THREEBET_OOP_X), passive)
            return "call" if strength <= R.FLAT[pos] else give_up
        if self.raises == 2:
            if strength <= R.FOURBET[pos]:
                return self._raise_or(state, current * FOURBET_X, passive)
            return "call" if strength <= R.CALL_3BET[pos] else give_up
        if strength <= R.JAM[pos]:
            return self._raise_or(state, state["max_raise_to"], passive)
        return give_up

    def decide(self, state):
        if self.street == "preflop":
            return self._preflop_decision(state)

        to_call, pot = state["to_call"], state["pot"]
        if to_call > 0:
            needed = to_call / (pot + to_call)  # B / (P + 2B) when facing a plain bet
            return "call" if self._hero_equity() >= needed else "fold"

        if not state["can_raise"]:
            return "check"
        if self.hole not in self.ranges[self.hero]:
            self.ranges[self.hero] = sorted(self.ranges[self.hero] + [self.hole])
        effective = self._effective(state["stacks"], self.hero, self.live)
        size, combos = self._program(self.hero, pot, effective)
        if not size or self.hole not in combos:
            return "check"
        target = state["bets"][self.hero] + size
        return ("raise", max(state["min_raise_to"], min(target, state["max_raise_to"])))


class RangeBot:
    def __init__(self):
        self.model = None

    def __call__(self, state):
        model, history = self.model, state["history"]
        if (model is None or model.hole != combo(state["hole"])
                or model.hero != state["seat"] or model.button != state["button"]
                or history[:len(model.events)] != model.events):
            model = self.model = HandModel(state)
        model.sync(state)
        return model.decide(state)


act = RangeBot()
