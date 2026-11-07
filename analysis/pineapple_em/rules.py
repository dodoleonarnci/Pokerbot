"""Turn a report.py summary into spot-keyed exploit rules (rules.json) and the README's rule tables."""
import argparse
import json
import pathlib
import re
from datetime import datetime, timezone

from .cards import BUCKET_NAMES
from .equity import bucket_equity

SIZE_FALLBACK = {"small": 0.33, "medium": 0.6, "pot": 1.0, "overbet": 1.5, "jam": 1.0}
STREET_NAMES = {"F": "flop", "T": "turn", "R": "river"}
MARK_START, MARK_END = "<!-- rules:start -->", "<!-- rules:end -->"


def bluff_rules(bets, min_n):
    rules = []
    for b in bets:
        if b["n"] < min_n:
            continue
        s = b["mean_size"]
        ev_low = b["fold_low"] - (1 - b["fold_low"]) * s
        if b["fold_low"] > b["breakeven"]:
            verdict = "bluff"
        elif b["fold_high"] < b["breakeven"]:
            verdict = "value_only"
        else:
            verdict = "neutral"
        rules.append({"key": b["node"], "street": STREET_NAMES[b["street"]], "players": b["players"],
                      "role": b["role"], "situation": b["situation"], "faced_size": b["size"],
                      "bet_size": b["bet_size"], "size_fraction": round(s, 3), "n": b["n"],
                      "fold_through": round(b["fold_through"], 3), "fold_low": round(b["fold_low"], 3),
                      "fold_high": round(b["fold_high"], 3), "breakeven_fold": round(b["breakeven"], 3),
                      "bluff_ev_pots": round(b["bluff_ev_pots"], 3), "bluff_ev_low_pots": round(ev_low, 3),
                      "per_1000_hands": round(b["per_1000_hands"], 2), "verdict": verdict})
    return sorted(rules, key=lambda r: -r["bluff_ev_low_pots"])


def call_rule(key, street, size, s, mix, n, source, equity, margin, low=None, high=None):
    required = s / (1 + 2 * s)
    table = equity[street]["equity"]
    by_bucket = [None if all(v is None for v in table[ours]) else
                 sum(m * (table[ours][theirs] if table[ours][theirs] is not None else 0.5) for theirs, m in enumerate(mix))
                 for ours in range(len(mix))]
    threshold = required + (margin if street != "river" else 0.0)
    calls = [BUCKET_NAMES[i] for i, e in enumerate(by_bucket) if e is not None and e >= threshold]
    bluff = mix[0] + (mix[1] if street != "river" else 0.0)
    if low is not None and low > required:
        verdict = "call_bluffcatchers"
    elif high is not None and high < required:
        verdict = "fold_bluffcatchers"
    else:
        verdict = "equity"
    parts = key.split("|")
    return {"key": key, "street": street, "players": parts[1], "bettor_role": parts[2], "bettor_situation": parts[3],
            "faced_size": parts[4], "bet_size": size, "size_fraction": round(s, 3), "n": n, "source": source,
            "bluff_share": round(bluff, 3), "mix": [round(m, 3) for m in mix], "required_equity": round(required, 3),
            "equity_by_our_bucket": [None if e is None else round(e, 3) for e in by_bucket], "call_with": calls, "verdict": verdict}


def call_rules(summary, equity, min_river, min_em, margin):
    sizes = {(b["node"], b["bet_size"]): b["mean_size"] for b in summary["bets"]}
    rules = []
    for r in summary["river"]:
        if r["n"] >= min_river:
            rules.append(call_rule(r["node"], "river", r["bet_size"], r["mean_size"], r["mix"], r["n"],
                                   "river showdowns", equity, margin, r["air_low"], r["air_high"]))
    for r in summary["earlier"]:
        if r.get("em_mix") and r.get("em_n", 0) >= min_em:
            s = sizes.get((r["node"], r["bet_size"]), SIZE_FALLBACK.get(r["bet_size"], 0.6))
            rules.append(call_rule(r["node"], STREET_NAMES[r["street"]], r["bet_size"], s, r["em_mix"], r["em_n"],
                                   "EM", equity, margin))
    return sorted(rules, key=lambda r: (-r["n"]))


