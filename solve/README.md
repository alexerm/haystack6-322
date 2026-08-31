# Solvers

What was actually run. These reproduce the 321; none of them has ever produced
a 322.

Read [THE-CAMPAIGN.md](../THE-CAMPAIGN.md) before spending real compute here.
Its central finding is that **hardness is conserved across every
reformulation** — the box model, the restricted-case model and the
group-quotient model all wall in the same place — so re-encoding the problem is
the one move already known not to work.

## The model of record

`solve_cpsat_map.py` (Python, needs `ortools`). One global circuit over the real
graph: a self-loop per node meaning "not selected", a virtual depot closing the
tour, and one at-most-one constraint per link group. 40,017 booleans.

```bash
pip install ortools

# reproduce the incumbent: warm-start from a known route and maximise
python3 solve/solve_cpsat_map.py --hint routes/best-321-partial.json --max \
    --time 120 --workers 4 --all-different-circuit --probing-level 0 \
    --out my-route.json

# then referee it — the solver's own report is not a claim
bun verify/validate.ts my-route.json
```

That run reaches **FEASIBLE, 321/322** in 120 s on four workers, and the referee
confirms 322 steps missing group `1972812849`.

**Those two flags matter more than anything else you will tune.** On a
40,000-boolean circuit, `--all-different-circuit` and `--probing-level 0` are
the difference between the configuration that found the 319 and the 321 and
OR-Tools' defaults, which did not.

`run_cpsat_circuit.mjs` (Node, no dependencies beyond `node:fs`) is the
standalone version of the same model, and it is the one that actually produced
the 319 and then the 321.

```bash
node solve/run_cpsat_circuit.mjs data/graph.json out.json 600 1
```

A cold free solve is **expected to return UNKNOWN**. Fact 84: on this instance a
verdict arrives in under two seconds or never, and no verdict has ever exceeded
120 s. Long runs buy nothing. Budget distinct probes, not seconds.

## Ranking routes by novelty

`mine_routes.py` (Python, standard library only). This is the tool
[THE-CAMPAIGN.md](../THE-CAMPAIGN.md) §4 tells you to use, and running it makes
the point better than the prose does:

```bash
python3 solve/mine_routes.py --min 315
```

```
score  omits                      novelE novelB  file
  321  2102405473                      7      3  routes/best-321-alt.json
  321  1055171169                      7      3  routes/best-321-third.json
  321  1972812849                      0      0  routes/best-321-partial.json
  320  1055171169,1875528577          11      5  routes/best-320-contested.json
```

`novelE` is edges the route uses that appear nowhere in `archive/`. **The best
route by score carries zero of them, and a 320 carries eleven.** Since the union
of every known route is INFEASIBLE (fact 113), a 322 needs edges outside that
pool, so the bottom of this table is worth more than the top.

Point `--peer` at a larger pool as you collect one.

## Flags worth knowing on `solve_cpsat_map.py`

| flag | what it does |
|---|---|
| `--hint <route.json>` | warm-start from a known route |
| `--max` | maximise groups claimed instead of demanding all 322 |
| `--min-score N` | require at least N groups |
| `--require-groups g1,g2` | force specific groups to be claimed |
| `--require-nodes id1,id2` | force specific boxes into the route |
| `--ban-nodes id,id` | forbid boxes |
| `--repair K` | freeze the hint's first K steps and re-solve the rest |
| `--focus g1,g2` / `--focus-bonus B` | the cumulative-union recombination objective |

**A hint that contradicts its own constraints is silently discarded.** Six lanes
once ran cold for an hour because each demanded a group its own hint did not
claim. If a run is much slower than expected, check that first.

## What is not here

The recombination driver and the group-quotient master are not shipped. They are
the reformulations that walled, and their value is the conclusion already
recorded in [THE-CAMPAIGN.md](../THE-CAMPAIGN.md) rather than the code.

`--skeleton` is documented in the script but cannot run: it needs a
per-position candidate table derived from the author's split times, and that
table prunes the middle of the route by about 1% (6,368 candidates down to
6,309) for 7 MB. The splits themselves are in
[`data/author-waypoints.json`](../data/author-waypoints.json) if you want to
model timing yourself.
