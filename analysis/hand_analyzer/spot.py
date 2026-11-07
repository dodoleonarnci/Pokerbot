"""Spot tracker shared by the analyzer and the bot, so both label every state identically.

Feed it raw actions one at a time. It works out the pot, the amount to call, who acts and when a
street closes by itself, and it never looks ahead. Standard library only.
"""

from dataclasses import dataclass

STREET_NAMES = ("preflop", "flop", "turn", "river")
_MIDDLE = {8: ("UTG", "UTG+1", "LJ", "HJ", "CO"), 7: ("UTG", "LJ", "HJ", "CO"), 6: ("LJ", "HJ", "CO"),
           5: ("HJ", "CO"), 4: ("CO",), 3: ()}


class MalformedHand(ValueError):
    pass


def positions(n: int) -> tuple:
    """Position names in table order, starting from the first blind."""
    if n == 2:
        return ("BTN", "BB")
    if n > 8:
        return ("SB", "BB", *(f"EP{i}" for i in range(n - 8)), *_MIDDLE[8], "BTN")
    return ("SB", "BB", *_MIDDLE[n], "BTN")


def post_size_code(bet: int, pot: int) -> str:
    """S up to 0.4 pot, M to 0.8, L to 1.2, O above: the bet's fraction of the pot before it."""
    tenths = bet * 10
    if tenths <= pot * 4:
        return "S"
    if tenths <= pot * 8:
        return "M"
    if tenths <= pot * 12:
        return "L"
    return "O"


def depth_bucket(chips: int, bb: int) -> str:
    if chips < 10 * bb:
        return "d<10"
    if chips < 20 * bb:
        return "d10-20"
    if chips < 40 * bb:
        return "d20-40"
    if chips < 80 * bb:
        return "d40-80"
    return "d80+"


@dataclass(frozen=True, slots=True)
class Spot:
    path: str
    key: str
    pot: int
    to_call: int
    players_left: int
    live: tuple
    actor: int | None
    actor_pos: str | None
    street: int


