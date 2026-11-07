"""Flop discard-and-reveal bot v8: v7 preflop, selection and ICM, with postflop play driven by
the exploit rules in rules.json (spot keys, hand buckets, overfold bluffs, call lists)."""

import hashlib
import json
import os
import random
import time

import eval7
import poker_agent_sdk
from poker_agent_sdk import Action, GameState

RANKS = "23456789TJQKA"
RANK_VALUE = {r: i for i, r in enumerate(RANKS)}
DECK = [r + s for r in RANKS for s in "shdc"]
CARD = {c: eval7.Card(c) for c in DECK}

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "preflop3.json")) as handle:
    PREFLOP = json.load(handle)

SELECT_SAMPLES = 30
KEEP_OPTIONS = ((0, 1, 2), (0, 2, 1), (1, 2, 0))  # (keep, keep, discard)

MONSTER, TOP, PAIR, HIGH = 3, 2, 1, 0
STRONG_BRANCH_AGGRESSION = {MONSTER: 0.95, TOP: 0.85, PAIR: 0.5, HIGH: 0.35}
WEAK_BRANCH_AGGRESSION = {MONSTER: 0.7, TOP: 0.55, PAIR: 0.45, HIGH: 0.4}
DRAW_BONUS = 0.15

OPEN_WIDTH_BY_PLAYERS_AFTER = {0: 0.22, 1: 0.55, 2: 0.48, 3: 0.35, 4: 0.29, 5: 0.25}
DEFAULT_OPEN_WIDTH = 0.21
# Exploration of decision points round 1 showed we rarely reached (raise share facing a bet).
EXPLORE_LIGHT_THREE_BET = 0.15
EXPLORE_RAISE_FACING_BET = {3: 0.06, 4: 0.08, 5: 0.10}
PUSH_WIDTH_BY_PLAYERS_AFTER = {0: 0.15, 1: 0.45, 2: 0.33, 3: 0.27, 4: 0.22, 5: 0.18}

POSTFLOP_SCALE_RANGE = (0.4, 1.6)
PREFLOP_WIDTH_SCALE_RANGE = (0.7, 1.3)
SHOVE_WIDTH_SCALE_RANGE = (0.85, 1.15)
MAX_BET_PROBABILITY = 0.97

rng = random.Random()
EQUITY_TIME_LIMIT_NS = 450_000
decision_started_ns = [0]

# ---------------------------------------------------------------- aggressiveness


def aggression_seed(hand_number, cards):
    return f"{hand_number}:{''.join(sorted(cards))}"


def factor_from_seed(seed):
    return int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) / 2**32


def table_aggression(state, memory):
    """One factor in [0, 1) per table, fixed at the bot's first decision there. It is a hash
    of that hand's number and dealt cards, so analysis can recompute it from hand histories."""
    factor = memory.get("a")
    if isinstance(factor, (int, float)) and 0.0 <= factor < 1.0:
        return float(factor)
    factor = factor_from_seed(aggression_seed(state.hand_number, state.cards))
    memory["a"] = factor
    return factor


def scaled(factor, bounds):
    low, high = bounds
    return low + (high - low) * factor

# ---------------------------------------------------------------- helpers


def hand_key(cards):
    ordered = sorted(cards, key=lambda c: RANK_VALUE[c[0]], reverse=True)
    groups = {}
    for card in ordered:
        groups.setdefault(card[1], []).append(card[0])
    shape = sorted(("".join(v) for v in groups.values()), key=lambda s: (-len(s), s))
    return "".join(c[0] for c in ordered) + ":" + "|".join(shape)


def me(state):
    for seat in state.seats:
        if seat.seat == state.seat:
            return seat
    raise LookupError("own seat missing")


def clamp_raise(state, total):
    legal = state.can("raise")
    if legal is None:
        return None
    total = int(max(legal.min_amount, min(legal.max_amount, total)))
    return Action.raise_to(total)


def call_or_check(state):
    if state.can("check"):
        return Action.check()
    if state.can("call"):
        return Action.call()
    return Action.fold()


