"""Hand histories in, game-tree vulnerability statistics out (JSON for the visualization)."""
import argparse
import json
import time

from .history import replay_file
from .tree import TreeStats, em_bettor_mix, summarize


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("histories", nargs="+")
    parser.add_argument("--out", required=True)
    parser.add_argument("--label", default="")
    parser.add_argument("--max-hands", type=int, default=0)
    parser.add_argument("--em-hands", type=int, default=60000)
    parser.add_argument("--min-count", type=int, default=30)
    args = parser.parse_args()
    started = time.perf_counter()
    stats, replays = TreeStats(), []
    for path in args.histories:
        for replay in replay_file(path, args.max_hands or None):
            stats.add(replay)
            if len(replays) < args.em_hands:
                replays.append(replay)
    parsed = time.perf_counter()
    print(f"replayed {stats.hands:,} hands in {parsed - started:.1f}s")
    mix, fit_info = em_bettor_mix(replays, args.em_hands) if args.em_hands else ({}, None)
    print(f"EM on {len(replays):,} hands in {time.perf_counter() - parsed:.1f}s: {fit_info}")
    summary = summarize(stats, mix, args.min_count)
    summary["label"] = args.label
    summary["em"] = fit_info
    with open(args.out, "w") as f:
        json.dump(summary, f)
    print(f"nodes {len(summary['nodes'])}, bet spots {len(summary['bets'])}, river spots {len(summary['river'])}, "
          f"flop/turn spots {len(summary['earlier'])} -> {args.out}")


if __name__ == "__main__":
    main()
