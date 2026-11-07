"""The four deviation tests, the pool summary, and report.md. Verdicts appear only on usable cells."""

import math

from backoff import BET_SIZE_VERDICT, USABLE

BLUFF = ("air", "draw")
WEAK = ("air", "draw", "weak")
PULL = BET_SIZE_VERDICT
MIN_COVERAGE = 0.8  # Below this share of known cards, a class rate describes who got shown, not the pool.


def summary(tree, shows, meta) -> dict:
    seen = [node for node in tree.values() if node["n"]]
    counts = sorted((node["n"] for node in seen), reverse=True)
    half, running, decisions = 0, 0, sum(counts)
    for count in counts:
        running += count
        half += 1
        if running * 2 >= decisions:
            break
    class_cells = usable_cc = big_cc = 0
    split_cells = usable_split = big_split = 0
    split_decisions = 0
    class3_seen = set()
    for node in seen:
        per_class = {}
        for table in node["cls"].values():
            for cls, count in table.items():
                per_class[cls] = per_class.get(cls, 0) + count
        class_cells += len(per_class)
        for count in per_class.values():
            usable_cc += count >= USABLE
            big_cc += count >= BET_SIZE_VERDICT
        if node["k"].startswith("preflop") and node["n"]:
            class3_seen.update(per_class)
        for cell in node.get("splits", {}).values():
            split_cells += 1
            if cell["n"] >= USABLE:
                usable_split += 1
                split_decisions += cell["n"]
            big_split += cell["n"] >= BET_SIZE_VERDICT
    postflop = meta["postflop"] or 1
    return {
        "hands": meta["hands"], "errors": meta["errors"], "conservation_failures": meta["conservation"],
        "decisions": decisions, "excluded_decisions": meta["excluded_decisions"],
        "path_nodes": len(seen), "path_nodes_20": sum(c >= USABLE for c in counts),
        "path_nodes_200": sum(c >= BET_SIZE_VERDICT for c in counts),
        "node_class_cells": class_cells, "node_class_cells_20": usable_cc, "node_class_cells_200": big_cc,
        "show_nodes": len(shows), "show_nodes_20": sum(s["n"] >= USABLE for s in shows.values()),
        "show_nodes_200": sum(s["n"] >= BET_SIZE_VERDICT for s in shows.values()),
        "split_cells": split_cells, "split_cells_20": usable_split, "split_cells_200": big_split,
        "postflop_decisions": meta["postflop"], "postflop_share_in_usable_cells": round(split_decisions / postflop, 4),
        "nodes_holding_half_of_decisions": half, "preflop_classes_seen": len(class3_seen),
    }


def z_score(rate, threshold, n):
    spread = threshold * (1 - threshold) / n if n else 0
    return (rate - threshold) / math.sqrt(spread) if spread > 0 else 0.0


def key_parts(key):
    parts = key.split(";")
    return parts + [""] * (6 - len(parts))


def _street_fold(pool):
    """Fold rate by street and size code faced, the parent for a bet that needs a response rate."""
    totals = {}
    for key, table in pool["responses"].items():
        street, _, code = key.split(";")
        cell = totals.setdefault((street, code), [0, 0])
        cell[0] += sum(table.values())
        cell[1] += table.get("f", 0)
    return totals


def pull(rate, n, parent):
    """Below 200 samples a bet-size verdict uses a rate pulled toward the parent."""
    if n >= PULL or parent is None:
        return rate
    return (n * rate + PULL * parent) / (n + PULL)


def _bounds(table, names, total):
    """Lowest and highest possible share of `names` among `total` actions, given unknown hands.

    Cards are often known only for hands that reached showdown, so a share of the known hands alone
    is biased. A verdict must hold for every way the unknown hands could fall.
    """
    known = sum(table.values())
    part = sum(table.get(name, 0) for name in names)
    if not total:
        return 0.0, 1.0, 0.0
    return part / total, (part + total - known) / total, known / total


