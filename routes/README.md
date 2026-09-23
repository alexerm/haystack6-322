# Routes

Every route here has been checked, edge by edge, by the independent referee
`verify/validate.ts` against `../data/graph.json`. Nothing goes in on a solver's
say-so — only what the referee confirms is a legal walk: every step a real
directed edge, starting at a `START` pit, ending at the Finish, no group claimed
twice.

**Re-validate before trusting any of them:**

```bash
./verify/check.sh                                # all eight at once
bun verify/validate.ts routes/best-321-partial.json
```

Exit **0** complete winner · **1** legal but partial · **2** illegal.

## The finished route

| file | player | time | steps | groups |
|---|---|---|---|---|
| [`finish-322-kattz95.json`](finish-322-kattz95.json) | Kattz95 | 15:04.135 | 323 | **322 / 322**, exit 0 |
| [`finish-322-ciryll.json`](finish-322-ciryll.json) | Ciryll | 16:21.645 | 323 | **322 / 322**, exit 0 |

Both files hold **the same 323 boxes in the same order** (fact 134). They are
kept apart because each carries its own driver's timing: `t` is the millisecond
each claim registered, and `d` is the distance from the car to the matched box.
The route was read out of the leaderboard ghost named in each file's `meta`,
and the graph's edges were never consulted (fact 133).

## Solver routes

None of these is a winner. Each returns exit 1.

| file | steps | groups | omits |
|---|---|---|---|
| [`best-321-partial.json`](best-321-partial.json) | 322 | **321 / 322** | `1972812849` |
| [`best-321-alt.json`](best-321-alt.json) | 322 | **321 / 322** | `2102405473` |
| [`best-321-third.json`](best-321-third.json) | 322 | **321 / 322** | `1055171169` |
| [`best-320-contested.json`](best-320-contested.json) | 321 | 320 / 322 | `1875528577`, `1055171169` |
| [`best-319-partial.json`](best-319-partial.json) | 320 | 319 / 322 | `1055171172`, `1399226756`, `1867416289` |
| [`best-315-partial.json`](best-315-partial.json) | 316 | 315 / 322 | seven abundant groups: `1038983089`, `1404196129`, `1664870129`, `1949788289`, `1975919425`, `2035648737`, `2133528401` |

**The three 321s omit three different groups, and that is the point.** Each
claims the two the other two cannot, so every pair of those groups is jointly
achievable with an explicit witness, and no group, pair or triple explains the
one-group wall (fact 111, fact 112).

`best-320-contested` is the intermediate that broke the 319 ceiling for routes
claiming `1972812849`. `best-321-alt` and `best-321-third` came from
cumulative-union recombination on 2026-08-09.

**Rank these by novelty, not by score.** The union of every solver route is
INFEASIBLE (fact 113), so a 322 needs edges no solver route has — and some of
these 321s lie entirely inside the pool already explored, while a 320 from the
recombination lane carries thirty edges beyond it. The finished route carries
288 (fact 135).
[THE-CAMPAIGN.md](../THE-CAMPAIGN.md) §4 has the numbers.

## Format

Two shapes are accepted, and these files use the first. Fields beyond `cp` are
for reading and the referee ignores them:

```json
{"route": [{"cp": 28}, {"cp": 101}, …]}
{"steps": [{"exit": {"cp": 28}}, …]}
```
