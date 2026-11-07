"""Practice opponents, including the spec's stress cases. All cheap and rule-based."""
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bot.evaluator import CARD, CATEGORY_SHIFT, score7  # noqa: E402
from bot.tables import TABLES  # noqa: E402


def _pct(state):
    a, b = (CARD[c] for c in state["hole"])
    return TABLES.percentile_of(a, b)


def _category(state):
    if not state["board"]:
        return -1
    cards = [CARD[c] for c in state["hole"] + state["board"]]
    return score7(cards) >> CATEGORY_SHIFT


def _raise(state, target):
    if not state["can_raise"]:
        return "check" if state["to_call"] == 0 else "call"
    return ("raise", max(state["min_raise_to"], min(int(target), state["max_raise_to"])))


class Base:
    def __init__(self, seed=1):
        self.rng = random.Random(seed)


class CheckOrFold(Base):
    def __call__(self, s):
        return "check" if s["to_call"] == 0 else "fold"


class CheckOrCall(Base):
    def __call__(self, s):
        return "check" if s["to_call"] == 0 else "call"


class MinRaiser(Base):
    def __call__(self, s):
        return _raise(s, s["min_raise_to"])


class AllIn(Base):
    def __call__(self, s):
        return _raise(s, s["max_raise_to"])


class Tag(Base):
    """Tight-aggressive: strong preflop ranges, bets made hands, folds without one."""

    def __call__(self, s):
        free = s["to_call"] == 0
        bb = s["big_blind"]
        if s["street"] == "preflop":
            p = _pct(s)
            if p <= 6:
                return _raise(s, max(s["bets"]) * 3 + bb)
            if p <= 15:
                if max(s["bets"]) <= bb:
                    return _raise(s, 3 * bb)
                return "call" if s["to_call"] <= 6 * bb else "fold"
            return "check" if free else "fold"
        cat = _category(s)
        pot = s["pot"]
        if cat >= 2:
            return _raise(s, s["bets"][s["seat"]] + s["to_call"] + int(0.7 * pot))
        if cat == 1:
            if free:
                return _raise(s, int(0.5 * pot)) if self.rng.random() < 0.6 else "check"
            return "call" if s["to_call"] <= 0.5 * pot else "fold"
        if free:
            return _raise(s, int(0.5 * pot)) if self.rng.random() < 0.2 else "check"
        return "fold"


class Station(Base):
    """Loose and sticky: calls a lot with any pair or better, rarely raises."""

    def __call__(self, s):
        free = s["to_call"] == 0
        if s["street"] == "preflop":
            if _pct(s) <= 45:
                return "check" if free else ("call" if s["to_call"] <= s["stacks"][s["seat"]] / 4 else "fold")
            return "check" if free else "fold"
        cat = _category(s)
        if free:
            return _raise(s, int(0.5 * s["pot"])) if cat >= 2 else "check"
        if cat >= 1 or s["to_call"] <= 0.3 * s["pot"]:
            return "call"
        return "fold"


class Nit(Base):
    """Folds almost everything and only continues with very strong hands."""

    def __call__(self, s):
        free = s["to_call"] == 0
        if s["street"] == "preflop":
            if _pct(s) <= 5:
                return _raise(s, max(s["bets"]) * 3)
            return "check" if free else "fold"
        cat = _category(s)
        if cat >= 3:
            return _raise(s, s["bets"][s["seat"]] + s["to_call"] + int(s["pot"]))
        if cat == 2 and not free:
            return "call" if s["to_call"] <= 0.5 * s["pot"] else "fold"
        return "check" if free else "fold"


class Maniac(Base):
    """Raises often with random sizes and calls a lot."""

    def __call__(self, s):
        if s["can_raise"] and self.rng.random() < 0.35:
            return ("raise", self.rng.randint(s["min_raise_to"], s["max_raise_to"]))
        if s["to_call"] == 0:
            return "check"
        return "call" if self.rng.random() < 0.6 else "fold"


class StyleSwitcher(Base):
    """Stress case: changes style every 30 hands within a table."""

    def __init__(self, seed=1):
        super().__init__(seed)
        self.styles = [Tag(seed), Maniac(seed), Nit(seed), Station(seed)]

    def __call__(self, s):
        return self.styles[(s.get("hand_number", 0) // 30) % 4](s)


FIELD = {
    "tag": Tag, "station": Station, "nit": Nit, "maniac": Maniac,
    "minraiser": MinRaiser, "allin": AllIn, "checkfold": CheckOrFold,
    "checkcall": CheckOrCall, "switcher": StyleSwitcher,
}