def deviation_tests(tree, pool, withheld=None):
    """Returns verdict rows: test, spot key, path, size, n, observed, threshold, z, edge, chips.

    `withheld`, if given, counts the verdicts the known hands alone suggest but the unknown hands
    could overturn.
    """
    spots = pool["spots"]
    parent_fold = _street_fold(pool)
    withheld = {} if withheld is None else withheld
    rows = []
    for node_key, node in tree.items():
        n = node["n"]
        implied = node.get("if", 0)
        if n + implied < USABLE:
            continue
        key = node["k"]
        street = key.split(";", 1)[0]
        path = node_key.rsplit(" @", 1)[0] if " @" in node_key else ""
        pot_bb = node["pot"]
        if "fb" in node:
            B, P = node["fb"], node["fp"]
            size = _faced_size(path)
            decisions = n + implied
            f = (node["a"].get("f", 0) + implied) / decisions
            # With k players still to answer, a bet needs them all to fold: each needs alpha^(1/k).
            k = max(node.get("fk", 1), 1)
            threshold = (B / (P + B)) ** (1 / k) if P + B else 0.0
            z = z_score(f, threshold, decisions)
            joint = f ** k
            edge = (joint * P - (1 - joint) * B) / P if P else 0.0
            chips = edge * max(pot_bb, P)
            if f > threshold and z >= 2:
                rows.append(("folds_too_much", key, path, size, decisions, f, threshold, z, edge, chips))
            elif f < threshold and z <= -2 and street != "preflop":
                calls = node["a"].get("c", 0)
                table = node["cls"].get("c", {})
                low, high, _ = _bounds(table, WEAK, calls)
                if calls >= USABLE and low > 0.5:
                    rows.append(("calls_too_much", key, path, size, decisions, low, 0.5, z, -edge, -chips))
                elif calls >= USABLE and high > 0.5 and sum(table.values()) >= USABLE \
                        and sum(table.get(name, 0) for name in WEAK) * 2 > sum(table.values()):
                    withheld["calls_too_much"] = withheld.get("calls_too_much", 0) + 1
        if street == "preflop":
            continue
        parent = spots.get(key, {})
        for code, (count, b_sum, p_sum) in node.get("s", {}).items():
            if count < USABLE:
                continue
            B, P = b_sum / count, p_sum / count
            threshold = B / (P + 2 * B) if P + 2 * B else 0.0
            table = node["cls"].get(code, {})
            low, high, _ = _bounds(table, BLUFF, count)
            parent_low, parent_high, _ = _bounds(parent.get("cls", {}).get(code, {}), BLUFF, parent.get("a", {}).get(code, 0))
            low, high = pull(low, count, parent_low), pull(high, count, parent_high)
            faced = parent_fold.get((street, code))
            f = faced[1] / faced[0] if faced and faced[0] else 0.0
            if low > threshold and z_score(low, threshold, count) >= 2:
                edge = (f * P - (1 - f) * B) / P if P else 0.0
                rows.append(("bluffs_too_much", key, path, code, count, low, threshold,
                             z_score(low, threshold, count), edge, edge * P))
            elif high < threshold and z_score(high, threshold, count) <= -2:
                edge = _value_edge(node, code, f, B, P)
                rows.append(("value_too_much", key, path, code, count, high, threshold,
                             z_score(high, threshold, count), edge, edge * P))
            else:
                known = sum(table.values())
                if known >= USABLE:
                    share = sum(table.get(name, 0) for name in BLUFF) / known
                    if abs(z_score(share, threshold, known)) >= 2:
                        test = "bluffs_too_much" if share > threshold else "value_too_much"
                        withheld[test] = withheld.get(test, 0) + 1
    rows.sort(key=lambda row: (-abs(row[9]), row[0], row[2], row[3]))
    return rows