def fold_or_check(state):
    if state.can("check"):
        return Action.check()
    return Action.fold()


def passive(state):
    if state.phase == "select":
        return Action("select", cards=(2, 0))
    return fold_or_check(state)


def load_memory(memory):
    try:
        data = json.loads(memory) if memory else {}
        return data if isinstance(data, dict) else {}
    except (ValueError, UnicodeDecodeError):
        return {}


# ---------------------------------------------------------------- selection


def choose_selection(state, memory):
    hole = list(state.cards)
    board = list(state.board)
    dead = set(hole) | set(board)
    for seat in state.seats:
        dead.update(seat.shown_cards)
    rest = [CARD[c] for c in DECK if c not in dead]
    hole_cards = [CARD[c] for c in hole]
    board_cards = [CARD[c] for c in board]
    need = 5 - len(board_cards)

    scores = [0.0, 0.0, 0.0]
    evaluate = eval7.evaluate
    sample = rng.sample
    for _ in range(SELECT_SAMPLES):
        drawn = sample(rest, 2 + need)
        runout = board_cards + drawn[2:]
        villain = evaluate(drawn[:2] + runout)
        for option, (a, b, _discard) in enumerate(KEEP_OPTIONS):
            hero = evaluate([hole_cards[a], hole_cards[b]] + runout)
            if hero > villain:
                scores[option] += 1.0
            elif hero == villain:
                scores[option] += 0.5
    best = max(range(3), key=lambda i: scores[i])
    keep_a, keep_b, discard = KEEP_OPTIONS[best]

    rank_a, rank_b = RANK_VALUE[hole[keep_a][0]], RANK_VALUE[hole[keep_b][0]]
    if rank_a == rank_b:
        reveal = pair_reveal(hole, keep_a, keep_b, board)
        branch = 1
    else:
        stronger, weaker = (keep_a, keep_b) if rank_a > rank_b else (keep_b, keep_a)
        branch = 1 if rng.random() < 0.5 else 0
        reveal = stronger if branch else weaker
    memory["h"] = state.hand_number
    memory["b"] = branch
    return Action("select", cards=(discard, reveal))


def pair_reveal(hole, keep_a, keep_b, board):
    board_suits = [c[1] for c in board]
    count_a = board_suits.count(hole[keep_a][1])
    count_b = board_suits.count(hole[keep_b][1])
    if count_a >= 2 and count_a > count_b:
        return keep_b
    if count_b >= 2 and count_b > count_a:
        return keep_a
    return keep_a if rng.random() < 0.5 else keep_b


# ---------------------------------------------------------------- postflop


def classify(hole, board):
    """Made-hand category and whether a flush or open-ended straight draw is live."""
    cards = [CARD[c] for c in hole + board]
    value = eval7.evaluate(cards)
    kind = eval7.handtype(value)
    board_ranks = [RANK_VALUE[c[0]] for c in board]
    hole_ranks = [RANK_VALUE[c[0]] for c in hole]
    top_board = max(board_ranks)

    if kind in ("Straight", "Flush", "Full House", "Quads", "Straight Flush"):
        if len(board) == 5 and eval7.evaluate([CARD[c] for c in board]) == value:
            category = HIGH
        else:
            category = MONSTER
    elif kind == "Trips":
        board_trips = any(board_ranks.count(r) >= 3 for r in board_ranks)
        category = HIGH if board_trips else MONSTER
    else:
        paired = [r for r in hole_ranks if r in board_ranks]
        pocket = hole_ranks[0] == hole_ranks[1]
        if len(set(paired)) == 2:
            category = MONSTER
        elif paired:
            category = TOP if max(paired) >= top_board else PAIR
        elif pocket:
            category = TOP if hole_ranks[0] > top_board else PAIR
        else:
            category = HIGH

    draw = False
    if len(board) < 5 and category < MONSTER:
        suits = [c[1] for c in hole + board]
        for suit in set(c[1] for c in hole):
            if suits.count(suit) == 4:
                draw = True
        ranks = set(hole_ranks + board_ranks)
        if 12 in ranks:
            ranks.add(-1)
        for low in range(-1, 9):
            window = {low, low + 1, low + 2, low + 3}
            if window <= ranks and (set(hole_ranks) & window) and low >= 0 and low + 4 <= 12:
                draw = True
    return category, draw


