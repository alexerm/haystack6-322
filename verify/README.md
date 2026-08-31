# The referee

`validate.ts` re-reads the graph and checks the rules from scratch. It
**deliberately shares no code with any solver**, so a bug in a solver's own
bookkeeping — or in how it extracts a tour from its model — cannot hide behind
agreeing with itself. Every route in `routes/` went through it before it was
committed.

It has no dependencies. It imports `node:fs` and nothing else.

## Running it

```bash
./verify/check.sh                                    # re-validate every route in this repo
RUNNER="node --experimental-strip-types" ./verify/check.sh   # under Node instead of Bun

bun verify/validate.ts routes/best-321-partial.json
node --experimental-strip-types verify/validate.ts my-route.json
bun verify/validate.ts my-route.json --graph some-other-graph.json
```

`check.sh` also confirms that every `fact N` cited by a document exists in
`FACTS.md`. It exits 0 only when everything passes.

## The rules it enforces

1. Every step follows a directed edge of the graph.
2. The run begins at a `START` pit.
3. The run ends by crossing the Finish.
4. No link group is ever claimed twice.
5. A winning run claims all 322 groups.

The Finish clears no group, so it is not one of the 322.

## Route format

Either shape is accepted:

```json
{"route": [{"cp": 28}, {"cp": 101}, …]}
{"steps": [{"exit": {"cp": 28}}, …]}
```

Each `cp` is a node `id` from `data/graph.json`.

## What counts as a claim

| exit | meaning |
|---|---|
| **0** | complete — all 322 groups claimed, legally |
| **1** | legal, but partial |
| **2** | illegal — a broken edge, a repeated group, or an unknown checkpoint |

**A 322 claim is a route file plus exit code 0. Nothing else is a claim.**

On failure the referee names the step, the two checkpoints involved, and — when
the reverse edge exists but the forward one does not — says the direction is
flipped. Direction is the whole point: a route that reads fine backwards is
still not drivable.
