#!/usr/bin/env python3
# check_figures.py — prove the figures in viz/ still tell the truth.
#
# The three PNGs are drawn by hand, so nothing stops them drifting from the
# data except this file. Every structural claim any figure makes is asserted
# here against data/graph.json and data/spire.json. If a claim stops holding,
# this fails and the figure is wrong, not the data.
#
#   python3 viz/check_figures.py
#
# No dependencies.
import json, collections, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
G = json.loads((ROOT / "data/graph.json").read_text())
SP = json.loads((ROOT / "data/spire.json").read_text())

NODE = {n["id"]: n for n in G["nodes"]}
out, inn = collections.defaultdict(set), collections.defaultdict(set)
for e in G["edges"]:
    out[e["source"]].add(e["target"])
    inn[e["target"]].add(e["source"])

checks, failed = [], 0


def claim(figure, what, ok, detail=""):
    global failed
    checks.append((figure, what, ok, detail))
    if not ok:
        failed += 1


# ------------------------------------------------- contested-corridor.png
S = {862, 1861, 1939, 1950, 2024, 3044}
T = {1942, 1943, 1944, 1945, 1946, 1947}
claim("corridor", "1947 and 1944 have identical entries", inn[1947] == inn[1944] == S,
      f"in(1947)={sorted(inn[1947])}")
claim("corridor", "1861 and 3044 have identical exits", out[1861] == out[3044] == T,
      f"out(1861)={sorted(out[1861])}")
claim("corridor", "the 6x6 block is complete", all(t in out[s] for s in S for t in T))
claim("corridor", "1947 carries the group the best 321 omits",
      NODE[1947]["group"] == 1972812849, f"group={NODE[1947]['group']}")
claim("corridor", "1944 carries g1410852097", NODE[1944]["group"] == 1410852097)

# --------------------------------------------------- endgame-conveyor.png
ch = SP["chains"]
L = len(ch[0]["boxes"])
claim("conveyor", "8 chains", len(ch) == 8, f"{len(ch)}")
claim("conveyor", "every chain is 12 boxes", all(len(c["boxes"]) == L == 12 for c in ch))
distinct = [len({c["boxes"][k] for c in ch}) for k in range(L)]
claim("conveyor", "positions 1-5 are private to each chain", distinct[:5] == [8] * 5, f"{distinct}")
claim("conveyor", "positions 6-10 are shared by pairs", distinct[5:10] == [4] * 5, f"{distinct}")
claim("conveyor", "position 11 is CP#104 for all", distinct[10] == 1 and ch[0]["boxes"][10] == 104)
claim("conveyor", "position 12 is the Finish for all", distinct[11] == 1 and ch[0]["boxes"][11] == -1)
claim("conveyor", "62 distinct boxes", len({b for c in ch for b in c["boxes"]}) == 62)
doors = collections.Counter(e["target"] for e in SP["entries"])
claim("conveyor", "24 doors", len(SP["doors"]) == 24 and sum(doors.values()) == 24)
claim("conveyor", "3 doors per chain head, 8 heads",
      len(doors) == 8 and set(doors.values()) == {3}, f"{dict(doors)}")

# --------------------------------------------------------- room-kinds.png
rooms = collections.defaultdict(list)
for n in G["nodes"]:
    rooms[n["room"]].append(n)
claim("rooms", "1,178 rooms", len(rooms) == 1178, f"{len(rooms)}")

PIT = ("FW", "FWSide", "Up", "Down")
OFFSETS = {("FW", 1, 10), ("FW", -1, -10), ("FWSide", 10, 3),
           ("FWSide", -10, -3), ("Down", 7, -6), ("Up", -7, 6)}
std, same = 0, 0
for r, ns in rooms.items():
    pits = [n for n in ns if n["variant"] in PIT]
    if len(pits) != 6 or "," not in r:
        continue
    std += 1
    cx, _, cz = (int(v) for v in r.split(","))
    ox, oz = cx * 32 + 16, cz * 32 + 16
    got = {(p["variant"], p["pos"][0] - ox, p["pos"][2] - oz) for p in pits}
    if got == OFFSETS:
        same += 1
claim("rooms", "568 standard six-pit rooms", std == 568, f"{std}")
claim("rooms", "every one uses the identical six offsets", same == std, f"{same} of {std}")

us = [n for n in G["nodes"] if n["variant"] == "_U"]
claim("rooms", "18 lift rooms", len(us) == 18, f"{len(us)}")
claim("rooms", "a _U feeds every pit in its room",
      all(out[u["id"]] == {n["id"] for n in rooms[u["room"]] if n["variant"] in PIT} for u in us))

hub = [n for n in G["nodes"] if n["room"] == "HUB"]
lvl = lambda n: round(n["pos"][1])
portals = [n for n in hub if lvl(n) == 114]
# A station is authored by its fall edges, not by position: the portal sits
# 0-4.5 m horizontally from its checkpoints, which is the ballistic arc.
stations = []
for top in (n for n in hub if lvl(n) == 116):
    mid = [NODE[t] for t in out[top["id"]]]
    if len(mid) == 1 and lvl(mid[0]) == 115:
        bot = [NODE[t] for t in out[mid[0]["id"]]]
        if len(bot) == 1 and lvl(bot[0]) == 114:
            stations.append((top, mid[0], bot[0]))
claim("rooms", "24 hub boxes forming 8 columns of 3",
      len(hub) == 24 and len(stations) == 8,
      f"{len(hub)} boxes, {len(stations)} stations")
claim("rooms", "the portal sits within 4.5 m of its column (the ballistic arc)",
      all(max(abs(t["pos"][0]-b["pos"][0]), abs(t["pos"][2]-b["pos"][2])) <= 4.5
          for t, _, b in stations),
      str(sorted({round(max(abs(t["pos"][0]-b["pos"][0]), abs(t["pos"][2]-b["pos"][2])),1)
                  for t, _, b in stations})))
claim("rooms", "8 portals, each with 5 successors",
      len(portals) == 8 and all(len(out[p["id"]]) == 5 for p in portals))

starts = [n for n in G["nodes"] if n["variant"] == "START"]
claim("rooms", "4 START pits", len(starts) == 4)
claim("rooms", "each START shares its group with exactly 2 portals",
      all(sum(1 for p in portals if p["group"] == s["group"]) == 2 for s in starts))
claim("rooms", "all four STARTs land on the hub",
      all({NODE[t]["room"] for t in out[s["id"]]} == {"HUB"} for s in starts))

# --------------------------------------------------------------- report
fig = None
for f, what, ok, detail in checks:
    if f != fig:
        print(f"\n{f}")
        fig = f
    print(f"  {'ok  ' if ok else 'FAIL'} {what}" + (f"   [{detail}]" if detail and not ok else ""))
print(f"\n{len(checks) - failed}/{len(checks)} claims hold")
sys.exit(1 if failed else 0)