# Postflop v8: exploit rules from analysis/exploit_rules (rules.json + cards.bucket).
import importlib.util as _importlib_util

_BOT_DIR = os.path.dirname(os.path.abspath(__file__))
_spec = _importlib_util.spec_from_file_location("dr_cards", os.path.join(_BOT_DIR, "cards.py"))
cards = _importlib_util.module_from_spec(_spec)
_spec.loader.exec_module(cards)

with open(os.path.join(_BOT_DIR, "rules.json")) as handle:
    RULES = json.load(handle)

BLUFF_SPOTS = {(e["key"], e["bet_size"]): e for e in RULES["bluff_spots"]}
CALL_SPOTS = {(e["key"], e["bet_size"]): e for e in RULES["call_spots"]}
EQUITY_TABLES = {street[0].upper(): RULES["equity"][street]["equity"] for street in RULES["equity"]}
FLOP_TURN_MARGIN = RULES["parameters"]["flop_turn_equity_margin"]
DEFAULT_MIX = (0.10, 0.08, 0.06, 0.28, 0.28, 0.20)
SIZE_ORDER = ("small", "medium", "pot", "overbet", "jam")
MIN_BLUFF_EV_LOW = 0.05
SEAT_PRIOR_WEIGHT = 8
MAX_BLUFF_STACK_SHARE_NEAR_MONEY = 0.20
VALUE_SIZE_TOP_PAIR = 0.6
VALUE_SIZE_STRONG = 0.75
BLUFF_RAISE_SIZE = 0.8
STREET_BY_BOARD = {3: "F", 4: "T", 5: "R"}


def size_bucket(increment, pot, to_call, jam):
    if jam:
        return "jam"
    share = increment / max(1, pot + to_call)
    if share <= 0.4:
        return "small"
    if share <= 0.8:
        return "medium"
    if share <= 1.25:
        return "pot"
    return "overbet"


def replay(state):
    """Walk this hand's events into per-street action lists with the pot and price at each
    action, plus who was still in. Raise amounts are round totals; calls carry chips added."""
    streets = [[]]
    pot = 0
    contributed = {}
    highest = 0
    folded = set()
    for event in state.history:
        kind = event.kind
        if kind == "board":
            if len(streets) < 4:
                streets.append([])
            contributed, highest = {}, 0
            continue
        if kind in ("ante", "blind"):
            pot += event.amount
            if kind == "blind":
                contributed[event.seat] = contributed.get(event.seat, 0) + event.amount
                highest = max(highest, contributed[event.seat])
            continue
        if kind not in ("fold", "check", "call", "raise"):
            continue
        seat = event.seat
        before = contributed.get(seat, 0)
        to_call = max(0, highest - before)
        record = {"seat": seat, "kind": kind, "pot": pot, "to_call": to_call,
                  "live": None, "increment": 0, "folded_before": frozenset(folded)}
        if kind == "call":
            pot += event.amount
            contributed[seat] = before + event.amount
        elif kind == "raise":
            added = event.amount - before
            record["increment"] = event.amount - highest
            pot += added
            contributed[seat] = event.amount
            highest = event.amount
        elif kind == "fold":
            folded.add(seat)
        streets[-1].append(record)
    return streets


def dealt_seats(state):
    return {s.seat for s in state.seats if s.status != "busted"}


def role_for(seat, streets, street_index):
    if street_index == 1:
        raisers = [a["seat"] for a in streets[0] if a["kind"] == "raise"]
        if not raisers:
            return "limped"
        return "PFA" if raisers[-1] == seat else "caller"
    previous = [a["seat"] for a in streets[street_index - 1] if a["kind"] == "raise"]
    if not previous:
        return "checked"
    return "agg" if previous[-1] == seat else "def"


