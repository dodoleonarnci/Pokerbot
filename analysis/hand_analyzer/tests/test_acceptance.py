"""Acceptance tests. Default: 30,000 hands. HANDS=250000 also runs the 60-second speed test.

Run from the project folder: .venv/bin/python -m unittest discover -s tests -v
"""

import hashlib
import itertools
import json
import math
import os
import pathlib
import re
import shutil
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyze import analyze, known_cards, loads, play_hand, empty_aggregate  # noqa: E402
from backoff import lookup  # noqa: E402
from buckets import class3, pub_bucket, strength_class  # noqa: E402
from deviations import deviation_tests, pool_rates  # noqa: E402
from generate import DECK, PLANTED, generate  # noqa: E402
from spot import MalformedHand, SpotTracker, post_size_code  # noqa: E402

HANDS = int(os.environ.get("HANDS", "30000"))
SIGMAS = 4.0  # Each planted number has its own sampling error; many are checked at once.


def setUpModule():
    global WORK, DATA, OUT, STATS, TREE, POOL, SHOWS, SECONDS
    WORK = tempfile.mkdtemp(prefix="analyzer-test-")
    DATA = os.path.join(WORK, "hands.jsonl")
    generate(DATA, HANDS, seed=7)
    OUT = os.path.join(WORK, "out")
    begun = time.perf_counter()
    STATS = analyze(DATA, OUT, workers=2, quiet=True)
    SECONDS = time.perf_counter() - begun
    TREE = json.load(open(os.path.join(OUT, "tree.json")))
    POOL = json.load(open(os.path.join(OUT, "pool.json")))
    SHOWS = json.load(open(os.path.join(OUT, "shows.json")))


def tearDownModule():
    shutil.rmtree(WORK, ignore_errors=True)


def within(observed, planted, n, sigmas=SIGMAS):
    error = math.sqrt(max(planted * (1 - planted), 1e-6) / max(n, 1))
    return abs(observed - planted) <= sigmas * error


class ChipsAndFrequencies(unittest.TestCase):
    def test_1_chips_conserve_on_every_hand(self):
        self.assertEqual(STATS["hands"], HANDS)
        self.assertEqual(STATS["errors"], 0)
        self.assertEqual(STATS["conservation_failures"], 0)

    def test_1b_broken_chips_are_detected(self):
        with open(DATA, "rb") as handle:
            hand = loads(handle.readline())
        seat = next(iter(hand["winnings"]))
        hand["winnings"][seat] += 1
        agg = empty_aggregate()
        with self.assertRaises(MalformedHand):
            play_hand(hand, agg)
        self.assertEqual(agg["conservation"], 1)
        self.assertEqual(agg["hands"], 0)

    def test_2_frequencies(self):
        for key, node in TREE.items():
            if not node["n"]:
                continue
            self.assertEqual(sum(node["a"].values()), node["n"], key)
            for code, table in node["cls"].items():
                self.assertLessEqual(sum(table.values()), node["a"][code], key)
            for cell in node.get("splits", {}).values():
                self.assertEqual(sum(cell["a"].values()), cell["n"], key)
        rates = [count / node["n"] for node in TREE.values() if node["n"] for count in node["a"].values()]
        self.assertTrue(rates)

    def test_2b_class_counts_equal_decisions_with_known_cards(self):
        """A small replay that counts known-card decisions independently of the tree."""
        path = os.path.join(WORK, "few.jsonl")
        with open(DATA, "rb") as source, open(path, "wb") as target:
            lines = [next(source) for _ in range(3000)]
            target.writelines(lines)
        out = os.path.join(WORK, "few")
        analyze(path, out, workers=1, quiet=True)
        tree = json.load(open(os.path.join(out, "tree.json")))
        expected = {}
        for line in lines:
            hand = loads(line)
            known = known_cards(hand)
            tracker = SpotTracker([(e["seat"], e["stack"]) for e in hand["seats"]], hand["button"], hand["sb"],
                                  hand["bb"], hand["ante"])
            for action in hand["actions"]:
                while tracker.needs_implied_fold(action["seat"], action["street"]):
                    tracker.apply_implied_fold()
                node_key = f"{tracker.path} @{tracker.actor_pos}" if tracker.path else f"@{tracker.actor_pos}"
                street, seat = action["street"], action["seat"]
                code = tracker.apply(seat, action["type"], action.get("to", 0), street)
                if code is not None and known[seat][0 if street == 0 else 1]:
                    expected[node_key] = expected.get(node_key, 0) + 1
        for key, count in expected.items():
            actual = sum(sum(t.values()) for t in tree[key]["cls"].values())
            self.assertEqual(actual, count, key)

    def test_3_class_map(self):
        hands = list(itertools.combinations(DECK, 3))
        self.assertEqual(len(hands), 22_100)
        self.assertEqual(len({class3(h) for h in hands}), 1_755)
        self.assertEqual(class3(("As", "Kh", "2d")), class3(("Ks", "2h", "Ad")))


