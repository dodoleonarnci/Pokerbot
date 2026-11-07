"""Converts a participant hand-history download (.jsonl or .jsonl.gz) to the analyzer's canonical JSONL.

Usage: adapter.py DOWNLOAD OUTPUT.jsonl

Your own seat and filler seats are listed in each hand's `exclude`, so the analyzer can describe
the opponents' pool without them (analyze.py --include-excluded keeps them).

Cards are limited to what the file makes known: your own deal, kept and discarded cards, every
player's exposed card, and retained cards shown at showdown. Winnings are derived from the stack
balances, which the format names as authoritative, so uncalled refunds count as collected.
"""

import gzip
import json
import sys

try:
    import orjson

    loads, dumps = orjson.loads, orjson.dumps
except ImportError:
    loads = json.loads

    def dumps(obj):
        return json.dumps(obj, separators=(",", ":")).encode()


def convert_hand(hand, hid, own_seat, own_cards, private, fillers):
    before, after = hand["stacks_before"], hand["stacks_after"]
    sb, bb, ante = hand["blinds"]
    in_play = [s for s, chips in enumerate(before) if chips > 0]
    put = dict.fromkeys(in_play, 0)
    street_put = dict.fromkeys(in_play, 0)
    board, actions, shown, retained, blinds = [], [], {}, {}, []
    street = 0
    for event in hand["events"]:
        kind, seat = event["kind"], event.get("seat")
        amount = event.get("amount", 0)
        if kind == "ante":
            put[seat] += amount
        elif kind == "blind":
            put[seat] += amount
            street_put[seat] += amount
            blinds.append(seat)
        elif kind == "board":
            board.extend(event["cards"])
            street = {3: 1, 4: 2, 5: 3}[len(board)]
            street_put = dict.fromkeys(in_play, 0)
        elif kind in ("fold", "check"):
            actions.append({"street": street, "seat": seat, "type": kind})
        elif kind == "call":
            put[seat] += amount
            street_put[seat] += amount
            actions.append({"street": street, "seat": seat, "type": "call"})
        elif kind == "raise":
            put[seat] += amount - street_put[seat]
            street_put[seat] = amount
            actions.append({"street": street, "seat": seat, "type": "raise", "to": amount})
        elif kind == "reveal":
            shown[seat] = event["cards"][0]
        elif kind == "show":
            retained[seat] = event["cards"]
    # The blinds fix the positions: the seat in play before the small blind holds the button.
    # Heads-up the button is the small blind and acts first, and the big blind is posted first.
    if len(in_play) == 2 or not blinds:
        button = hand["button"]
    else:
        button = in_play[in_play.index(blinds[0]) - 1]
    seats, shows = [], {}
    for seat in in_play:
        entry = {"seat": seat, "stack": before[seat]}
        if seat == own_seat and own_cards:
            entry["cards3"] = own_cards
        if seat == own_seat and private.get("kept"):
            entry["cards"] = private["kept"]
        elif seat in retained and len(retained[seat]) == 2:
            entry["cards"] = retained[seat]
        seats.append(entry)
    for seat, card in shown.items():
        shows[str(seat)] = {"show": card}
        if seat == own_seat and private.get("discarded"):
            shows[str(seat)]["discard"] = private["discarded"][0]
    exclude = [s for s in in_play if s == own_seat or fillers[s]]
    winnings = {str(s): after[s] - before[s] + put[s] for s in in_play if after[s] - before[s] + put[s]}
    return {"id": hid, "bb": bb, "sb": sb, "ante": ante, "button": button, "seats": seats, "actions": actions,
            "board": board, "shows": shows, "winnings": winnings, "exclude": exclude}


def convert(source_path, output_path):
    opener = gzip.open if source_path.endswith(".gz") else open
    counts = {"tables": 0, "hands": 0, "own_hands": 0, "filler_tables": 0, "tables_by_size": {}, "header": None}
    hid = 0
    with opener(source_path, "rb") as source, open(output_path, "wb") as output:
        lines = iter(source)
        header = loads(next(lines))
        counts["header"] = {"tournament_id": header["tournament_id"], "entries": len(header["entries"])}
        for line in lines:
            table = loads(line)
            own = loads(next(lines))["you"]
            private = {}
            for event in own.get("private_events", []):
                private.setdefault(event["hand"], {})[event["kind"]] = event["cards"]
            counts["tables"] += 1
            counts["filler_tables"] += any(table["fillers"])
            size = str(len(table["seats"]))
            counts["tables_by_size"][size] = counts["tables_by_size"].get(size, 0) + 1
            for index, hand in enumerate(table["hands"]):
                dealt = own["cards"][index] if index < len(own["cards"]) else []
                counts["own_hands"] += bool(dealt)
                record = convert_hand(hand, hid, own["seat"], dealt, private.get(hand["hand"], {}), table["fillers"])
                output.write(dumps(record) + b"\n")
                hid += 1
                counts["hands"] += 1
    return counts


if __name__ == "__main__":
    print(json.dumps(convert(sys.argv[1], sys.argv[2]), indent=1))
