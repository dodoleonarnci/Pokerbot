"""VariantSpec: everything about the game that an announced variant can change.

The event-day job is to copy HoldemSpec, change what RULES.md changes, and set ACTIVE.
README.md lists every place a variant touches. Choices for extra decision types (discard,
bid, choose-a-card) come back as Choice(kind, value); bot/kit.py turns them into the kit's
Action, so a hook never builds kit objects itself.
"""
import time
from itertools import combinations

from .evaluator import CARD, class_of, score7

HOLDEM_DECK = tuple(CARD.values())
CARD_TEXT = {i: text for text, i in CARD.items()}


class Choice:
    __slots__ = ("kind", "value")

    def __init__(self, kind, value=None):
        self.kind, self.value = kind, value

    def __repr__(self):
        return f"Choice({self.kind!r}, {self.value!r})"


class DecisionContext:
    """What a hook sees: our cards and the table, already parsed by the spec."""
    __slots__ = ("hole", "board", "pot", "to_call", "stack", "opponents", "option", "options",
                 "deadline", "rng")

    def __init__(self, hole, board, pot, to_call, stack, opponents, option, options, deadline, rng):
        self.hole, self.board, self.pot, self.to_call = hole, board, pot, to_call
        self.stack, self.opponents, self.option, self.options = stack, opponents, option, options
        self.deadline, self.rng = deadline, rng


class HoldemSpec:
    name = "holdem"
    hole_cards = 2
    board_streets = {0: "preflop", 3: "flop", 4: "turn", 5: "river"}
    board_size = 5
    deck = HOLDEM_DECK
    # The precomputed strategy in bot/policy.py assumes exactly this game. A variant that
    # changes cards, hand ranks or streets sets this False and gets the generic engine.
    uses_holdem_policy = True
    extra_kinds = ("discard", "bid", "choose_card")

    # ---- Cards and hands ---------------------------------------------------------
    def parse_card(self, text):
        return CARD[text]

    def card_text(self, card):
        return CARD_TEXT[card]

    def to_kit(self, choice):
        """A Choice's value in the kit's format: cards back to strings like "As"."""
        value = choice.value
        if choice.kind in ("discard", "choose_card"):
            return [self.card_text(c) for c in value] if isinstance(value, list) else self.card_text(value)
        return value

    def street(self, board_count):
        return self.board_streets.get(board_count, "river")

    def evaluate(self, hole, board):
        """Strength of our best hand; larger is stronger."""
        return score7(list(hole) + list(board))

    def hand_class(self, hole):
        """Preflop class index used by the precomputed tables."""
        return class_of(hole[0], hole[1])

    def equity(self, hole, board, opponents, deadline, rng, max_samples=200):
        """Monte Carlo share of pots won against random hands, stopped at the deadline."""
        used = set(hole) | set(board)
        live = [c for c in self.deck if c not in used]
        missing = self.board_size - len(board)
        need = missing + self.hole_cards * max(1, opponents)
        if need > len(live):
            return 0.5
        won = samples = 0.0
        while samples < max_samples and (samples < 8 or time.perf_counter() < deadline):
            drawn = rng.sample(live, need)
            full_board = list(board) + drawn[:missing]
            ours = self.evaluate(hole, full_board)
            best = max(self.evaluate(drawn[missing + k * self.hole_cards:
                                           missing + (k + 1) * self.hole_cards], full_board)
                       for k in range(max(1, opponents)))
            won += 1.0 if ours > best else 0.5 if ours == best else 0.0
            samples += 1
        return won / samples

    # ---- Scoring -----------------------------------------------------------------
    def payouts(self, announced):
        """Points by finishing place. A variant with payout modifiers changes them here."""
        return tuple(announced)

    # ---- Extra decision types ----------------------------------------------------
    def extra_decision(self, kind, ctx):
        """Return a Choice for a non-betting decision, or None to take the automatic choice."""
        handler = getattr(self, f"decide_{kind}", None)
        return handler(ctx) if handler else None

    def decide_discard(self, ctx):
        """Keep the subset that evaluates best; option.min_amount/max_amount bound the count."""
        low = int(ctx.option.min_amount or 0)
        high = int(ctx.option.max_amount if ctx.option.max_amount is not None else low)
        best, best_score = (), None
        for count in range(low, min(high, len(ctx.hole)) + 1):
            for thrown in combinations(ctx.hole, count):
                kept = [c for c in ctx.hole if c not in thrown]
                score = self._kept_strength(kept, ctx)
                if best_score is None or score > best_score:
                    best, best_score = thrown, score
        return Choice("discard", list(best))

    def _kept_strength(self, kept, ctx):
        """(1, made-hand score) once five cards exist, else (0, pairs/suits/ranks heuristic)."""
        cards = list(kept) + list(ctx.board)
        if len(cards) >= 5:
            if len(cards) <= 7:
                return (1, score7(cards))
            return (1, max(score7(list(seven)) for seven in combinations(cards, 7)))
        ranks = [c >> 2 for c in cards]
        pairs = len(ranks) - len(set(ranks))
        suited = max((sum(1 for c in cards if c & 3 == s) for s in range(4)), default=0)
        high = sum(c >> 2 for c in kept) / max(1, len(kept))
        return (0, pairs * 100 + suited * 10 + high)

    def decide_bid(self, ctx):
        """Bid our equity share of the pot, inside the offered range."""
        equity = self.equity(ctx.hole, ctx.board, ctx.opponents, ctx.deadline, ctx.rng, 60)
        low = int(ctx.option.min_amount or 0)
        high = int(ctx.option.max_amount if ctx.option.max_amount is not None else low)
        edge = max(0.0, equity - 1.0 / (ctx.opponents + 1))
        return Choice("bid", max(low, min(high, int(edge * ctx.pot))))

    def decide_choose_card(self, ctx):
        """Pick the offered card that makes our hand strongest."""
        cards = [self.parse_card(c) if isinstance(c, str) else c
                 for c in getattr(ctx.option, "cards", None) or ()]
        if not cards:
            return None
        best = max(cards, key=lambda c: self._kept_strength(list(ctx.hole) + [c], ctx))
        return Choice("choose_card", best)


ACTIVE = HoldemSpec()

