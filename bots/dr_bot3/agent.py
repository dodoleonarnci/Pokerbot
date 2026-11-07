"""Flop discard-and-reveal bot: three-card preflop ranges with ICM, equity-based discard,
mixed reveal, and branch-dependent postflop aggression."""

import hashlib
import json
import os
import random

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

OPEN_WIDTH_BY_PLAYERS_AFTER = {0: 0.15, 1: 0.40, 2: 0.35, 3: 0.25, 4: 0.20, 5: 0.17}
PUSH_WIDTH_BY_PLAYERS_AFTER = {0: 0.15, 1: 0.45, 2: 0.33, 3: 0.27, 4: 0.22, 5: 0.18}

POSTFLOP_SCALE_RANGE = (0.4, 1.6)
PREFLOP_WIDTH_SCALE_RANGE = (0.7, 1.3)
SHOVE_WIDTH_SCALE_RANGE = (0.85, 1.15)
MAX_BET_PROBABILITY = 0.97

rng = random.Random()

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


def postflop(state, memory, factor):
    hole = list(state.cards)
    board = list(state.board)
    own = me(state)
    category, draw = classify(hole, board)
    branch = memory.get("b", 1) if memory.get("h") == state.hand_number else infer_branch(state, own)
    table = STRONG_BRANCH_AGGRESSION if branch else WEAK_BRANCH_AGGRESSION
    base = table[category] + (DRAW_BONUS if draw else 0.0)
    aggression = min(MAX_BET_PROBABILITY, base * scaled(factor, POSTFLOP_SCALE_RANGE))

    opponents = sum(1 for s in state.seats if s.seat != state.seat and s.status in ("active", "all_in"))
    if category == HIGH and opponents >= 2:
        aggression *= 0.5

    pot = state.pot
    to_call = state.to_call
    stack = own.stack
    highest = own.bet + to_call
    roll = rng.random()

    if to_call == 0:
        if roll < aggression and state.can("raise"):
            fraction = 0.66 if category >= TOP else 0.5
            return bet_or_shove(state, own, highest + max(1, int(fraction * pot)))
        return call_or_check(state)

    odds = to_call / (pot + to_call)
    committed = stack - to_call < 0.25 * (pot + to_call)

    if category == MONSTER:
        if roll < aggression and state.can("raise"):
            return bet_or_shove(state, own, highest + int(0.8 * (pot + to_call)))
        return call_or_check(state)
    if category == TOP:
        if roll < aggression * 0.4 and state.can("raise"):
            return bet_or_shove(state, own, highest + int(0.8 * (pot + to_call)))
        if odds <= 0.4 or committed:
            return call_or_check(state)
        return fold_or_check(state)
    if category == PAIR:
        if len(board) == 3 and roll < aggression * 0.2 and state.can("raise"):
            return bet_or_shove(state, own, highest + int(0.75 * (pot + to_call)))
        if odds <= 0.3 or (committed and odds <= 0.4):
            return call_or_check(state)
        return fold_or_check(state)
    if draw:
        if roll < aggression * 0.3 and state.can("raise"):
            return bet_or_shove(state, own, highest + int(0.75 * (pot + to_call)))
        if odds <= 0.28:
            return call_or_check(state)
        return fold_or_check(state)
    if opponents == 1 and roll < aggression * 0.1 and state.can("raise"):
        return bet_or_shove(state, own, highest + int(0.75 * (pot + to_call)))
    if odds <= 0.15:
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
        width = OPEN_WIDTH_BY_PLAYERS_AFTER.get(after, 0.14) * tight * width_scale
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
        threshold = 0.80 if highest <= 3 * big else 0.86
        if in_big_blind:
            threshold -= 0.08
        threshold = 1 - (1 - threshold) * tight
        if strength >= threshold:
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
        data = load_memory(memory)
        try:
            factor = table_aggression(state, data)
        except Exception:
            factor = 0.5
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