def situation_for(actions_before):
    raises = [a for a in actions_before if a["kind"] == "raise"]
    if not raises:
        return ("first" if not actions_before else "checked-to"), ""
    last = raises[-1]
    faced = size_bucket(last["increment"], last["pot"], last["to_call"], last.get("jam", False))
    return ("vs-bet" if len(raises) == 1 else "vs-raise"), faced


def players_label(live_count):
    return "HU" if live_count == 2 else "MW"


def our_key(state, streets):
    street_index = len(streets) - 1
    current = streets[-1]
    live = sum(1 for s in state.seats if s.status in ("active", "all_in"))
    situation, faced = situation_for(current)
    role = role_for(state.seat, streets, street_index)
    return f"{STREET_BY_BOARD[len(state.board)]}|{players_label(live)}|{role}|{situation}|{faced}"


def bettor_key(state, streets):
    """Key and size of the last bet or raise we face, from the bettor's point of view."""
    street_index = len(streets) - 1
    current = streets[-1]
    index = max(i for i, a in enumerate(current) if a["kind"] == "raise")
    bet = current[index]
    seat_status = {s.seat: s.status for s in state.seats}
    later_raise = any(a["kind"] == "raise" and a["seat"] == bet["seat"] for a in current[index + 1:])
    jam = seat_status.get(bet["seat"]) == "all_in" and not later_raise
    live = len(dealt_seats(state) - bet["folded_before"])
    situation, faced = situation_for(current[:index])
    role = role_for(bet["seat"], streets, street_index)
    key = f"{STREET_BY_BOARD[len(state.board)]}|{players_label(live)}|{role}|{situation}|{faced}"
    size = size_bucket(bet["increment"], bet["pot"], bet["to_call"], jam)
    return key, size, bet


def our_bucket(state):
    parsed = [cards.parse_card(c) for c in state.cards]
    board = [cards.parse_card(c) for c in state.board]
    return cards.bucket(parsed[0], parsed[1], cards.BoardView(board))


def update_seat_folds(state, memory):
    """Count, per seat, how often they folded to our last postflop bet at this table."""
    pending = memory.pop("pb", None)
    if not pending:
        return
    counts = memory.setdefault("sf", {})
    for event in state.events:
        if event.kind in ("board", "hand"):
            break
        if event.seat is None or event.seat == state.seat:
            continue
        if event.kind in ("fold", "call", "raise"):
            entry = counts.setdefault(str(event.seat), [0, 0])
            entry[0] += 1
            entry[1] += event.kind == "fold"


def seat_fold_rate(memory, seat, pool_rate):
    faced, folds = memory.get("sf", {}).get(str(seat), [0, 0])
    return (folds + SEAT_PRIOR_WEIGHT * pool_rate) / (faced + SEAT_PRIOR_WEIGHT)


def bet_total(state, own, fraction, pot, to_call):
    highest = own.bet + to_call
    return highest + max(1, int(fraction * (pot + to_call)))


def remember_bet(state, memory, action):
    if action is not None and action.kind == "raise":
        memory["pb"] = [state.hand_number, len(state.board)]
    return action


def icm_extra_equity(state, own, to_call):
    if icm_tightness(state) >= 1.0:
        return 0.0
    needed, _bubble = icm_price(state, own, to_call)
    chip_needed = to_call / max(1, state.pot + to_call)
    return max(0.0, needed - chip_needed)


def icm_price(state, own, to_call):
    stacks = {s.seat: s.stack for s in state.seats if s.status != "busted"}
    bettors = [s for s in state.seats if s.seat != state.seat and s.bet > own.bet]
    villain = max(bettors, key=lambda s: s.bet).seat if bettors else None
    order = list(stacks)
    hero = order.index(state.seat)
    payouts = state.config.payouts
    risk = min(to_call, own.stack)
    win_amount = state.pot - own.bet

    def equity(delta_hero, delta_villain):
        values = [stacks[s] for s in order]
        values[hero] = max(0, values[hero] + delta_hero)
        if villain is not None:
            v = order.index(villain)
            values[v] = max(0, values[v] + delta_villain)
        return own_icm_equity(values, hero, payouts)

    now, win, lose = equity(0, 0), equity(win_amount, 0), equity(-risk, risk)
    if win - lose <= 1e-9:
        return 1.0, 9.9
    return (now - lose) / (win - lose), 1.0


