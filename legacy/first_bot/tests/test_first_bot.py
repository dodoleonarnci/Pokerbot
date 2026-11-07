"""Checks against the spec's formulas and rules. Run: python3.12 -m unittest discover tests"""
import json
import math
import pathlib
import random
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "sim"), str(ROOT / "offline"), str(ROOT.parent / "practice")]

import agent  # noqa: E402
import engine as practice_engine  # noqa: E402
from bot import policy as S  # noqa: E402
from bot.evaluator import CARD, CLASSES, class_of, score7  # noqa: E402
from bot.features import count_outs, ppot  # noqa: E402
from bot.icm import CHARTS, icm_values, risk  # noqa: E402
from bot.params import PARAMS, PAYOUTS  # noqa: E402
from bot.spots import ActionTracker, position_label, size_bucket, spot_chain  # noqa: E402
from bot.tables import TABLES  # noqa: E402
from field_bots import FIELD  # noqa: E402
from tournament import run_table  # noqa: E402

import pipeline  # noqa: E402


def cards(text):
    return [CARD[c] for c in text.split()]


def event(street, seat, action, to=None, pot=0, amount=0, stacks=(1000, 1000)):
    return {"street": street, "seat": seat, "action": action, "to": to,
            "pot": pot, "amount": amount, "stacks": list(stacks)}


def raise_call_preflop():
    """Seat 0 is the button and opens to 50; seat 1 calls from the big blind."""
    return [event("preflop", 0, "raise", 50, 30, 40, (1990, 1980)),
            event("preflop", 1, "call", None, 70, 30, (1950, 1980))]


def state(seat, street, board, hole, history, pot=100, to_call=0, stacks=(1950, 1950),
          bets=(0, 0), hand=30):
    return {
        "seat": seat, "button": 0, "street": street, "hole": hole.split(), "board": board.split(),
        "pot": pot, "to_call": to_call, "can_raise": True,
        "min_raise_to": bets[seat] + to_call + 20, "max_raise_to": bets[seat] + stacks[seat],
        "stacks": list(stacks), "bets": list(bets), "folded": [False, False],
        "big_blind": 20, "small_blind": 10, "history": history, "hand_number": hand,
        "hands_remaining": 170, "players_left": 2, "seat_ids": [0, 1],
    }


class Formulas(unittest.TestCase):
    def test_mdf_example(self):
        self.assertAlmostEqual(S.mdf(100, 50), 2 / 3)

    def test_band_equity_formula(self):
        self.assertAlmostEqual(S.band_equity([(0.2, 1.0)], 0.6), 0.5)
        self.assertEqual(S.band_equity([(0.5, 1.0)], 0.2), 0.0)
        self.assertEqual(S.band_equity([(0.0, 0.5)], 0.9), 1.0)

    def test_call_narrows_to_top_of_band(self):
        band = S.band_top([(0.1, 0.7)], 2 / 3)
        self.assertAlmostEqual(band[0][0], 0.3)
        self.assertAlmostEqual(band[0][1], 0.7)

    def test_e_called_matches_spec_formula(self):
        lo, hi, m = 0.2, 1.0, 2 / 3
        t = hi - lo
        for q in (0.3, 0.5, 0.7, 0.9):
            spec = max(0.0, min(1.0, (q - (hi - m * t)) / (m * t)))
            self.assertAlmostEqual(S.band_equity(S.band_top([(lo, hi)], m), q), spec)

    def test_betting_band_ratio_and_bet_equity(self):
        pot, bet, ve = 100, 75, 0.5
        band = S.betting_band([(0.0, 1.0)], pot, bet, ve)
        bluff_width, value_width = (hi - lo for lo, hi in band)
        self.assertAlmostEqual(bluff_width / (bluff_width + value_width), bet / (pot + 2 * bet))
        q = 0.9
        hi, lo = 1.0, 0.0
        spec = (max(0, min(q - (hi - value_width), value_width))
                + max(0, min(q - lo, bluff_width))) / (value_width + bluff_width)
        self.assertAlmostEqual(S.band_equity(band, q), spec)

    def test_geometric_fraction(self):
        pot, stack = 100, 900
        f = S.geometric_fraction(pot, stack)
        self.assertAlmostEqual((1 + 2 * f) ** 2, 1 + 2 * stack / pot)

    def test_required_equity(self):
        self.assertAlmostEqual(S.required_equity(50, 150), 50 / 200)  # B / (P + 2B), P=100, B=50

    def test_ppot(self):
        self.assertAlmostEqual(ppot(9, "turn"), 9 / 46)
        self.assertAlmostEqual(ppot(9, "flop"), 0.36)
        self.assertEqual(ppot(20, "flop"), 0.6)