def _value_edge(node, code, f, B, P):
    """c*(E_called(h)*(P+2B)-B), in pots, for the commonest value class in the node."""
    best = None
    for r_key, (called, share_sum) in node.get("ec", {}).items():
        if r_key.startswith(code + "#") and r_key.rsplit("#", 1)[1] in ("top", "strong"):
            if best is None or called > best[0]:
                best = (called, share_sum / called)
    if best is None or not P:
        return 0.0
    return (1 - f) * (best[1] * (P + 2 * B) - B) / P


def _faced_size(path):
    for token in reversed(path.replace(" /", "").split(" ")):
        code = token.split(":")[-1]
        if code and code[0] in "br":
            return code
    return "blind"


def pool_rates(pool, shows) -> dict:
    """Pool-wide rates, generic to any data: the numbers a planted-leak check reads from the report."""
    opens, three, by_street = {}, {"n": 0, "r": 0, "c": 0}, {}
    vs3 = {"n": 0, "f": 0, "c": 0, "r": 0}
    vs4 = {"n": 0, "f": 0, "c": 0, "r": 0}
    for key, spot in pool["spots"].items():
        street, line, pos = key.split(";")[:3]
        if street != "preflop":
            continue
        a = spot["a"]
        raises = sum(v for k, v in a.items() if k[0] == "r")
        if line == "unopened":
            cell = opens.setdefault(pos, {"n": 0, "r": 0, "c": 0})
            cell["n"] += spot["n"]
            cell["r"] += raises
            cell["c"] += a.get("c", 0)
        elif line == "vs_open":
            three["n"] += spot["n"]
            three["r"] += raises
            three["c"] += a.get("c", 0)
        elif line in ("vs_3bet", "vs_4bet+"):
            cell = vs3 if line == "vs_3bet" else vs4
            cell["n"] += spot["n"]
            cell["r"] += raises
            cell["c"] += a.get("c", 0)
            cell["f"] += a.get("f", 0)
    bet_by_class = {}
    coverage = {}
    for key, (n, bets) in pool["bet_class"].items():
        cls = key.split(";")[1]
        known = cls != "?"
        cover = coverage.setdefault("bets", [0, 0])
        cover[0] += bets if known else 0
        cover[1] += bets
        if not known:
            continue
        cell = bet_by_class.setdefault(cls, [0, 0])
        cell[0] += n
        cell[1] += bets
    fold_by_class = {}
    for key, table in pool["resp_class"].items():
        street, faced, prev, cls = key.split(";")
        if street != "flop" or faced[0] != "b" or faced[1] not in "SLO":
            continue
        group = "small" if faced[1] == "S" else "big"
        cover = coverage.setdefault(f"folds;{group}", [0, 0])
        cover[0] += table.get("f", 0) if cls != "?" else 0
        cover[1] += table.get("f", 0)
        if cls == "?":
            continue
        cell = fold_by_class.setdefault(f"{group};{cls}", [0, 0])
        cell[0] += sum(table.values())
        cell[1] += table.get("f", 0)
    lines = {}
    for key, table in pool["lines"].items():
        street, prev, faced = key.split(";")
        cell = lines.setdefault(f"{street};{prev}", [0, 0])
        cell[0] += sum(table.values())
        cell[1] += table.get("f", 0)
    pair_opp = sum(s["pair_opp"] for s in shows.values())
    pair_shown = sum(s["pair_shown"] for s in shows.values())
    discard_opp = sum(s["discard_opp"] for s in shows.values())
    bad = sum(s["bad_discard"] for s in shows.values())
    return {"open": opens, "vs_open": three, "vs_3bet": vs3, "vs_4bet": vs4, "bet_by_class": bet_by_class,
            "fold_by_class": fold_by_class, "two_street": lines,
            "show_helper": [pair_opp, pair_shown], "keep_best": [discard_opp, discard_opp - bad],
            "coverage": coverage}


def table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell).replace("|", "/") for cell in row) + " |")
    return "\n".join(lines) + "\n"


def _pct(n, part):
    return f"{part / n:.3f}" if n else "-"


