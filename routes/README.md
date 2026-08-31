# Routes

Every route here has been checked, edge by edge, by the independent referee
`verify/validate.ts` against `../data/graph.json`. Nothing goes in on a solver's
say-so — only what the referee confirms is a legal walk: every step a real
directed edge, starting at a `START` pit, ending at the Finish, no group claimed
twice.

**Re-validate before trusting any of them:**

```bash
./verify/check.sh                                # all six at once
bun verify/validate.ts routes/best-321-partial.json
```

Exit **0** complete winner · **1** legal but partial · **2** illegal. Every file
below returns 1. None is a winner.

## Files

| file | steps | groups | omits |
|---|---|---|---|
| [`best-321-partial.json`](best-321-partial.json) | 322 | **321 / 322** | `1972812849` |
| [`best-321-alt.json`](best-321-alt.json) | 322 | **321 / 322** | `2102405473` |
| [`best-321-third.json`](best-321-third.json) | 322 | **321 / 322** | `1055171169` |
| [`best-320-contested.json`](best-320-contested.json) | 321 | 320 / 322 | `1875528577`, `1055171169` |
| [`best-319-partial.json`](best-319-partial.json) | 320 | 319 / 322 | `1055171172`, `1399226756`, `1867416289` |
| [`best-315-partial.json`](best-315-partial.json) | 316 | 315 / 322 | seven abundant groups |

**The three 321s omit three different groups, and that is the point.** Each
claims the two the other two cannot, so every pair of those groups is jointly
achievable with an explicit witness, and no group, pair or triple explains the
one-group wall (fact 111, fact 112).

`best-320-contested` is the intermediate that broke the 319 ceiling for routes
claiming `1972812849`. `best-321-alt` and `best-321-third` came from
cumulative-union recombination on 2026-08-09.

**Rank these by novelty, not by score.** The union of every known route is
INFEASIBLE (fact 113), so a 322 needs edges nobody has — and some of these 321s
lie entirely inside the pool already explored, while a 320 from the
recombination lane carries thirty edges beyond it.
[THE-CAMPAIGN.md](../THE-CAMPAIGN.md) §4 has the numbers.

## Format

Two shapes are accepted, and these files use the first:

```json
{"route": [{"cp": 28}, {"cp": 101}, …]}
{"steps": [{"exit": {"cp": 28}}, …]}
```
