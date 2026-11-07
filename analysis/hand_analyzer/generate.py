"""Plays 8 simulated pool bots with planted tendencies and writes canonical JSONL plus planted.json.

The betting engine here is deliberately separate from spot.py, so the tracker is checked against
an independent implementation of the rules. Variant-specific policy lives in `select_cards`.
"""

import argparse
import json
import multiprocessing
import random
from itertools import combinations

import eval7

from buckets import R, RANKS, SUITS, STRENGTH_ORDER, class3, pairs_board, strength_class
from spot import positions, post_size_code

try:
    import orjson

    def dumps(obj) -> bytes:
        return orjson.dumps(obj)
except ImportError:
    def dumps(obj) -> bytes:
        return json.dumps(obj, separators=(",", ":")).encode()

DECK = [r + s for r in RANKS for s in SUITS]
EVAL = {c: eval7.Card(c) for c in DECK}

PLANTED = {
    "open": {"UTG": 0.12, "UTG+1": 0.14, "LJ": 0.17, "HJ": 0.21, "CO": 0.27, "BTN": 0.36, "SB": 0.30},
    "limp": 0.05,
    "three_bet": 0.08,
    "call_open": 0.20,
    "vs_3bet": {"fold": 0.55, "call": 0.35, "raise": 0.10},
    "vs_4bet": {"fold": 0.45, "call": 0.50, "raise": 0.05},
    "bet": {"air": 0.15, "draw": 0.35, "weak": 0.25, "top": 0.55, "strong": 0.75},
    "bet_sizes": {"S": [0.40, 0.33], "M": [0.40, 0.60], "L": [0.15, 1.00], "O": [0.05, 1.50]},
    "fold_small": {"air": 0.55, "draw": 0.25, "weak": 0.35, "top": 0.10, "strong": 0.02},
    "fold_big": {"air": 0.85, "draw": 0.55, "weak": 0.70, "top": 0.30, "strong": 0.05},
    "raise_vs_bet": {"air": 0.0, "draw": 0.06, "weak": 0.0, "top": 0.04, "strong": 0.25},
    "keep_best": 0.90,
    "show_helper": 0.60,
    "turn_leak_fold": 0.80,  # Folds to any turn bet after a called small flop bet.
    "hidden_cards": 0.05,
}


def _percentiles() -> dict:
    """Each of the 22,100 hands' uniform rank in [0, 1), best first, by a simple hand score."""
    def score(hand):
        ranks = sorted((R[c[0]] for c in hand), reverse=True)
        suited = len({c[1] for c in hand}) < 3
        paired = len(set(ranks)) < 3
        pair_rank = max((r for r in ranks if ranks.count(r) > 1), default=0)
        return (paired * (8 + pair_rank * 1.5) + ranks[0] * 1.2 + ranks[1] * 0.7 + ranks[2] * 0.2
                + suited * 2.0)
    hands = sorted(combinations(DECK, 3), key=lambda h: (-score(h), h))
    return {frozenset(h): i / len(hands) for i, h in enumerate(hands)}


PCT = _percentiles()


def select_cards(rng, cards3, flop, plant, hidden):
    """Variant policy: keep the best pair most of the time; show the helper card 60% of the time."""
    options = []
    for discard in range(3):
        kept = [c for i, c in enumerate(cards3) if i != discard]
        options.append((STRENGTH_ORDER[strength_class(kept, flop)], discard, kept))
    best = max(o[0] for o in options)
    good = [o for o in options if o[0] == best]
    worse = [o for o in options if o[0] < best]
    chosen = rng.choice(worse) if worse and rng.random() >= plant["keep_best"] else rng.choice(good)
    kept = chosen[2]
    helpers = [c for c in kept if pairs_board(c, flop)]
    if len(helpers) == 1:
        helper = helpers[0]
        other = kept[0] if kept[1] == helper else kept[1]
        shown = helper if rng.random() < plant["show_helper"] else other
    else:
        shown = rng.choice(kept)
    return kept, shown, cards3[chosen[1]]


def _pick(rng, weights: dict) -> str:
    x = rng.random()
    total = 0.0
    last = None
    for kind, p in weights.items():
        total += p
        last = kind
        if x < total:
            return kind
    return last