def build_report(tree, shows, pool, meta, stats) -> str:
    out = ["# Hand analyzer report\n"]
    out.append(table(["Measure", "Value"], [(k, v) for k, v in stats.items()]))
    out.append(f"\nMalformed lines skipped: {meta['errors']} {meta['error_kinds']}\n")
    out.append("\n## Top 30 nodes by chips at stake\n\nChips at stake = decisions x average pot (BB).\n\n")
    ranked = sorted(((node["n"] * node["pot"], key) for key, node in tree.items() if node["n"]),
                    key=lambda item: (-item[0], item[1]))[:30]
    rows = []
    for chips, key in ranked:
        node = tree[key]
        parts = key_parts(node["k"])
        path = key.rsplit(" @", 1)[0] if " @" in key else "(start)"
        rows.append((parts[0], parts[1], node["actor"], parts[3], parts[4], parts[5], path, node["n"],
                     f"{node['pot']:.1f}", f"{chips:.0f}"))
    out.append(table(["Street", "Line", "Pos", "Players", "Depth", "So far", "Path", "n", "Pot BB", "Chips"], rows))

    withheld = {}
    verdicts = deviation_tests(tree, pool, withheld)
    names = {"folds_too_much": "Folds too much", "calls_too_much": "Calls too much",
             "bluffs_too_much": "Bluffs too much", "value_too_much": "Value bets too much"}
    out.append("\n## Deviation verdicts\n\nUsable cells only (20+ samples, |z| >= 2). A bet size with under "
               "200 samples is pulled toward its pooled spot. Edge is in pots; chips = edge x pot (BB). Depth, "
               "players and so-far columns show each node's commonest spot.\n\nFold thresholds allow for the k "
               "players still to answer: each must fold alpha^(1/k) for a bet to work. Class-mix verdicts must hold "
               "for every way the unknown hands could fall; Observed is the bound that decided it.\n")
    for test, title in names.items():
        mine = [row for row in verdicts if row[0] == test]
        held = withheld.get(test, 0)
        note = f"; {held} withheld, unknown hands could overturn them" if held else ""
        out.append(f"\n### {title}: {len(mine)} flagged{note}, top 30\n\n")
        rows = []
        for _, key, path, size, n, observed, threshold, z, edge, chips in mine[:30]:
            parts = key_parts(key)
            rows.append((parts[0], parts[1], parts[2], parts[3], parts[4], parts[5], path or "(start)", size, n,
                         f"{observed:.3f}", f"{threshold:.3f}", f"{z:.1f}", f"{edge:.3f}", f"{chips:.2f}"))
        out.append(table(["Street", "Line", "Pos", "Players", "Depth", "So far", "Path", "Size", "n", "Observed",
                          "Threshold", "z", "Edge", "Chips"], rows))

    rates = pool_rates(pool, shows)
    out.append("\n## Pool rates\n\n### Unopened, by position\n\n")
    out.append(table(["Pos", "n", "Open", "Limp"],
                     [(p, c["n"], _pct(c["n"], c["r"]), _pct(c["n"], c["c"])) for p, c in sorted(rates["open"].items())]))
    out.append("\n### Facing raises\n\n")
    out.append(table(["Spot", "n", "Fold", "Call", "Raise"],
                     [("vs_open", rates["vs_open"]["n"], _pct(rates["vs_open"]["n"], rates["vs_open"]["n"]
                                                             - rates["vs_open"]["c"] - rates["vs_open"]["r"]),
                       _pct(rates["vs_open"]["n"], rates["vs_open"]["c"]), _pct(rates["vs_open"]["n"], rates["vs_open"]["r"]))]
                     + [(name, c["n"], _pct(c["n"], c["f"]), _pct(c["n"], c["c"]), _pct(c["n"], c["r"]))
                        for name, c in (("vs_3bet", rates["vs_3bet"]), ("vs_4bet+", rates["vs_4bet"]))]))
    bets_cover = rates["coverage"].get("bets", [0, 0])
    out.append(f"\n### Postflop bet frequency by class (no bet to face)\n\nClass known on {_pct(bets_cover[1], bets_cover[0])} "
               f"of these bets. Rates need {MIN_COVERAGE:.0%}: below that they describe hands that got shown.\n\n")
    bet_ok = bets_cover[1] and bets_cover[0] / bets_cover[1] >= MIN_COVERAGE
    out.append(table(["Class", "Known n", "Bet"], [(k, v[0], _pct(v[0], v[1]) if bet_ok else "withheld")
                                                  for k, v in sorted(rates["bet_by_class"].items())]))
    out.append(f"\n### Flop fold rate by bet size and class\n\nRates need {MIN_COVERAGE:.0%} of the folds to have known "
               "cards, since a folded hand is rarely shown.\n\n")
    rows = []
    for k, v in sorted(rates["fold_by_class"].items()):
        group, cls = k.split(";")
        cover = rates["coverage"].get(f"folds;{group}", [0, 0])
        ok = cover[1] and cover[0] / cover[1] >= MIN_COVERAGE
        rows.append((group, cls, v[0], _pct(cover[1], cover[0]), _pct(v[0], v[1]) if ok else "withheld"))
    out.append(table(["Size", "Class", "Known n", "Folds with known cards", "Fold"], rows))
    out.append("\n### Fold rate facing a first bet, by the previous street (two-street lines)\n\n")
    out.append(table(["Street", "Previous street", "n", "Fold"],
                     [(*k.split(";"), v[0], _pct(v[0], v[1])) for k, v in sorted(rates["two_street"].items())]))
    seen, known = meta["shows_seen"], meta["shows_known"]
    out.append("\n## Show and discard\n\n")
    out.append(f"Kept cards are known for {known} of {seen} players who reached the flop ({_pct(seen, known)}). ")
    if seen and known / seen < MIN_COVERAGE:
        out.append("Below 80%, these rates describe hands that reached showdown, not every flop.")
    out.append("\n\n")
    out.append(table(["Measure", "Spots", "Rate"],
                     [("Shows the card that pairs the flop, when one kept card does", rates["show_helper"][0],
                       _pct(*rates["show_helper"])),
                      ("Keeps the best pair, when the pairs differ", rates["keep_best"][0], _pct(*rates["keep_best"]))]))
    out.append("\n### Show leaks by position and class\n\nHow often the player shows the kept card that pairs the "
               "flop, when exactly one does: the choice that gives the hand away. Grouped without the public "
               "bucket, because bucket P means the shown card pairs the flop by definition. 20+ spots only.\n\n")
    grouped = {}
    for key, node in shows.items():
        pos, cls, _ = key.split(";")
        cell = grouped.setdefault((pos, cls), [0, 0, 0])
        cell[0] += node["n"]
        cell[1] += node["pair_opp"]
        cell[2] += node["pair_shown"]
    ranked = sorted(((c[2] / c[1], p, cl, c[0], c[1]) for (p, cl), c in grouped.items() if c[1] >= USABLE),
                    key=lambda row: (-row[0], row[1], row[2]))
    out.append(table(["Pos", "Class", "n", "Spots", "Shows strong card"],
                     [(p, cl, n, spots, f"{rate:.3f}") for rate, p, cl, n, spots in ranked[:30]]))
    out.append("\n### Bad discards by position and best available class\n\nGrouped by the best pair the player could "
               "have kept, because a kept class of air with a better option is a bad discard by definition. Needs the "
               "three dealt cards, so it is empty when only opponents are counted. 20+ spots only.\n\n")
    ranked = sorted(((c[1] / c[0], *k.split(";"), c[0]) for k, c in pool["discards"].items() if c[0] >= USABLE),
                    key=lambda row: (-row[0], row[1], row[2]))
    out.append(table(["Pos", "Best available", "Spots", "Bad discard"],
                     [(p, cl, n, f"{rate:.3f}") for rate, p, cl, n in ranked[:30]]))
    return "".join(out)
