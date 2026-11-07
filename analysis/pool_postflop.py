#!/usr/bin/env python3
"""Pool postflop frequencies from an official hand-history download, for heads-up pots.

Usage: python3 pool_postflop.py HANDS.jsonl.gz [--tables N]

Facing the first bet on a street: fold/call/raise rates by street and bet-to-pot bucket, for
the pool facing the pool and the pool facing us. When a bet is called and the hand reaches
showdown: how often the bettor wins. Also how often the pool bets when checked to.
"""
import argparse
import gzip
import json
from collections import defaultdict

STREETS = ("flop", "turn", "river")
BUCKETS = ((0.4, "<0.4"), (0.7, "0.4-0.7"), (1.1, "0.7-1.1"), (9e9, ">1.1"))


def bucket(ratio):
    return next(name for limit, name in BUCKETS if ratio < limit)


def hands(path, max_tables):
    with gzip.open(path, "rb") as f:
        lines = iter(f)
        next(lines)
        for count, line in enumerate(lines):
            if count >= max_tables:
                return
            table = json.loads(line)
            own = json.loads(next(lines))["you"]
            for hand in table["hands"]:
                yield hand, own["seat"], table["fillers"]


def analyse(path, max_tables):
    facing = defaultdict(lambda: [0, 0, 0])      # (who, street, bucket) -> fold, call, raise
    showdown = defaultdict(lambda: [0, 0.0])     # (bettor, street) -> called-to-showdown count, bettor wins
    our_calls = defaultdict(lambda: [0, 0])      # street -> times we called the pool's bet, net chips
    checked_to = defaultdict(lambda: [0, 0])     # street -> pool acting after a check: chances, bets
    n_hands = 0
    for hand, own, fillers in hands(path, max_tables):
        n_hands += 1
        before, after = hand["stacks_before"], hand["stacks_after"]
        in_play = [s for s, c in enumerate(before) if c > 0]
        put = dict.fromkeys(in_play, 0)
        street_put = dict.fromkeys(in_play, 0)
        folded = set()
        street, board_len = None, 0
        first_bet = None   # (street, bettor, ratio)
        bets = []          # first bets that were called: (street, bettor seat)
        we_called = []
        last_check_by = None
        live_at_street = 0
        for e in hand["events"]:
            kind, seat, amount = e["kind"], e.get("seat"), e.get("amount", 0)
            if kind in ("ante", "blind"):
                put[seat] += amount
                if kind == "blind":
                    street_put[seat] += amount
            elif kind == "board":
                board_len += len(e["cards"])
                street = {3: "flop", 4: "turn", 5: "river"}.get(board_len)
                street_put = dict.fromkeys(in_play, 0)
                first_bet, last_check_by = None, None
                live_at_street = len([s for s in in_play if s not in folded])
            elif kind in ("fold", "check", "call", "raise"):
                heads_up = street is not None and live_at_street == 2
                if heads_up and first_bet is not None and first_bet[1] != seat and first_bet[3] is None:
                    who = "us" if first_bet[1] == own else "pool"
                    if seat != own and seat not in fillers_set(fillers):
                        row = facing[(who, street, first_bet[2])]
                        row[{"fold": 0, "call": 1, "raise": 2}.get(kind, 1)] += kind != "check"
                    first_bet = first_bet[:3] + (kind,)
                    if kind == "call":
                        bets.append((street, first_bet[1]))
                        if seat == own:
                            we_called.append(street)
                if heads_up and last_check_by is not None and seat != last_check_by:
                    if seat != own:
                        checked_to[street][0] += 1
                        checked_to[street][1] += kind == "raise"
                    last_check_by = None
                elif heads_up and kind == "check" and first_bet is None:
                    last_check_by = seat
                if kind == "fold":
                    folded.add(seat)
                elif kind == "call":
                    put[seat] += amount
                    street_put[seat] += amount
                elif kind == "raise":
                    pot_before = sum(put.values())
                    if heads_up and first_bet is None:
                        first_bet = (street, seat, bucket((amount - street_put[seat]) / max(1, pot_before)), None)
                    put[seat] += amount - street_put[seat]
                    street_put[seat] = amount
        live = [s for s in in_play if s not in folded]
        net = {s: after[s] - before[s] for s in in_play}
        if len(live) == 2:
            for st, bettor in bets:
                who = "us" if bettor == own else "pool"
                other = next(s for s in live if s != bettor) if bettor in live else None
                if other is None:
                    continue
                row = showdown[(who if other != own else "pool-vs-us", st)]
                row[0] += 1
                row[1] += 1.0 if net[bettor] > 0 else 0.5 if net[bettor] == 0 else 0.0
        for st in we_called:
            our_calls[st][0] += 1
            our_calls[st][1] += net[own] / max(1, hand["blinds"][1])
    return n_hands, facing, showdown, our_calls, checked_to


_FILLERS = {}


def fillers_set(fillers):
    key = id(fillers)
    if key not in _FILLERS:
        _FILLERS.clear()
        _FILLERS[key] = {i for i, f in enumerate(fillers) if f}
    return _FILLERS[key]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--tables", type=int, default=3000)
    args = parser.parse_args()
    n, facing, showdown, our_calls, checked_to = analyse(args.path, args.tables)
    print(f"hands {n}")
    print("\nFacing the first bet of a heads-up street (responder = pool): fold / call / raise")
    for who in ("pool", "us"):
        for st in STREETS:
            for _, b in BUCKETS:
                f, c, r = facing[(who, st, b)]
                t = f + c + r
                if t >= 30:
                    print(f"  bettor={who:4} {st:5} bet {b:7} n={t:6}  fold {f/t:.2f}  call {c/t:.2f}  raise {r/t:.2f}")
    print("\nBet called, reached showdown: bettor's win rate")
    for key in sorted(showdown):
        cnt, wins = showdown[key]
        if cnt >= 30:
            print(f"  {key[0]:10} {key[1]:5} n={cnt:6}  bettor wins {wins/cnt:.2f}")
    print("\nOur calls of the pool's first bet (whole-hand result)")
    for st in STREETS:
        cnt, chips = our_calls[st]
        if cnt:
            print(f"  {st:5} n={cnt:5}  avg net {chips/cnt:+.2f} BB per hand")
    print("\nPool acting after a heads-up check: bet rate")
    for st in STREETS:
        cnt, b = checked_to[st]
        if cnt:
            print(f"  {st:5} n={cnt:6}  bets {b/cnt:.2f}")


if __name__ == "__main__":
    main()
