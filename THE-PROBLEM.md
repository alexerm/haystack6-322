# THE PROBLEM

The instance, its rules, and every bound anyone has established.

This document is self-contained. You do not need to read
[THE-MAP.md](THE-MAP.md) or know anything about Trackmania to work on it.

---

## 1. The instance

`data/graph.json` — a directed graph, 4 MB.

```
6,396 nodes · 34,007 edges · 323 group ids, of which 322 are claimable
```

```json
{"meta": {…},
 "nodes": [
   {"id": 0, "kind": "cp", "variant": "EndFW", "group": 1227757121, "groupSize": 21,
    "room": "23,4,24", "region": "spire", "pos": [762,144,777], "depth": 17},
   {"id": 100, "kind": "cp", "variant": "CP", "group": 2111633252, "groupSize": 3,
    "room": "HUB", "region": "hub", "pos": [739,116,778], "depth": 1}],
 "edges": [
   {"source": 26, "target": 89, "kind": "teleport", "forced": false, "region": "spire"},
   {"source": 1081, "target": 1087, "kind": "teleport", "forced": false, "region": "rooms"}]}
```

A node is one checkpoint box in the map, and this document says **box** and
**node** interchangeably. The fields that matter are `id`, `group` and the
`source`/`target` pair.
`variant`, `room`, `region`, `pos` and `depth` are there to help you reason and
carry no rule. Edge `kind` is `teleport` (33,814), `elevator` (120) or `fall`
(73); all three behave identically.

`data/facing.json` gives the authored horizontal facing of each spawn, read out
of the map's own data. Nothing in the rules uses it. It is published because it
is expensive to recover and someone modelling driving time will want it.

## 2. The rules

A route is a sequence of node ids. It is legal when:

1. **every step follows a directed edge of the graph;**
2. **the run begins at a `START` pit** (`variant == "START"`, four of them);
3. **the run ends by crossing the Finish** (`variant == "FINISH"`);
4. **no link group is ever claimed twice** — claiming any node claims every node
   sharing its `group`;
5. **a winning run claims all 322 groups.**

The Finish clears no group. That is why there are 323 group ids and 322
claimable groups, and why **a complete route is exactly 323 boxes** — the
`START` plus one box per group — so any repeat is a violation rather than a
detour (fact 128).

`verify/validate.ts` enforces exactly these five and nothing else. It is the
referee for any claim; §7 below.

## 3. Known bounds

**Best known: 321 of 322.** Nobody, human or solver, has produced a legal 322.

**The missing group is mobile.** Three refereed routes reach 321, each omitting
a *different* group (fact 111):

| route | omits |
|---|---|
| `routes/best-321-partial.json` | `1972812849` |
| `routes/best-321-alt.json` | `2102405473` |
| `routes/best-321-third.json` | `1055171169` |

Every pair of those three is jointly achievable with an explicit witness, and
all three together are achievable at 295 or above (fact 112). Over 216 complete
routes, every pair *and* every triple among the twelve most-missed groups is
claimed together by some route: zero never-co-claimed pairs, zero
never-co-claimed triples. `routes/best-315-partial.json` claims all twelve at
once. **So no group, pair or triple is the obstruction.** It is diffuse and it
lives in the routing.

**The union of every known route is INFEASIBLE** (fact 113). A 322 needs an edge
nobody has used yet.

**No route diverges from the 321 at or after step 171** (fact 110).

**In the game, a 322 certainly exists.** The author's validation run is embedded
in the released build as 323 waypoint timestamps (fact 132) — that is the map's
own data, and it settles the question for the map. **In this graph it is open.**
There is no proof in either direction. §4 is why that gap is not a formality.

### 3a. The sharpest statement of the wall

**A legal walk claiming all 322 groups exists. It is illegal by exactly one
duplicated group, and the duplicate cannot be excised** (fact 128).

