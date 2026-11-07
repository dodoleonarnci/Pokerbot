#!/usr/bin/env python3
"""Play practice tables through kit_agent.py the way the tournament calls it.

Each practice state is rewritten as an official-style state (per the Getting started page),
every decision goes to a brand-new Agent with only the memory bytes carried over, and the
rebuilt practice state is compared with the original. Reports both builds side by side.

Usage: python3.12 sim/kit_harness.py --tables 100 --field mixed
"""
import argparse
import gc
import json
import pathlib
import sys
import time
from types import SimpleNamespace as NS

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "sim"))

import kit_agent  # noqa: E402
from bot import kit  # noqa: E402
from runner import FIELDS, play  # noqa: E402

STREETS = ("preflop", "flop", "turn", "river")
BOARD_SLICES = {"flop": (0, 3), "turn": (3, 4), "river": (4, 5)}
TABLE_SEATS = 8
COMPARED = ("seat", "button", "street", "hole", "board", "pot", "to_call", "can_raise", "stacks", "bets", "folded", "big_blind", "small_blind",
            "hand_number", "hands_remaining", "players_left", "seat_ids")
EVENT_FIELDS = ("street", "seat", "action", "to", "pot", "amount", "stacks")


class FakeAction:
    def __init__(self, kind, amount=None):
        self.kind, self.amount = kind, amount

    @classmethod
    def fold(cls):
        return cls("fold")

    @classmethod
    def check(cls):
        return cls("check")

    @classmethod
    def call(cls):
        return cls("call")

    @classmethod
    def raise_to(cls, total):
        return cls("raise", total)


def official_events(practice, posted):
    alive = practice["seat_ids"]
    events = [NS(kind="hand", seat=None, amount=practice["hand_number"], cards=None)]
    events += [NS(kind="blind", seat=alive[i], amount=amount, cards=None) for i, amount in posted]
    street = "preflop"

    def advance_to(target):
        nonlocal street
        while street != target:
            street = STREETS[STREETS.index(street) + 1]
            lo, hi = BOARD_SLICES[street]
            events.append(NS(kind="board", seat=None, amount=None, cards=practice["board"][lo:hi]))

    for event in practice["history"]:
        advance_to(event["street"])
        kind = event["action"]
        amount = event["to"] if kind == "raise" else event["amount"] if kind == "call" else 0
        events.append(NS(kind=kind, seat=alive[event["seat"]], amount=amount, cards=None))
    advance_to(practice["street"])
    return events


def official_state(practice, posted, table_id):
    alive = practice["seat_ids"]
    seats = []
    for number in range(TABLE_SEATS):
        if number in alive:
            i = alive.index(number)
            status = ("folded" if practice["folded"][i] else
                      "all_in" if practice["stacks"][i] == 0 else "active")
            seats.append(NS(seat=number, stack=practice["stacks"][i], bet=practice["bets"][i],
                            status=status, shown_cards=None))
        else:
            seats.append(NS(seat=number, stack=0, bet=0, status="busted", shown_cards=None))
    if practice["to_call"] == 0:
        legal = [NS(kind="check", min_amount=None, max_amount=None)]
    else:
        legal = [NS(kind="fold", min_amount=None, max_amount=None),
                 NS(kind="call", min_amount=practice["to_call"], max_amount=practice["to_call"])]
    if practice["can_raise"]:
        legal.append(NS(kind="raise", min_amount=practice["min_raise_to"],
                        max_amount=practice["max_raise_to"]))
    config = NS(table_id=table_id, seat=alive[practice["seat"]], players=TABLE_SEATS,
                hand_cap=practice["hand_number"] + practice["hands_remaining"],
                decision_ms=1, time_bank_ms=100, memory_bytes=65536, payouts=practice.get("payouts"))
    return NS(seat=alive[practice["seat"]], cards=practice["hole"], board=practice["board"],
              pot=practice["pot"], to_call=practice["to_call"], legal_actions=legal,
              history=official_events(practice, posted), events=[], phase="betting",
              seats=seats, button=alive[practice["button"]],
              blinds=(practice["small_blind"], practice["big_blind"]),
              hand_number=practice["hand_number"], players_remaining=practice["players_left"],
              config=config, variant=None)


