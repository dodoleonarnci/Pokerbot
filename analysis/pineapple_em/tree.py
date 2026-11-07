"""Game-tree statistics for overfolding and overbluffing, from replayed hand histories."""
from collections import Counter, defaultdict

import numpy as np

from . import em
from .cards import AIR, BUCKET_NAMES, N_BUCKETS
from .history import hand_bucket, hand_value

SIZES = ("small", "medium", "pot", "overbet", "jam")
ACTION_IDS = {"check": 0, "fold": 1, "call": 2, **{f"raise-{s}": 3 + i for i, s in enumerate(SIZES)}}
N_ACTIONS = len(ACTION_IDS)


def action_label(decision):
    return f"raise-{decision.size}" if decision.action == "raise" else decision.action


def bet_or_raise(node):
    return "bet" if node.split("|")[3] in ("first", "checked-to") else "raise"


def node_parts(node):
    parts = node.split("|")
    if parts[0] == "P":
        return {"street": "P", "players": parts[1], "role": "", "situation": parts[2], "size": parts[3]}
    return dict(zip(("street", "players", "role", "situation", "size"), parts))


def wilson(successes, n, z=1.96):
    if n == 0:
        return 0.0, 1.0
    p = successes / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return float(max(0.0, centre - half)), float(min(1.0, centre + half))


class TreeStats:
    def __init__(self):
        self.hands = 0
        self.node_actions = defaultdict(Counter)
        self.node_alpha = defaultdict(list)
        self.bet_results = defaultdict(list)
        self.river_shown = defaultdict(list)
        self.shown_mix = defaultdict(lambda: np.zeros(N_BUCKETS))
        self.hu_tree = defaultdict(Counter)
        self.hu_tree_bets = defaultdict(list)
        self.hu_tree_actor = {}

    def add(self, replay):
        self.hands += 1
        for d in replay.decisions:
            if not d.population:
                continue
            self.node_actions[d.node][action_label(d)] += 1
            if d.to_call > 0 and d.street > 0:
                self.node_alpha[d.node].append(d.faced / max(d.pot, 1))
            if d.path is not None:
                key = (hu_root(replay), d.path)
                self.hu_tree[key][path_action(d)] += 1
                self.hu_tree_actor[key] = (d.position, d.street)
        board = replay.board
        for bet in replay.bets:
            if not bet.hero_responds and bet.responders | bet.callers:
                s = bet.increment / max(bet.pot, 1)
                won = bet.outcome == "folded"
                self.bet_results[(bet.node, bet.size)].append((won, s))
                if bet.path is not None:
                    self.hu_tree_bets[(hu_root(replay), bet.path)].append((bet.size, won, s))
            if not bet.population or bet.seat not in replay.shown:
                continue
            cards = replay.shown[bet.seat]
            street_board = board[:2 + bet.street]
            self.shown_mix[(bet.node, bet.size)][hand_bucket(cards, street_board)] += 1
            if bet.street == 3 and bet.outcome == "called" and len(board) == 5:
                callers = [replay.shown[c] for c in bet.callers if c in replay.shown]
                if not callers:
                    continue
                mine = hand_value(cards, board)
                best = max(hand_value(c, board) for c in callers)
                result = 0.0 if mine > best else 0.5 if mine == best else 1.0
                self.river_shown[(bet.node, bet.size)].append(
                    (hand_bucket(cards, board), result, bet.increment / max(bet.pot, 1)))


def hu_root(replay):
    if replay.preflop_aggressor not in replay.flop_players:
        return "limped pot"
    first = next(d.seat for d in replay.decisions if d.street == 1)
    return "raiser out of position" if replay.preflop_aggressor == first else "raiser in position"


def path_action(decision):
    if decision.action == "raise":
        return f"{bet_or_raise(decision.node)} {decision.size}"
    return decision.action


def em_bettor_mix(replays, max_hands=60000):
    """EM-corrected hand mix behind population bets on the flop and turn, by (node, size)."""
    node_ids, observations, bet_index = {}, [], []
    for replay in replays[:max_hands]:
        if len(replay.board) < 3:
            continue
        hero = set(replay.hero_cards)
        exposed_cards = set(replay.exposed.values())
        for seat in replay.flop_players:
            if seat == replay.hero_seat or seat not in replay.exposed:
                continue
            mine = [d for d in replay.decisions if d.seat == seat and d.street > 0 and d.population]
            if not mine:
                continue
            others_shown = {c for s, cards in replay.shown.items() if s != seat for c in cards}
            exposed = replay.exposed[seat]
            shown = replay.shown.get(seat)
            hidden = next((c for c in shown if c != exposed), None) if shown else None
            decisions = []
            for d in mine:
                node = node_ids.setdefault(d.node, len(node_ids))
                decisions.append((node, ACTION_IDS[action_label(d)], d.street - 1))
                if d.action == "raise" and d.street in (1, 2):
                    bet_index.append((len(observations), len(decisions) - 1, d.node, d.size))
            line = 0 if replay.preflop_aggressor == seat else 1
            observations.append(em.Observation(
                line=line, exposed=exposed, board=tuple(replay.board),
                blocked=frozenset(hero | (exposed_cards - {exposed}) | others_shown),
                decisions=tuple(decisions), hidden=hidden))
    if not observations:
        return {}, None
    arrays = em.build(observations)
    model = em.fit(arrays, len(node_ids), N_ACTIONS, 2)
    mixes = em.decision_bucket_mix(model, arrays)
    group_of = {key: g for g, key in enumerate(arrays.groups)}
    by_spot = defaultdict(lambda: np.zeros(N_BUCKETS))
    counts = Counter()
    for instance, position, node, size in bet_index:
        by_spot[(node, size)] += mixes[group_of[(instance, position)]]
        counts[(node, size)] += 1
    fit_info = {"instances": len(observations), "rows": int(len(arrays.row_cell)),
                "iterations": model.iterations, "nodes": len(node_ids)}
    return {key: (counts[key], (total / counts[key]).tolist()) for key, total in by_spot.items()}, fit_info


