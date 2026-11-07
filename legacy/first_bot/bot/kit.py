"""Kit interface: the official state and memory in, an official Action and memory out.

Everything the policy keeps between decisions travels in memory, because any copy of the
bot may answer any table and self or globals do not survive between calls. The official
state is rebuilt into the practice-engine dict that bot/view.py reads, so the policy is
unchanged. Field names follow the organizers' Getting started page and are provisional
until the kit's SDK is available; every read goes through field() so a rename is one edit.
"""
import pickle
import random
import time
import zlib

from . import generic, rules
from .params import PARAMS
from .policy import Policy
from .variant import ACTIVE, DecisionContext
from .view import make_view

MEMORY_TAG = b"FB2"
BETTING_KINDS = ("fold", "check", "call", "raise")

diagnostics = {"errors": 0, "last_error": None, "memory_resets": 0, "layers": {}}
decision_log = None  # set to a list in sims to get one row per decision


def field(obj, name, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def kind_name(kind):
    if isinstance(kind, str):
        return kind.lower()
    for attr in ("value", "name"):
        value = getattr(kind, attr, None)
        if isinstance(value, str):
            return value.lower()
    return str(kind).rsplit(".", 1)[-1].lower()


# ---- Memory ----------------------------------------------------------------------
def load_policy(memory):
    if memory and memory.startswith(MEMORY_TAG):
        try:
            policy = pickle.loads(memory[len(MEMORY_TAG):])
            if isinstance(policy, Policy):
                return policy
        except Exception:
            pass
        diagnostics["memory_resets"] += 1
    return Policy()


def save_policy(policy):
    rng, policy.rng = policy.rng, None
    try:
        return MEMORY_TAG + pickle.dumps(policy, pickle.HIGHEST_PROTOCOL)
    finally:
        policy.rng = rng


def decision_seed(state, history_length):
    config = field(state, "config")
    key = f"{field(config, 'table_id')}|{field(state, 'hand_number')}|{history_length}"
    return zlib.crc32(key.encode())


# ---- State -----------------------------------------------------------------------
def blind_sizes(state, history):
    blinds = field(state, "blinds")
    small = big = None
    if isinstance(blinds, (list, tuple)) and len(blinds) >= 2 and all(
            isinstance(b, (int, float)) for b in blinds[:2]):
        small, big = blinds[0], blinds[1]
    elif blinds is not None:
        for name in ("small_blind", "small", "sb"):
            small = small if small is not None else field(blinds, name)
        for name in ("big_blind", "big", "bb"):
            big = big if big is not None else field(blinds, name)
    if not big:
        posted = [field(e, "amount") or 0 for e in history if kind_name(field(e, "kind")) == "blind"]
        big = max(posted, default=0) or 2
    return int(small if small else big // 2), int(big)


def table_order(state):
    """Seats still in the tournament, in seat order, and each seat number's index."""
    seats = sorted((s for s in field(state, "seats", []) if kind_name(field(s, "status")) != "busted"),
                   key=lambda s: field(s, "seat"))
    index = {field(s, "seat"): i for i, s in enumerate(seats)}
    return seats, index


def button_index(state, seats, index):
    button = field(state, "button")
    if button in index:
        return index[button]
    later = [i for i, s in enumerate(seats) if field(s, "seat") > button]
    return later[0] if later else 0


def replay_history(history, index, players):
    """Official events of this hand to practice events: street, seat, action, to, pot,
    amount (chips added) and stacks (each index's chips paid so far, made absolute later)."""
    street, board_cards = "preflop", 0
    round_bet = [0] * players
    paid = [0] * players
    pot = 0
    events = []
    for event in history:
        kind = kind_name(field(event, "kind"))
        seat = index.get(field(event, "seat"))
        amount = field(event, "amount") or 0
        if kind == "board":
            board_cards += len(field(event, "cards") or ())
            street = ACTIVE.board_streets.get(board_cards, street)
            round_bet = [0] * players
            continue
        if seat is None:
            continue
        if kind in ("ante", "blind"):
            if kind == "blind":
                round_bet[seat] += amount
            paid[seat] += amount
            pot += amount
            continue
        if kind not in BETTING_KINDS:  # show, win, stack and any kind a variant adds
            continue
        added, to = 0, None
        if kind == "call":
            added = amount
        elif kind == "raise":
            to = amount
            added = amount - round_bet[seat]
        events.append({"street": street, "seat": seat, "action": kind, "to": to,
                       "pot": pot, "amount": added, "stacks": list(paid)})
        round_bet[seat] += added
        paid[seat] += added
        pot += added
    return events, paid


def practice_state(state):
    """The dict bot/view.py reads, built from the official state."""
    seats, index = table_order(state)
    players = len(seats)
    history = list(field(state, "history") or ())
    events, paid = replay_history(history, index, players)
    stacks = [field(s, "stack") or 0 for s in seats]
    starting = [stacks[i] + paid[i] for i in range(players)]
    for event in events:
        event["stacks"] = [starting[i] - event["stacks"][i] for i in range(players)]
    small, big = blind_sizes(state, history)
    board = list(field(state, "board") or ())
    raise_option = next((a for a in field(state, "legal_actions") or ()
                         if kind_name(field(a, "kind")) == "raise"), None)
    config = field(state, "config")
    hand_number = field(state, "hand_number") or 0
    hand_cap = field(config, "hand_cap")
    return {
        "seat": index[field(state, "seat", field(config, "seat"))],
        "button": button_index(state, seats, index),
        "street": ACTIVE.street(len(board)),
        "hole": list(field(state, "cards") or ()),
        "board": board,
        "pot": field(state, "pot") or 0,
        "to_call": field(state, "to_call") or 0,
        "can_raise": raise_option is not None,
        "min_raise_to": field(raise_option, "min_amount") or 0,
        "max_raise_to": field(raise_option, "max_amount") or 0,
        "stacks": stacks,
        "bets": [field(s, "bet") or 0 for s in seats],
        "folded": [kind_name(field(s, "status")) == "folded" for s in seats],
        "big_blind": big,
        "small_blind": small,
        "history": events,
        "hand_number": hand_number,
        "hands_remaining": hand_cap - hand_number if hand_cap else 100,
        "players_left": field(state, "players_remaining") or players,
        "seat_ids": [field(s, "seat") for s in seats],
    }


# ---- Actions ---------------------------------------------------------------------
def offered(state):
    return {kind_name(field(a, "kind")): a for a in field(state, "legal_actions") or ()}


def automatic_action(state, action_type):
    """Check if free, otherwise fold, otherwise the first offered action at its minimum."""
    legal = offered(state)
    if "check" in legal:
        return action_type.check()
    if "fold" in legal:
        return action_type.fold()
    first = (field(state, "legal_actions") or ())[0]
    return action_type(field(first, "kind"), field(first, "min_amount"))


def official_action(state, reply, action_type):
    """The policy's clamped reply as an offered Action, or the automatic choice."""
    legal = offered(state)
    kind = reply[0] if isinstance(reply, tuple) else reply
    if kind == "raise" and "raise" in legal:
        option = legal["raise"]
        total = max(int(field(option, "min_amount")), min(int(reply[1]), int(field(option, "max_amount"))))
        return action_type.raise_to(total)
    if kind in legal and kind in ("fold", "check", "call"):
        return getattr(action_type, kind)()
    return automatic_action(state, action_type)


def clamp_reply(state, action):
    """Same rules as agent.legal_action: fit any reply into the legal set ourselves."""
    kind = action[0]
    free = state["to_call"] == 0
    if kind == "raise":
        if not state["can_raise"]:
            return "check" if free else "call"
        return ("raise", max(state["min_raise_to"], min(int(action[1]), state["max_raise_to"])))
    if kind == "call":
        return "check" if free else "call"
    return "check" if free else "fold"


# ---- Layers ----------------------------------------------------------------------
def record(layer, practice=None, action=None, start=None):
    diagnostics["layers"][layer] = diagnostics["layers"].get(layer, 0) + 1
    if decision_log is not None:
        decision_log.append({
            "layer": layer,
            "street": practice["street"] if practice else None,
            "hand": practice["hand_number"] if practice else None,
            "action": action if isinstance(action, (str, tuple)) else repr(action),
            "ms": 1000 * (time.perf_counter() - start) if start else None,
        })


def extra_decision(state, action_type, deadline):
    """A non-betting decision a variant adds: the spec's hook, else the automatic choice."""
    legal = field(state, "legal_actions") or ()
    option = next((a for a in legal if kind_name(field(a, "kind")) not in BETTING_KINDS), legal[0])
    kind = kind_name(field(option, "kind"))
    seats = field(state, "seats", [])
    ctx = DecisionContext(
        hole=[ACTIVE.parse_card(c) for c in field(state, "cards") or ()],
        board=[ACTIVE.parse_card(c) for c in field(state, "board") or ()],
        pot=field(state, "pot") or 0, to_call=field(state, "to_call") or 0,
        stack=next((field(s, "stack") for s in seats if field(s, "seat") == field(state, "seat")), 0),
        opponents=max(1, sum(1 for s in seats if kind_name(field(s, "status")) in ("active", "all_in")) - 1),
        option=option, options=legal, deadline=deadline,
        rng=random.Random(decision_seed(state, len(field(state, "history") or ()))))
    choice = ACTIVE.extra_decision(kind, ctx)
    if choice is None or choice.kind not in offered(state):
        return None
    # TODO(kit): confirm how the kit builds a variant action; RULES.md describes it.
    return action_type(field(option, "kind"), ACTIVE.to_kit(choice))


def betting_decision(state, memory, action_type, start, deadline):
    practice = practice_state(state)
    policy = load_policy(memory)
    policy.rng = random.Random(decision_seed(state, len(practice["history"])))
    view = make_view(practice)
    rule = rules.first_firing(rules.RuleContext(view, policy, practice))
    if rule is not None:
        layer, reply = "rule:" + rule.name, rule.action(rules.RuleContext(view, policy, practice))
    elif ACTIVE.uses_holdem_policy:
        try:
            layer, reply = "policy", policy.decide(view, deadline)
        except Exception as error:
            diagnostics["errors"] += 1
            diagnostics["last_error"] = repr(error)
            layer, reply = "generic-after-error", generic.decide(practice, ACTIVE, deadline, policy.rng)
    else:
        layer, reply = "generic", generic.decide(practice, ACTIVE, deadline, policy.rng)
    action = official_action(state, clamp_reply(practice, reply), action_type)
    record(layer, practice, reply, start)
    return action, save_policy(policy)


def play(state, memory, action_type):
    """One decision: (Action, memory). Layers, first that answers wins:
    safety (this try/except) > extra decision hook > rules > hold'em policy > generic engine.
    Any failure keeps the old memory and checks, else folds, else takes the automatic choice."""
    start = time.perf_counter()
    deadline = start + PARAMS["DECISION_BUDGET_S"]
    try:
        if field(state, "phase", "betting") != "betting" or not set(offered(state)) <= set(BETTING_KINDS):
            action = extra_decision(state, action_type, deadline)
            if action is not None:
                record("extra", start=start)
                return action, memory
            record("automatic", start=start)
            return automatic_action(state, action_type), memory
        return betting_decision(state, memory, action_type, start, deadline)
    except Exception as error:
        diagnostics["errors"] += 1
        diagnostics["last_error"] = repr(error)
        record("safety", start=start)
        return automatic_action(state, action_type), memory
