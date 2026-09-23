# haystack6-322

**[Haystack 6](https://trackmania.exchange/maps/323677)** by **FruitSesh** is a
Trackmania 2020 map with 6,396 checkpoints collapsing into **322 link groups**.
Its leaderboard stayed empty for three months after release. Then two players
finished it within two days, and both drove **the same route**:

| player | time | set | respawns |
|---|---|---|---|
| Kattz95 | **15:04.135** | 2026-09-08 | 317 |
| Ciryll | 16:21.645 | 2026-09-06 | 326 |

Kattz95's run is 7.5 s under the 15:11.615 author time. The author's own
validation run is a third complete run, embedded in the released map as 323
split times, and it takes a different route.

This repo is the map as a graph, the finished route refereed against it, and a
six-week solver campaign that reached 321 of 322 and no further.

![The endgame conveyor: 24 doors, 8 chains, one finish](viz/endgame-conveyor.png)

*The endgame. [viz/](viz) has two more: the five kinds of room beside their
graphs, and the contested corridor that is the wall.*

## What the finish settled

> **Claim all 322 link groups in one run, then cross the Finish.**

- **A 322 exists in this graph.** Both finished runs pass the referee with exit
  0. The route was read out of the players' ghosts without consulting a single
  edge, so the verdict also checks the graph: all 322 moves are edges it
  already had.
- **No solver found it.** The campaign's best is **321 of 322**, from three
  routes that each omit a different group. The finished route differs from all
  of them at the first step: it begins at `START#29`, and all 138 solver routes
  here begin at `START#28`.
- **The finished route lies almost entirely outside the solver pool.** 288 of
  its 322 edges and 255 of its 323 boxes appear in none of the 138 solver
  routes (fact 135). The campaign bet that a 322 needs edges nobody had used.
  It needed hundreds.

## What is still open

- **Can a solver find a 322 unaided?** Every method in
  [THE-CAMPAIGN.md](THE-CAMPAIGN.md) stopped at 321. The instance now has a
  known solution to measure a solver against.
- **Is there a faster route?** Both leaderboard runs drive one route, and the
  author drove another. Only the author's split times survive, not the boxes
  (fact 79).

## Three ways in

| you want to | read |
|---|---|
| drive the map, and know how it works | **[THE-MAP.md](THE-MAP.md)** |
| solve it as a routing instance | **[THE-PROBLEM.md](THE-PROBLEM.md)** |
| know what was already tried, and what died | **[THE-CAMPAIGN.md](THE-CAMPAIGN.md)** |

Four interactive viewers are at **https://alexerm.github.io/haystack6-322/**.
Two of them draw any route file, the finished route included.

[FACTS.md](FACTS.md) is the register those three cite. Each numbered row is a
finding that was measured or observed rather than argued; the documents cite a
row instead of restating it.

## What is here

```
data/graph.json            6,396 nodes · 34,007 edges · 323 group ids, 322 claimable
data/facing.json           the authored spawn facing of every checkpoint
data/spire.json            the endgame conveyor as its own graph
data/author-waypoints.json the author's 323 split times, from the released map
routes/                    the finished 322 from both ghosts, and six solver routes, 315 to 321
viz/                       figures, and the script that proves they match the data
archive/                   the 132-route known pool that "novel" is measured against
solve/                     the CP-SAT model that reaches 321, and the novelty ranker
verify/                    the referee, and how to submit a claim
```

Each directory has its own README.

## Checking a route

```bash
./verify/check.sh                                    # re-validate everything here
bun verify/validate.ts my-route.json                 # or:
node --experimental-strip-types verify/validate.ts my-route.json
```

Exit **0** complete · **1** legal but partial · **2** illegal. **A 322 claim is
a route file plus exit code 0. Nothing else is a claim.**

No dependencies, no build step. The referee needs only Bun or Node 22.6+.

## Reproducing the 321

```bash
pip install ortools
python3 solve/solve_cpsat_map.py --hint routes/best-321-partial.json --max \
    --time 120 --workers 4 --all-different-circuit --probing-level 0 --out mine.json
bun verify/validate.ts mine.json
```

Reaches FEASIBLE at 321/322 in 120 s on four workers. Those two solver flags are
the difference between the configuration that found the 321 and OR-Tools'
defaults, which did not. [solve/README.md](solve/README.md) has the rest.

## Credit and licence

The map is **Haystack 6 by FruitSesh**, TMX 323677. It is not redistributed
here; the graph is data derived from it.

`verify/` is MIT ([LICENSE](LICENSE)). The data, the routes and these documents
are CC-BY-4.0 ([LICENSE-DATA](LICENSE-DATA)).
