import random
import unittest

import range_bot as B
import ranges as R
from bots import BOTS
from engine import Hand
from equity import combo


def event(street, seat, action, to=None, pot=0, amount=0, stacks=(1000, 1000)):
    return {"street": street, "seat": seat, "action": action, "to": to,
            "pot": pot, "amount": amount, "stacks": list(stacks)}


def preflop_raise_call():
    """Seat 0 is the button and opens; seat 1 calls from the big blind."""
    return [event("preflop", 0, "raise", 25, 15, 20, (995, 990)),
            event("preflop", 1, "call", None, 35, 15, (970, 990))]


def state(seat, street, board, hole, history, pot=50, to_call=0, stacks=(975, 975), bets=(0, 0)):
    return {
        "seat": seat, "button": 0, "street": street, "hole": hole, "board": board,
        "pot": pot, "to_call": to_call, "can_raise": True,
        "min_raise_to": bets[seat] + to_call + 10, "max_raise_to": bets[seat] + stacks[seat],
        "stacks": list(stacks), "bets": list(bets), "folded": [False, False],
        "big_blind": 10, "history": history,
    }


class Formulas(unittest.TestCase):
    def test_mdf_matches_the_plan_example(self):
        self.assertAlmostEqual(B.mdf(100, 50), 2 / 3)

    def test_bluff_share_and_call_price(self):
        self.assertAlmostEqual(B.bluff_share(100, 100), 1 / 3)
        self.assertAlmostEqual(B.bluff_share(100, 50), 0.25)

    def test_bluff_count_gives_the_formula_share(self):
        pot, bet, value = 100, 75, 70
        bluffs = B.bluffs_for(value, pot, bet)
        self.assertAlmostEqual(bluffs / (bluffs + value), B.bluff_share(pot, bet), delta=0.01)

    def test_geometric_sizes_reach_all_in(self):
        pot, stack = 100, 900
        turn = B.geometric_bet(pot, stack, 2)
        river = B.geometric_bet(pot + 2 * turn, stack - turn, 1)
        self.assertEqual(river, stack - turn)
        self.assertAlmostEqual(turn / pot, river / (pot + 2 * turn), delta=0.01)

    def test_river_size_is_the_rest_of_the_stack(self):
        self.assertEqual(B.geometric_bet(200, 700, 1), 700)


class Preflop(unittest.TestCase):
    def test_percentages_are_close_to_their_names(self):
        for percent in (5, 15, 45, 85):
            self.assertAlmostEqual(100 * len(R.top(percent)) / 1326, percent, delta=2)

    def test_order_has_premium_hands_first(self):
        self.assertLess(R.percentile(combo(["As", "Ah"])), 1)
        self.assertLess(R.percentile(combo(["As", "Qd"])), R.percentile(combo(["As", "Jd"])))
        self.assertEqual(R.percentile(combo(["7s", "2d"])) > 90, True)

    def test_trash_folds_and_premium_raises(self):
        base = dict(seat=2, button=0, street="preflop", board=[], pot=15, to_call=10,
                    can_raise=True, min_raise_to=20, max_raise_to=1000,
                    stacks=[1000, 995, 1000, 990, 1000, 1000], bets=[0, 5, 0, 10, 0, 0],
                    folded=[False] * 6, big_blind=10, history=[])
        base["seat"] = 4  # first to act at a six-handed table
        self.assertEqual(B.RangeBot()({**base, "hole": ["7s", "2d"]}), "fold")
        self.assertEqual(B.RangeBot()({**base, "hole": ["As", "Ah"]})[0], "raise")


