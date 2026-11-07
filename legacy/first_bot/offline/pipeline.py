#!/usr/bin/env python3
"""M8 offline field-data pipeline. Runs on the build machine, never inside the bot.

    collect  run probe tables and write hand histories (a stand-in for practice runs)
    build    parse histories into pool Tables A, B and C
    resolve  re-solve jam/fold charts as a best response to Table C
    check    compare pool tables on versus off
    ship     zip the bot with the winning data and check its size

With the kit, parse_table() is the only part that needs rewriting.
"""
import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import zipfile
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "sim"))

from bot.evaluator import CARD  # noqa: E402
from bot.params import PARAMS  # noqa: E402
from bot.policy import ALL_CLASSES, range_percentile  # noqa: E402
from bot.spots import (ActionTracker, depth_bucket, players_bucket, position_label,  # noqa: E402
                       size_bucket, spot_chain)

LOGS = ROOT / "offline" / "logs"
POOL_DATA = ROOT / "data_pool"
BOARD_SIZE = {"preflop": 0, "flop": 3, "turn": 4, "river": 5}


def crowd(players_left):
    return "8-6" if players_left >= 6 else "5-3" if players_left >= 3 else "2"


def parse_hand(hand, showdown_only=False):
    """Yield one record per decision: spot, size, action, and strength where hole cards show."""
    players = len(hand["seats"])
    tracker = ActionTracker(players, hand["button"], hand["bb"])
    shown = set(range(players))
    if showdown_only:
        folded = {e["seat"] for e in hand["history"] if e["action"] == "fold"}
        shown = (shown - folded) if len(folded) < players - 1 else set()
    board = [CARD[c] for c in hand["board"]]
    holes = [[CARD[c] for c in hole] for hole in hand["holes"]]

    def strength(seat, street):
        cards = board[:BOARD_SIZE[street]]
        if seat not in shown or not cards:
            return None
        return range_percentile(holes[seat], cards, ALL_CLASSES)

    for event in hand["history"]:
        street, seat, kind = event["street"], event["seat"], event["action"]
        if street != tracker.street:
            tracker.enter_street(street)
        stack = event["stacks"][seat]
        common = {
            "street": street, "kind": kind, "seat": seat,
            "pos": tracker.position_word(seat),
            "players": players_bucket(len(tracker.live)),
            "depth": depth_bucket(stack, hand["bb"]),
            "pfa": tracker.pfa_word(seat),
            "label": position_label(seat, hand["button"], players),
            "crowd": crowd(hand["players_left"]),
            "raises": tracker.raises,
        }
        if tracker.last_bet is not None:
            yield {**common, "table": "A", "line": tracker.last_bet[0],
                   "size": tracker.last_bet[1], "strength": strength(seat, street)
                   if kind != "fold" and street != "preflop" else None}
        if kind == "raise":
            bet = event["to"] - tracker.current_bet
            pot = event["pot"] + event["amount"] - bet
            all_in = event["amount"] >= stack
            yield {**common, "table": "B", "line": tracker.bet_line(seat, all_in),
                   "size": size_bucket(bet, pot, all_in), "all_in": all_in,
                   "strength": strength(seat, street)}
        if street == "preflop":
            all_in = kind == "raise" and event["amount"] >= stack
            facing_jam = tracker.last_bet is not None and tracker.last_bet[0] == "jam"
            yield {**common, "table": "C", "all_in": all_in, "facing_jam": facing_jam}
        tracker.apply(event)