def default_equity(street, ours):
    row = EQUITY_TABLES[street][ours]
    total = weight = 0.0
    for share, value in zip(DEFAULT_MIX, row):
        if value is not None:
            total += share * value
            weight += share
    return total / weight if weight else 0.0


def postflop(state, memory, factor):
    own = me(state)
    streets = replay(state)
    ours = our_bucket(state)
    street = STREET_BY_BOARD[len(state.board)]
    pot, to_call = state.pot, state.to_call
    heads_up = sum(1 for s in state.seats if s.status in ("active", "all_in")) == 2
    opponents = [s for s in state.seats if s.seat != state.seat and s.status in ("active", "all_in")]
    near_money = icm_tightness(state) < 1.0
    bluff_gate = rng.random() < scaled(factor, (0.7, 1.3))

    if to_call == 0:
        key = our_key(state, streets)
        if ours == cards.STRONG and state.can("raise"):
            return remember_bet(state, memory, bet_or_shove(state, own, bet_total(state, own, VALUE_SIZE_STRONG, pot, 0)))
        if ours == cards.TOP_PAIR and state.can("raise"):
            return remember_bet(state, memory, bet_or_shove(state, own, bet_total(state, own, VALUE_SIZE_TOP_PAIR, pot, 0)))
        if ours in (cards.AIR, cards.WEAK_DRAW, cards.STRONG_DRAW) and state.can("raise") and bluff_gate:
            best = None
            for size in SIZE_ORDER[:4]:
                entry = BLUFF_SPOTS.get((key, size))
                if not entry or entry["verdict"] != "bluff":
                    continue
                if entry["bluff_ev_low_pots"] < MIN_BLUFF_EV_LOW and ours != cards.STRONG_DRAW:
                    continue
                if heads_up and opponents:
                    rate = seat_fold_rate(memory, opponents[0].seat, entry["fold_through"])
                    if rate <= entry["breakeven_fold"]:
                        continue
                if best is None or entry["bluff_ev_low_pots"] > best["bluff_ev_low_pots"]:
                    best = entry
            if best is not None:
                total = bet_total(state, own, best["size_fraction"], pot, 0)
                if not (near_money and total - own.bet > MAX_BLUFF_STACK_SHARE_NEAR_MONEY * (own.stack + own.bet)):
                    return remember_bet(state, memory, clamp_raise(state, total))
        return call_or_check(state)

    if not any(a["kind"] == "raise" for a in streets[-1]):
        return call_or_check(state)
    key, size, bet = bettor_key(state, streets)
    extra = icm_extra_equity(state, own, to_call)

    if ours == cards.STRONG and state.can("raise"):
        return remember_bet(state, memory, bet_or_shove(state, own, bet_total(state, own, VALUE_SIZE_STRONG, pot, to_call)))

    entry = CALL_SPOTS.get((key, size))
    margin = FLOP_TURN_MARGIN if street != "R" else 0.0
    if entry:
        equity = entry["equity_by_our_bucket"][ours]
        required = entry["required_equity"] + margin + extra
        calls = cards.BUCKET_NAMES[ours] in entry["call_with"] and (equity or 0.0) >= required
    else:
        share = bet["increment"] / max(1, bet["pot"] + bet["to_call"])
        required = share / (1 + 2 * share) + margin + extra
        calls = default_equity(street, ours) >= required

    if ours in (cards.AIR, cards.WEAK_DRAW, cards.STRONG_DRAW) and heads_up and state.can("raise") and bluff_gate:
        raise_key = our_key(state, streets)
        for size_name in ("medium", "pot"):
            raise_entry = BLUFF_SPOTS.get((raise_key, size_name))
            if raise_entry and raise_entry["verdict"] == "bluff" and raise_entry["bluff_ev_low_pots"] >= MIN_BLUFF_EV_LOW:
                total = bet_total(state, own, raise_entry["size_fraction"], pot, to_call)
                if not (near_money and total - own.bet > MAX_BLUFF_STACK_SHARE_NEAR_MONEY * (own.stack + own.bet)):
                    return remember_bet(state, memory, clamp_raise(state, total))
    if calls:
        return call_or_check(state)
    return fold_or_check(state)


