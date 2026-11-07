"""Reads canonical JSONL hands and writes tree.json, shows.json, pool.json and report.md.

Usage: analyze.py HANDS.jsonl --out DIR [--workers 2] [--include-excluded]

Seats a hand lists in `exclude` (the adapter lists your own bot and fillers) still play through the
tracker and count for chips, but their decisions and show nodes are not added to the tables.
"""

import argparse
import gc
import json
import multiprocessing
import os
import time

from buckets import STRENGTH_ORDER, STRENGTHS, class3, pairs_board, pub_bucket, strength_class
from spot import MalformedHand, SpotTracker

try:
    import orjson

    loads = orjson.loads

    def dump_bytes(obj) -> bytes:
        return orjson.dumps(obj, option=orjson.OPT_SORT_KEYS)
except ImportError:
    loads = json.loads

    def dump_bytes(obj) -> bytes:
        return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()

# A node: [n, pot sum, actor, a, cls, r, facing bet sum, facing pot sum, facing n, implied folds,
#          s, ec, splits, key counts, responders sum, line, previous street, size faced].
# A split cell: [n, pot sum, a, cls, r].  A spot: [n, pot sum, a, cls].
N, POT, ACTOR, A, CLS, R_, FB, FP, FN, IF, S, EC, SPLITS, KS, FK, LINE, PREV, FACED = range(18)
INCLUDE_EXCLUDED = False


def empty_aggregate() -> dict:
    return {"nodes": {}, "shows": {}, "pool": {}, "discards": {}, "hands": 0, "decisions": 0, "postflop": 0,
            "excluded_decisions": 0, "shows_seen": 0, "shows_known": 0, "errors": 0, "conservation": 0,
            "error_kinds": {}}


def known_cards(hand):
    """Per seat: (cards3 or None, kept2 or None), parsed by field name."""
    shows = hand.get("shows") or {}
    out = {}
    for entry in hand["seats"]:
        seat = entry["seat"]
        cards3, kept = entry.get("cards3"), entry.get("cards")
        show = shows.get(str(seat))
        if kept is None and cards3 and show and show.get("discard"):
            kept = [c for c in cards3 if c != show["discard"]]
        out[seat] = (tuple(cards3) if cards3 else None, tuple(kept) if kept else None)
    return out


def actor_class(street, cards, board_at):
    """The variant's hand class for an actor: 3-card class preflop, strength class after."""
    if street == 0:
        return class3(cards[0]) if cards[0] else None
    return strength_class(cards[1], board_at) if cards[1] else None


