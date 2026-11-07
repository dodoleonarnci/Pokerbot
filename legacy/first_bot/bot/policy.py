"""M5: the Strategy spec. Range versus range on one shared 0-1 scale, S1 to S10.

Every bet, call and bluff is a closed-form formula once q has been ranked for the street.
"""
import math
import random
import time

from .evaluator import (CATEGORY_SHIFT, CLASS_COMBOS, CLASSES, FLUSH, N_CLASSES, PAIR_INDEX,
                        class_of, score7)
from .features import count_outs, hand_key, ppot
from .icm import CHARTS, risk
from .opponent import POOL, OpponentModel
from .params import PARAMS as P
from .spots import ActionTracker, depth_bucket, players_bucket, position_label, size_bucket
from .tables import TABLES

ALL_CLASSES = list(range(N_CLASSES))
PAIR_WAYS = (6, 3, 1, 0, 0)


# ---- S1: the range scale ----------------------------------------------------------
def range_percentile(hole, board, classes):
    """q: the share of the given classes that our hand beats on this board."""
    hero = score7(list(hole) + list(board))
    if TABLES.rank_table is None:
        return min(1.0, ((hero >> CATEGORY_SHIFT) + 0.5) / 5)
    table = TABLES.rank_table
    offset = TABLES.row_offset(board)

    rank_counts = [0] * 13
    suit_counts = [0, 0, 0, 0]
    for c in board:
        rank_counts[c >> 2] += 1
        suit_counts[c & 3] += 1
    flush_suit = max(range(4), key=suit_counts.__getitem__)
    need = 5 - suit_counts[flush_suit] if suit_counts[flush_suit] >= 3 else 3

    category = hero >> CATEGORY_SHIFT
    hero_flush_top = -1
    if category == FLUSH:
        hero_flush_top = max((c >> 2 for c in hole if c & 3 == flush_suit), default=-1)

    below = total = 0.0
    for index in classes:
        high, low, kind = CLASSES[index]
        if kind == 0:
            weight = PAIR_WAYS[rank_counts[high]]
        else:
            ways = (4 - rank_counts[high]) * (4 - rank_counts[low])
            weight = ways * 0.25 if kind == 1 else ways * 0.75
        if weight <= 0:
            continue
        score = table[offset + PAIR_INDEX[index]]
        if score < 0:
            continue
        total += weight
        share = 0.0
        if need <= 2:
            if need == 2:
                share = 0.25 if kind == 1 else 0.0
            elif need == 1:
                share = 0.25 if kind == 1 else 0.5
            else:
                share = 1.0
        if share:
            if category > FLUSH:
                below += weight * share
            elif category == FLUSH:
                if high < hero_flush_top:
                    below += weight * share
                elif high == hero_flush_top:
                    below += weight * share * 0.5
        rest = weight * (1 - share)
        if rest:
            if score < hero:
                below += rest
            elif score == hero:
                below += rest * 0.5
    return below / total if total else 0.5


# ---- S1 and S3: bands, as sorted lists of (lo, hi) --------------------------------
def band_width(band):
    return sum(hi - lo for lo, hi in band)


def band_equity(band, q):
    width = band_width(band)
    if width <= 1e-9:
        return 1.0 if q >= band[-1][1] else 0.0
    return sum(max(0.0, min(q - lo, hi - lo)) for lo, hi in band) / width


def band_top(band, share):
    """Keep the top share of a band's width."""
    keep = max(0.0, min(1.0, share)) * band_width(band)
    kept = []
    for lo, hi in reversed(band):
        if keep <= 0:
            break
        take = min(keep, hi - lo)
        kept.append((hi - take, hi))
        keep -= take
    kept.reverse()
    return kept or [band[-1]]


def mdf(pot, bet):
    return pot / (pot + bet) if pot + bet > 0 else 1.0


