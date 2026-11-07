import collections, json, sys, zlib
raw = open(sys.argv[1], "rb").read(); out = []
while raw:
    d = zlib.decompressobj(zlib.MAX_WBITS | 16); out.append(d.decompress(raw)); raw = d.unused_data
recs = [json.loads(l) for l in b"".join(out).decode().splitlines() if l.strip()]
hdr = recs[0]; names = {e["entry_id"]: e["team_name"] for e in hdr["entries"]}
vp = collections.Counter(); hands = collections.Counter(); pts = collections.defaultdict(list)
for r in recs[1:]:
    if "hands" not in r: continue
    seats = r["seats"]
    for i, ent in enumerate(seats):
        if not r["fillers"][i] and r["hands"]: pts[ent].append(r["hands"][-1]["equity_after"][i])
    for h in r["hands"]:
        acted, put = set(), set(); street = 0
        for e in h["events"]:
            if e["kind"] == "board": street += 1
            if street == 0 and e["kind"] in ("fold", "check", "call", "raise"):
                acted.add(e["seat"])
                if e["kind"] in ("call", "raise"): put.add(e["seat"])
        for s in acted:
            hands[seats[s]] += 1; vp[seats[s]] += s in put
rows = sorted(((sum(p)/len(p), vp[e]/hands[e], e) for e, p in pts.items() if len(p) >= 15 and hands[e] > 200), reverse=True)
n = len(rows); top = rows[:max(1, n // 5)]
print("bots", n, "| top-20% avg points", round(sum(r[0] for r in top)/len(top), 2), "VPIP", round(sum(r[1] for r in top)/len(top), 3))
print("field VPIP median", round(sorted(r[1] for r in rows)[n//2], 3))
for r in rows[:8]: print(round(r[0], 1), round(r[1], 3), names.get(r[2], r[2])[:30])
me = hdr["you"]; print("us", [(round(r[0],2), round(r[1],3)) for r in rows if r[2] == me])
