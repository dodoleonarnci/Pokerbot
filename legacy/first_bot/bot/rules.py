"""Rules layer: small high-confidence exceptions that run before the policy.

Each rule has a name, a priority (lower runs first), an enable flag in PARAMS["RULES"] and a
fire counter. trigger() and action() read a RuleContext and action() returns a reply in the
policy's format: "fold", "check", "call" or ("raise", total).
"""
import time

from .params import PARAMS
from .variant import ACTIVE


class RuleContext:
    __slots__ = ("view", "policy", "practice")

    def __init__(self, view, policy, practice):
        self.view, self.policy, self.practice = view, policy, practice


def beta_rate(hits, trials, prior_hits, prior_trials):
    return (hits + prior_hits) / (trials + prior_trials)


class Rule:
    name = "rule"
    priority = 100
    fires = 0

    def enabled(self):
        return PARAMS["RULES"].get(self.name, False)

    def trigger(self, ctx):
        raise NotImplementedError

    def action(self, ctx):
        raise NotImplementedError


def preflop_players_behind(view):
    """Seats still to act after us preflop, for three or more players."""
    order = [(view.button + 3 + k) % view.players for k in range(view.players)]
    mine = order.index(view.seat)
    return [s for s in order[mine + 1:] if not view.folded[s]]


class StealVsFolders(Rule):
    """Open-raise any two cards when everyone behind folds to bets at a high, well-sampled rate."""
    name = "steal_vs_folders"
    priority = 10

    def trigger(self, ctx):
        view = ctx.view
        if view.street != "preflop" or view.players < 3 or not view.can_raise:
            return False
        if any(e["action"] in ("raise", "call") for e in view.history):
            return False
        behind = preflop_players_behind(view)
        if not behind:
            return False
        P = PARAMS
        seats = ctx.policy.opponents.seats
        for seat in behind:
            stats = seats.get(view.seat_ids[seat])
            if stats is None or stats.faced_bet < P["RULE_MIN_SAMPLE"]:
                return False
            rate = beta_rate(stats.folded_bet, stats.faced_bet, P["RULE_PRIOR_FOLDS"], P["RULE_PRIOR_TRIALS"])
            if rate < P["STEAL_FOLD_RATE"]:
                return False
        return True

    def action(self, ctx):
        view = ctx.view
        return ("raise", max(view.min_raise, int(PARAMS["OPEN_BB"] * view.bb)))


def observe_aggression(ctx):
    """Per-seat raises and decisions this table, kept on the policy so they travel in memory."""
    view, policy = ctx.view, ctx.policy
    counts = getattr(policy, "aggression", None)
    if counts is None:
        counts = policy.aggression = {}
    if getattr(policy, "aggression_hand", None) != view.hand_number:
        policy.aggression_hand, policy.aggression_seen = view.hand_number, 0
    for event in view.history[policy.aggression_seen:]:
        if event["seat"] != view.seat:
            row = counts.setdefault(view.seat_ids[event["seat"]], [0, 0])
            row[0] += event["action"] == "raise"
            row[1] += 1
    policy.aggression_seen = len(view.history)


class VersusManiac(Rule):
    """Heads-up in the pot against a seat that raises almost every decision: its range is any
    two cards, so call or shove on equity against a random hand."""
    name = "versus_maniac"
    priority = 20

    def bettor(self, view):
        raises = [e["seat"] for e in view.history if e["action"] == "raise"]
        return raises[-1] if raises else None

    def trigger(self, ctx):
        view = ctx.view
        if view.to_call <= 0:
            return False
        live = [i for i in range(view.players) if i != view.seat and not view.folded[i]]
        bettor = self.bettor(view)
        if len(live) != 1 or bettor != live[0]:
            return False
        raises, decisions = getattr(ctx.policy, "aggression", {}).get(view.seat_ids[bettor], (0, 0))
        P = PARAMS
        return decisions >= P["RULE_MIN_SAMPLE"] and beta_rate(
            raises, decisions, P["RULE_PRIOR_FOLDS"], P["RULE_PRIOR_TRIALS"]) >= P["MANIAC_RAISE_RATE"]

    def action(self, ctx):
        view, P = ctx.view, PARAMS
        deadline = time.perf_counter() + P["RULE_EQUITY_S"]
        equity = ACTIVE.equity(view.hole, view.board, 1, deadline, ctx.policy.rng, 150)
        if equity >= P["MANIAC_SHOVE_EQUITY"] and view.can_raise:
            return ("raise", view.max_raise)
        if equity >= view.to_call / (view.pot + view.to_call) + P["MANIAC_CALL_MARGIN"]:
            return "call"
        return "fold"


RULES = sorted([StealVsFolders(), VersusManiac()], key=lambda r: r.priority)


def first_firing(ctx):
    observe_aggression(ctx)
    for rule in RULES:
        if rule.enabled() and rule.trigger(ctx):
            type(rule).fires += 1
            return rule
    return None