def deciles(values):
    if len(values) < 20:
        return []
    ordered = sorted(values)
    return [round(ordered[len(ordered) * i // 10], 3) for i in range(1, 10)]


def _shrink(chain, counts, rates, K):
    """Walk from the global cell down the chain, shrinking each toward its parent."""
    parent = None
    result = None
    for key in reversed(chain):
        if key not in counts:
            continue
        n = counts[key]
        hits = rates[key]
        estimate = [h / n for h in hits] if parent is None else [
            (h + K * p) / (n + K) for h, p in zip(hits, parent)]
        parent = result = estimate
        yield key, n, estimate


def build_tables(paths, showdown_only=False):
    K, minimum = PARAMS["K_POOL"], PARAMS["MIN_SAMPLES"]
    a_counts = defaultdict(int)
    a_hits = defaultdict(lambda: [0, 0, 0])
    a_called = defaultdict(list)
    b_counts = defaultdict(int)
    b_strength = defaultdict(list)
    street_decisions = defaultdict(int)
    c_counts = defaultdict(lambda: [0, 0])
    chains = set()

    def c_add(key, hit):
        c_counts[key][0] += 1
        c_counts[key][1] += hit

    hands = 0
    for path in paths:
        with open(path) as f:
            for line in f:
                for hand in json.loads(line)["hands"]:
                    hands += 1
                    for r in parse_hand(hand, showdown_only):
                        kind = r["kind"]
                        if r["table"] == "A":
                            chain = spot_chain(r["street"], r["line"], r["size"], r["pos"],
                                               r["players"], r["depth"], r["pfa"])
                            chains.add(chain)
                            for key in chain:
                                a_counts[key] += 1
                                row = a_hits[key]
                                row[0] += kind == "fold"
                                row[1] += kind == "call"
                                row[2] += kind == "raise"
                                if kind == "call" and r["strength"] is not None:
                                    a_called[key].append(r["strength"])
                        elif r["table"] == "B":
                            chain = spot_chain(r["street"], r["line"], r["size"], r["pos"],
                                               r["players"], r["depth"], r["pfa"])
                            for key in chain:
                                b_counts[key] += 1
                                if r["strength"] is not None:
                                    b_strength[key].append(r["strength"])
                        else:
                            label, depth, group = r["label"], r["depth"], r["crowd"]
                            names = []
                            if r["raises"] == 0:
                                names.append(("open", kind == "raise"))
                            elif r["raises"] == 1:
                                names.append(("3bet", kind == "raise"))
                            if r["raises"] >= 1:
                                names.append(("call", kind == "call"))
                            for name, hit in names:
                                c_add(f"{name}|{label}|{depth}|{group}", hit)
                                c_add(f"{name}|{label}", hit)
                                c_add(name, hit)
                            c_add(f"jam|{depth}|{group}", r["all_in"])
                            c_add("jam", r["all_in"])
                            if r["facing_jam"]:
                                c_add(f"call-vs-jam|{depth}|{group}", kind in ("call", "raise"))
                                c_add("call-vs-jam", kind in ("call", "raise"))

    table_a = {}
    for chain in chains:
        for key, n, estimate in _shrink(chain, a_counts, a_hits, K):
            if n >= minimum or key == "global":
                table_a[key] = [n, round(estimate[0], 4), round(estimate[1], 4), deciles(a_called[key])]
    table_b = {}
    for key, n in b_counts.items():
        if n >= minimum or key == "global":
            table_b[key] = [n, 0.0, deciles(b_strength[key])]
    table_c = {key: [n, round(h / n, 4)] for key, (n, h) in c_counts.items()
               if n >= minimum or "|" not in key}
    return {"a": table_a, "b": table_b, "c": table_c, "hands": hands,
            "showdown_only": showdown_only}


def _prepare_pool_data():
    POOL_DATA.mkdir(exist_ok=True)
    for path in (ROOT / "data").iterdir():
        if path.name != "pool_tables.json":
            shutil.copy(path, POOL_DATA / path.name)


def collect(tables, round_tag, seed):
    """Stand-in for practice runs: a probe build plays the house field."""
    import agent as agent_module
    from runner import play

    LOGS.mkdir(exist_ok=True)
    path = LOGS / f"{round_tag}.jsonl"
    result = play(tables, "mixed", seed=seed,
                  make_hero=lambda s: agent_module.Agent(seed=s, use_pool=False,
                                                         use_exploits=False,
                                                         probe_rate=PARAMS["PROBE_RATE"]),
                  log_path=path)
    print(f"wrote {path} from {result['tables']} tables, errors {result['errors']}")


def run_gate_table(data_dir, tables, field, seed, pool):
    code = ("import json,sys;sys.path[:0]=['.','sim'];import agent;from runner import play;"
            f"print(json.dumps(play({tables},{field!r},{seed},"
            f"make_hero=lambda s: agent.Agent(seed=s,use_pool={pool}))))")
    env = {**os.environ, "FIRST_BOT_DATA": str(data_dir)}
    out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env, capture_output=True, text=True)
    if out.returncode:
        raise RuntimeError(out.stderr)
    return json.loads(out.stdout.strip().splitlines()[-1])


def check(tables, seed):
    with_pool = run_gate_table(POOL_DATA, tables, "mixed", seed, True)
    without = run_gate_table(ROOT / "data", tables, "mixed", seed, False)
    diff = with_pool["points"] - without["points"]
    err = (with_pool["stderr"] ** 2 + without["stderr"] ** 2) ** 0.5
    keep = diff > err
    print(f"pool on {with_pool['points']:.2f} +/- {with_pool['stderr']:.2f}; "
          f"off {without['points']:.2f} +/- {without['stderr']:.2f}; "
          f"difference {diff:+.2f} +/- {err:.2f}: {'KEEP' if keep else 'SHIP WITHOUT'}")
    return keep


def ship(use_pool):
    data = POOL_DATA if use_pool else ROOT / "data"
    target = ROOT / "dist" / "bot.zip"
    target.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(ROOT / "agent.py", "agent.py")
        for path in sorted((ROOT / "bot").glob("*.py")):
            z.write(path, f"bot/{path.name}")
        for path in sorted(data.iterdir()):
            if path.is_file():
                z.write(path, f"data/{path.name}")
    with zipfile.ZipFile(target) as z:
        infos = z.infolist()
    unpacked = sum(i.file_size for i in infos)
    print(f"{target}: {target.stat().st_size / 1e6:.2f} MB zipped, {unpacked / 1e6:.2f} MB unpacked, "
          f"{len(infos)} entries, agent.py {(ROOT / 'agent.py').stat().st_size / 1e3:.1f} KB")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["collect", "build", "resolve", "check", "ship"])
    parser.add_argument("--tables", type=int, default=300)
    parser.add_argument("--round", default="round0")
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--showdown-only", action="store_true")
    parser.add_argument("--with-pool", action="store_true")
    args = parser.parse_args()
    if args.command == "collect":
        collect(args.tables, args.round, args.seed)
    elif args.command == "build":
        _prepare_pool_data()
        built = build_tables(sorted(LOGS.glob("*.jsonl")), args.showdown_only)
        built["round"] = args.round
        with open(POOL_DATA / "pool_tables.json", "w") as f:
            json.dump(built, f)
        print(f"{built['hands']} hands: A {len(built['a'])} cells, "
              f"B {len(built['b'])}, C {len(built['c'])}")
    elif args.command == "resolve":
        subprocess.run([str(ROOT / "offline/.venv/bin/python"), str(ROOT / "offline/build_icm.py"), "--pool"],
                       env={**os.environ, "FIRST_BOT_DATA": str(POOL_DATA)}, check=True)
    elif args.command == "check":
        check(args.tables, args.seed)
    elif args.command == "ship":
        ship(args.with_pool)


if __name__ == "__main__":
    main()
