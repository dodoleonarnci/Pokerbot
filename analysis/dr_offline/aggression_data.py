"""Turn a NO LIMIT hand-history download into per-table and per-hand CSVs labeled with the
bot's aggressiveness factor, recomputed exactly as agent.py assigns it.

Usage: python3 aggression_data.py HISTORY.jsonl.gz OUT_PREFIX
Writes OUT_PREFIX-tables.csv and OUT_PREFIX-hands.csv.
"""

import csv
import gzip
import hashlib
import json
import sys
import zlib

DECISIONS = {"fold", "check", "call", "raise", "select"}
BETTING = ("fold", "check", "call", "raise")
RANKS = "23456789TJQKA"


def factor_for(hand_number, cards):
    seed = f"{hand_number}:{''.join(sorted(cards))}"
    return int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) / 2**32


def lines(path):
    with open(path, "rb") as handle:
        raw = handle.read()
    if raw[:2] == b"\x1f\x8b":
        chunks, data = [], raw
        while data:
            decompressor = zlib.decompressobj(zlib.MAX_WBITS | 16)
            chunks.append(decompressor.decompress(data))
            data = decompressor.unused_data
        raw = b"".join(chunks)
    for line in raw.decode().splitlines():
        if line.strip():
            yield json.loads(line)


def table_pairs(path):
    stream = lines(path)
    header = next(stream)
    pending = None
    for record in stream:
        if "you" in record and isinstance(record["you"], dict) and "seat" in record["you"]:
            yield header, pending, record["you"]
            pending = None
        else:
            pending = record


def branch_of(hand, seat, private_events):
    kept = next((e["cards"] for e in private_events if e.get("hand") == hand["hand"] and e.get("kind") == "kept"), None)
    shown = next((e.get("cards") for e in hand["events"] if e["kind"] == "reveal" and e.get("seat") == seat), None)
    if not kept or not shown:
        return ""
    other = kept[0] if kept[1] == shown[0] else kept[1]
    return "strong" if RANKS.index(shown[0][0]) >= RANKS.index(other[0]) else "weak"


def main(path, prefix):
    table_rows, hand_rows = [], []
    for _header, table, private in table_pairs(path):
        seat = private["seat"]
        automatic = {tuple(pair) for pair in private.get("automatic", [])}
        hands = table["hands"]
        factor, first_hand = None, None
        for index, hand in enumerate(hands):
            for event_index, event in enumerate(hand["events"]):
                if event.get("seat") == seat and event["kind"] in DECISIONS and (hand["hand"], event_index) not in automatic:
                    factor, first_hand = factor_for(hand["hand"], private["cards"][index]), hand["hand"]
                    break
            if factor is not None:
                break
        totals = {kind: 0 for kind in BETTING}
        for index, hand in enumerate(hands):
            counts = {kind: 0 for kind in BETTING}
            for event in hand["events"]:
                if event.get("seat") == seat and event["kind"] in counts:
                    counts[event["kind"]] += 1
            for kind in BETTING:
                totals[kind] += counts[kind]
            hand_rows.append({
                "iteration": table["iteration"], "table": table["table"], "hand": hand["hand"],
                "factor": factor, "branch": branch_of(hand, seat, private.get("private_events", [])),
                "chips_before": hand["stacks_before"][seat],
                "chip_delta": hand["stacks_after"][seat] - hand["stacks_before"][seat],
                "big_blind": hand["blinds"][1],
                "showdown": int(any(e["kind"] == "show" and e.get("seat") == seat for e in hand["events"])),
                "won": int(any(e["kind"] == "win" and e.get("seat") == seat for e in hand["events"])),
                **{f"n_{kind}": counts[kind] for kind in BETTING},
            })
        decisions = sum(totals.values())
        last = hands[-1] if hands else None
        table_rows.append({
            "iteration": table["iteration"], "table": table["table"], "seat": seat,
            "filler": int(table["fillers"][seat]), "factor": factor, "factor_hand": first_hand,
            "hands": len(hands), "points": last["equity_after"][seat] if last else None,
            "final_chips": last["stacks_after"][seat] if last else None,
            "decisions": decisions, "raise_share": totals["raise"] / decisions if decisions else None,
            "automatic": len(automatic), **{f"n_{kind}": totals[kind] for kind in BETTING},
        })
    for suffix, rows in (("tables", table_rows), ("hands", hand_rows)):
        if rows:
            with open(f"{prefix}-{suffix}.csv", "w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
    print(f"{len(table_rows)} tables, {len(hand_rows)} hands -> {prefix}-tables.csv, {prefix}-hands.csv")
    return table_rows


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