class Evaluator(unittest.TestCase):
    def test_matches_independent_rule_on_random_hands(self):
        rng = random.Random(4)
        deck = practice_engine.DECK
        for _ in range(3000):
            a, b = rng.sample(deck, 7), rng.sample(deck, 7)
            first = practice_engine.best_hand(a) > practice_engine.best_hand(b)
            second = score7([CARD[c] for c in a]) > score7([CARD[c] for c in b])
            self.assertEqual(first, second)

    def test_rank_table_agrees_with_score_when_no_flush(self):
        board = cards("Ks 7d 2c")
        offset = TABLES.row_offset(board)
        for hole, index in ((cards("Ah Ad"), class_of(*cards("Ah Ad"))),
                            (cards("9h 8d"), class_of(*cards("9h 8d")))):
            from bot.evaluator import PAIR_INDEX
            self.assertEqual(TABLES.rank_table[offset + PAIR_INDEX[index]], score7(hole + board))

    def test_scale_orders_hands(self):
        board = cards("Ks 7d 2c 9h 4s")
        all_classes = list(range(169))
        nuts = S.range_percentile(cards("Kh Kd"), board, all_classes)
        mid = S.range_percentile(cards("9c 8c"), board, all_classes)
        junk = S.range_percentile(cards("3h 5d"), board, all_classes)
        self.assertGreater(nuts, 0.97)
        self.assertGreater(nuts, mid)
        self.assertGreater(mid, junk)

    def test_outs(self):
        self.assertEqual(count_outs(cards("Ah 2h"), cards("Kh 7h 9c")), 9)
        self.assertEqual(count_outs(cards("9s 8d"), cards("Th Jc 2d")), 8)


class Rules(unittest.TestCase):
    flop = "Ks 7d 2c"

    def test_range_bet_flop_in_position(self):
        history = raise_call_preflop() + [event("flop", 1, "check", None, 100, 0, (1950, 1950))]
        for hole in ("3h 4h", "As Ad"):
            action = agent.Agent(seed=1, use_pool=False)(state(0, "flop", self.flop, hole, history))
            self.assertEqual(action, ("raise", 33))

    def test_no_donk_check_flop_oop_as_caller(self):
        for hole in ("Kh Kd", "3h 4h"):
            action = agent.Agent(seed=1, use_pool=False)(
                state(1, "flop", self.flop, hole, raise_call_preflop()))
            self.assertEqual(action, "check")

    def test_no_dunk_on_turn_after_calling_flop(self):
        history = raise_call_preflop() + [
            event("flop", 1, "check", None, 100, 0, (1950, 1950)),
            event("flop", 0, "raise", 33, 100, 33, (1950, 1950)),
            event("flop", 1, "call", None, 133, 33, (1917, 1950)),
        ]
        action = agent.Agent(seed=1, use_pool=False)(
            state(1, "turn", self.flop + " Kd", "Kh Ah", history, pot=166, stacks=(1917, 1917)))
        self.assertEqual(action, "check")

    def test_turn_uses_geometric_size_capped_by_f_max(self):
        history = raise_call_preflop() + [
            event("flop", 1, "check", None, 100, 0, (1950, 1950)),
            event("flop", 0, "raise", 33, 100, 33, (1950, 1950)),
            event("flop", 1, "call", None, 133, 33, (1917, 1950)),
            event("turn", 1, "check", None, 166, 0, (1917, 1917)),
        ]
        action = agent.Agent(seed=1, use_pool=False)(
            state(0, "turn", self.flop + " Kd", "Kh Ah", history, pot=166, stacks=(1917, 1917)))
        self.assertEqual(action[0], "raise")
        self.assertEqual(action[1], round(PARAMS["F_MAX"] * 166))

    def test_calls_nuts_folds_junk_on_river(self):
        board = self.flop + " 9h 4s"
        history = raise_call_preflop() + [
            event("river", 1, "check", None, 100, 0, (1950, 1950)),
            event("river", 0, "raise", 100, 100, 100, (1950, 1950)),
        ]
        for hole, expected in (("3h 5h", "fold"), ("Kh Kd", {"call", "raise"})):
            action = agent.Agent(seed=1, use_pool=False)(
                state(1, "river", board, hole, history, pot=200, to_call=100,
                      stacks=(1850, 1950), bets=(100, 0)))
            kind = action[0] if isinstance(action, tuple) else action
            self.assertIn(kind, expected if isinstance(expected, set) else {expected})

    def test_positions_for_eight_seats(self):
        names = [position_label(s, 0, 8) for s in range(8)]
        self.assertEqual(names, ["BTN", "SB", "BB", "UTG", "MP", "LJ", "HJ", "CO"])

    def test_opening_ranges_are_near_spec(self):
        for percent in (12, 25, 45):
            combos = sum({0: 6, 1: 4, 2: 12}[CLASSES[i][2]] for i in TABLES.top[percent])
            self.assertAlmostEqual(100 * combos / 1326, percent, delta=1.5)


