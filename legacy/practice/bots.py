"""Baseline opponents. Each one is a function: act(state) -> action."""
import random

_rng = random.Random(7)


def check_or_fold(state):
    return "check" if state["to_call"] == 0 else "fold"


def caller(state):
    return "check" if state["to_call"] == 0 else "call"


def min_raiser(state):
    if state["can_raise"]:
        return ("raise", state["min_raise_to"])
    return "check" if state["to_call"] == 0 else "call"


def maniac(state):
    if state["can_raise"] and _rng.random() < 0.35:
        return ("raise", _rng.randint(state["min_raise_to"], state["max_raise_to"]))
    if state["to_call"] == 0:
        return "check"
    return "call" if _rng.random() < 0.6 else "fold"


BOTS = {
    "check_or_fold": check_or_fold,
    "caller": caller,
    "min_raiser": min_raiser,
    "maniac": maniac,
}
