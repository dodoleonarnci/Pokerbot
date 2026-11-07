#!/usr/bin/env python3
"""Run many tables, and report points, errors, timeouts and decision timing.

Usage: python3.12 sim/runner.py --tables 200 --field mixed
Output is one JSON report line per run, so scripts can compare builds.
"""
import argparse
import json
import pathlib
import random
import statistics
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "sim"))

import agent as agent_module  # noqa: E402
from field_bots import FIELD  # noqa: E402
from tournament import run_table  # noqa: E402

MIXED = ["tag", "station", "nit", "maniac", "minraiser", "checkcall", "tag"]
FIELDS = {
    "mixed": MIXED,
    "tight": ["tag", "tag", "nit", "tag", "nit", "tag", "nit"],
    "allin": ["allin"] * 7,
    "checkers": ["checkcall", "checkfold"] * 3 + ["checkcall"],
    "switchers": ["switcher"] * 7,
    "examples": ["checkfold", "minraiser"] * 3 + ["checkfold"],
}


class Timed:
    def __init__(self, bot):
        self.bot = bot
        self.times = []

    def __call__(self, state):
        start = time.perf_counter()
        reply = self.bot(state)
        self.times.append(time.perf_counter() - start)
        return reply


def play(tables, field, seed=1, make_hero=None, limit=None, log_path=None, starting=None):
    """Hero sits in a random seat at every table. Fresh opponents and hero per table."""
    rng = random.Random(seed)
    names = FIELDS[field]
    points, places_hands = [], []
    errors = failures = timeouts = 0
    all_times = []
    last_error = None
    log_file = open(log_path, "w") if log_path else None
    for table in range(tables):
        hero_bot = (make_hero or (lambda r: agent_module.Agent(seed=r)))(rng.randrange(1 << 30))
        timed = Timed(hero_bot)
        opponents = [FIELD[name](rng.randrange(1 << 30)) for name in names]
        seats = [timed] + opponents
        rng.shuffle(seats)
        hero_seat = seats.index(timed)
        limits = {hero_seat: limit} if limit else None
        log = [] if log_file else None
        kwargs = {} if starting is None else {"starting": starting}
        result = run_table(seats, rng, limits=limits, log=log, **kwargs)
        points.append(result["points"][hero_seat])
        places_hands.append(result["hands"])
        failures += result["failures"][hero_seat]
        timeouts += result["timeouts"][hero_seat]
        errors += getattr(hero_bot, "errors", 0)
        last_error = getattr(hero_bot, "last_error", None) or last_error
        all_times += timed.times
        if log_file:
            log_file.write(json.dumps({"table": table, "hands": log}) + "\n")
    if log_file:
        log_file.close()
    all_times.sort()
    n = len(all_times)
    return {
        "field": field, "tables": tables,
        "points": statistics.mean(points),
        "stderr": statistics.stdev(points) / tables ** 0.5 if tables > 1 else 0,
        "mean_hands": statistics.mean(places_hands),
        "errors": errors, "failures": failures, "timeouts": timeouts, "last_error": last_error,
        "decisions": n,
        "avg_ms": 1000 * sum(all_times) / n if n else 0,
        "p99_ms": 1000 * all_times[int(n * 0.99)] if n else 0,
        "max_ms": 1000 * all_times[-1] if n else 0,
        "under_1ms": sum(t < 0.001 for t in all_times) / n if n else 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tables", type=int, default=50)
    parser.add_argument("--field", default="mixed", choices=FIELDS)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--limit", type=float, default=None, help="decision limit in seconds")
    args = parser.parse_args()
    print(json.dumps(play(args.tables, args.field, args.seed, limit=args.limit)))


if __name__ == "__main__":
    main()