class Table:
    def __init__(self, rng, plant, hid):
        self.rng, self.plant, self.hid = rng, plant, hid
        n = rng.choices((8, 7, 6), weights=(85, 10, 5))[0]
        numbers = sorted(rng.sample(range(8), n))
        self.bb = rng.choice((20, 40, 60, 100))
        self.sb = self.bb // 2
        button = rng.choice(numbers)
        at = numbers.index(button)
        self.button = button
        self.seats = [numbers[(at + 1 + i) % n] for i in range(n)]
        self.pos = positions(n)
        self.n = n
        self.start = [rng.randint(40, 150) * self.bb for _ in range(n)]
        self.stack = list(self.start)
        self.total = [0] * n
        self.bet = [0] * n
        self.live = [True] * n
        self.entered = [False] * n
        self.actions = []
        self.record_folds = hid % 2 == 0  # Half the hands leave out never-entered folds.
        deck = rng.sample(DECK, 3 * n + 5)
        self.cards3 = [deck[3 * i:3 * i + 3] for i in range(n)]
        self.board_all = deck[3 * n:]
        self.board = []
        self.kept = [None] * n
        self.shows = {}

    def _pay(self, i, chips):
        self.stack[i] -= chips
        self.bet[i] += chips
        self.total[i] += chips

    def betting(self, street):
        n, live, stack, bet = self.n, self.live, self.stack, self.bet
        self.street = street
        self.raises = 1 if street == 0 else 0
        if street == 0:
            self._pay(0, min(self.sb, stack[0]))
            self._pay(1, min(self.bb, stack[1]))
            cur, inc = self.bb, self.bb
            first = 2 % n
            self.limped = False
        else:
            bet[:] = [0] * n
            cur, inc = 0, self.bb
            first = 0
            self.flop_bets = 0
        queue = [(first + k) % n for k in range(n)]
        queue = [i for i in queue if live[i] and stack[i] > 0]
        while queue:
            if sum(live) == 1:
                return
            i = queue.pop(0)
            others = any(live[j] and stack[j] > 0 and j != i for j in range(n))
            kind, to = self.decide(i, cur, inc, others)
            if kind == "fold":
                live[i] = False
                if street > 0 or self.entered[i] or self.record_folds:
                    self.actions.append({"street": street, "seat": self.seats[i], "type": "fold"})
                continue
            if kind == "check":
                self.actions.append({"street": street, "seat": self.seats[i], "type": "check"})
                continue
            if kind == "call":
                self._pay(i, min(cur - bet[i], stack[i]))
                self.entered[i] = True
                if street == 0:
                    self.limped = True
                else:
                    self.line_called = True
                self.actions.append({"street": street, "seat": self.seats[i], "type": "call"})
                continue
            self._pay(i, to - bet[i])
            self.entered[i] = True
            kind = "bet" if street > 0 and cur == 0 else "raise"
            self.actions.append({"street": street, "seat": self.seats[i], "type": kind, "to": to})
            inc = max(inc, to - cur)
            cur = to
            self.raises += 1
            queue = [(i + k) % n for k in range(1, n)]
            queue = [j for j in queue if live[j] and stack[j] > 0]

    def decide(self, i, cur, inc, others):
        owed = cur - self.bet[i]
        plant, rng = self.plant, self.rng
        min_to = cur + inc
        can_raise = others and self.stack[i] > owed
        cap = self.bet[i] + self.stack[i]
        if self.street == 0:
            pct = PCT[frozenset(self.cards3[i])]
            strength = 2 * (1 - pct)
            pos = self.pos[i]
            if self.raises == 1:
                if owed == 0:  # The big blind's option.
                    return ("raise", min(cap, 3 * self.bb)) if can_raise and rng.random() < 0.10 else ("check", 0)
                p_open = plant["open"].get(pos, 0.0) * strength
                x = rng.random()
                if x < p_open and can_raise:
                    size = rng.choices((2, 3, 4, 6), weights=(35, 55, 8, 2))[0]
                    return "raise", min(cap, max(min_to, size * self.bb))
                if x < p_open + plant["limp"]:
                    return "call", 0
                return "fold", 0
            if self.raises == 2:
                x = rng.random()
                p_three = plant["three_bet"] * strength
                if x < p_three and can_raise:
                    multiple = rng.choices((2, 3, 4), weights=(25, 60, 15))[0]
                    return "raise", min(cap, max(min_to, multiple * cur))
                if x < p_three + plant["call_open"]:
                    return "call", 0
                return "fold", 0
            table = plant["vs_3bet"] if self.raises == 3 else plant["vs_4bet"]
            kind = _pick(rng, table)
            if kind == "raise" and can_raise:
                return "raise", min(cap, max(min_to, 3 * cur))
            return ("fold", 0) if kind == "fold" else ("call", 0)
        kept = self.kept[i]
        cls = strength_class(kept, self.board)
        pot = sum(self.total)
        if owed == 0:
            if rng.random() < plant["bet"][cls]:
                size = _pick(rng, {k: v[0] for k, v in plant["bet_sizes"].items()})
                amount = max(self.bb, int(plant["bet_sizes"][size][1] * pot))
                amount = min(cap, amount)
                self.note_bet(amount, pot)
                return "bet", amount
            return "check", 0
        # Facing a bet.
        if (self.street == 2 and self.raises == 1 and self.flop_line == "bS-c"
                and rng.random() < plant["turn_leak_fold"]):
            return "fold", 0
        if self.street == 2 and self.raises == 1 and self.flop_line == "bS-c":
            return self._continue(i, cur, min_to, cap, can_raise, pot, owed, cls, leak=True)
        size = post_size_code(self.last_bet, self.pot_before_bet)
        table = plant["fold_small"] if size == "S" else plant["fold_big"] if size in "LO" else None
        p_fold = table[cls] if table else (plant["fold_small"][cls] + plant["fold_big"][cls]) / 2
        if rng.random() < p_fold:
            return "fold", 0
        return self._continue(i, cur, min_to, cap, can_raise, pot, owed, cls, leak=False)

    def _continue(self, i, cur, min_to, cap, can_raise, pot, owed, cls, leak):
        if not leak and can_raise and self.rng.random() < self.plant["raise_vs_bet"][cls]:
            to = min(cap, max(min_to, cur + int(0.75 * (pot + owed))))
            self.last_bet = to - cur
            self.pot_before_bet = pot + owed
            return "raise", to
        return "call", 0

    def note_bet(self, amount, pot):
        self.last_bet = amount
        self.pot_before_bet = pot
        if self.street == 1:
            self.flop_bet_code = "b" + post_size_code(amount, pot)

    def select(self):
        flop = self.board
        for i in range(self.n):
            if self.live[i]:
                self.kept[i], shown, discard = select_cards(self.rng, self.cards3[i], flop, self.plant, False)
                self.shows[i] = (shown, discard)

    def play(self):
        self.flop_line = "x"
        self.betting(0)
        for street in (1, 2, 3):
            if sum(self.live) == 1:
                break
            self.board = self.board_all[: street + 2]
            if street == 1:
                self.select()
                self.flop_bet_code = ""
            start_actions = len(self.actions)
            self.line_called = False
            if sum(1 for i in range(self.n) if self.live[i] and self.stack[i] > 0) >= 2:
                self.betting(street)
            else:
                self.bet[:] = [0] * self.n
            if street == 1:
                bets = [a for a in self.actions[start_actions:] if a["type"] in ("bet", "raise")]
                calls = any(a["type"] == "call" for a in self.actions[start_actions:])
                if len(bets) == 1 and calls:
                    self.flop_line = self.flop_bet_code + "-c"
        return self.finish()

    def finish(self):
        n, totals, live = self.n, self.total, self.live
        collected = [0] * n
        contenders = [i for i in range(n) if live[i]]
        if len(contenders) == 1:
            collected[contenders[0]] = sum(totals)
        else:
            self.board = self.board_all
            board = [EVAL[c] for c in self.board]
            value = {i: eval7.evaluate([EVAL[c] for c in self.kept[i]] + board) for i in contenders}
            levels = sorted(set(totals))
            floor = 0
            winners = None
            carry = 0
            for level in levels:
                layer = sum(min(t, level) - min(t, floor) for t in totals)
                eligible = [i for i in contenders if totals[i] >= level]
                if eligible:
                    high = max(value[i] for i in eligible)
                    winners = sorted(i for i in eligible if value[i] == high)
                    layer += carry
                    carry = 0
                    share, odd = divmod(layer, len(winners))
                    for rank, i in enumerate(winners):
                        collected[i] += share + (rank < odd)
                else:
                    carry += layer
                floor = level
            if carry:
                collected[winners[0]] += carry
        return self.record(collected)

    def record(self, collected):
        rng, plant = self.rng, self.plant
        seats = []
        hidden = set()
        for i in range(self.n):
            entry = {"seat": self.seats[i], "stack": self.start[i]}
            if rng.random() < plant["hidden_cards"]:
                hidden.add(i)
            else:
                entry["cards3"] = self.cards3[i]
                if self.kept[i]:
                    entry["cards"] = self.kept[i]
            seats.append(entry)
        shows = {}
        for i, (shown, discard) in self.shows.items():
            shows[str(self.seats[i])] = {"show": shown} if i in hidden else {"show": shown, "discard": discard}
        return {"id": self.hid, "bb": self.bb, "sb": self.sb, "ante": 0, "button": self.button,
                "seats": seats, "actions": self.actions, "board": self.board, "shows": shows,
                "winnings": {str(self.seats[i]): c for i, c in enumerate(collected) if c}}


def _generate_part(args):
    path, first, count, seed, plant = args
    rng = random.Random(seed)
    with open(path, "wb") as out:
        for hid in range(first, first + count):
            out.write(dumps(Table(rng, plant, hid).play()) + b"\n")
    return path


def generate(path: str, hands: int, seed: int = 1, plant=None, workers: int = 2) -> None:
    plant = plant or PLANTED
    per = max(1, hands // workers)
    parts = [(f"{path}.part{i}", i * per, per if i < workers - 1 else hands - i * per, seed * 1000 + i, plant)
             for i in range(workers)]
    with multiprocessing.Pool(workers) as pool:
        names = pool.map(_generate_part, parts)
    with open(path, "wb") as out:
        for name in names:
            with open(name, "rb") as part:
                out.write(part.read())
    import os
    for name in names:
        os.remove(name)
    with open(path + ".planted.json", "w") as out:
        json.dump(plant, out, indent=1, sort_keys=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output")
    parser.add_argument("--hands", type=int, default=250_000)
    parser.add_argument("--seed", type=int, default=1)
    options = parser.parse_args()
    generate(options.output, options.hands, options.seed)