def play_hand(hand, agg, include_excluded=False):
    """Replays one hand and commits it to `agg`. Raises on a malformed hand before committing."""
    bb = hand["bb"]
    tracker = SpotTracker([(e["seat"], e["stack"]) for e in hand["seats"]], hand["button"], hand.get("sb") or bb // 2,
                          bb, hand.get("ante") or 0)
    excluded = () if include_excluded else (hand.get("exclude") or ())
    cards = known_cards(hand)
    board = hand.get("board") or []
    flop = board[:3]
    bucket = {}
    if flop:
        for seat_key, show in (hand.get("shows") or {}).items():
            if show.get("show"):
                bucket[int(seat_key)] = pub_bucket(show["show"], flop)
    boards = (None, tuple(board[:3]), tuple(board[:4]), tuple(board[:5]))
    decisions = []
    skipped = []
    excluded_count = 0
    active_bet = None  # The decision index of the latest counted bet or raise on this street.

    def skip_fold():
        i = tracker.actor
        if tracker.seats[i] not in excluded:
            line = tracker.line()
            to_call = tracker.to_call
            skipped.append((tracker.path, tracker.pos[i], tracker.spot_key(line), to_call, tracker.pot, tracker.pending,
                            line, tracker.prev_line, tracker.last_code))

    for action in hand["actions"]:
        street, seat, kind = action["street"], action["seat"], action["type"]
        while tracker.needs_implied_fold(seat, street):
            skip_fold()
            tracker.apply_implied_fold()
        i = tracker.actor
        if i is None:
            raise MalformedHand("action after the hand ended")
        if kind == "fold" and street == 0 and not tracker.entered[i]:
            skip_fold()
            tracker.apply(seat, kind, 0, street)
            continue
        if seat in excluded:
            code = tracker.apply(seat, kind, action.get("to", 0), street)
            excluded_count += 1
            if code[0] in "br":
                active_bet = None
            elif code == "c" and active_bet is not None:
                decisions[active_bet][-1] = True
            continue
        line = tracker.line()
        path, pos, pot, to_call = tracker.path, tracker.pos[i], tracker.pot, tracker.to_call
        key = tracker.spot_key(line)
        faced, prev, n_live, pending, put_before = tracker.last_code, tracker.prev_line, tracker.n_live, \
            tracker.pending, tracker.put[i]
        other = None
        if street and n_live == 2:
            live = tracker.live
            for j in range(tracker.n):
                if live[j] and j != i:
                    other = tracker.seats[j]
        code = tracker.apply(seat, kind, action.get("to", 0), street)
        cls = actor_class(street, cards[seat], boards[street]) if seat in cards else None
        decisions.append([path, pos, key, code, cls, pot, to_call, seat, put_before, tracker.put[i] - put_before, line,
                          faced, prev, n_live, other, street, pending, False])
        if code[0] in "br":
            active_bet = len(decisions) - 1
        elif code == "c" and active_bet is not None and decisions[active_bet][15] == street:
            decisions[active_bet][-1] = True
    while tracker.can_imply_fold():
        skip_fold()
        tracker.apply_implied_fold()

    winnings = {int(k): v for k, v in (hand.get("winnings") or {}).items()}
    total_put = sum(tracker.put)
    if total_put != sum(winnings.values()):
        agg["conservation"] += 1
        raise MalformedHand("chips do not conserve")
    agg["excluded_decisions"] += excluded_count
    commit(agg, hand, tracker, decisions, skipped, winnings, cards, bucket, flop, bb, total_put, excluded)


def commit(agg, hand, tracker, decisions, skipped, winnings, cards, bucket, flop, bb, total_put, excluded):
    nodes = agg["nodes"]
    pool = agg["pool"]
    final_put = dict(zip(tracker.seats, tracker.put))
    for path, pos, key, to_call, pot, pending, line, prev, faced in skipped:
        node_key = f"{path} @{pos}" if path else f"@{pos}"
        node = nodes.get(node_key)
        if node is None:
            node = nodes[node_key] = [0, 0.0, pos, {}, {}, {}, 0.0, 0.0, 0, 0, {}, {}, {}, {}, 0, line, prev, faced]
        node[IF] += 1
        ks = node[KS]
        ks[key] = ks.get(key, 0) + 1
        if to_call:
            node[FB] += to_call / bb
            node[FP] += (pot - to_call) / bb
            node[FN] += 1
            node[FK] += pending
        spot = pool.get(key)
        if spot is None:
            spot = pool[key] = [0, 0.0, {}, {}]
        spot[0] += 1
        spot[1] += pot / bb
        a = spot[2]
        a["f"] = a.get("f", 0) + 1

    agg["hands"] += 1
    agg["decisions"] += len(decisions)
    for path, pos, key, code, cls, pot, to_call, seat, put_before, added, line, faced, prev, n_live, other, street, \
            pending, called in decisions:
        node_key = f"{path} @{pos}" if path else f"@{pos}"
        node = nodes.get(node_key)
        if node is None:
            node = nodes[node_key] = [0, 0.0, pos, {}, {}, {}, 0.0, 0.0, 0, 0, {}, {}, {}, {}, 0, line, prev, faced]
        pot_bb = pot / bb
        node[N] += 1
        node[POT] += pot_bb
        a = node[A]
        a[code] = a.get(code, 0) + 1
        ks = node[KS]
        ks[key] = ks.get(key, 0) + 1
        if to_call:
            node[FB] += to_call / bb
            node[FP] += (pot - to_call) / bb
            node[FN] += 1
            node[FK] += pending
        spot = pool.get(key)
        if spot is None:
            spot = pool[key] = [0, 0.0, {}, {}]
        spot[0] += 1
        spot[1] += pot_bb
        spot_a = spot[2]
        spot_a[code] = spot_a.get(code, 0) + 1
        if cls is not None:
            net = (winnings.get(seat, 0) - (final_put[seat] - put_before)) / pot
            cls_table = node[CLS].get(code)
            if cls_table is None:
                cls_table = node[CLS][code] = {}
            cls_table[cls] = cls_table.get(cls, 0) + 1
            r_key = f"{code}#{cls}"
            result = node[R_].get(r_key)
            if result is None:
                node[R_][r_key] = [1, net, net * net]
            else:
                result[0] += 1
                result[1] += net
                result[2] += net * net
            spot_cls = spot[3].get(code)
            if spot_cls is None:
                spot_cls = spot[3][code] = {}
            spot_cls[cls] = spot_cls.get(cls, 0) + 1
        if code[0] in "br":
            size = node[S].get(code)
            if size is None:
                size = node[S][code] = [0, 0.0, 0.0]
            size[0] += 1
            size[1] += (added - to_call) / bb
            size[2] += (pot + to_call) / bb
            if called and cls is not None:
                ec = node[EC].get(r_key)
                if ec is None:
                    ec = node[EC][r_key] = [0, 0.0]
                ec[0] += 1
                ec[1] += winnings.get(seat, 0) / total_put
        if street == 0:
            continue
        agg["postflop"] += 1
        mine = bucket.get(seat)
        if mine is None:
            continue
        if n_live == 2:
            theirs = bucket.get(other)
            if theirs is None:
                continue
        else:
            theirs = "M"
        split_key = f"{mine}|{theirs}"
        cell = node[SPLITS].get(split_key)
        if cell is None:
            cell = node[SPLITS][split_key] = [0, 0.0, {}, {}, {}]
        cell[0] += 1
        cell[1] += pot_bb
        cell_a = cell[2]
        cell_a[code] = cell_a.get(code, 0) + 1
        if cls is not None:
            cell_cls = cell[3].get(code)
            if cell_cls is None:
                cell_cls = cell[3][code] = {}
            cell_cls[cls] = cell_cls.get(cls, 0) + 1
            result = cell[4].get(r_key)
            if result is None:
                cell[4][r_key] = [1, net, net * net]
            else:
                result[0] += 1
                result[1] += net
                result[2] += net * net
    if flop:
        commit_shows(agg, hand, tracker, cards, flop, bucket, excluded)