Two of the 321s differ by two blocks that are edge-independent, so they compose:
insert one, delete the other, and you get a 324-entry walk that is
edge-legal from `START` to `FINISH` and claims 322 of 322. It violates one rule
— a single group claimed at two different steps. It is one box too long.

The excision is sealed exhaustively, not by search. Any bridge replacing a
removed copy must itself belong to the duplicated group, and of its 21 members
exactly one has both required edges at each site: 0 duplicate-free bridges. Nor
does any short contiguous rewrite fix it — 2,592 windows at half-width 35, zero
rewrites. This generalises: there are **52 such composites** over four
(gained, duplicated) pairs, giving 104 excision sites, and **not one has the
edge that would make the deletion legal** (fact 130).

### 3b. Why one-box repair is dead everywhere

**The graph has zero 2-path freedom.** Over 184,432 connected pairs of boxes,
*every single one* is joined by exactly one midpoint — no pair `(x,z)` admits
two distinct paths `x→y→z` (fact 129).

So swapping one box for another is impossible anywhere on this map, on any
walk, forever. The smallest repair primitive with any freedom is a 2-for-2 swap,
and 67.8% of length-3-connected pairs admit two or more length-3 walks. Neither
primitive pays the debt: over 757 near-miss walks, 1-for-1 offered 0 legal moves
and 2-for-2 offered 3,617 legal swaps with 0 wins.

**Do not run single-node insertion or node-for-node substitution on this map.**
It is dead by construction.

### 3c. Where the search has not been

Of the 21 members of `g1972812849`, only five appear in *any* of the 99 legal
walks on disk. **Sixteen have never been visited by any route this campaign
holds**, and 19 of the 21 have out-degree 4 or more (fact 130). The gap is not a
scarcity problem and it is not an exhausted one.

The only bridge to that group anywhere on disk is a single corridor,
`1861 → 1947 → 3044 → 1944`, whose second box is one the route already uses.
`1947` and `1944` compete for exactly the same six entry boxes.

## 4. How honest this instance is

**Read this before you model it.** The graph is derived from the map by rules,
and some of those rules were invented rather than read out of the game. Every
one was swept (fact 6):

| constant | value | status |
|---|---|---|
| `CELL` | 32 | the map's own lattice — not a choice |
| `SPAN` | 8 | invented, **inert** — identical edge set across 6–10 |
| `GOAL_AXIS` | 2 | invented, **inert** — identical edge set across 1–4 |
| `SURFACES_ON` | on | invented, **inert** — `off` gives a byte-identical edge set |
| `SPREAD` | 5 | invented, then pinned — the only integer the geometry permits |
| `FORCED_RADIUS` | 5 | invented, on the plateau [4.12, 6.08) with no data inside it |

The distances these thresholds compare against are **quantised** — a handful of
exact lattice values, not a continuum — so each constant sits on a plateau
rather than a slope. Nearest-box distances occur at 1.00, 1.41, 2.24, 3.61 and
4.12, then nothing until 6.08, so `FORCED_RADIUS = 5` sits in a 2 m gap with no
data in it. `SPREAD`'s plateau is [4.47, 5.10), floored by a
player-verified hub column and ceilinged by twelve same-height box pairs that
must not merge, which leaves 5 as the only integer available with 0.099 m of
headroom.

**And no setting opens a door into the trap.** Across every variation, the edges
added or removed touch the seven-group cluster the 315 never claims only six
times, and **not once as an entry from outside**. That cluster is not an
artifact of a guessed number.

**The caveat that remains.** `SPREAD = 5` over-merges one authored structure
inside its own plateau: `EndFW#7` at y=144 and `CP#104` at y=146 are 4.00 m
apart and are genuinely different shafts. `GOAL_AXIS` exists solely as a
hand-carved exception for that one case. The rule is right at 4.47 m and wider
and wrong at 4.00 m, and the fix was a special case rather than a better rule.

If a 322 turns out not to exist in this graph, that is where to look first.

## 5. What the wall looks like

