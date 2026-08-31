#!/usr/bin/env python3
# mine_routes.py — the routes we already found and threw away.
#
# WHY THIS EXISTS. Every recombination round writes a route, and the driver
# keeps only what improves. But fact 111 is the whole lesson of the day: an
# equal-score route that omits a DIFFERENT group is not a duplicate, it is a
# different basin, and crossing basins is the only thing that has produced
# progress here. Those routes are sitting on disk unlabelled.
#
# Novelty is measured against the peer solver's 132-route archive, because that
# is the pool their bridge enumeration treats as known. A route matters to us
# in proportion to the edges it brings that nobody has seen — fact 113 says the
# union of everything known is INFEASIBLE, so a 322 needs edges outside it, and
# a new route that is a rearrangement inside the known pool adds nothing.
#
#   python3 solve/mine_routes.py [--min 320]
import argparse, collections, glob, hashlib, json, os

ap = argparse.ArgumentParser()
ap.add_argument("--graph", default="data/graph.json")
ap.add_argument("--peer", default="archive")
ap.add_argument("--min", type=int, default=320)
args = ap.parse_args()

G = json.load(open(args.graph))
grp = {n["id"]: n["group"] for n in G["nodes"]}
finish = next(n for n in G["nodes"] if n.get("variant") == "FINISH")["group"]
all_groups = {n["group"] for n in G["nodes"]} - {finish}

peer_edges, peer_boxes = set(), set()
for f in glob.glob(os.path.join(args.peer, "route-*.txt")):
    ids = [int(x) for x in open(f).read().split()[1:]]
    peer_boxes.update(ids)
    peer_edges.update(zip(ids, ids[1:]))

seen = {}
for f in glob.glob("routes/*.json"):
    try:
        d = json.load(open(f))
    except Exception:
        continue
    route = d.get("route")
    if not route:
        continue
    # route entries are dicts in our format; some peer/state files store bare ids
    try:
        ids = [s["cp"] if isinstance(s, dict) else int(s) for s in route]
    except (TypeError, ValueError, KeyError):
        continue
    claimed = {grp.get(i) for i in ids} - {finish, None}
    if len(claimed) < args.min:
        continue
    key = hashlib.sha256(",".join(map(str, ids)).encode()).hexdigest()[:12]
    if key in seen:
        continue
    edges = set(zip(ids, ids[1:]))
    seen[key] = {
        "score": len(claimed),
        "omits": tuple(sorted(all_groups - claimed)),
        "novel_edges": len(edges - peer_edges),
        "novel_boxes": len(set(ids) - peer_boxes),
        "file": f,
    }

hist = collections.Counter(v["score"] for v in seen.values())
print(f"distinct routes >= {args.min} on disk: "
      f"{dict(sorted(hist.items(), reverse=True))}")
by_omit = collections.defaultdict(list)
for v in seen.values():
    by_omit[v["omits"]].append(v)
print(f"distinct omission signatures: {len(by_omit)}\n")

print(f"{'score':>5}  {'omits':<26} {'novelE':>6} {'novelB':>6}  file")
for v in sorted(seen.values(), key=lambda v: (-v["score"], -v["novel_edges"])):
    print(f"{v['score']:>5}  {','.join(map(str, v['omits'])):<26} "
          f"{v['novel_edges']:>6} {v['novel_boxes']:>6}  {v['file']}")