def betting_band(band, pot, bet, value_eq, continue_rate=None):
    """S6 applied to a band: value at the top plus bluffs at the bottom."""
    width = band_width(band)
    low, high = band[0][0], band[-1][1]
    m = mdf(pot, bet) if continue_rate is None else continue_rate
    value = max(0.0, min(width, m * width * (1 - value_eq)))
    bluffs = min(width - value, value * bet / (pot + bet)) if pot + bet > 0 else 0.0
    built = []
    if bluffs > 1e-9:
        built.append((low, low + bluffs))
    if value > 1e-9:
        built.append((high - value, high))
    return built or [(high - 1e-3, high)]


def geometric_fraction(pot, stack):
    """S4: the same pot fraction twice puts the stack in by the river."""
    if pot <= 0:
        return P["F_MAX"]
    return (math.sqrt(1 + 2 * stack / pot) - 1) / 2


def required_equity(to_call, pot):
    return to_call / (pot + to_call) if to_call > 0 else 0.0


def decile_share(deciles, q):
    """Share of observed hands below q, from a stored decile list."""
    below = sum(1 for d in deciles if d < q)
    return below / len(deciles) if deciles else 0.5


class Policy:
    def __init__(self, seed=None, use_pool=True, use_exploits=True, probe_rate=0.0):
        self.rng = random.Random(seed)
        self.use_pool = use_pool
        self.use_exploits = use_exploits
        self.probe_rate = probe_rate
        self.hand_number = None
        self.opponents = OpponentModel()
        self.tracker = None
        self.fallback_q = 0.5
        self.reset_hand_state()

    def reset_hand_state(self):
        self.seen = 0
        self.pre_bet_band = {}
        self.bands = {}
        self.pct = {}
        self.hero_range = ("top", 100.0)
        self.hero_classes = None
        self.q_street = None
        self.q = 0.5
        self.q_all = None
        self.outs = 0
        self.planned_jam = False
        self.exploit_used = False
        self.start_stack = None

    # ---- Following the hand ----------------------------------------------------
    def _start_hand(self, view):
        if self.hand_number is not None and view.hand_number < self.hand_number:
            self.opponents = OpponentModel()
            self.exploit_used = False
        elif self.exploit_used and self.start_stack is not None:
            # Book losses from the previous hand against the exploit loss budget.
            ids = view.seat_ids
            if self.hero_id in ids:
                now = view.stacks[ids.index(self.hero_id)] + view.bets[ids.index(self.hero_id)]
                self.opponents.exploit_loss += max(0, self.start_stack - now)
        self.hand_number = view.hand_number
        self.reset_hand_state()
        self.hero_id = view.seat_ids[view.seat]
        self.start_stack = view.stacks[view.seat] + view.bets[view.seat]
        self.tracker = ActionTracker(view.players, view.button, view.bb)

    def _their_preflop_pct(self, view, seat, kind, raises):
        label = position_label(seat, view.button, view.players)
        stack = view.stacks[seat] + view.bets[seat]
        if kind == "raise":
            base = {0: P["OPEN_PCT"].get(label, 20), 1: P["THEIR_3BET_PCT"],
                    2: P["THEIR_4BET_PCT"]}.get(raises, P["THEIR_JAM_PCT"])
            table_kind = {0: "open", 1: "3bet"}.get(raises, "jam")
        elif kind == "call":
            base = P["THEIR_LIMP_PCT"] if raises == 0 else P["THEIR_CALL_PCT"]
            table_kind = "call"
        else:
            return 100.0
        if self.use_pool:
            observed = POOL.preflop_pct(table_kind, label, stack, view.bb, view.players_left)
            if observed is not None:
                base = max(1.0, observed)
        if self.use_exploits:
            base = self.opponents.range_pct(view.seat_ids[seat], base, kind)
        return base

    def _observe(self, view, event):
        tracker = self.tracker
        seat, kind = event["seat"], event["action"]
        facing = tracker.last_bet is not None
        if seat != view.seat:
            self.opponents.observe(view.seat_ids[seat], view.hand_number,
                                   tracker.street, kind, facing)
        if tracker.street == "preflop":
            if seat != view.seat and kind in ("raise", "call", "check"):
                self.pct[seat] = self._their_preflop_pct(view, seat, kind, tracker.raises)
            tracker.apply(event)
            return

        was_unopened = tracker.current_bet == 0
        may_bet = was_unopened and tracker.may_bet_unopened(seat)
        whole_range_spot = (tracker.street == "flop" and len(tracker.live) == 2
                            and tracker.in_position(seat))
        previous_pending = tracker.current_bet
        result = tracker.apply(event)
        if seat == view.seat or seat not in self.bands:
            return
        band = self.bands[seat]
        value_eq = P["VALUE_EQ"][tracker.street]
        if kind == "check":
            if may_bet and not whole_range_spot:
                pot = event["pot"]
                bet = self._default_size(tracker.street, pot, event["stacks"][seat])
                built = betting_band(band, pot, bet, value_eq)
                keep = band_top(band, 1.0)
                value = built[-1][1] - built[-1][0]
                top = keep[-1][1]
                self.bands[seat] = [(lo, min(hi, top - value)) for lo, hi in keep
                                    if lo < top - value] or band
        elif kind == "raise":
            bet, pot = result
            self.pre_bet_band[seat] = band
            if not whole_range_spot or previous_pending:
                self.bands[seat] = betting_band(band, pot, bet, value_eq, self._their_continue(view, seat, pot, bet))
        elif kind == "call" and event["amount"] > 0:
            pot = event["pot"] - event["amount"]
            m = self._their_continue(view, seat, pot, event["amount"])
            self.bands[seat] = band_top(band, m)

    def _their_continue(self, view, seat, pot, bet):
        """S3: MDF, replaced by observed continue rates when M7 has them."""
        m = mdf(pot, bet)
        tracker = self.tracker
        if self.use_pool and POOL.a and tracker.last_bet:
            cell = POOL.lookup(POOL.a, tracker.street, tracker.last_bet[0], tracker.last_bet[1],
                               tracker.position_word(seat), players_bucket(len(tracker.live)),
                               depth_bucket(view.stacks[seat], view.bb), tracker.pfa_word(seat))
            if cell:
                m = max(0.05, min(0.95, 1 - cell[1]))
        return m

    def _sync(self, view):
        tracker = self.tracker
        history = view.history
        for event in history[self.seen:]:
            if event["street"] != tracker.street:
                self._enter_street(view, event["street"])
            self._observe(view, event)
        self.seen = len(history)
        if view.street != tracker.street:
            self._enter_street(view, view.street)

    def _enter_street(self, view, street):
        tracker = self.tracker
        first_postflop = tracker.street == "preflop"
        tracker.enter_street(street)
        if first_postflop:
            self._build_bands(view)

    def _build_bands(self, view):
        """S1: the starting band of each opponent, on our scale."""
        ours = self._ours_pct()
        for seat in self.tracker.live:
            if seat == view.seat:
                continue
            theirs = self.pct.get(seat, 100.0)
            self.bands[seat] = [(1.0 - theirs / ours, 1.0)]

    def _ours_pct(self):
        kind, *args = self.hero_range
        if kind == "top":
            return max(1.0, args[0])
        combos = sum(CLASS_COMBOS[i] for i in self._hero_classes())
        return max(1.0, combos / 13.26)

    def _hero_classes(self):
        if self.hero_classes is None:
            kind, *args = self.hero_range
            if kind == "top":
                self.hero_classes = TABLES.top[max(1, min(100, int(args[0] + 0.5)))]
            else:
                percent, threshold = args
                versus = TABLES.versus_top
                self.hero_classes = [i for i in ALL_CLASSES if versus(i, percent) >= threshold] \
                    or TABLES.top[5]
        return self.hero_classes

    # ---- S1: hand strength ------------------------------------------------------
    def _rank(self, view, deadline):
        """q and outs, once per street. Slow paths use the cached q or the M4 key table."""
        if self.q_street == view.street:
            return
        if time.perf_counter() > deadline:
            if self.q_street is None:
                self.q = self._key_strength(view)
            self.q_street = view.street
            self.q_all = None
            self.outs = 0
            return
        self.q = range_percentile(view.hole, view.board, self._hero_classes())
        self.q_all = None
        self.outs = count_outs(view.hole, view.board) if view.street != "river" else 0
        self.q_street = view.street

    def _key_strength(self, view):
        row = TABLES.postflop.get(hand_key(view.hole, view.board)) if len(view.board) < 5 else None
        return row[1] if row else 0.5

    def _q_all(self, view):
        if self.q_all is None:
            self.q_all = range_percentile(view.hole, view.board, ALL_CLASSES)
        return self.q_all

    # ---- S4: sizes -------------------------------------------------------------
    def _default_size(self, street, pot, stack):
        if street == "flop":
            return min(stack, max(1, round(P["FLOP_SIZE"] * pot)))
        fraction = geometric_fraction(pot, stack)
        if fraction < P["F_MIN"]:
            return stack
        return min(stack, max(1, round(min(fraction, P["F_MAX"]) * pot)))

    def _effective(self, view):
        tracker = self.tracker
        others = [view.stacks[s] + view.bets[s] for s in tracker.live if s != view.seat]
        mine = view.stacks[view.seat] + view.bets[view.seat]
        return min(mine, max(others)) if others else mine

    # ---- S2 and M6: preflop -----------------------------------------------------
    def _preflop(self, view):
        tracker = self.tracker
        index = class_of(view.hole[0], view.hole[1])
        effective = self._effective(view)
        depth = effective / view.bb
        free = view.to_call == 0
        give_up = ("check",) if free else ("fold",)
        label = position_label(view.seat, view.button, view.players)

        if depth <= P["JAM_BB"]:
            chart = self._chart(view, index, depth)
            if chart is not None:
                return chart

        percentile = TABLES.percentile[index]
        if tracker.raises == 0:
            limpers = tracker.in_pot
            threshold = P["OPEN_PCT"].get(label, 20) - 3 * limpers
            if percentile <= threshold and view.can_raise:
                self.hero_range = ("top", threshold)
                return ("raise", int((P["OPEN_BB"] + limpers) * view.bb))
            if free:
                self.hero_range = ("top", 100.0)
                return ("check",)
            if limpers == 0 and view.to_call <= view.sb and percentile <= threshold + 10:
                self.hero_range = ("top", threshold + 10)
                return ("call",)
            return ("fold",)

        # Facing a raise: our range against theirs.
        raiser = tracker.street_aggressor
        their_pct = self.pct.get(raiser, 15.0)
        equity = TABLES.versus_top(index, their_pct)
        in_position = tracker.in_position(view.seat)
        margin = P["PRE_CALL_MARGIN_IP"] if in_position else P["PRE_CALL_MARGIN_OOP"]
        extra = max(0, tracker.in_pot - 1) * P["MULTIWAY_TIGHTEN"]
        needed = required_equity(view.to_call, view.pot)
        call_at = needed + margin + extra
        value_at = 0.5 + extra
        current = tracker.current_bet

        if view.can_raise and equity > value_at:
            self.hero_range = ("eq", their_pct, value_at)
            return ("raise", self._reraise_size(view, current, in_position, depth))

        if tracker.raises == 1 and view.can_raise and equity < call_at:
            # S2: 3-bet bluffs are the hands just below the calling range.
            target = int(current * (P["THREEBET_IP"] if in_position else P["THREEBET_OOP"]))
            bet = max(1, target - current)
            pot_before = view.pot + view.to_call
            versus, value_pct, call_pct = TABLES.versus_top, 0.0, 0.0
            for candidate in TABLES.order:
                value = versus(candidate, their_pct)
                if value >= call_at:
                    call_pct = TABLES.percentile[candidate]
                    if value > value_at:
                        value_pct = call_pct
                else:
                    break
            bluff_pct = value_pct * bet / (pot_before + bet)
            if call_pct < percentile <= call_pct + bluff_pct:
                self.hero_range = ("eq", their_pct, value_at)
                return ("raise", target)

        if equity >= call_at and view.to_call > 0:
            self.hero_range = ("eq", their_pct, call_at)
            return ("call",)
        if free:
            self.hero_range = ("top", 100.0)
        return give_up

    def _reraise_size(self, view, current, in_position, depth):
        tracker = self.tracker
        if tracker.raises == 1:
            return int(current * (P["THREEBET_IP"] if in_position else P["THREEBET_OOP"]))
        if depth < P["FOURBET_JAM_BB"] or tracker.raises >= 3:
            return view.max_raise
        return int(current * P["FOURBET_X"])

    def _chart(self, view, index, depth):
        """M6: at or under JAM_BB the chart overrides S2."""
        tracker = self.tracker
        players = view.players_left
        big_blind_seat = (view.button + (1 if view.players == 2 else 2)) % view.players
        if tracker.raises == 0:
            if view.to_call == 0:
                self.hero_range = ("top", 100.0)
                return ("check",)
            behind = (big_blind_seat - view.seat) % view.players
            behind_ids = [view.seat_ids[(view.seat + k) % view.players] for k in range(1, behind + 1)]
            widen = self.use_exploits and self.opponents.tight_callers(behind_ids)
            answer = CHARTS.should_jam(players, max(1, behind), depth, index, widen)
            if answer is None:
                return None
            if self.use_exploits and self.opponents.loose_callers(behind_ids):
                # Someone behind rarely folds, so fold equity is gone: jam only hands
                # strong enough to want a call.
                answer = bool(answer and CHARTS.should_call(players, max(1, behind), depth, index))
            if answer and view.can_raise:
                self.hero_range = ("top", TABLES.percentile[index])
                return ("raise", view.max_raise)
            return ("fold",)
        raiser = tracker.street_aggressor
        behind = (big_blind_seat - raiser) % view.players
        answer = CHARTS.should_call(players, max(1, behind), depth, index)
        if answer is None:
            return None
        if answer:
            self.hero_range = ("top", TABLES.percentile[index])
            if view.can_raise and view.max_raise > tracker.current_bet:
                return ("raise", view.max_raise)
            return ("call",)
        return ("check",) if view.to_call == 0 else ("fold",)

    # ---- S6 and S7 -------------------------------------------------------------
    def _opponents(self, view):
        return [s for s in self.tracker.live if s != view.seat and s in self.bands]

    def _bluff_scale(self):
        return P["MULTIWAY_BLUFF"].get(len(self.tracker.live), 0.0)

    def _risk(self, view, amount):
        mine = view.stacks[view.seat]
        if mine <= 0:
            return 0.0
        return risk(amount / mine, view.players_left, view.hands_remaining)

    def _seat_equity(self, view, seat, q):
        """E vs. one opponent's band, with S10's in-table layer.

        A seat that bets far more often than the program would is not always strong: its
        betting band is at least as wide as it really bets. MAX_SHIFT caps the change.
        """
        narrow = band_equity(self.bands[seat], q)
        if not self.use_exploits or seat not in self.pre_bet_band:
            return narrow
        share = self.opponents.bet_share(view.seat_ids[seat])
        if share is None:
            return narrow
        wide = band_equity(band_top(self.pre_bet_band[seat], share), q)
        if wide <= narrow:
            return narrow
        self.exploit_used = True
        return narrow + min(wide - narrow, P["MAX_SHIFT"]) * self.opponents.fade()

    def _facing_bet(self, view, q):
        tracker = self.tracker
        pot, to_call = view.pot, view.to_call
        opponents = self._opponents(view)
        bettor = tracker.street_aggressor

        equity = 1.0
        for seat in opponents:
            equity *= self._seat_equity(view, seat, q)
        cell = None
        if self.use_pool and POOL.b and not POOL.biased and bettor in self.bands and tracker.last_bet:
            cell = POOL.lookup(POOL.b, tracker.street, tracker.last_bet[0], tracker.last_bet[1],
                               tracker.position_word(bettor), players_bucket(len(tracker.live)),
                               depth_bucket(view.stacks[bettor], view.bb), tracker.pfa_word(bettor))
            if cell and len(cell) > 2 and cell[2]:
                equity = decile_share(cell[2], self._q_all(view))
                for seat in opponents:
                    if seat != bettor:
                        equity *= self._seat_equity(view, seat, q)

        needed = required_equity(to_call, pot) + self._risk(view, to_call)

        if view.can_raise:
            current = tracker.current_bet
            target = int(current * P["RAISE_X"])
            target = max(view.min_raise, min(target, view.max_raise))
            mine_after = view.max_raise - target
            pot_after = pot + (target - view.bets[view.seat])
            if pot_after > 0 and mine_after / pot_after < P["RAISE_JAM_SPR"]:
                target = view.max_raise
            bet = max(1, target - current)
            pot_before = pot + max(0, current - view.bets[view.seat])
            m = mdf(pot_before, bet)
            raise_equity = 1.0
            for seat in opponents:
                raise_equity *= band_equity(band_top(self.bands[seat], m), q)
            penalty = self._risk(view, target - view.bets[view.seat])
            if raise_equity > P["RAISE_VALUE_EQ"] + penalty:
                return ("raise", target)
            if (tracker.street != "river" and self.outs >= P["DRAW_OUTS"] and equity < 0.5
                    and penalty == 0 and opponents):
                width = band_width(self.bands[opponents[0]])
                value = m * width * (1 - P["RAISE_VALUE_EQ"])
                bluffs = value * bet / (pot_before + bet) * self._bluff_scale()
                if self.rng.random() < min(1.0, bluffs / P["DRAW_SHARE"]):
                    return ("raise", target)
        if equity >= needed:
            return ("call",)
        return ("fold",)

    def _pool_fold_rate(self, view, line, size, opponent):
        tracker = self.tracker
        return POOL.lookup(POOL.a, tracker.street, line, size, tracker.position_word(opponent),
                           players_bucket(len(tracker.live)),
                           depth_bucket(view.stacks[opponent], view.bb), tracker.pfa_word(opponent))

    def _choose_size(self, view, default_bet, q_all, opponent, effective):
        """S10 Table A: pick the size with the largest EV when its cells are filled."""
        pot = view.pot
        best, best_ev, cells = default_bet, None, 0
        for size in P["SIZES"]:
            bet = effective if size == "all-in" else min(effective, max(1, round(size * pot)))
            all_in = bet >= effective
            line = self.tracker.bet_line(view.seat, all_in)
            cell = self._pool_fold_rate(view, line, size_bucket(bet, pot, all_in), opponent)
            if not cell or len(cell) < 4 or not cell[3] or POOL.biased:
                continue
            cells += 1
            fold_rate, call_rate = cell[1], cell[2]
            equity = decile_share(cell[3], q_all)
            ev = fold_rate * pot + call_rate * (equity * (pot + 2 * bet) - bet)
            if best_ev is None or ev > best_ev:
                best, best_ev = bet, ev
        return best if cells >= 2 else default_bet

    def _unopened(self, view, q):
        tracker = self.tracker
        if not view.can_raise or not tracker.may_bet_unopened(view.seat):
            return ("check",)
        street, pot = view.street, view.pot
        effective = min(view.stacks[view.seat], max(
            (view.stacks[s] for s in tracker.live if s != view.seat), default=0))
        if effective <= 0:
            return ("check",)
        opponents = self._opponents(view)
        if not opponents:
            return ("check",)
        heads_up = len(tracker.live) == 2

        if street == "river" and self.planned_jam and tracker.previous_aggressor == view.seat:
            bet = effective
        else:
            bet = self._default_size(street, pot, effective)

        # S10: replace MDF with the pool's and the seat's observed continue rate.
        m = mdf(pot, bet)
        fold_rate = None
        cell = None
        opponent = opponents[0]
        all_in = bet >= effective
        line = tracker.bet_line(view.seat, all_in)
        if self.use_pool and POOL.a and heads_up:
            cell = self._pool_fold_rate(view, line, size_bucket(bet, pot, all_in), opponent)
            if cell:
                fold_rate = cell[1]
                m = max(0.05, min(0.95, 1 - fold_rate))
        if self.use_exploits and heads_up:
            prior = fold_rate if fold_rate is not None else 1 - m
            seat_fold = self.opponents.fold_rate(view.seat_ids[opponent], prior)
            if seat_fold != prior:
                self.exploit_used = True
                fold_rate = seat_fold
                m = max(0.05, min(0.95, 1 - seat_fold))

        # S6, flop in position heads-up: bet the whole range at the small size.
        if street == "flop" and heads_up and tracker.in_position(view.seat):
            return self._make_bet(view, bet)

        value_eq = P["VALUE_EQ"][street] + self._risk(view, bet)
        is_value, cutoff_share = self._value_test(view, q, opponents, m, value_eq)
        if cell and len(cell) > 3 and cell[3] and not POOL.biased:
            is_value = decile_share(cell[3], self._q_all(view)) >= value_eq

        if is_value:
            if self.use_pool and POOL.a and heads_up and street != "flop":
                bet = self._choose_size(view, bet, self._q_all(view), opponent, effective)
            if street == "turn":
                fraction = geometric_fraction(pot, effective)
                self.planned_jam = P["F_MIN"] <= fraction <= P["F_MAX"]
            return self._make_bet(view, bet)

        # Bluffs: the formula's count, then S10's adjustment and cap.
        base = cutoff_share * bet / (pot + bet) * self._bluff_scale()
        bluffs = base
        if fold_rate is not None:
            break_even = bet / (pot + bet)
            if fold_rate > break_even + P["BLUFF_MARGIN"] + 0.15:
                bluffs = min(base * P["MAX_BLUFF_MULT"], 0.5)
                self.exploit_used = True
            elif fold_rate < break_even - P["BLUFF_MARGIN"]:
                bluffs = 0.0
        if self._risk(view, bet) > 0.05:
            bluffs = 0.0
        if street == "river":
            if q <= bluffs:
                return self._make_bet(view, bet)
            return ("check",)
        if q < 0.5 and self.outs >= P["DRAW_OUTS"]:
            if self.rng.random() < min(1.0, bluffs / P["DRAW_SHARE"]):
                if street == "turn":
                    fraction = geometric_fraction(pot, effective)
                    self.planned_jam = P["F_MIN"] <= fraction <= P["F_MAX"]
                return self._make_bet(view, bet)
        return ("check",)

    def _value_test(self, view, q, opponents, m, value_eq):
        """E_called(q) >= value_eq (S5). Returns the test and the value share v."""
        if len(opponents) == 1:
            band = self.bands[opponents[0]]
            width = band_width(band)
            cutoff = band[-1][1] - m * width * (1 - value_eq)
            return q >= cutoff, max(0.0, 1.0 - cutoff)
        equity = 1.0
        width = 0.0
        for seat in opponents:
            narrowed = band_top(self.bands[seat], m)
            equity *= band_equity(narrowed, q)
            width = max(width, band_width(narrowed))
        return equity >= value_eq, max(0.0, width * (1 - value_eq))

    def _make_bet(self, view, bet):
        return ("raise", view.bets[view.seat] + bet)

    # ---- M8: practice probes -----------------------------------------------------
    def _probe(self, view):
        rate = self.probe_rate or P["EXPLORE"]
        if rate <= 0 or not view.can_raise:
            return None
        effective = self._effective(view)
        if effective / view.bb <= 40 or view.pot > 15 * view.bb:
            return None  # cheap spots only: small pots, deep stacks, never jam/fold
        if self.rng.random() >= rate:
            return None
        pot = max(view.pot, view.bb)
        current = view.bets[view.seat] + view.to_call
        choice = self.rng.randrange(3)
        if view.to_call == 0:
            bet = {0: pot * 3 // 2, 1: max(view.bb, pot // 4), 2: pot // 2}[choice]
            return ("raise", current + bet)
        if choice == 0:
            return ("raise", view.min_raise)
        if view.street == "preflop":
            return ("raise", current * 3)
        return ("raise", current * 2)

    # ---- Entry --------------------------------------------------------------------
    def decide(self, view, deadline):
        if self.hand_number != view.hand_number or self.tracker is None or self.seen > len(view.history):
            self._start_hand(view)
        self._sync(view)

        probe = self._probe(view)
        if probe is not None:
            return probe
        if view.street == "preflop":
            return self._preflop(view)

        self._rank(view, deadline)
        q = self.q
        if view.street != "river":
            q = q + (1 - q) * ppot(self.outs, view.street)
        if view.to_call > 0:
            return self._facing_bet(view, q)
        return self._unopened(view, q)