**It is a budget, not a conflict** (fact 131). Measured over 201 distinct legal
routes, the "hard five" are the contested triple `{1972812849, 2102405473,
1055171169}` — abundant by membership at 21, 21 and 20 — plus the
member-scarce pair `{1055171172 (4 members), 1399226756 (3)}`. The staircase:

| demand | best route |
|---|---|
| 2 of the triple | **321** |
| all 3 of the triple | **320** (99 routes do; none higher) |
| all five | **319** (48 routes do) |

Every 4-subset of the five is jointly claimable, so there is no exclusion at any
fixed set size — only a constant −1 per added demand. And the payment does not
localise: among triple-claimers, the omission scatters across at least thirteen
different abundant groups. **"Find the region where the cost concentrates" has
the answer: none.**

**Solutions are abundant, not rare.** The route space is about 10^1076
candidates and roughly 10^234 physically walkable length-322 walks; the expected
number of valid routes is about 10^107 (fact 18, fact 19). The expectation is
carried by rare branches while the typical branch dies at k = 268 — expected
fresh exits are `5.317 × (322−k)/322`, which crosses 1 there (fact 12). **That,
not scarcity, is why forward search fails.**

**A group order determines the box path.** From any box, 99.32% of the time a
given successor group contains exactly one reachable box (fact 23). So ordering
the groups is the real problem; choosing members is almost never a free
variable.

**There is no waist to meet at.** The set of boxes reaching the Finish in
exactly `j` steps is 1, 4, 4, 8 … for small `j` and then **6,310 for every `j`
from 50 to 322**. Meet-in-the-middle has no cheap join (fact 33).

**A verdict arrives in under two seconds or never** (fact 84). Over the
campaign's first 259 runs, 59 of the 60 conclusive results returned in under
2 s and not one ever exceeded 120 s, while 33 thread-hours produced nothing.
Everything conclusive here is decided in presolve, and presolve does not get
smarter with time — it gets smarter with constraints. **Budget distinct probes,
not duration.**

## 6. What has been ruled out

Do not spend compute on these; each was closed by measurement, not opinion.

- **Single-box substitution and single-node insertion** — impossible on this
  graph (fact 129, §3b).
- **Composing routes already on disk** — the census is complete and returns
  zero over all 8,372 ordered pairs of the 92 best walks (fact 130).
- **Meet-in-the-middle** — no waist (fact 33).
- **Symmetry folding** — the box layout is 180°-rotationally symmetric but the
  grouping ignores that symmetry, so it buys nothing (fact 11).
- **Long solver runs** — a verdict comes fast or not at all (fact 84).
- **Raw throughput** — unpruned search saturates by 10^7 expansions; the next
  tenfold bought nothing and 10^8 was fractionally worse. The algorithm is
  wrong, not slow (fact 22).

## 7. Submitting a claim

```bash
./verify/check.sh                                  # confirm this repo's own data first
bun verify/validate.ts my-route.json               # or:
node --experimental-strip-types verify/validate.ts my-route.json
```

Accepted route shapes are `{"route": [{"cp": <id>}, …]}` and
`{"steps": [{"exit": {"cp": <id>}}, …]}`.

Exit **0** complete · **1** legal but partial · **2** illegal.

**A 322 claim is a route file plus exit code 0. Nothing else is a claim.** The
referee shares no code with any solver, deliberately, so a solver's own
bookkeeping bug cannot hide behind agreeing with itself.

## 8. Starting from where this left off

[`solve/`](solve) holds the CP-SAT model of record, which reproduces the 321
from a warm start, and `mine_routes.py`, which ranks routes by edges no known
route uses. [`archive/`](archive) is the 132-route pool that novelty is measured
against; all 132 are refereed. Read [solve/README.md](solve/README.md) before
running anything, and §6 above before choosing what to run.

---

[THE-CAMPAIGN.md](THE-CAMPAIGN.md) is what was tried and what died.
[FACTS.md](FACTS.md) holds the evidence behind every numbered claim above.