class KitHero:
    """One table's hero: a fresh Agent per decision, with only the memory carried over."""

    instances = []

    def __init__(self, seed):
        self.table_id = f"t{seed}"
        self.memory = b""
        self.posted_hand, self.posted = None, []
        self.times, self.memory_sizes = [], []
        self.mismatches, self.first_mismatch, self.illegal, self.cycles = 0, None, 0, 0
        self.errors_at_start = kit.diagnostics["errors"]
        KitHero.instances.append(self)

    @property
    def errors(self):
        return kit.diagnostics["errors"] - self.errors_at_start

    def _blinds_posted(self, practice):
        if practice["street"] == "preflop" and self.posted_hand != practice["hand_number"]:
            paid = list(practice["bets"])
            for event in practice["history"]:
                paid[event["seat"]] -= event["amount"]
            self.posted = sorted(((i, p) for i, p in enumerate(paid) if p > 0), key=lambda x: x[1])
            self.posted_hand = practice["hand_number"]
        return self.posted if self.posted_hand == practice["hand_number"] else None

    def _compare(self, practice, state):
        rebuilt = kit.practice_state(state)
        problems = [k for k in COMPARED if rebuilt[k] != practice[k]]
        if practice["can_raise"]:
            problems += [k for k in ("min_raise_to", "max_raise_to") if rebuilt[k] != practice[k]]
        ours = [{k: e[k] for k in EVENT_FIELDS} for e in rebuilt["history"]]
        theirs = [{k: e[k] for k in EVENT_FIELDS} for e in practice["history"]]
        if ours != theirs:
            problems.append("history")
        if problems:
            self.mismatches += 1
            self.first_mismatch = self.first_mismatch or {
                k: (rebuilt[k], practice[k]) for k in problems if k != "history"} or "history"

    def __call__(self, practice):
        posted = self._blinds_posted(practice)
        state = official_state(practice, posted or [], self.table_id)
        if posted is not None:
            self._compare(practice, state)
        agent = kit_agent.Agent()
        agent.action_type = FakeAction
        gc.collect()
        start = time.perf_counter()
        action, self.memory = agent.act(state, self.memory)
        self.times.append(time.perf_counter() - start)
        del agent
        self.cycles += gc.collect()
        self.memory_sizes.append(len(self.memory))
        legal = {o.kind: o for o in state.legal_actions}
        option = legal.get(action.kind)
        if option is None or action.kind == "raise" and not (
                option.min_amount <= action.amount <= option.max_amount):
            self.illegal += 1
        return ("raise", action.amount) if action.kind == "raise" else action.kind


def percentile_ms(times, share):
    return 1000 * times[min(len(times) - 1, int(len(times) * share))] if times else 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tables", type=int, default=100)
    parser.add_argument("--field", default="mixed", choices=FIELDS)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    baseline = play(args.tables, args.field, args.seed)
    KitHero.instances.clear()
    kit_run = play(args.tables, args.field, args.seed, make_hero=KitHero)
    heroes = KitHero.instances
    times = sorted(t for h in heroes for t in h.times)
    sizes = [s for h in heroes for s in h.memory_sizes]
    print(json.dumps({"baseline": baseline, "kit": kit_run}, indent=1))
    print(json.dumps({
        "kit_act_p50_ms": percentile_ms(times, 0.5),
        "kit_act_p99_ms": percentile_ms(times, 0.99),
        "kit_act_p999_ms": percentile_ms(times, 0.999),
        "kit_act_max_ms": 1000 * times[-1] if times else 0,
        "kit_over_1ms": sum(t >= 0.001 for t in times),
        "memory_max_bytes": max(sizes, default=0),
        "memory_mean_bytes": sum(sizes) / len(sizes) if sizes else 0,
        "state_mismatches": sum(h.mismatches for h in heroes),
        "first_mismatch": next((h.first_mismatch for h in heroes if h.first_mismatch), None),
        "illegal_actions": sum(h.illegal for h in heroes),
        "kit_errors": kit.diagnostics["errors"], "kit_last_error": kit.diagnostics["last_error"],
        "memory_resets": kit.diagnostics["memory_resets"],
        "cyclic_garbage_from_act": sum(h.cycles for h in heroes),
    }, indent=1))


if __name__ == "__main__":
    main()