class Aggressor(unittest.TestCase):
    flop = ["Ks", "7d", "2c"]

    def test_range_bets_small_in_position_on_the_flop(self):
        history = preflop_raise_call() + [event("flop", 1, "check", None, 50, 0, (975, 975))]
        for hole in (["3h", "4h"], ["As", "Ad"]):
            action = B.RangeBot()(state(0, "flop", self.flop, hole, history))
            self.assertEqual(action, ("raise", 16))  # about 1/3 of 50

    def test_turn_size_is_two_street_geometric(self):
        history = preflop_raise_call() + [
            event("flop", 1, "check", None, 50, 0, (975, 975)),
            event("flop", 0, "raise", 16, 50, 16, (975, 975)),
            event("flop", 1, "call", None, 66, 16, (975, 959)),
            event("turn", 1, "check", None, 82, 0, (959, 959)),
        ]
        action = B.RangeBot()(state(0, "turn", self.flop + ["Kd"], ["Kh", "Ah"],
                                    history, pot=82, stacks=(959, 959)))
        self.assertEqual(action[0], "raise")
        self.assertEqual(action[1], B.geometric_bet(82, 959, 2))

    def test_river_bluffs_match_the_formula(self):
        history = preflop_raise_call()
        model = B.HandModel(state(0, "preflop", [], ["As", "Ad"], []))
        model.sync(state(0, "river", self.flop + ["9h", "4c"], ["As", "Ad"], history))
        pot, bet = 50, 50
        combos = model._betting_range(0, pot, bet)
        calling = model._top_share(model._refs(0), model.ranges[0], B.mdf(pot, bet))
        rated = model._rated(model.ranges[0], calling)
        value = {c for c in combos if sum(rated[c]) / len(rated[c]) >= 0.5}
        bluffs = combos - value
        self.assertGreater(len(value), 0)
        self.assertAlmostEqual(
            len(bluffs) / len(combos), B.bluff_share(pot, bet), delta=0.02)


class Caller(unittest.TestCase):
    flop = ["Ks", "7d", "2c"]

    def test_checks_flop_out_of_position_with_any_hand(self):
        for hole in (["Kh", "Kd"], ["3h", "4h"]):
            action = B.RangeBot()(state(1, "flop", self.flop, hole, preflop_raise_call()))
            self.assertEqual(action, "check")

    def test_no_dunk_on_the_turn_after_calling_the_flop(self):
        history = preflop_raise_call() + [
            event("flop", 1, "check", None, 50, 0, (975, 975)),
            event("flop", 0, "raise", 16, 50, 16, (975, 975)),
            event("flop", 1, "call", None, 66, 16, (959, 975)),
        ]
        action = B.RangeBot()(state(1, "turn", self.flop + ["Kd"], ["Kh", "Ah"],
                                    history, pot=82, stacks=(959, 959)))
        self.assertEqual(action, "check")

    def test_folds_junk_and_calls_the_nuts_facing_a_river_bet(self):
        board = self.flop + ["9h", "4c"]
        history = preflop_raise_call() + [event("river", 1, "check", None, 50, 0, (975, 975)),
                                          event("river", 0, "raise", 50, 50, 50, (975, 975))]
        for hole, expected in ((["3h", "5h"], "fold"), (["Kh", "Kd"], "call")):
            action = B.RangeBot()(state(1, "river", board, hole, history, pot=100, to_call=50,
                                        stacks=(925, 975), bets=(50, 0)))
            self.assertEqual(action, expected, hole)

    def test_call_narrows_range_by_mdf(self):
        history = preflop_raise_call() + [
            event("flop", 1, "check", None, 50, 0, (975, 975)),
            event("flop", 0, "raise", 25, 50, 25, (975, 975)),
            event("flop", 1, "call", None, 75, 25, (950, 975)),
        ]
        model = B.HandModel(state(0, "preflop", [], ["As", "Ad"], []))
        model.sync(state(0, "flop", self.flop, ["As", "Ad"], history[:2]))
        before = len(model.ranges[1])
        model.sync(state(0, "flop", self.flop, ["As", "Ad"], history))
        self.assertAlmostEqual(len(model.ranges[1]) / before, 2 / 3, delta=0.01)


class Matches(unittest.TestCase):
    def test_no_failed_decisions_and_no_postflop_raises(self):
        for players in (2, 3, 6):
            agents = [B.RangeBot()] + [BOTS["maniac"], BOTS["caller"], BOTS["min_raiser"],
                                        BOTS["check_or_fold"], B.RangeBot()][:players - 1]
            rng = random.Random(players)
            for hand_no in range(60):
                hand = Hand(agents, [1000] * players, hand_no % players, 5, 10, rng)
                self.assertEqual(sum(hand.play()), 1000 * players)
                self.assertEqual(hand.failures[0], 0)
                self.assertEqual(hand.failures[-1] if players == 6 else 0, 0)
                for entry in hand.history:
                    if entry["seat"] == 0 and entry["action"] == "raise" and entry["street"] != "preflop":
                        previous = [e for e in hand.history[:hand.history.index(entry)]
                                    if e["street"] == entry["street"] and e["action"] == "raise"]
                        self.assertEqual(previous, [])


if __name__ == "__main__":
    unittest.main()
