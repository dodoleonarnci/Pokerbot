#!/usr/bin/env python3
"""Run a match. Stacks reset every hand, and the button rotates."""
import argparse
import importlib.util
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from bots import BOTS  # noqa: E402
from engine import Hand  # noqa: E402


def load(spec, index):
    if spec in BOTS:
        return BOTS[spec]
    path = pathlib.Path(spec)
    if not path.is_file():
        sys.exit(f"Unknown player {spec!r}. Use a .py file or one of: {', '.join(BOTS)}")
    module_spec = importlib.util.spec_from_file_location(f"player_{index}", path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module.act


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("players", nargs="+", help="agent .py files or bot names (2 to 9)")
    parser.add_argument("--hands", type=int, default=1000)
    parser.add_argument("--stack", type=int, default=1000)
    parser.add_argument("--sb", type=int, default=5)
    parser.add_argument("--bb", type=int, default=10)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    if not 2 <= len(args.players) <= 9:
        parser.error("use 2 to 9 players")

    agents = [load(p, i) for i, p in enumerate(args.players)]
    rng = random.Random(args.seed)
    n = len(agents)
    net, failures = [0] * n, [0] * n
    for hand_no in range(args.hands):
        hand = Hand(agents, [args.stack] * n, hand_no % n, args.sb, args.bb, rng)
        stacks = hand.play()
        if sum(stacks) != args.stack * n:
            sys.exit(f"Chip total changed on hand {hand_no}: {stacks}")
        for i in range(n):
            net[i] += stacks[i] - args.stack
            failures[i] += hand.failures[i]

    width = max(len(p) for p in args.players)
    print(f"{args.hands} hands, {n} players, seed {args.seed}")
    print(f"{'player':<{width}}  {'net chips':>10}  {'bb/100':>8}  {'failed':>6}")
    for i, name in enumerate(args.players):
        rate = net[i] / args.bb / args.hands * 100
        print(f"{name:<{width}}  {net[i]:>10}  {rate:>8.1f}  {failures[i]:>6}")


if __name__ == "__main__":
    main()
