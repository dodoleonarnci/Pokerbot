"""Replay participant hand histories into abstract game-tree decisions for the Bay Area variant."""
import gzip
import json
from dataclasses import dataclass, field

from .cards import BoardView, bucket, evaluate, parse_card

STREET_NAMES = ("preflop", "flop", "turn", "river")
STREET_LETTERS = "PFTR"
BETTING_KINDS = {"fold", "check", "call", "raise"}


def read_tables(path):
    """Yield (table, own) pairs from a participant download (.jsonl or .jsonl.gz)."""
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt") as stream:
        header = json.loads(next(stream))
        for line in stream:
            table = json.loads(line)
            own = json.loads(next(stream))["you"]
            yield header, table, own


def size_bucket(increment, pot_before, all_in):
    if all_in:
        return "jam"
    fraction = increment / max(pot_before, 1)
    if fraction <= 0.4:
        return "small"
    if fraction <= 0.8:
        return "medium"
    if fraction <= 1.25:
        return "pot"
    return "overbet"


def preflop_size_bucket(increment, big_blind, all_in):
    if all_in:
        return "jam"
    multiple = increment / max(big_blind, 1)
    return "≤3bb" if multiple <= 3 else "≤6bb" if multiple <= 6 else ">6bb"


@dataclass
class Decision:
    street: int
    seat: int
    population: bool
    players: int
    pot: int
    to_call: int
    faced: int
    node: str
    path: tuple | None
    action: str
    size: str = ""
    fraction: float = 0.0
    position: str = ""


@dataclass
class Bet:
    street: int
    seat: int
    population: bool
    node: str
    path: tuple | None
    size: str
    pot: int
    increment: int
    responders: set
    hero_responds: bool
    faced_by: frozenset = frozenset()
    outcome: str = "open"
    callers: set = field(default_factory=set)


@dataclass
class HandReplay:
    decisions: list
    bets: list
    exposed: dict
    shown: dict
    board: list
    hero_cards: list
    hero_seat: int
    flop_players: list
    preflop_aggressor: int | None