def infer_branch(state, own):
    if not own.shown_cards or len(state.cards) != 2:
        return 1
    shown = own.shown_cards[0]
    hidden = state.cards[0] if state.cards[1] == shown else state.cards[1]
    return 1 if RANK_VALUE[shown[0]] >= RANK_VALUE[hidden[0]] else 0


def bet_or_shove(state, own, total):
    legal = state.can("raise")
    if legal is None:
        return call_or_check(state)
    if total >= 0.6 * (own.stack + own.bet):
        total = legal.max_amount
    return clamp_raise(state, total)


# ---------------------------------------------------------------- preflop


def players_after(state):
    live = sorted(s.seat for s in state.seats if s.status != "busted")
    if state.button not in live or state.seat not in live:
        return 3
    count = len(live)
    position = (live.index(state.seat) - live.index(state.button)) % count
    if count == 2:
        return 1 if position == 0 else 0
    if position == 0:
        return 2
    if position == 1:
        return 1
    if position == 2:
        return 0
    return (count - 1 - position) + 3


def icm_tightness(state):
    paid = sum(1 for p in state.config.payouts if p > 0)
    gap = state.players_remaining - paid
    if gap <= 0:
        return 0.9
    if gap <= 2:
        return 0.75
    return 1.0


def own_icm_equity(stacks, hero, payouts):
    """Malmuth-Harville equity of one player only, which is far cheaper than every player's."""
    live = [i for i, s in enumerate(stacks) if s > 0]
    if stacks[hero] <= 0:
        return 0.0
    places = [p for p in payouts if p > 0][: len(live)]

    def place_from(depth, remaining, used):
        if depth >= len(places):
            return 0.0
        total = stacks[hero] / remaining * places[depth]
        if depth + 1 < len(places):
            for j in live:
                if j == hero or j in used:
                    continue
                share = stacks[j] / remaining
                total += share * place_from(depth + 1, remaining - stacks[j], used + (j,))
        return total

    return place_from(0, float(sum(stacks[i] for i in live)), ())


def icm_required_equity(state, own, villain_seats):
    """Equity needed to call an all-in so the call is ICM-neutral against folding."""
    if not villain_seats:
        return 0.5
    stacks = {s.seat: s.stack + s.bet for s in state.seats if s.status != "busted"}
    villain = max(villain_seats, key=lambda seat: stacks.get(seat, 0))
    mine = own.stack + own.bet
    risk = min(mine, stacks[villain])
    dead = state.pot - own.bet - next(s.bet for s in state.seats if s.seat == villain)
    order = list(stacks)
    payouts = state.config.payouts

    def equity_of(adjust):
        values = [max(0, stacks[seat] + adjust.get(seat, 0)) for seat in order]
        return own_icm_equity(values, order.index(state.seat), payouts)

    win = equity_of({state.seat: risk + dead, villain: -risk})
    lose = equity_of({state.seat: -risk, villain: risk + dead})
    fold = equity_of({state.seat: -own.bet, villain: own.bet + dead})
    if win - lose <= 1e-9:
        return 1.0
    return (fold - lose) / (win - lose)


