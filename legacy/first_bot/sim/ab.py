#!/usr/bin/env python3
"""A/B-test settings through the kit path on identical seeds and seatings.

Usage: python3.12 sim/ab.py --tables 200 --fields mixed checkers \
           --b RULES.steal_vs_folders=false --b-generic
Each arm reports average points with a 95% interval and which layers made the decisions.
"""
import argparse
import copy
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "sim")]

import kit_harness  # noqa: E402
from bot import kit, variant  # noqa: E402
from bot.params import PARAMS  # noqa: E402
from runner import FIELDS, play  # noqa: E402

FIELDS.setdefault("minraisers", ["minraiser"] * 7)
FIELDS.setdefault("one_min", ["minraiser"] + ["checkfold"] * 6)
FIELDS.setdefault("stations", ["station"] * 7)
FIELDS.setdefault("nits", ["nit"] * 7)


def parse_value(text):
    try:
        return json.loads(text)
    except ValueError:
        return text


def apply(settings):
    for item in settings:
        path, value = item.split("=", 1)
        target, keys = PARAMS, path.split(".")
        for key in keys[:-1]:
            target = target[key]
        target[keys[-1]] = parse_value(value)


def arm(name, settings, generic, tables, fields, seed):
    saved, saved_flag = copy.deepcopy(PARAMS), variant.ACTIVE.uses_holdem_policy
    apply(settings)
    variant.ACTIVE.uses_holdem_policy = not generic
    try:
        rows = {}
        for field in fields:
            kit.diagnostics["layers"] = {}
            result = play(tables, field, seed, make_hero=kit_harness.KitHero)
            rows[field] = {"points": round(result["points"], 2),
                           "ci95": round(1.96 * result["stderr"], 2),
                           "failures": result["failures"], "errors": result["errors"],
                           "layers": dict(kit.diagnostics["layers"])}
        return {"arm": name, "settings": settings, "generic": generic, "fields": rows}
    finally:
        PARAMS.clear()
        PARAMS.update(saved)
        variant.ACTIVE.uses_holdem_policy = saved_flag


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tables", type=int, default=200)
    parser.add_argument("--fields", nargs="+", default=["mixed"], choices=list(FIELDS))
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--a", action="append", default=[], help="KEY=VALUE for arm A")
    parser.add_argument("--b", action="append", default=[], help="KEY=VALUE for arm B")
    parser.add_argument("--a-generic", action="store_true")
    parser.add_argument("--b-generic", action="store_true")
    args = parser.parse_args()
    for name, settings, generic in (("A", args.a, args.a_generic), ("B", args.b, args.b_generic)):
        print(json.dumps(arm(name, settings, generic, args.tables, args.fields, args.seed)))


if __name__ == "__main__":
    main()
