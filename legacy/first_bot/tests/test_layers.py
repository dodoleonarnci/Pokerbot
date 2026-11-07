"""Variant seam, extra-decision hooks, rules, generic engine, adapter, safety and latency.

Run: python3.12 -m unittest discover -s tests
"""
import pathlib
import random
import sys
import time
import unittest
from types import SimpleNamespace as NS

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "sim"), str(ROOT.parent / "practice")]

import kit_harness as H  # noqa: E402
from bot import kit, rules, variant  # noqa: E402
from bot.evaluator import CARD, score7  # noqa: E402
from bot.opponent import OpponentModel, SeatStats  # noqa: E402
from bot.params import PARAMS  # noqa: E402
from bot.policy import Policy  # noqa: E402
from bot.view import make_view  # noqa: E402
from runner import play  # noqa: E402

SPEC = variant.ACTIVE
FAR = float("inf")


def cards(text):
    return [CARD[c] for c in text.split()]


def option(kind, low=None, high=None, **extra):
    return NS(kind=kind, min_amount=low, max_amount=high, **extra)


def extra_state(phase, legal, hole, board=(), pot=100):
    seats = [NS(seat=0, stack=1000, bet=0, status="active", shown_cards=None),
             NS(seat=1, stack=1000, bet=0, status="active", shown_cards=None)]
    return NS(phase=phase, legal_actions=legal, cards=list(hole), board=list(board), pot=pot,
              to_call=0, seat=0, seats=seats, history=[], hand_number=3,
              config=NS(table_id="t", seat=0))


class VariantSpecTests(unittest.TestCase):
    def test_card_round_trip(self):
        for text in ("As", "Td", "2c", "9h"):
            self.assertEqual(SPEC.card_text(SPEC.parse_card(text)), text)

    def test_evaluate_matches_score7(self):
        hole, board = cards("Ah Kh"), cards("Qh Jh Th 2c 3d")
        self.assertEqual(SPEC.evaluate(hole, board), score7(hole + board))

    def test_streets_follow_board_size(self):
        self.assertEqual([SPEC.street(n) for n in (0, 3, 4, 5)], ["preflop", "flop", "turn", "river"])

    def test_equity_orders_hands(self):
        rng = random.Random(4)
        aces = SPEC.equity(cards("As Ad"), [], 1, FAR, rng, 2000)
        trash = SPEC.equity(cards("7c 2d"), [], 1, FAR, rng, 2000)
        self.assertGreater(aces, 0.78)
        self.assertLess(trash, 0.42)

    def test_equity_stops_at_deadline(self):
        start = time.perf_counter()
        SPEC.equity(cards("As Kd"), [], 3, start + 0.0003, random.Random(1), 10_000)
        self.assertLess(time.perf_counter() - start, 0.002)