def replay_hand(hand, hero_seat, fillers, hero_cards):
    n = len(hand["stacks_before"])
    stacks = list(hand["stacks_before"])
    in_hand = {s for s in range(n) if stacks[s] > 0}
    big_blind = hand["blinds"][1]
    street, pot = 0, 0
    bets = [0] * n
    level, last_increment, last_size = 0, 0, ""
    acted_this_street = False
    aggressor = {0: None}
    preflop_aggressor = None
    board, exposed, shown = [], {}, {}
    decisions, all_bets, open_bets = [], [], []
    flop_players, path_tokens, oop_seat = [], [], None

    def population(seat):
        return seat != hero_seat and not fillers[seat]

    def role_of(seat):
        if street == 1:
            if preflop_aggressor is None:
                return "limped"
            return "PFA" if seat == preflop_aggressor else "caller"
        previous = aggressor.get(street - 1)
        if previous is None:
            return "checked"
        return "agg" if seat == previous else "def"

    def node_key(seat):
        players = "HU" if len(in_hand) == 2 else "MW"
        if street == 0:
            if level <= 1:
                situation, size = "unopened", ""
            else:
                situation, size = ("vs-open" if level == 2 else "vs-3bet+"), last_size
            return f"P|{players}|{situation}|{size}"
        if level == 0:
            situation, size = ("checked-to" if acted_this_street else "first"), ""
        else:
            situation, size = ("vs-bet" if level == 1 else "vs-raise"), last_size
        return f"{STREET_LETTERS[street]}|{players}|{role_of(seat)}|{situation}|{size}"

    def hu_path():
        if street == 0 or len(flop_players) != 2:
            return None
        return tuple(path_tokens)

    for event in hand["events"]:
        kind, seat = event["kind"], event.get("seat")
        amount = event.get("amount", 0) or 0
        if kind == "ante":
            stacks[seat] -= amount
            pot += amount
        elif kind == "blind":
            stacks[seat] -= amount
            bets[seat] += amount
            pot += amount
            level = 1
            last_increment = max(last_increment, amount)
        elif kind == "board":
            board.extend(parse_card(c) for c in event["cards"])
            street = {3: 1, 4: 2, 5: 3}[len(board)]
            bets = [0] * n
            level, last_increment, last_size = 0, 0, ""
            acted_this_street = False
            aggressor[street] = None
            if street == 1:
                flop_players = sorted(in_hand)
        elif kind == "reveal":
            exposed[seat] = parse_card(event["cards"][0])
        elif kind == "show":
            shown[seat] = [parse_card(c) for c in event["cards"]]
        elif kind in BETTING_KINDS:
            to_call = max(bets) - bets[seat]
            if street == 1 and not acted_this_street and len(flop_players) == 2:
                oop_seat = seat
            position = "o" if seat == oop_seat else "i"
            node = node_key(seat)
            path = hu_path()
            decision = Decision(street, seat, population(seat), len(in_hand), pot, to_call,
                                last_increment, node, path, kind, position=position if path is not None else "")
            if kind == "fold":
                in_hand.discard(seat)
                token = "F"
            elif kind == "check":
                token = "X"
            elif kind == "call":
                stacks[seat] -= amount
                bets[seat] += amount
                pot += amount
                token = "C"
            else:
                increment = amount - max(bets)
                added = amount - bets[seat]
                pot_before = pot
                stacks[seat] -= added
                bets[seat] = amount
                pot += added
                all_in = stacks[seat] <= 0
                size = (preflop_size_bucket(increment, big_blind, all_in) if street == 0
                        else size_bucket(increment, pot_before + to_call, all_in))
                decision.size = size
                decision.fraction = increment / max(pot_before + to_call, 1)
                level += 1
                last_increment, last_size = increment, size
                aggressor[street] = seat
                if street == 0:
                    preflop_aggressor = seat
                else:
                    responders = {s for s in in_hand if s != seat and stacks[s] > 0}
                    all_bets.append(Bet(street, seat, population(seat), node, path, size,
                                        pot_before + to_call, increment, set(responders),
                                        hero_seat in responders, frozenset(responders)))
                token = ("B" if decision.node.split("|")[3] in ("first", "checked-to") else "R") + size
            for bet in open_bets:
                if bet.outcome == "open" and seat in bet.responders:
                    if kind in ("call", "raise"):
                        bet.outcome = "called" if kind == "call" else "raised"
                        bet.callers.add(seat)
                    elif kind == "fold":
                        bet.responders.discard(seat)
                        if not bet.responders:
                            bet.outcome = "folded"
            if kind == "raise" and street > 0:
                open_bets = [b for b in open_bets if b.outcome == "open"] + [all_bets[-1]]
            elif kind == "call":
                for bet in all_bets:
                    if bet.street == street and seat in bet.responders and bet.outcome != "folded":
                        bet.callers.add(seat)
            decisions.append(decision)
            if street > 0 and path is not None:
                path_tokens.append(f"{STREET_LETTERS[street]}{position}{token}")
            acted_this_street = True
    for bet in all_bets:
        if bet.outcome == "open":
            bet.outcome = "folded" if not (bet.responders & in_hand) else "called"
    return HandReplay(decisions, all_bets, exposed, shown, board, hero_cards, hero_seat,
                      flop_players, preflop_aggressor)


def replay_file(path, limit_hands=None):
    count = 0
    for header, table, own in read_tables(path):
        fillers = table["fillers"]
        for index, hand in enumerate(table["hands"]):
            hero_cards = [parse_card(c) for c in own["cards"][index]] if own["cards"][index] else []
            yield replay_hand(hand, own["seat"], fillers, hero_cards)
            count += 1
            if limit_hands and count >= limit_hands:
                return


def hand_bucket(cards, board):
    return bucket(cards[0], cards[1], BoardView(board))


def hand_value(cards, board):
    return evaluate(list(cards) + list(board))