def commit_shows(agg, hand, tracker, cards, flop, bucket, excluded):
    """One show node per player and hand that reached the flop, when the kept cards are known."""
    shows = agg["shows"]
    for seat_key, show in (hand.get("shows") or {}).items():
        seat = int(seat_key)
        if seat in excluded or not show.get("show"):
            continue
        agg["shows_seen"] += 1
        known = cards.get(seat)
        if known is None or known[1] is None:
            continue
        agg["shows_known"] += 1
        kept = known[1]
        cls = strength_class(kept, flop)
        pos = tracker.pos[tracker.index[seat]]
        key = f"{pos};{cls};{bucket[seat]}"
        node = shows.get(key)
        if node is None:
            node = shows[key] = [0, 0, 0, 0, 0]
        node[0] += 1
        shown = show["show"]
        other = kept[0] if kept[1] == shown else kept[1]
        shown_pairs = pairs_board(shown, flop)
        if shown_pairs != pairs_board(other, flop):
            node[1] += 1
            node[2] += shown_pairs
        full = known[0]
        if full:
            values = [STRENGTH_ORDER[strength_class(pair, flop)]
                      for pair in ((full[0], full[1]), (full[0], full[2]), (full[1], full[2]))]
            best = max(values)
            if min(values) != best:
                bad = STRENGTH_ORDER[cls] < best
                node[3] += 1
                node[4] += bad
                discard_key = f"{pos};{STRENGTHS[best]}"
                cell = agg["discards"].get(discard_key)
                if cell is None:
                    cell = agg["discards"][discard_key] = [0, 0]
                cell[0] += 1
                cell[1] += bad


def process_chunk(args):
    path, start, end, include_excluded = args
    gc.disable()
    agg = empty_aggregate()
    errors = agg["error_kinds"]
    with open(path, "rb") as handle:
        handle.seek(start)
        data = handle.read(end - start)
    for line in data.split(b"\n"):
        if not line.strip():
            continue
        try:
            play_hand(loads(line), agg, include_excluded)
        except (MalformedHand, KeyError, TypeError, ValueError, IndexError, AttributeError,
                ZeroDivisionError) as error:
            agg["errors"] += 1
            errors[type(error).__name__] = errors.get(type(error).__name__, 0) + 1
    return agg


