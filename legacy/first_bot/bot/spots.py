"""Spot keys (S10) and action tracking. Shared by the live bot and the M8 parser."""

STREET_ORDER = {"preflop": 0, "flop": 1, "turn": 2, "river": 3}


def position_label(seat, button, players):
    distance = (seat - button) % players
    if players == 2:
        return "HU_BTN" if distance == 0 else "HU_BB"
    if distance == 0:
        return "BTN"
    if distance == 1:
        return "SB"
    if distance == 2:
        return "BB"
    # Count back from the button; the earliest seat is always UTG.
    from_end = players - distance
    return {1: "CO", 2: "HJ", 3: "LJ", 4: "MP"}.get(from_end, "UTG")


def size_bucket(bet, pot, all_in=False):
    if all_in:
        return "allin"
    ratio = bet / pot if pot > 0 else 9.0
    if ratio <= 0.4:
        return "s"
    if ratio <= 0.8:
        return "m"
    if ratio <= 1.2:
        return "l"
    return "x"


def depth_bucket(stack, bb):
    depth = stack / bb
    if depth <= 15:
        return "short"
    return "mid" if depth <= 40 else "deep"


def players_bucket(count):
    return "2" if count <= 2 else "3+"


def spot_chain(street, line, size, pos, players, depth, pfa):
    """Most to least specific keys, in the spec's back-off order."""
    return (
        f"{street}|{line}|{size}|{pos}|{players}|{depth}|{pfa}",
        f"{street}|{line}|{size}|{pos}|{players}||{pfa}",
        f"{street}|{line}|{size}||{players}||{pfa}",
        f"{street}|{line}|{size}",
        street,
        "global",
    )


class ActionTracker:
    """Follows one hand's action. Replays the same way live and offline."""

    def __init__(self, players, button, big_blind):
        self.players = players
        self.button = button
        self.big_blind = big_blind
        self.live = set(range(players))
        self.street = "preflop"
        self.raises = 0
        self.preflop_aggressor = None
        self.street_aggressor = None
        self.previous_aggressor = None
        self.checked = set()
        self.acted_on_street = set()
        self.current_bet = big_blind
        self.last_bet = None  # (line, size bucket, bettor) of the bet now pending
        self.in_pot = 0  # voluntary preflop players

    def enter_street(self, street):
        self.previous_aggressor = self.street_aggressor
        self.street = street
        self.street_aggressor = None
        self.checked = set()
        self.acted_on_street = set()
        self.current_bet = 0
        self.last_bet = None

    def order_key(self, seat):
        return (seat - self.button - 1) % self.players

    def in_position(self, seat):
        return max(self.live, key=self.order_key) == seat

    def position_word(self, seat):
        return "ip" if self.in_position(seat) else "oop"

    def may_bet_unopened(self, seat):
        """No donks: never lead into last street's aggressor while they have not checked."""
        aggressor = self.previous_aggressor
        if aggressor is None or aggressor == seat or aggressor not in self.live:
            return True
        return aggressor in self.checked

    def bet_line(self, seat, all_in):
        if self.street == "preflop":
            if all_in:
                return "jam"
            return "open" if self.raises == 0 else "3bet"
        if self.current_bet > 0:
            return "check-raise"
        if seat == self.previous_aggressor:
            return "c-bet"
        if not self.may_bet_unopened(seat):
            return "donk"
        if seat == self.preflop_aggressor:
            return "delayed"
        return "probe"

    def pfa_word(self, seat):
        return "pfa" if seat == self.preflop_aggressor else "non"

    def apply(self, event):
        """Update for one event. Returns (bet, pot before the bet) for a bet or raise."""
        seat, kind = event["seat"], event["action"]
        self.acted_on_street.add(seat)
        if kind == "fold":
            self.live.discard(seat)
            return None
        if kind == "check":
            self.checked.add(seat)
            return None
        if kind == "call":
            if self.street == "preflop":
                self.in_pot += 1
            return None
        bet = event["to"] - self.current_bet
        pot = event["pot"] + event["amount"] - bet
        all_in = event["amount"] >= event["stacks"][seat]
        line = self.bet_line(seat, all_in)
        self.last_bet = (line, size_bucket(bet, pot, all_in), seat)
        if self.street == "preflop":
            self.raises += 1
            self.in_pot += 1
            self.preflop_aggressor = seat
        self.street_aggressor = seat
        self.current_bet = event["to"]
        return bet, pot
