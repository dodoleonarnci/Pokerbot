import collections, json, sys, zlib
raw = open(sys.argv[1], "rb").read(); out = []
while raw:
    d = zlib.decompressobj(zlib.MAX_WBITS | 16); out.append(d.decompress(raw)); raw = d.unused_data
recs = [json.loads(l) for l in b"".join(out).decode().splitlines() if l.strip()]
counts = collections.Counter(); visits = collections.Counter(); vpip = [0, 0]
pending = None
for r in recs[1:]:
    if "you" in r and "seat" in r.get("you", {}):
        seat = r["you"]["seat"]
        for hand in pending["hands"]:
            street, raised, put_in = 0, False, False
            dealt = False
            for e in hand["events"]:
                k = e["kind"]
                if k == "board": street += 1; raised = False; continue
                if k not in ("fold", "check", "call", "raise"): continue
                if e.get("seat") == seat:
                    node = (["pre", "flop", "turn", "river"][min(street, 3)], "facing" if raised or (street == 0) else "open")
                    if street == 0 and not raised: node = ("pre", "unopened")
                    visits[node] += 1; counts[node + (k,)] += 1; dealt = True
                    if street == 0 and k in ("call", "raise"): put_in = True
                if k == "raise": raised = True
            if dealt: vpip[1] += 1; vpip[0] += put_in
        pending = None
    else:
        pending = r
print("VPIP", round(vpip[0] / vpip[1], 3), "hands with a decision", vpip[1])
for node in sorted(visits):
    acts = {k: counts[node + (k,)] for k in ("fold", "check", "call", "raise") if counts[node + (k,)] or True}
    tot = visits[node]
    print(node, tot, {k: f"{v/tot:.1%}" for k, v in acts.items()})