def chunks(path: str, count: int, include_excluded=False):
    """Byte ranges split at line ends."""
    size = os.path.getsize(path)
    cuts = [0]
    with open(path, "rb") as handle:
        for i in range(1, count):
            handle.seek(size * i // count)
            handle.readline()
            cuts.append(min(handle.tell(), size))
    cuts.append(size)
    return [(path, cuts[i], cuts[i + 1], include_excluded) for i in range(count) if cuts[i + 1] > cuts[i]]


def merge_counts(into, other):
    for key, value in other.items():
        into[key] = into.get(key, 0) + value


def merge_nested(into, other):
    for key, value in other.items():
        table = into.get(key)
        if table is None:
            into[key] = value
        else:
            merge_counts(table, value)


def merge_results(into, other):
    for key, value in other.items():
        cell = into.get(key)
        if cell is None:
            into[key] = value
        else:
            cell[0] += value[0]
            cell[1] += value[1]
            cell[2] += value[2]


def merge(into, other):
    nodes = into["nodes"]
    for key, node in other["nodes"].items():
        mine = nodes.get(key)
        if mine is None:
            nodes[key] = node
            continue
        mine[N] += node[N]
        mine[POT] += node[POT]
        merge_counts(mine[A], node[A])
        merge_nested(mine[CLS], node[CLS])
        merge_results(mine[R_], node[R_])
        mine[FB] += node[FB]
        mine[FP] += node[FP]
        mine[FN] += node[FN]
        mine[FK] += node[FK]
        mine[IF] += node[IF]
        merge_counts(mine[KS], node[KS])
        merge_results(mine[S], node[S])
        for r_key, ec in node[EC].items():
            cell = mine[EC].get(r_key)
            if cell is None:
                mine[EC][r_key] = ec
            else:
                cell[0] += ec[0]
                cell[1] += ec[1]
        splits = mine[SPLITS]
        for split_key, cell in node[SPLITS].items():
            own = splits.get(split_key)
            if own is None:
                splits[split_key] = cell
            else:
                own[0] += cell[0]
                own[1] += cell[1]
                merge_counts(own[2], cell[2])
                merge_nested(own[3], cell[3])
                merge_results(own[4], cell[4])
    for key, node in other["shows"].items():
        mine = into["shows"].get(key)
        if mine is None:
            into["shows"][key] = node
        else:
            for i, value in enumerate(node):
                mine[i] += value
    for key, spot in other["pool"].items():
        mine = into["pool"].get(key)
        if mine is None:
            into["pool"][key] = spot
        else:
            mine[0] += spot[0]
            mine[1] += spot[1]
            merge_counts(mine[2], spot[2])
            merge_nested(mine[3], spot[3])
    for key, cell in other["discards"].items():
        mine = into["discards"].get(key)
        if mine is None:
            into["discards"][key] = cell
        else:
            mine[0] += cell[0]
            mine[1] += cell[1]
    for name in ("hands", "decisions", "postflop", "excluded_decisions", "shows_seen", "shows_known", "errors",
                 "conservation"):
        into[name] += other[name]
    merge_counts(into["error_kinds"], other["error_kinds"])


def to_tree(nodes):
    tree = {}
    for key, node in nodes.items():
        n = node[N]
        modal = max(node[KS].items(), key=lambda item: (item[1], item[0]))[0]
        out = {"n": n, "actor": node[ACTOR], "pot": node[POT] / n if n else 0.0, "a": node[A], "cls": node[CLS],
               "r": node[R_], "k": modal, "line": node[LINE], "prev": node[PREV], "faced": node[FACED]}
        if node[IF]:
            out["if"] = node[IF]
        if node[FN]:
            out["fb"] = node[FB] / node[FN]
            out["fp"] = node[FP] / node[FN]
            out["fk"] = node[FK] / node[FN]
        if node[S]:
            out["s"] = node[S]
        if node[EC]:
            out["ec"] = node[EC]
        if node[SPLITS]:
            out["splits"] = {k: {"n": c[0], "pot": c[1] / c[0], "a": c[2], "cls": c[3], "r": c[4]}
                             for k, c in node[SPLITS].items()}
        tree[key] = out
    return tree


def derive_pool(tree) -> dict:
    """Pool tables built from the merged nodes, so the per-decision loop stays small."""
    bets, responses, lines, resp_class, bet_class = {}, {}, {}, {}, {}
    for node in tree.values():
        street = node["k"].split(";", 1)[0]
        pos, line, prev, faced = node["actor"], node["line"], node["prev"], node["faced"]
        facing = "fb" in node
        if facing:
            table = responses.setdefault(f"{street};{pos};{faced}", {})
            if node.get("if"):
                table["f"] = table.get("f", 0) + node["if"]
        for code, count in node["a"].items():
            is_bet = code[0] in "br"
            group = "r" if is_bet else code
            if facing:
                table[group] = table.get(group, 0) + count
            if street == "preflop":
                continue
            if is_bet:
                bet_id = f"{street};{line};{pos};{code}"
                bets[bet_id] = bets.get(bet_id, 0) + count
            if facing and line == "vs_bet":
                by_line = lines.setdefault(f"{street};{prev};{faced}", {})
                by_line[group] = by_line.get(group, 0) + count
            known = node["cls"].get(code, {})
            unknown = count - sum(known.values())
            for cls, cls_count in (*known.items(), ("?", unknown)):
                if not cls_count:
                    continue
                if facing:
                    by_class = resp_class.setdefault(f"{street};{faced};{prev};{cls}", {})
                    by_class[group] = by_class.get(group, 0) + cls_count
                else:
                    cell = bet_class.setdefault(f"{street};{cls}", [0, 0])
                    cell[0] += cls_count
                    cell[1] += cls_count if is_bet else 0
    return {"bets": bets, "responses": responses, "lines": lines, "resp_class": resp_class, "bet_class": bet_class}


def analyze(path, out_dir, workers=2, quiet=False, include_excluded=False):
    begun = time.perf_counter()
    gc.disable()  # Unpickling and merging make millions of containers; collections only slow them.
    os.makedirs(out_dir, exist_ok=True)
    ranges = chunks(path, workers, include_excluded)
    if workers > 1 and len(ranges) > 1:
        with multiprocessing.Pool(workers) as pool:
            parts = pool.map(process_chunk, ranges, chunksize=1)
    else:
        parts = [process_chunk(r) for r in ranges]
    phases = {"map": time.perf_counter() - begun}
    agg = parts[0] if parts else empty_aggregate()
    for part in parts[1:]:
        merge(agg, part)
    phases["merge"] = time.perf_counter() - begun
    tree = to_tree(agg["nodes"])
    shows = {k: {"n": v[0], "pair_opp": v[1], "pair_shown": v[2], "discard_opp": v[3], "bad_discard": v[4]}
             for k, v in agg["shows"].items()}
    spots = {k: {"n": v[0], "pot": v[1] / v[0], "a": v[2], "cls": v[3]} for k, v in agg["pool"].items()}
    pool = {"spots": spots, "discards": agg["discards"], **derive_pool(tree)}
    meta = {k: agg[k] for k in ("hands", "decisions", "postflop", "excluded_decisions", "shows_seen", "shows_known",
                                "errors", "conservation", "error_kinds")}
    from deviations import build_report, summary
    stats = summary(tree, shows, meta)
    report = build_report(tree, shows, pool, meta, stats)
    phases["report"] = time.perf_counter() - begun
    for name, obj in (("tree.json", tree), ("shows.json", shows), ("pool.json", pool)):
        with open(os.path.join(out_dir, name), "wb") as handle:
            handle.write(dump_bytes(obj))
    with open(os.path.join(out_dir, "report.md"), "w") as handle:
        handle.write(report)
    phases["write"] = time.perf_counter() - begun
    stats["seconds"] = round(time.perf_counter() - begun, 1)
    stats["phase_seconds_cumulative"] = {k: round(v, 1) for k, v in phases.items()}
    if not quiet:
        print(json.dumps(stats, indent=1))
    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("hands")
    parser.add_argument("--out", default="out")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--include-excluded", action="store_true",
                        help="Count the seats hands list in `exclude`, such as your own bot.")
    options = parser.parse_args()
    analyze(options.hands, options.out, options.workers, include_excluded=options.include_excluded)