class ExtraDecisionHookTests(unittest.TestCase):
    def test_discard_keeps_the_made_hand(self):
        state = extra_state("discard", [option("discard", 1, 1)], ["Ah", "2c"], ["Ad", "Ac", "7h"])
        action, memory = kit.play(state, b"mem", H.FakeAction)
        self.assertEqual((action.kind, action.amount), ("discard", ["2c"]))
        self.assertEqual(memory, b"mem")

    def test_bid_stays_in_range(self):
        for hole in (["As", "Ad"], ["7c", "2d"]):
            state = extra_state("auction", [option("bid", 0, 60)], hole, pot=200)
            action, _ = kit.play(state, b"", H.FakeAction)
            self.assertEqual(action.kind, "bid")
            self.assertTrue(0 <= action.amount <= 60)

    def test_strong_hand_bids_more(self):
        bids = []
        for hole in (["As", "Ad"], ["7c", "2d"]):
            state = extra_state("auction", [option("bid", 0, 200)], hole, pot=200)
            bids.append(kit.play(state, b"", H.FakeAction)[0].amount)
        self.assertGreater(bids[0], bids[1])

    def test_choose_card_takes_the_best(self):
        state = extra_state("draft", [option("choose_card", cards=["3c", "Kd"])], ["Ks", "Kh"])
        action, _ = kit.play(state, b"", H.FakeAction)
        self.assertEqual((action.kind, action.amount), ("choose_card", "Kd"))

    def test_unknown_kind_takes_automatic_choice(self):
        state = extra_state("swap", [option("swap", 2, 5)], ["As", "Kd"])
        action, _ = kit.play(state, b"", H.FakeAction)
        self.assertEqual((action.kind, action.amount), ("swap", 2))

    def test_failing_hook_falls_back_and_keeps_memory(self):
        original = SPEC.decide_bid
        SPEC.decide_bid = lambda ctx: 1 / 0
        try:
            state = extra_state("auction", [option("bid", 5, 60)], ["As", "Ad"])
            action, memory = kit.play(state, b"keep", H.FakeAction)
        finally:
            SPEC.decide_bid = original
        self.assertEqual((action.kind, action.amount, memory), ("bid", 5, b"keep"))

    def test_variant_subclass_hook_is_used(self):
        class Biddy(variant.HoldemSpec):
            def decide_bid(self, ctx):
                return variant.Choice("bid", int(ctx.option.max_amount))
        saved, kit.ACTIVE = kit.ACTIVE, Biddy()
        try:
            action, _ = kit.play(extra_state("auction", [option("bid", 0, 77)], ["2c", "3d"]),
                                 b"", H.FakeAction)
        finally:
            kit.ACTIVE = saved
        self.assertEqual(action.amount, 77)


def steal_view(fold_rates, faced=10):
    practice = {"seat": 3, "button": 0, "street": "preflop", "hole": ["7c", "2d"], "board": [],
                "pot": 30, "to_call": 20, "can_raise": True, "min_raise_to": 40, "max_raise_to": 1000,
                "stacks": [1000, 990, 980, 1000], "bets": [0, 10, 20, 0], "folded": [False] * 4,
                "big_blind": 20, "small_blind": 10, "history": [], "hand_number": 30,
                "hands_remaining": 170, "players_left": 4, "seat_ids": [10, 11, 12, 13]}
    policy = Policy()
    policy.opponents = OpponentModel()
    for seat_id, rate in zip((10, 11, 12), fold_rates):
        stats = SeatStats()
        stats.faced_bet, stats.folded_bet = faced, faced * rate
        policy.opponents.seats[seat_id] = stats
    return rules.RuleContext(make_view(practice), policy, practice)


class RuleTests(unittest.TestCase):
    def test_steal_fires_against_folders(self):
        before = rules.StealVsFolders.fires
        rule = rules.first_firing(steal_view([1.0, 1.0, 1.0]))
        self.assertIsInstance(rule, rules.StealVsFolders)
        self.assertEqual(rule.action(steal_view([1.0, 1.0, 1.0])), ("raise", 50))
        self.assertEqual(rules.StealVsFolders.fires, before + 1)

    def test_steal_needs_every_player_behind(self):
        self.assertIsNone(rules.first_firing(steal_view([1.0, 0.3, 1.0])))

    def test_steal_needs_a_minimum_sample(self):
        self.assertIsNone(rules.first_firing(steal_view([1.0, 1.0, 1.0], faced=2)))

    def test_enable_flag(self):
        PARAMS["RULES"]["steal_vs_folders"] = False
        try:
            self.assertIsNone(rules.first_firing(steal_view([1.0, 1.0, 1.0])))
        finally:
            PARAMS["RULES"]["steal_vs_folders"] = True

    def test_players_behind_order(self):
        view = steal_view([1.0, 1.0, 1.0]).view
        self.assertEqual(rules.preflop_players_behind(view), [0, 1, 2])


