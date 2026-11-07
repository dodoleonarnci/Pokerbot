"""M6: ICM values, jam/fold chart lookups and the all-in risk penalty."""
import pathlib
import os

from .evaluator import N_CLASSES
from .params import MAX_HANDS, PARAMS, PAYOUTS, TABLE_SIZE

DATA = pathlib.Path(os.environ.get("FIRST_BOT_DATA", pathlib.Path(__file__).resolve().parent.parent / "data"))


def icm_values(stacks, payouts):
    """Malmuth-Harville expected payout per player, by subset dynamic programming."""
    n = len(stacks)
    total = sum(stacks)
    if total <= 0:
        return [sum(payouts) / n] * n
    probability = {0: 1.0}
    values = [0.0] * n
    # Masks of players already finished above the current place.
    for mask in range(1 << n):
        p = probability.get(mask)
        if not p:
            continue
        place = bin(mask).count("1")
        if place >= len(payouts):
            continue
        remaining = total - sum(stacks[i] for i in range(n) if mask >> i & 1)
        if remaining <= 0:
            continue
        for i in range(n):
            if mask >> i & 1 or stacks[i] <= 0:
                continue
            chance = p * stacks[i] / remaining
            values[i] += chance * payouts[place]
            next_mask = mask | 1 << i
            probability[next_mask] = probability.get(next_mask, 0.0) + chance
    return values


def chart_key(players, behind, depth):
    return players, behind, depth


class Charts:
    """Packed bits per (players left, players behind, stack in big blinds)."""

    def __init__(self):
        self.jam = {}
        self.call = {}
        try:
            raw = (DATA / "icm_charts.bin").read_bytes()
        except OSError:
            return
        size = N_CLASSES // 8 + 1
        position = 0
        for players in range(2, TABLE_SIZE + 1):
            for behind in range(1, players):
                for depth in range(1, PARAMS["JAM_BB"] + 1):
                    key = (players, behind, depth)
                    self.jam[key] = raw[position:position + size]
                    self.call[key] = raw[position + size:position + 2 * size]
                    position += 2 * size

    @staticmethod
    def _lookup(table, players, behind, depth, index):
        players = max(2, min(TABLE_SIZE, players))
        behind = max(1, min(players - 1, behind))
        depth = max(1, min(PARAMS["JAM_BB"], int(depth + 0.5)))
        bits = table.get((players, behind, depth))
        if bits is None:
            return None
        return bool(bits[index >> 3] >> (index & 7) & 1)

    def should_jam(self, players, behind, depth, index, widen=False):
        answer = self._lookup(self.jam, players, behind, depth, index)
        if answer is None:
            return None
        if widen and not answer and behind > 1:
            # Tight callers behind us: use the wider chart for one fewer caller.
            return self._lookup(self.jam, players, behind - 1, depth, index)
        return answer

    def should_call(self, players, behind, depth, index):
        return self._lookup(self.call, players, behind, depth, index)


CHARTS = Charts()


def risk(stack_at_risk_share, players_left, hands_remaining):
    """Equity added to a threshold for a call or bet risking much of our stack."""
    if stack_at_risk_share < PARAMS["RISK_STACK_FRAC"]:
        return 0.0
    late = 1.0 - hands_remaining / MAX_HANDS
    place = max(2, min(TABLE_SIZE, players_left))
    jump = (PAYOUTS[place - 2] - PAYOUTS[place - 1]) / max(1, PAYOUTS[0])
    closeness = min(1.0, jump * 4)
    return PARAMS["RISK_MAX"] * (0.25 + 0.35 * late + 0.40 * closeness)
