import random
import unittest

from bots import BOTS
from engine import Hand, best_hand, eval5, side_pots


def fixed(*actions):
    queue = list(actions)
    return lambda state: queue.pop(0) if queue else ("check" if state["to_call"] == 0 else "call")


class Ranking(unittest.TestCase):
    def test_category_order(self):
        hands = [
            "2c 4d 6h 8s Tc", "2c 2d 6h 8s Tc", "2c 2d 6h 6s Tc", "2c 2d 2h 8s Tc",
            "Ac 2d 3h 4s 5c", "2c 3d 4h 5s 6c", "2c 4c 6c 8c Tc", "2c 2d 2h 8s 8c",
            "2c 2d 2h 2s Tc", "Ac 2c 3c 4c 5c", "Tc Jc Qc Kc Ac",
        ]
        ranks = [eval5(h.split()) for h in hands]
        self.assertEqual(ranks, sorted(ranks))
        self.assertEqual(len(set(ranks)), len(ranks))

    def test_kicker_and_seven_cards(self):
        self.assertGreater(eval5("Ac Ad Kh 4s 2c".split()), eval5("Ah As Qh 4d 2d".split()))
        self.assertEqual(best_hand("Ac Kc Qc Jc Tc 2d 3d".split())[0], 8)


class SidePots(unittest.TestCase):
    def test_three_way_all_in(self):
        self.assertEqual(side_pots([50, 100, 100], [False] * 3), [[150, [0, 1, 2]], [100, [1, 2]]])

    def test_uncalled_excess_refunds(self):
        self.assertEqual(side_pots([100, 40], [False, False]), [[80, [0, 1]], [60, [0]]])

    def test_folded_chips_stay_in_pot(self):
        self.assertEqual(side_pots([30, 100, 100], [True, False, False]), [[230, [1, 2]]])

    def test_folded_top_layer_merges_down(self):
        self.assertEqual(side_pots([5, 3], [True, False]), [[8, [1]]])


class Play(unittest.TestCase):
    def test_everyone_folds_to_big_blind(self):
        fold = BOTS["check_or_fold"]
        stacks = Hand([fold, fold, fold], [100] * 3, 0, 5, 10, random.Random(1)).play()
        self.assertEqual(stacks, [100, 95, 105])

    def test_heads_up_button_posts_small_blind_and_acts_first(self):
        seen = []

        def spy(state):
            seen.append((state["seat"], state["to_call"]))
            return "fold"

        Hand([spy, spy], [100, 100], 0, 5, 10, random.Random(1)).play()
        self.assertEqual(seen, [(0, 5)])

    def test_illegal_action_counts_as_failure(self):
        hand = Hand([lambda s: ("raise", 1), BOTS["caller"]], [100, 100], 0, 5, 10, random.Random(1))
        self.assertEqual(hand.play(), [95, 105])
        self.assertEqual(hand.failures, [1, 0])

    def test_short_all_in_does_not_reopen_raising(self):
        seen = {}

        def opener(state):
            if state["street"] == "preflop" and "first" not in seen:
                seen["first"] = True
                return ("raise", 100)
            seen.setdefault("reopened", state["can_raise"])
            return "call"

        short = lambda state: ("raise", state["max_raise_to"])  # all-in for 120 total
        caller = BOTS["caller"]
        Hand([opener, short, caller], [1000, 120, 1000], 2, 0, 10, random.Random(1)).play()
        self.assertFalse(seen["reopened"])

    def test_chips_conserved_with_random_stacks(self):
        rng = random.Random(3)
        names = list(BOTS)
        for hand_no in range(3000):
            n = rng.randint(2, 9)
            agents = [BOTS[rng.choice(names)] for _ in range(n)]
            stacks = [rng.randint(1, 500) for _ in range(n)]
            result = Hand(agents, stacks, hand_no % n, 5, 10, rng).play()
            self.assertEqual(sum(result), sum(stacks))
            self.assertTrue(all(s >= 0 for s in result))


if __name__ == "__main__":
    unittest.main()
