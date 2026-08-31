# The known pool

132 routes produced during the campaign. **This is not a highlights reel.** It
is the pool that "novel" is measured against, and it exists so that a new route
can be judged on what it brings rather than on what it scores.

| score | routes |
|---|---|
| 321 | 5 |
| 319 | 30 |
| 318 | 8 |
| 317 | 34 |
| 316 | 4 |
| 315 | 51 |

The six routes worth reading individually are in [`../routes/`](../routes),
with their omissions named.

## Why the pool matters more than any route in it

The exact circuit over the **union** of every route known — these plus the ones
in `routes/` — is INFEASIBLE (fact 113). So a 322 cannot be assembled from
edges that appear here. It needs edges nobody has used.

That makes this directory a measuring stick rather than a source of answers.
`solve/mine_routes.py` scores any route by how many of its edges appear nowhere
in this pool, and the result is the reason the campaign concluded that novelty
beats score: the best route by score carries **zero** novel edges, while a
lower-scoring one carries eleven.

```bash
python3 solve/mine_routes.py --min 315
```

## Format

Plain text, two lines. The first is the number of groups claimed. The second is
the route as space-separated checkpoint ids, matching `id` in
[`../data/graph.json`](../data/graph.json).

```
315
28 101 94 85 575 1611 2711 ...
```

The filename carries the score and a hash of the route, so duplicates collapse
by name.

**All 132 have been refereed.** Every one is a legal walk, and every filename's
score matches the referee's own count of groups claimed. Re-check the whole
pool with `./verify/check.sh --archive`, or convert a single route by hand:

```bash
python3 -c "import json,sys; ids=open(sys.argv[1]).read().split()[1:]; \
  json.dump({'route':[{'cp':int(i)} for i in ids]}, open('/tmp/r.json','w'))" \
  archive/route-321-<hash>.txt
bun verify/validate.ts /tmp/r.json
```