class SpotTracker:
    __slots__ = ("bb", "seats", "index", "pos", "n", "stack", "put", "sp", "live", "entered", "pot",
                 "street", "cur", "n_live", "n_active", "pending", "actor", "path", "raises",
                 "street_bets", "last_code", "first_bet", "street_raised", "called", "pfr", "aggr",
                 "street_aggr", "acted_street", "so_far", "pot_type", "prev_line", "done", "_top")

    def __init__(self, seats, button, sb, bb, ante=0):
        """`seats` is a list of (seat number, stack) for the seats in play."""
        ordered = sorted(seats)
        numbers = [s for s, _ in ordered]
        at = next((i for i, s in enumerate(numbers) if s >= button), 0)
        if numbers[at] != button:
            at -= 1  # A dead button: the last seat in play before it acts as the button.
        n = len(numbers)
        start = at if n == 2 else at + 1
        rotated = [ordered[(start + i) % n] for i in range(n)]
        self.bb = bb
        self.n = n
        self.seats = tuple(s for s, _ in rotated)
        self.index = {s: i for i, s in enumerate(self.seats)}
        self.pos = positions(n)
        self.stack = [c for _, c in rotated]
        self.put = [0] * n
        self.sp = [0] * n
        self.live = [True] * n
        self.entered = [False] * n
        self.pot = 0
        self._top = None
        if ante:
            for i in range(n):
                self._pay(i, ante)
            self.sp = [0] * n
        self._pay(0, sb)
        self._pay(1, bb)
        self.cur = max(self.sp[0], self.sp[1])  # A short big blind sets a lower level.
        self.street = 0
        self.n_live = n
        self.n_active = sum(c > 0 for c in self.stack)
        self.path = ""
        self.raises = 0
        self.street_bets = 0
        self.last_code = "blind"
        self.first_bet = ""
        self.street_raised = False
        self.called = False
        self.pfr = None
        self.aggr = None
        self.street_aggr = None
        self.acted_street = [False] * n
        self.so_far = ""
        self.pot_type = "LP"
        self.prev_line = "pre"
        self.done = False
        self.pending = self.n_active
        self.actor = None
        self._set_first(2 % n if n > 2 else 0)

    def _pay(self, i, chips):
        chips = min(chips, self.stack[i])
        self._top = None
        self.stack[i] -= chips
        self.put[i] += chips
        self.sp[i] += chips
        self.pot += chips
        return chips

    def _set_first(self, start):
        n, live, stack = self.n, self.live, self.stack
        if self.n_active < 1 or self.pending <= 0:
            self.actor = None
            return
        for step in range(n):
            i = (start + step) % n
            if live[i] and stack[i] > 0:
                self.actor = i
                return
        self.actor = None

    # What a decision sees.

    @property
    def to_call(self) -> int:
        i = self.actor
        if i is None:
            return 0
        return min(self.cur - self.sp[i], self.stack[i])

    @property
    def actor_seat(self):
        return None if self.actor is None else self.seats[self.actor]

    @property
    def actor_pos(self):
        return None if self.actor is None else self.pos[self.actor]

    def line(self) -> str:
        i, street = self.actor, self.street
        if street == 0:
            if self.raises == 0:
                return "vs_limp" if self.called else "unopened"
            return ("vs_open", "vs_3bet")[self.raises - 1] if self.raises < 3 else "vs_4bet+"
        if self.street_bets == 1:
            return "vs_bet"
        if self.street_bets > 1:
            return "vs_raise"
        aggr = self.aggr
        if aggr == i:
            return "cbet" if street == 1 else "barrel"
        if aggr is None or not self.live[aggr] or self.acted_street[aggr] or self.stack[aggr] == 0:
            return "stab"
        return "donk"

    def _largest_other(self, i) -> int:
        """The largest stack among the other live players; cached, since most folds change nothing."""
        top = self._top
        if top is None:
            first = second = 0
            holder = -1
            stack, live = self.stack, self.live
            for j in range(self.n):
                if live[j]:
                    chips = stack[j]
                    if chips > first:
                        first, second, holder = chips, first, j
                    elif chips > second:
                        second = chips
            top = self._top = (holder, first, second)
        return top[2] if top[0] == i else top[1]

    def spot_key(self, line) -> str:
        """Pooled spot: street, line, position, players left, depth bucket, line so far."""
        i = self.actor
        mine, others = self.stack[i], self._largest_other(i)
        depth = depth_bucket(mine if mine < others else others, self.bb)
        so_far = self.pot_type + self.so_far if self.street else "PF"
        return f"{STREET_NAMES[self.street]};{line};{self.pos[i]};{self.n_live};{depth};{so_far}"

    @property
    def key(self) -> str:
        return self.spot_key(self.line())

    def state(self) -> Spot:
        actor = self.actor
        return Spot(self.path, self.key if actor is not None else "", self.pot, self.to_call, self.n_live,
                    tuple(s for i, s in enumerate(self.seats) if self.live[i]), self.actor_seat,
                    self.actor_pos, self.street)

    def live_seats(self):
        return [s for i, s in enumerate(self.seats) if self.live[i]]

    # Moving the hand forward.

    def needs_implied_fold(self, seat, street) -> bool:
        """True when the next recorded action shows that the current actor folded unrecorded."""
        return (self.street == 0 and self.actor is not None
                and (street > 0 or self.seats[self.actor] != seat))

    def can_imply_fold(self) -> bool:
        return self.street == 0 and self.actor is not None and not self.entered[self.actor]

    def apply_implied_fold(self):
        if not self.can_imply_fold():
            raise MalformedHand("an entered player cannot fold unrecorded")
        return self._fold(self.actor, token=False)

    def apply(self, seat, kind, to=0, street=None):
        """Apply one action. Returns its code, or None for a fold that gets no path token."""
        i = self.actor
        if i is None or self.seats[i] != seat:
            raise MalformedHand(f"seat {seat} acted out of turn")
        if street is not None and street != self.street:
            raise MalformedHand(f"action on street {street}, hand is on {self.street}")
        if kind == "fold":
            return self._fold(i, token=self.street > 0 or self.entered[i])
        if kind == "check":
            if self.cur > self.sp[i]:
                raise MalformedHand("check facing a bet")
            code = "x"
        elif kind == "call":
            owed = self.cur - self.sp[i]
            if owed <= 0:
                raise MalformedHand("call with nothing to call")
            self._pay(i, owed)
            self.called = True
            self.entered[i] = self.street == 0 or self.entered[i]
            code = "c"
        elif kind in ("raise", "bet"):
            code = self._raise(i, to)
        else:
            raise MalformedHand(f"unknown action {kind!r}")
        if self.stack[i] == 0:
            self.n_active -= 1
        self._token(i, code)
        self.acted_street[i] = True
        if code[0] not in "br":
            self.pending -= 1
        self._after(i)
        return code

    def _raise(self, i, to):
        sp = self.sp[i]
        cur = self.cur
        if to <= cur or to - sp > self.stack[i]:
            raise MalformedHand(f"raise to {to} over {cur}")
        owed = cur - sp
        if self.street == 0:
            if self.raises == 0:
                bbs = int(to / self.bb + 0.5)
                code = "rX" if bbs > 4 else f"r{max(2, bbs)}"
                self.pot_type = "SRP"
            else:
                multiple = max(2, min(5, int(to / cur + 0.5)))
                code = f"rx{multiple}"
                self.pot_type = "3BP" if self.raises == 1 else "4BP"
            self.raises += 1
            self.pfr = i
            self.aggr = i
            self.entered[i] = True
        else:
            size = post_size_code(to - cur, self.pot + owed)
            code = ("r" if cur else "b") + size
            if self.street_bets == 0:
                self.first_bet = code
            else:
                self.street_raised = True
            self.street_aggr = i
        self.street_bets += 1
        self.last_code = code
        self.called = self.called if self.street == 0 else False
        self._pay(i, to - sp)
        self.cur = to
        self.pending = self.n_active - 1  # The raiser still counts as active here.
        return code

    def _token(self, i, code):
        token = f"{self.pos[i]}:{code}"
        path = self.path
        self.path = f"{path} {token}" if path else token

    def _fold(self, i, token):
        code = "f" if token else None
        self.live[i] = False
        self._top = None
        self.n_live -= 1
        if self.stack[i] > 0:
            self.n_active -= 1
        if token:
            self._token(i, "f")
        self.acted_street[i] = True
        self.pending -= 1
        self._after(i)
        return code

    def _after(self, i):
        if self.n_live <= 1:
            self.actor = None
            self.done = True
            return
        if self.pending > 0:
            n, live, stack = self.n, self.live, self.stack
            for step in range(1, n):
                j = (i + step) % n
                if live[j] and stack[j] > 0:
                    self.actor = j
                    return
            self.actor = None
            self.done = True
            return
        self._next_street()

    def _next_street(self):
        street = self.street
        if street:
            summary = "x" if not self.street_bets else ("r" if self.street_raised else "b")
            self.so_far += "-" + summary
            if not self.street_bets:
                self.prev_line = "x"
            else:
                self.prev_line = self.first_bet + ("-r" if self.street_raised else "-c")
            self.aggr = self.street_aggr
        elif self.raises == 0:
            self.pot_type = "LP"
        if street >= 3:
            self.actor = None
            self.done = True
            return
        self.street = street + 1
        self.path += " /"
        self.sp = [0] * self.n
        self.cur = 0
        self.street_bets = 0
        self.street_aggr = None
        self.first_bet = ""
        self.street_raised = False
        self.called = False
        self.last_code = ""
        self.acted_street = [False] * self.n
        if self.n_active < 2:
            self.actor = None  # Everyone is all in: the board runs out with no more decisions.
            self.done = True
            return
        self.pending = self.n_active
        self._set_first(1 if self.n == 2 else 0)