def maniac_view(folded_third=True, raises=10, decisions=10):
    history = [{"street": "flop", "seat": 1, "action": "raise", "to": 50, "pot": 150, "amount": 50,
                "stacks": [900, 900, 1000]}]
    practice = {"seat": 0, "button": 0, "street": "flop", "hole": ["As", "Ad"],
                "board": ["2c", "7d", "9h"], "pot": 200, "to_call": 50, "can_raise": True,
                "min_raise_to": 100, "max_raise_to": 900, "stacks": [900, 850, 1000],
                "bets": [0, 50, 0], "folded": [False, False, folded_third], "big_blind": 20,
                "small_blind": 10, "history": history, "hand_number": 40, "hands_remaining": 160,
                "players_left": 3, "seat_ids": [10, 11, 12]}
    policy = Policy()
    policy.rng = random.Random(2)
    policy.aggression = {11: [raises, decisions]}
    policy.aggression_hand, policy.aggression_seen = 40, len(history)
    return rules.RuleContext(make_view(practice), policy, practice)


class ManiacRuleTests(unittest.TestCase):
    def test_shoves_strong_hand_heads_up(self):
        ctx = maniac_view()
        rule = rules.first_firing(ctx)
        self.assertIsInstance(rule, rules.VersusManiac)
        self.assertEqual(rule.action(ctx), ("raise", 900))

    def test_not_multiway(self):
        self.assertIsNone(rules.first_firing(maniac_view(folded_third=False)))

    def test_needs_a_high_raise_rate(self):
        self.assertIsNone(rules.first_firing(maniac_view(raises=3, decisions=10)))

    def test_enable_flag(self):
        PARAMS["RULES"]["versus_maniac"] = False
        try:
            self.assertIsNone(rules.first_firing(maniac_view()))
        finally:
            PARAMS["RULES"]["versus_maniac"] = True

    def test_aggression_counts_travel_in_memory(self):
        ctx = maniac_view()
        restored = kit.load_policy(kit.save_policy(ctx.policy))
        self.assertEqual(restored.aggression, {11: [10, 10]})


class AdapterAndSafetyTests(unittest.TestCase):
    def run_tables(self, tables, generic=False, seed=5):
        H.KitHero.instances.clear()
        saved = variant.ACTIVE.uses_holdem_policy
        variant.ACTIVE.uses_holdem_policy = not generic
        errors = kit.diagnostics["errors"]
        try:
            play(tables, "mixed", seed, make_hero=H.KitHero)
        finally:
            variant.ACTIVE.uses_holdem_policy = saved
        heroes = H.KitHero.instances
        return heroes, kit.diagnostics["errors"] - errors

    def test_adapter_rebuilds_state_and_stays_legal(self):
        heroes, errors = self.run_tables(3)
        self.assertEqual(sum(h.mismatches for h in heroes), 0)
        self.assertEqual(sum(h.illegal for h in heroes), 0)
        self.assertEqual(errors, 0)

    def test_generic_engine_stays_legal(self):
        heroes, errors = self.run_tables(3, generic=True)
        self.assertEqual(sum(h.illegal for h in heroes), 0)
        self.assertEqual(errors, 0)

    def test_broken_state_falls_back_and_keeps_memory(self):
        state = NS(phase="betting", legal_actions=[option("check"), option("raise", 40, 100)],
                   seats=None, history=None, config=None)
        action, memory = kit.play(state, b"old", H.FakeAction)
        self.assertEqual((action.kind, memory), ("check", b"old"))
        self.assertIn("safety", kit.diagnostics["layers"])

    def test_fold_when_check_is_not_offered(self):
        state = NS(phase="betting", legal_actions=[option("fold"), option("call", 20, 20)], seats=None)
        self.assertEqual(kit.play(state, b"", H.FakeAction)[0].kind, "fold")

    def test_latency_p99_under_budget(self):
        heroes, _ = self.run_tables(4, seed=9)
        times = sorted(t for h in heroes for t in h.times)
        self.assertLess(times[int(len(times) * 0.99)], 0.001)


if __name__ == "__main__":
    unittest.main()