class PlantedLeaks(unittest.TestCase):
    """Reads the same pool rates report.md prints, with no access to generator state."""

    @classmethod
    def setUpClass(cls):
        cls.rates = pool_rates(POOL, SHOWS)

    def check(self, label, n, part, planted):
        self.assertGreater(n, 0, label)
        self.assertTrue(within(part / n, planted, n), f"{label}: {part / n:.4f} vs {planted} (n={n})")

    def test_open_rates(self):
        for pos, rate in PLANTED["open"].items():
            cell = self.rates["open"][pos]
            self.check(f"open {pos}", cell["n"], cell["r"], rate)
            self.check(f"limp {pos}", cell["n"], cell["c"], PLANTED["limp"])

    def test_three_bet_and_call(self):
        cell = self.rates["vs_open"]
        self.check("3-bet", cell["n"], cell["r"], PLANTED["three_bet"])
        self.check("call open", cell["n"], cell["c"], PLANTED["call_open"])

    def test_facing_reraises(self):
        for name, plant in (("vs_3bet", PLANTED["vs_3bet"]), ("vs_4bet", PLANTED["vs_4bet"])):
            cell = self.rates[name]
            # A planted raise with no chips left to raise becomes a call, so raise + call is the number.
            self.check(f"{name} fold", cell["n"], cell["f"], plant["fold"])
            self.check(f"{name} continue", cell["n"], cell["c"] + cell["r"], plant["call"] + plant["raise"])

    def test_bet_frequency_by_class(self):
        for cls, rate in PLANTED["bet"].items():
            n, bets = self.rates["bet_by_class"][cls]
            self.check(f"bet {cls}", n, bets, rate)

    def test_fold_small_and_big(self):
        for group, plant in (("small", PLANTED["fold_small"]), ("big", PLANTED["fold_big"])):
            for cls, rate in plant.items():
                n, folds = self.rates["fold_by_class"][f"{group};{cls}"]
                self.check(f"fold {group} {cls}", n, folds, rate)

    def test_show_and_discard_policy(self):
        self.check("show helper", *self.rates["show_helper"], PLANTED["show_helper"])
        self.check("keep best", *self.rates["keep_best"], PLANTED["keep_best"])

    def test_two_street_leak(self):
        self.check("turn after called small flop bet", *self.rates["two_street"]["turn;bS-c"],
                   PLANTED["turn_leak_fold"])
        n, folds = self.rates["two_street"]["turn;bM-c"]
        self.assertLess(folds / n, PLANTED["turn_leak_fold"] - 0.2, "the leak must be specific to the line")

    def test_report_prints_the_recovered_numbers(self):
        report = open(os.path.join(OUT, "report.md")).read()
        self.assertRegex(report, r"\| turn \| bS-c \| \d+ \| 0\.[78]\d\d \|")
        self.assertNotIn("withheld |", report)
        self.assertIn("### Folds too much", report)
        for line in report.splitlines():
            if line.startswith("|"):
                cells = line.strip().strip("|").split(" | ")
                self.assertGreaterEqual(len(cells), 2, line)

    def test_deviation_verdicts_only_on_usable_cells(self):
        rows = deviation_tests(TREE, POOL)
        self.assertTrue(rows)
        self.assertTrue(all(row[4] >= 20 for row in rows))

    @unittest.skipUnless(HANDS >= 250_000, "turn nodes reach 20 samples only on the full data")
    def test_planted_turn_over_fold_is_flagged(self):
        rows = deviation_tests(TREE, POOL)
        flagged = [r for r in rows if r[0] == "folds_too_much" and re.search(r"bS [^/]*/ [^/]*b[SMLO]$", r[2])]
        self.assertTrue(flagged, "the planted turn over-fold must be flagged")


