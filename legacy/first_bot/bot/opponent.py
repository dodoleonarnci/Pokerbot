"""M7: pool tables with back-off, plus a small per-seat layer. Rules are in spec S10.

Written from S10 because the spec's opponent_model.py was not available.
"""
import json
import os
import pathlib

from .params import PARAMS
from .spots import depth_bucket, players_bucket, spot_chain

DATA = pathlib.Path(os.environ.get("FIRST_BOT_DATA", pathlib.Path(__file__).resolve().parent.parent / "data"))


class PoolTables:
    """Tables A, B, C. Each cell already holds its shrunken estimate from M8."""

    def __init__(self):
        self.a, self.b, self.c, self.biased = {}, {}, {}, True
        try:
            with open(DATA / "pool_tables.json") as f:
                raw = json.load(f)
            self.a, self.b, self.c = raw["a"], raw["b"], raw["c"]
            self.biased = raw.get("showdown_only", True)
        except (OSError, ValueError, KeyError):
            pass

    def lookup(self, table, street, line, size, pos, players, depth, pfa):
        for key in spot_chain(street, line, size, pos, players, depth, pfa):
            cell = table.get(key)
            if cell is not None:
                return cell
        return None

    def preflop_pct(self, kind, position, stack, bb, players_left):
        """Observed range width for a preflop action, in percent of hands, or None."""
        depth = depth_bucket(stack, bb)
        crowd = "8-6" if players_left >= 6 else "5-3" if players_left >= 3 else "2"
        for key in (f"{kind}|{position}|{depth}|{crowd}", f"{kind}|{position}", kind):
            cell = self.c.get(key)
            if cell is not None:
                return 100 * cell[1]
        return None


POOL = PoolTables()


class SeatStats:
    __slots__ = ("hands", "faced_bet", "folded_bet", "vpip", "pfr", "last_hand",
                 "postflop_decisions", "postflop_raises")

    def __init__(self):
        self.postflop_decisions = 0.0
        self.postflop_raises = 0.0
        self.hands = 0.0
        self.faced_bet = 0.0
        self.folded_bet = 0.0
        self.vpip = 0.0
        self.pfr = 0.0
        self.last_hand = -1


class OpponentModel:
    """Per-seat stats for one table. Memory resets every table."""

    def __init__(self):
        self.seats = {}
        self.exploit_loss = 0
        self.K = PARAMS["K"]
        self.decay = PARAMS["DECAY"]

    def _seat(self, seat_id):
        stats = self.seats.get(seat_id)
        if stats is None:
            stats = self.seats[seat_id] = SeatStats()
        return stats

    def observe(self, seat_id, hand_number, street, kind, facing_bet):
        stats = self._seat(seat_id)
        if stats.last_hand != hand_number:
            stats.last_hand = hand_number
            stats.hands += 1
            stats.vpip *= self.decay
            stats.pfr *= self.decay
        if street == "preflop":
            if kind in ("call", "raise"):
                stats.vpip += 1
            if kind == "raise":
                stats.pfr += 1
        else:
            stats.postflop_decisions = stats.postflop_decisions * self.decay + 1
            stats.postflop_raises = stats.postflop_raises * self.decay + (kind == "raise")
        if facing_bet:
            stats.faced_bet = stats.faced_bet * self.decay + 1
            stats.folded_bet = stats.folded_bet * self.decay + (kind == "fold")

    def fade(self):
        """Fades exploits out as losses approach the budget."""
        return max(0.0, 1.0 - self.exploit_loss / PARAMS["LOSS_BUDGET"])

    def fold_rate(self, seat_id, prior):
        """Blend a seat's fold-to-bet rate into the prior, within MAX_SHIFT."""
        stats = self.seats.get(seat_id)
        if stats is None or stats.hands < PARAMS["SEAT_MIN_HANDS"]:
            return prior
        estimate = (stats.folded_bet + self.K * prior) / (stats.faced_bet + self.K)
        shift = max(-PARAMS["MAX_SHIFT"], min(PARAMS["MAX_SHIFT"], estimate - prior))
        return prior + shift * self.fade()

    def bet_share(self, seat_id):
        """How often a seat bets or raises after the flop, or None before enough hands."""
        stats = self.seats.get(seat_id)
        if stats is None or stats.hands < PARAMS["SEAT_MIN_HANDS"] or stats.postflop_decisions < 8:
            return None
        return stats.postflop_raises / stats.postflop_decisions

    def range_pct(self, seat_id, base, kind):
        """Widen or tighten an assumed preflop range toward the seat's observed VPIP or PFR."""
        stats = self.seats.get(seat_id)
        if stats is None or stats.hands < PARAMS["SEAT_MIN_HANDS"]:
            return base
        observed = 100 * (stats.pfr if kind == "raise" else stats.vpip) / max(1.0, stats.hands)
        limit = 100 * PARAMS["MAX_SHIFT"]
        shift = max(-limit, min(limit, observed - base))
        return max(1.0, min(100.0, base + shift * self.fade()))

    def loose_callers(self, seat_ids):
        """True if anyone behind us has clearly rarely folded to bets."""
        for seat_id in seat_ids:
            stats = self.seats.get(seat_id)
            if (stats is not None and stats.hands >= PARAMS["SEAT_MIN_HANDS"]
                    and stats.faced_bet > 3 and stats.folded_bet / stats.faced_bet < 0.3):
                return True
        return False

    def tight_callers(self, seat_ids):
        """True if every seen player behind us folds to bets well above the norm."""
        known = [self.seats[s] for s in seat_ids if s in self.seats
                 and self.seats[s].hands >= PARAMS["SEAT_MIN_HANDS"]]
        if not known or len(known) < len(seat_ids):
            return False
        return all(s.faced_bet > 3 and s.folded_bet / s.faced_bet > 0.7 for s in known)