def describe(rule):
    names = {"PFA": "preflop raiser", "caller": "preflop caller", "limped": "limped pot",
             "agg": "bet last street", "def": "called last street", "checked": "street before checked through"}
    moves = {"first": "first to act", "checked-to": "after a check", "vs-bet": "facing a bet", "vs-raise": "facing a raise"}
    role = rule.get("role") or rule.get("bettor_role")
    situation = rule.get("situation") or rule.get("bettor_situation")
    faced = f" ({rule['faced_size']})" if rule.get("faced_size") else ""
    return f"{rule['street']} · {rule['players']} · {names.get(role, role)} · {moves.get(situation, situation)}{faced}"


def markdown(rules):
    lines = [f"_Generated {rules['generated']} from {rules['source']['label']} ({rules['source']['hands']:,} hands)._", ""]
    bluffs = [r for r in rules["bluff_spots"] if r["verdict"] == "bluff"]
    lines += ["### Bluff here: opponents fold more than break-even", "",
              "| Spot (we are the bettor) | Size | Fold, 95% low | Break-even | EV per bet, low (pots) | Bets | Per 1k hands |",
              "|---|---|---|---|---|---|---|"]
    lines += [f"| {describe(r)} | {r['bet_size']} | {r['fold_low']:.0%} | {r['breakeven_fold']:.0%} | "
              f"{r['bluff_ev_low_pots']:+.2f} | {r['n']:,} | {r['per_1000_hands']:.1f} |" for r in bluffs]
    value = [r for r in rules["bluff_spots"] if r["verdict"] == "value_only"]
    lines += ["", "### Never bluff here: opponents fold less than break-even", "",
              "| Spot (we are the bettor) | Size | Fold, 95% high | Break-even | Bets |", "|---|---|---|---|---|"]
    lines += [f"| {describe(r)} | {r['bet_size']} | {r['fold_high']:.0%} | {r['breakeven_fold']:.0%} | {r['n']:,} |"
              for r in value]
    lines += ["", "### Facing a bet: what to call with", "",
              "| Spot (the opponent bet) | Size | Source | Bluff share | Required equity | Verdict | Call with | Sample |",
              "|---|---|---|---|---|---|---|---|"]
    lines += [f"| {describe(r)} | {r['bet_size']} | {r['source']} | {r['bluff_share']:.0%} | {r['required_equity']:.0%} | "
              f"{r['verdict'].replace('_', ' ')} | {', '.join(r['call_with']) or 'nothing'} | {r['n']:,} |"
              for r in rules["call_spots"][:40]]
    eq = rules["equity"]
    for street in ("flop", "turn", "river"):
        lines += ["", f"### Equity of our bucket (row) against theirs (column), {street}", "",
                  "| ours \\ theirs | " + " | ".join(BUCKET_NAMES) + " |", "|---|" + "---|" * len(BUCKET_NAMES)]
        lines += [f"| {BUCKET_NAMES[i]} | " + " | ".join("—" if v is None else f"{v:.2f}" for v in row) + " |"
                  for i, row in enumerate(eq[street]["equity"]) if any(v is not None for v in row)]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("summary")
    parser.add_argument("--out", required=True)
    parser.add_argument("--readme")
    parser.add_argument("--min-bets", type=int, default=100)
    parser.add_argument("--min-river", type=int, default=40)
    parser.add_argument("--min-em", type=int, default=100)
    parser.add_argument("--margin", type=float, default=0.05)
    parser.add_argument("--samples", type=int, default=150000)
    args = parser.parse_args()
    summary = json.load(open(args.summary))
    equity = bucket_equity(args.samples)
    rules = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": {"label": summary.get("label", ""), "hands": summary["hands"], "em": summary.get("em")},
        "parameters": {"min_bets": args.min_bets, "min_river_showdowns": args.min_river, "min_em_bets": args.min_em,
                       "flop_turn_equity_margin": args.margin},
        "buckets": list(BUCKET_NAMES),
        "equity": equity,
        "bluff_spots": bluff_rules(summary["bets"], args.min_bets),
        "call_spots": call_rules(summary, equity, args.min_river, args.min_em, args.margin),
    }
    pathlib.Path(args.out).write_text(json.dumps(rules, indent=1))
    print(f"{len(rules['bluff_spots'])} bluff spots, {len(rules['call_spots'])} call spots -> {args.out}")
    if args.readme:
        path = pathlib.Path(args.readme)
        text = path.read_text()
        block = f"{MARK_START}\n{markdown(rules)}\n{MARK_END}"
        text = re.sub(re.escape(MARK_START) + ".*?" + re.escape(MARK_END), lambda _: block, text, flags=re.S)
        path.write_text(text)
        print(f"rule tables written into {path}")


if __name__ == "__main__":
    main()