class Shell(unittest.TestCase):
    def test_error_returns_legal_action(self):
        bot = agent.Agent()
        bot.policy.decide = lambda *_: 1 / 0
        good = state(0, "flop", "Ks 7d 2c", "3h 4h", [])
        self.assertEqual(bot(good), "check")
        self.assertEqual(bot({**good, "to_call": 10}), "fold")
        self.assertEqual(bot.errors, 2)

    def test_raises_are_clamped(self):
        s = {"to_call": 0, "can_raise": True, "min_raise_to": 40, "max_raise_to": 100}
        self.assertEqual(agent.legal_action(s, ("raise", 5)), ("raise", 40))
        self.assertEqual(agent.legal_action(s, ("raise", 9999)), ("raise", 100))
        self.assertEqual(agent.legal_action({**s, "can_raise": False}, ("raise", 50)), "check")

    def test_slow_path_still_acts_without_ranking(self):
        policy = S.Policy(seed=1, use_pool=False)
        from bot.view import make_view
        view = make_view(state(0, "flop", "Ks 7d 2c", "Kh Ah", raise_call_preflop() + [
            event("flop", 1, "check", None, 100, 0, (1950, 1950))]))
        action = policy.decide(view, deadline=0.0)
        self.assertEqual(action[0], "raise")


class Icm(unittest.TestCase):
    def test_conserves_points(self):
        self.assertAlmostEqual(sum(icm_values([100, 200, 300], list(PAYOUTS[:3]))), sum(PAYOUTS[:3]))

    def test_more_chips_worth_more_but_less_than_linear(self):
        low, high = icm_values([100, 900], [100, 65])
        self.assertLess(low, high)
        self.assertGreater(low, 65)

    def test_charts_tighten_with_more_callers_behind(self):
        count = lambda behind: sum(bool(CHARTS.should_jam(8, behind, 10, i)) for i in range(169))
        self.assertGreater(count(1), count(7))
        self.assertTrue(CHARTS.should_jam(8, 7, 10, TABLES.order[0]))
        self.assertTrue(CHARTS.should_call(8, 7, 10, TABLES.order[0]))

    def test_risk_grows_late(self):
        self.assertEqual(risk(0.1, 4, 50), 0.0)
        self.assertGreater(risk(0.5, 4, 10), risk(0.5, 4, 190))


class Spots(unittest.TestCase):
    def test_chain_drops_fields_in_order(self):
        chain = spot_chain("flop", "c-bet", "s", "ip", "2", "deep", "pfa")
        self.assertEqual(chain[0], "flop|c-bet|s|ip|2|deep|pfa")
        self.assertEqual(chain[-2:], ("flop", "global"))

    def test_size_buckets(self):
        self.assertEqual([size_bucket(b, 100) for b in (30, 60, 100, 150)], ["s", "m", "l", "x"])
        self.assertEqual(size_bucket(10, 100, all_in=True), "allin")

    def test_lines(self):
        t = ActionTracker(2, 0, 20)
        t.apply(event("preflop", 0, "raise", 50, 30, 40, (1990, 1980)))
        t.apply(event("preflop", 1, "call", None, 70, 30, (1950, 1980)))
        t.enter_street("flop")
        self.assertEqual(t.bet_line(1, False), "donk")
        self.assertEqual(t.bet_line(0, False), "c-bet")
        t.apply(event("flop", 1, "check", None, 100, 0, (1950, 1950)))
        t.apply(event("flop", 0, "check", None, 100, 0, (1950, 1950)))
        t.enter_street("turn")
        self.assertEqual(t.bet_line(1, False), "probe")
        self.assertEqual(t.bet_line(0, False), "delayed")


class Pipeline(unittest.TestCase):
    def test_parses_and_builds_tables_from_real_history(self):
        rng = random.Random(9)
        bots = [FIELD[n](rng.randrange(1 << 30)) for n in
                ("tag", "station", "nit", "maniac", "minraiser", "checkcall", "tag", "tag")]
        log = []
        run_table(bots, rng, log=log)
        with tempfile.TemporaryDirectory() as folder:
            path = pathlib.Path(folder) / "round.jsonl"
            path.write_text(json.dumps({"table": 0, "hands": log}) + "\n")
            for showdown_only in (False, True):
                built = pipeline.build_tables([path], showdown_only)
                self.assertGreater(built["hands"], 0)
                self.assertIn("global", built["a"])
                self.assertIn("open", built["c"])
                fold, call = built["a"]["global"][1:3]
                self.assertLessEqual(fold + call, 1.0001)


class Tournament(unittest.TestCase):
    def test_points_are_conserved(self):
        for seed in range(3):
            rng = random.Random(seed)
            bots = [FIELD["maniac"](i) for i in range(4)] + [agent.Agent(seed=i, use_pool=False) for i in range(4)]
            result = run_table(bots, rng)
            self.assertAlmostEqual(sum(result["points"]), sum(PAYOUTS))
            self.assertEqual(sum(result["failures"]), 0)
            self.assertTrue(all(b.errors == 0 for b in bots[4:]))


if __name__ == "__main__":
    unittest.main()