class Tracker(unittest.TestCase):
    def test_5_output_is_byte_identical(self):
        again = os.path.join(WORK, "again")
        analyze(DATA, again, workers=2, quiet=True)
        for name in ("tree.json", "shows.json", "pool.json", "report.md"):
            first = hashlib.sha256(pathlib.Path(OUT, name).read_bytes()).hexdigest()
            second = hashlib.sha256(pathlib.Path(again, name).read_bytes()).hexdigest()
            self.assertEqual(first, second, name)

    def _replay(self, hand):
        tracker = SpotTracker([(e["seat"], e["stack"]) for e in hand["seats"]], hand["button"], hand["sb"], hand["bb"],
                              hand["ante"])
        seen = []
        for action in hand["actions"]:
            while tracker.needs_implied_fold(action["seat"], action["street"]):
                tracker.apply_implied_fold()
            seen.append(tracker.state())
            tracker.apply(action["seat"], action["type"], action.get("to", 0), action["street"])
        return seen, tracker

    def test_replaying_twice_gives_identical_paths(self):
        with open(DATA, "rb") as handle:
            for line in itertools.islice(handle, 500):
                hand = loads(line)
                self.assertEqual(self._replay(hand)[0], self._replay(hand)[0])

    def test_tracker_predicts_the_actor_without_reading_it(self):
        """The tracker alone must name the next actor and street from the raw state so far."""
        with open(DATA, "rb") as handle:
            for line in itertools.islice(handle, 3000):
                hand = loads(line)
                seen, _ = self._replay(hand)
                for spot, action in zip(seen, hand["actions"]):
                    self.assertEqual(spot.actor, action["seat"])
                    self.assertEqual(spot.street, action["street"])

    def test_path_example(self):
        seats = [(s, 2000) for s in range(8)]
        tracker = SpotTracker(seats, 7, 10, 20)  # Button at 7: SB 0, BB 1, UTG 2, ..., CO 6.
        for seat in (2, 3, 4, 5):
            tracker.apply(seat, "fold", street=0)
        tracker.apply(6, "raise", 60, 0)
        for seat in (7, 0):
            tracker.apply(seat, "fold", street=0)
        tracker.apply(1, "call", street=0)
        tracker.apply(1, "check", street=1)
        pot = tracker.pot
        tracker.apply(6, "bet", pot // 2, 1)
        tracker.apply(1, "call", street=1)
        self.assertEqual(tracker.path, "CO:r3 BB:c / BB:x CO:bM BB:c /")
        self.assertEqual(tracker.pot, pot + 2 * (pot // 2))
        self.assertEqual(tracker.actor_pos, "BB")

    def test_size_codes(self):
        self.assertEqual([post_size_code(b, 100) for b in (40, 41, 80, 81, 120, 121)], list("SMMLLO"))

    def test_positions_never_merge(self):
        for key, node in itertools.islice(TREE.items(), 5000):
            self.assertEqual(key.rsplit("@", 1)[1], node["actor"])

    def test_public_buckets_stay_out_of_the_path(self):
        for key in itertools.islice(TREE, 5000):
            self.assertNotIn("|", key)


class Buckets(unittest.TestCase):
    def test_strength(self):
        cases = [(("As", "Ks"), ("Qs", "7s", "2d"), "draw"), (("Qh", "3d"), ("Qs", "7s", "2d"), "top"),
                 (("7h", "3d"), ("Qs", "7s", "2d"), "weak"), (("Ah", "Ad"), ("Qs", "7s", "2d"), "top"),
                 (("5h", "5d"), ("Qs", "7s", "2d"), "weak"), (("Qh", "7d"), ("Qs", "7s", "2d"), "strong"),
                 (("8h", "9d"), ("Ts", "Js", "2d"), "draw"), (("Ah", "3d"), ("Ts", "7s", "2d"), "air"),
                 (("8h", "9d"), ("Ts", "Js", "2d", "Kc", "3h"), "air"), (("8h", "9d"), ("Ts", "Js", "Qd"), "strong"),
                 (("Ah", "Kh"), ("Qh", "7h", "2h"), "strong"), (("2h", "3d"), ("Ks", "Kd", "9c"), "air")]
        for kept, board, expected in cases:
            self.assertEqual(strength_class(kept, board), expected, (kept, board))

    def test_public_bucket_first_match_wins(self):
        self.assertEqual(pub_bucket("Td", ("Ts", "7s", "2d")), "P")
        self.assertEqual(pub_bucket("9s", ("Ts", "7s", "2d")), "F")
        self.assertEqual(pub_bucket("9c", ("Ts", "7s", "2d")), "S")
        self.assertEqual(pub_bucket("Ac", ("Ts", "7s", "4d")), "H")
        self.assertEqual(pub_bucket("3c", ("Ts", "9s", "Kd")), "S")
        self.assertEqual(pub_bucket("3c", ("Ts", "7s", "Kd")), "B")
        self.assertEqual(pub_bucket("Ac", ("2s", "3d", "9h")), "S", "an ace plays low in the window")


class Backoff(unittest.TestCase):
    def test_7_thin_cell_returns_parent_never_error(self):
        key, node = next((k, n) for k, n in TREE.items() if n["n"] == 1 and "/" in k)
        path, actor = key.rsplit(" @", 1)
        level, cell, thin = lookup(TREE, POOL, path, actor, "P", "H")
        self.assertIn(level, ("pool", "empty"))
        self.assertIn("split", thin)
        self.assertEqual(lookup(TREE, POOL, "no such path", "UTG")[0], "empty")
        self.assertEqual(lookup({}, {}, "", "UTG", "P", "H", key="nope")[1]["n"], 0)

    def test_7b_walks_every_level(self):
        for key, node in TREE.items():
            good = [k for k, c in node.get("splits", {}).items() if c["n"] >= 20]
            if good:
                path, actor = key.rsplit(" @", 1)
                mine, theirs = good[0].split("|")
                self.assertEqual(lookup(TREE, POOL, path, actor, mine, theirs)[0], "split")
                self.assertEqual(lookup(TREE, POOL, path, actor, mine)[0], "actor_bucket")
                self.assertEqual(lookup(TREE, POOL, path, actor)[0], "node")
                break
        else:
            self.fail("no usable split cell")


class HiddenCards(unittest.TestCase):
    def _node(self, cls, a):
        return {"n": sum(a.values()), "actor": "BTN", "pot": 10.0, "a": a, "cls": cls, "k": "flop;cbet;BTN;2;d80+;SRP",
                "s": {"bM": [a["bM"], 6.0 * a["bM"], 10.0 * a["bM"]]}}

    def _rows(self, node):
        pool = {"spots": {node["k"]: {"n": node["n"], "a": node["a"], "cls": node["cls"]}}, "responses": {}}
        withheld = {}
        return [row[0] for row in deviation_tests({"BTN:r3 BB:c / BB:x @BTN": node}, pool, withheld)], withheld

    def test_showdown_only_cards_cannot_prove_too_much_value(self):
        # 300 bets, 60 shown and all value: the 240 hidden hands could all be bluffs.
        rows, withheld = self._rows(self._node({"bM": {"strong": 60}}, {"bM": 300}))
        self.assertNotIn("value_too_much", rows)
        self.assertEqual(withheld.get("value_too_much"), 1)

    def test_fully_known_cards_still_give_the_verdict(self):
        rows, _ = self._rows(self._node({"bM": {"strong": 300}}, {"bM": 300}))
        self.assertIn("value_too_much", rows)
        rows, _ = self._rows(self._node({"bM": {"air": 300}}, {"bM": 300}))
        self.assertIn("bluffs_too_much", rows)

    def test_multiway_threshold(self):
        node = {"n": 100, "actor": "HJ", "pot": 6.0, "a": {"f": 100}, "cls": {}, "k": "preflop;vs_open;HJ;6;d80+;PF",
                "fb": 3.0, "fp": 3.0}
        pool = {"spots": {}, "responses": {}}
        path = {"CO:r3 @HJ": node}
        alone = deviation_tests(path, pool)
        self.assertAlmostEqual(alone[0][6], 0.5)
        node["fk"] = 4
        self.assertAlmostEqual(deviation_tests(path, pool)[0][6], 0.5 ** 0.25)

    def test_excluded_seat_is_not_counted(self):
        with open(DATA, "rb") as handle:
            hand = next(h for h in map(loads, handle) if h["board"] and len(h["actions"]) > 6)
        seat = hand["actions"][-1]["seat"]
        hand["exclude"] = [seat]
        counted, kept = empty_aggregate(), empty_aggregate()
        play_hand(hand, counted)
        play_hand(hand, kept, include_excluded=True)
        self.assertLess(counted["decisions"], kept["decisions"])
        self.assertEqual(counted["hands"], 1)
        self.assertGreater(counted["excluded_decisions"], 0)
        positions = {p for p in kept["shows"]}
        self.assertLessEqual({p for p in counted["shows"]}, positions)


class Robustness(unittest.TestCase):
    def test_malformed_lines_are_counted_and_skipped(self):
        path = os.path.join(WORK, "bad.jsonl")
        with open(DATA, "rb") as source:
            good = [next(source) for _ in range(50)]
        with open(path, "wb") as target:
            target.write(b"not json\n{\"id\": 1}\n")
            target.writelines(good)
            target.write(b'{"id":2,"bb":20,"sb":10,"button":0,"seats":[{"seat":0,"stack":1000},{"seat":1,"stack":1000}],'
                         b'"actions":[{"street":3,"seat":9,"type":"raise","to":5}],"winnings":{"0":30}}\n')
        stats = analyze(path, os.path.join(WORK, "bad"), workers=1, quiet=True)
        self.assertEqual(stats["errors"], 3)
        self.assertEqual(stats["hands"], 50)

    @unittest.skipUnless(HANDS >= 250_000, "needs HANDS=250000")
    def test_6_speed_250k_under_60_seconds(self):
        self.assertLess(SECONDS, 60.0)


if __name__ == "__main__":
    unittest.main()