def preflop(state, factor):
    own = me(state)
    width_scale = scaled(factor, PREFLOP_WIDTH_SCALE_RANGE)
    shove_scale = scaled(factor, SHOVE_WIDTH_SCALE_RANGE)
    stats = PREFLOP.get(hand_key(state.cards))
    if stats is None:
        return call_or_check(state)
    strength, versus_random, versus_top = stats
    big = max(1, state.blinds.big_blind)
    mine = own.stack + own.bet
    others = [s.stack + s.bet for s in state.seats if s.seat != state.seat and s.status in ("active", "all_in")]
    effective = min(mine, max(others) if others else mine) / big
    after = players_after(state)
    tight = icm_tightness(state)

    raisers = [e.seat for e in state.history if e.kind == "raise" and e.seat != state.seat]
    all_in_raisers = [s.seat for s in state.seats if s.status == "all_in" and s.seat in raisers]
    highest = max(s.bet for s in state.seats)
    to_call = state.to_call

    if not raisers:
        if to_call == 0:
            if strength >= 1 - 0.15 * tight * width_scale:
                return clamp_raise(state, highest + 3 * big) or Action.check()
            return Action.check()
        width = OPEN_WIDTH_BY_PLAYERS_AFTER.get(after, DEFAULT_OPEN_WIDTH) * tight * width_scale
        if effective <= 10:
            push = PUSH_WIDTH_BY_PLAYERS_AFTER.get(after, 0.14) * tight * shove_scale
            width = min(0.7, push * (10 / max(effective, 1)) ** 0.5)
            if strength >= 1 - width:
                legal = state.can("raise")
                return Action.raise_to(legal.max_amount) if legal else call_or_check(state)
            return fold_or_check(state)
        if strength >= 1 - width:
            limpers = sum(1 for e in state.history if e.kind == "call")
            return clamp_raise(state, int((2.5 + limpers) * big)) or call_or_check(state)
        return fold_or_check(state)

    call_cost = min(to_call, own.stack)
    commits = call_cost >= 0.4 * mine or bool(all_in_raisers) or highest >= 0.5 * mine
    if commits:
        villain_bb = max((s.stack + s.bet for s in state.seats if s.seat in raisers), default=mine) / big
        estimate = versus_top if villain_bb >= 15 else 0.5 * (versus_top + versus_random)
        if len(set(raisers)) >= 2:
            estimate *= 0.85
        needed = icm_required_equity(state, own, all_in_raisers or raisers)
        if estimate >= needed:
            legal = state.can("raise")
            if strength >= 0.97 and legal and not all_in_raisers:
                return Action.raise_to(legal.max_amount)
            return call_or_check(state)
        return fold_or_check(state)

    raise_count = len(raisers)
    in_big_blind = after == 0
    if raise_count == 1:
        if strength >= 1 - 0.04 * tight * width_scale:
            if effective <= 25:
                legal = state.can("raise")
                return Action.raise_to(legal.max_amount) if legal else call_or_check(state)
            return clamp_raise(state, 3 * highest) or call_or_check(state)
        threshold = 0.72 if highest <= 3 * big else 0.80
        if in_big_blind:
            threshold -= 0.10
        threshold = 1 - (1 - threshold) * tight
        if strength >= threshold:
            if rng.random() < EXPLORE_LIGHT_THREE_BET and effective > 25:
                return clamp_raise(state, 3 * highest) or call_or_check(state)
            return call_or_check(state)
        return fold_or_check(state)
    if strength >= 1 - 0.015 * tight * width_scale:
        legal = state.can("raise")
        return Action.raise_to(legal.max_amount) if legal else call_or_check(state)
    if strength >= 1 - 0.05 * tight and call_cost <= 0.2 * mine:
        return call_or_check(state)
    return fold_or_check(state)


# ---------------------------------------------------------------- agent


class Agent(poker_agent_sdk.Agent):
    def act(self, state: GameState, memory: bytes) -> tuple[Action, bytes]:
        decision_started_ns[0] = time.perf_counter_ns()
        data = load_memory(memory)
        try:
            factor = table_aggression(state, data)
        except Exception:
            factor = 0.5
        try:
            update_seat_folds(state, data)
        except Exception:
            data.pop("pb", None)
        try:
            if state.phase == "select":
                action = choose_selection(state, data)
            elif state.phase != "betting":
                first = state.legal_actions[0]
                action = Action(first.kind, first.min_amount)
            elif len(state.board) == 0:
                action = preflop(state, factor)
            else:
                action = postflop(state, data, factor)
        except Exception:
            action = passive(state)
        return action, json.dumps(data, separators=(",", ":")).encode()
