"""Flatten a report.py summary into row files for the dashboard."""
import argparse
import json
import pathlib
from datetime import datetime, timezone

STREETS = {"P": "preflop", "F": "flop", "T": "turn", "R": "river"}
TOKEN_STREETS = {"F": "Flop", "T": "Turn", "R": "River"}
BUCKET_KEYS = ("air", "weak_draw", "strong_draw", "weak_pair", "top_pair", "strong")


def base(row, size_key):
    return {"spot": f"{row['node']}|{row.get(size_key, '')}", "street": STREETS[row["street"]],
            "players": row["players"], "role": row["role"], "situation": row["situation"],
            "bet_size": row.get(size_key, "")}


def token_label(token):
    street, position, action = TOKEN_STREETS[token[0]], token[1], token[2:]
    who = "OOP" if position == "o" else "IP"
    names = {"X": "checks", "C": "calls", "F": "folds"}
    if action in names:
        return f"{street}: {who} {names[action]}"
    verb = "bets" if action[0] == "B" else "raises"
    return f"{street}: {who} {verb} {action[1:]}"


def tree_rows(roots):
    rows = []

    def walk(node, parent, path, depth):
        node_id = "/".join(path)
        actions = node.get("actions", {})
        bets = node.get("bets", {})
        best = max(bets.items(), key=lambda kv: kv[1]["bluff_ev_pots"], default=(None, None))
        rows.append({
            "id": node_id, "parent": parent, "label": node["name"] if depth == 0 else token_label(node["name"]),
            "depth": depth, "count": node["count"], "actor": node.get("actor", ""),
            "street": node.get("street", ""),
            "check": actions.get("check", 0.0), "call": actions.get("call", 0.0), "fold": actions.get("fold", 0.0),
            "bet": sum(v for k, v in actions.items() if k.startswith("bet")),
            "raise": sum(v for k, v in actions.items() if k.startswith("raise")),
            "best_bet_size": best[0] or "", "best_bluff_ev": best[1]["bluff_ev_pots"] if best[1] else None,
            "best_fold_through": best[1]["fold_through"] if best[1] else None,
            "best_bets_n": best[1]["n"] if best[1] else 0,
        })
        for child in sorted(node["children"], key=lambda c: -c["count"]):
            walk(child, node_id, path + [child["name"]], depth + 1)

    for root in roots:
        walk(root, "", [root["name"]], 0)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("summary")
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    data = json.load(open(args.summary))
    out = pathlib.Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    spots = [{**base(r, "bet_size"), "kind": r["kind"], "n": r["n"], "per_1000_hands": r["per_1000_hands"],
              "fold_through": r["fold_through"], "fold_low": r["fold_low"], "fold_high": r["fold_high"],
              "breakeven": r["breakeven"], "edge": r["fold_through"] - r["breakeven"],
              "bluff_ev_pots": r["bluff_ev_pots"], "mean_size": r["mean_size"]} for r in data["bets"]]
    river = [{**base(r, "bet_size"), "kind": r["kind"], "n": r["n"], "air_share": r["air_share"],
              "air_low": r["air_low"], "air_high": r["air_high"], "balanced": r["balanced"],
              "edge": r["air_share"] - r["balanced"], "bluffcatch_ev_pots": r["bluffcatch_ev_pots"],
              "caller_won": r["caller_won"], "mean_size": r["mean_size"],
              **{f"mix_{k}": v for k, v in zip(BUCKET_KEYS, r["mix"])}} for r in data["river"]]
    earlier = []
    for r in data["earlier"]:
        row = {**base(r, "bet_size"), "kind": r["kind"], "em_n": r.get("em_n", 0), "shown_n": r["shown_n"]}
        for prefix, mix in (("em", r.get("em_mix")), ("shown", r.get("shown_mix"))):
            for key, value in zip(BUCKET_KEYS, mix or [None] * 6):
                row[f"{prefix}_{key}"] = value
            row[f"{prefix}_bluff"] = (mix[0] + mix[1]) if mix else None
        earlier.append(row)
    responders = [{"node": r["node"], "street": STREETS[r["street"]], "players": r["players"],
                   "role": r["role"], "situation": r["situation"], "size": r["size"], "count": r["count"],
                   "fold_rate": r["fold_rate"], "fold_low": r["fold_low"], "fold_high": r["fold_high"],
                   "breakeven_fold": r["breakeven_fold"], "overfold": r["overfold"]}
                  for r in data["nodes"] if "fold_rate" in r]
    summary = [{"label": data.get("label", ""), "hands": data["hands"],
                "em_instances": (data.get("em") or {}).get("instances", 0),
                "em_iterations": (data.get("em") or {}).get("iterations", 0),
                "tree_nodes": len(data["nodes"]),
                "generated": datetime.now(timezone.utc).isoformat(timespec="seconds")}]
    files = {"summary": summary, "spots": spots, "river": river, "earlier": earlier,
             "responders": responders, "hu_tree": tree_rows(data["hu_tree"])}
    for name, rows in files.items():
        (out / f"{name}.json").write_text(json.dumps(rows))
        print(f"{name}: {len(rows)} rows")


if __name__ == "__main__":
    main()