def summarize(stats, em_mix=None, min_count=30):
    hands = max(stats.hands, 1)
    nodes = []
    for node, actions in stats.node_actions.items():
        n = sum(actions.values())
        if n < min_count:
            continue
        entry = {"node": node, **node_parts(node), "count": n, "per_1000_hands": 1000 * n / hands,
                 "actions": {k: v / n for k, v in actions.most_common()}}
        alphas = stats.node_alpha.get(node)
        if alphas and entry["street"] != "P":
            folds = actions.get("fold", 0)
            alpha = float(np.mean(alphas))
            low, high = wilson(folds, n)
            entry.update({"fold_rate": folds / n, "fold_low": low, "fold_high": high,
                          "breakeven_fold": alpha, "overfold": folds / n - alpha})
        nodes.append(entry)

    bets = []
    for (node, size), results in stats.bet_results.items():
        n = len(results)
        if n < min_count or node.startswith("P"):
            continue
        won = sum(w for w, _ in results)
        sizes = np.array([s for _, s in results])
        ev = np.mean([1.0 if w else -s for w, s in results])
        low, high = wilson(won, n)
        bets.append({"node": node, **node_parts(node), "bet_size": size, "kind": bet_or_raise(node),
                     "n": n, "fold_through": won / n, "fold_low": low, "fold_high": high,
                     "breakeven": float(np.mean(sizes / (1 + sizes))), "mean_size": float(sizes.mean()),
                     "bluff_ev_pots": float(ev), "per_1000_hands": 1000 * n / hands})

    river = []
    for (node, size), rows in stats.river_shown.items():
        n = len(rows)
        if n < 10:
            continue
        buckets = np.array([b for b, _, _ in rows])
        caller_won = np.array([r for _, r, _ in rows])
        sizes = np.array([s for _, _, s in rows])
        air = float(np.mean(buckets == AIR))
        balanced = float(np.mean(sizes / (1 + 2 * sizes)))
        call_ev = float(np.mean(air * (1 + sizes) - (1 - air) * sizes))
        low, high = wilson(int((buckets == AIR).sum()), n)
        river.append({"node": node, **node_parts(node), "bet_size": size, "kind": bet_or_raise(node),
                      "n": n, "air_share": air, "air_low": low, "air_high": high, "balanced": balanced,
                      "caller_won": float(caller_won.mean()), "mean_size": float(sizes.mean()),
                      "bluffcatch_ev_pots": call_ev,
                      "mix": (np.bincount(buckets, minlength=N_BUCKETS) / n).tolist()})

    earlier = []
    for (node, size), counts in stats.shown_mix.items():
        if node[0] not in "FT" or counts.sum() < 10:
            continue
        row = {"node": node, **node_parts(node), "bet_size": size, "kind": bet_or_raise(node),
               "shown_n": int(counts.sum()), "shown_mix": (counts / counts.sum()).tolist()}
        if em_mix and (node, size) in em_mix:
            row["em_n"], row["em_mix"] = em_mix[(node, size)]
        earlier.append(row)
    for (node, size), (n, mix) in (em_mix or {}).items():
        if not any(r["node"] == node and r["bet_size"] == size for r in earlier) and n >= min_count:
            earlier.append({"node": node, **node_parts(node), "bet_size": size, "kind": bet_or_raise(node),
                            "shown_n": 0, "shown_mix": None, "em_n": n, "em_mix": mix})
    return {"hands": stats.hands, "nodes": nodes, "bets": bets, "river": river, "earlier": earlier,
            "buckets": BUCKET_NAMES, "hu_tree": hu_tree(stats, min_count)}


def hu_tree(stats, min_count):
    roots = {}

    def child(parent, name):
        for c in parent["children"]:
            if c["name"] == name:
                return c
        node = {"name": name, "count": 0, "children": []}
        parent["children"].append(node)
        return node

    for (root, path), actions in stats.hu_tree.items():
        n = sum(actions.values())
        if n < min_count:
            continue
        node = roots.setdefault(root, {"name": root, "count": 0, "children": []})
        for token in path:
            node = child(node, token)
        node["count"] = max(node["count"], n)
        position, street = stats.hu_tree_actor[(root, path)]
        node["actor"] = "out of position" if position == "o" else "in position"
        node["street"] = ("preflop", "flop", "turn", "river")[street]
        node["actions"] = {k: v / n for k, v in actions.most_common()}
        bets = stats.hu_tree_bets.get((root, path), [])
        by_size = defaultdict(list)
        for size, won, s in bets:
            by_size[size].append((won, s))
        node["bets"] = {size: {"n": len(rows), "fold_through": float(np.mean([w for w, _ in rows])),
                               "breakeven": float(np.mean([s / (1 + s) for _, s in rows])),
                               "bluff_ev_pots": float(np.mean([1.0 if w else -s for w, s in rows]))}
                        for size, rows in by_size.items() if len(rows) >= 10}
    for root in roots.values():
        root["count"] = sum(c["count"] for c in root["children"]) or root["count"]
    return list(roots.values())
