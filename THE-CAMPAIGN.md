# THE CAMPAIGN

What was tried against Haystack 6, what died, and the four findings that reverse
an instinct.

Six weeks of work, no 322. This document exists so the next person spends their
compute somewhere new. You do not need [THE-MAP.md](THE-MAP.md) to read it;
[THE-PROBLEM.md](THE-PROBLEM.md) has the instance if you want to start work.

---

## 1. What was attempted

Verdicts: **DEAD** proven closed · **UNKNOWN** no verdict · **INSIGHT** no route
but something learned.

| experiment | verdict | takeaway |
|---|---|---|
| Free CP-SAT, GLKH and GLNS solves | UNKNOWN | all wall at 315, all missing the same 7 groups |
| Large-neighbourhood search and hinted runs | UNKNOWN | never beats the free solve |
| Oracle-guided DFS on a hand-walked pocket | DEAD | positions 152–153 dead by exhaustion; the wrong turn is earlier |
| Calibration ladder against restricted windows | INSIGHT | the solver closes 150 groups free in 14 s — hardness is the search economy, not the depth |
| Complete depth-6 opening partition, 3,048 openings raced | DEAD | exhaustive opening coverage is *worse per expansion* than random restarts. The opening is not the bottleneck |
| Room-peeling ladder, K = 3…12 | DEAD/UNKNOWN | tight variants refute instantly, the rest never resolve |
| GBX forensics — chronology, ids, orientation, clips | INSIGHT | the author's route is not recoverable from the file |
| Drop-one-scarce atlas, 16 probes | UNKNOWN | no single lock is the bottleneck |
| Group-quotient reformulation (groups as nodes) | INSIGHT | 322 nodes, 28,366 arcs, ~95% of group triples dead. **All three encodings wall in the same place** |
| Two-level method: lift a group order to a box path | DEAD | 103 complete group orders, **0 lifted**, all dying at layer 1–3 |
| Plateau measurement across the whole fleet, 12 h budgets | INSIGHT | best physically-threaded route 156/322; repair solvers stick near half |
| Cumulative-union recombination | **best result** | 315 → 319 → 321 in a single day |
| Contiguous window repair, exhaustive to width 52 | DEAD | exhausted on five route families |
| Composition of every route pair on disk | DEAD | complete census, 8,372 ordered pairs, **zero** |

## 2. How the incumbent moved, and where it stopped

On 2026-08-08 the best route went **315 → 319 → 321** in a single day, every
step refereed against the graph. Then it stopped, and six weeks of further
compute has not moved it.

The method that produced it is cumulative-union recombination: a
cardinality-dominant objective, warm-started from the incumbent, with every
round's omissions added to a growing focus set — and one rule doing the real
work. **Any result is kept if it scored higher *or* tied while carrying more of
the focus set.** That sideways rule is the engine, because an equal-scoring
route that swaps a hard group starts the next round in a different basin.

## 3. Four theories that died

**The scarce-pair obstruction.** The idea: two member-scarce groups conflict,
and that conflict is the wall. Killed by the census — every pair and every
triple among the twelve most-missed groups is claimed together by some route,
and one 315 claims all twelve at once (fact 112).

**The single-group blocker.** The idea: one group is structurally impossible
late in a route. Killed by three refereed 321s omitting three *different* groups
(fact 111). The omission is mobile.

**The group-exclusion account.** The retreat position: if not one group, then
some *set* of groups is jointly unachievable. Killed the same way — every pair
of the three is jointly achievable with an explicit witness, and all three
together are achievable at 295 or above (fact 112).

**Score as value.** The idea: rank routes by groups claimed. Killed twice. The
search reaches high scores by *skipping* the hard groups — over 334,000 deep
dives, the median high-scoring route claims two of the eight structurally forced
groups, and seven or eight is claimed **never** (fact 74). And separately, the
union of all 137 known routes is INFEASIBLE (fact 113), so a route sitting
inside the known pool has no path to 322 no matter what it scores.

## 4. The findings that reverse an instinct

These four are the reason to publish. Each one is the opposite of what the
obvious move suggests.

### Optimise novelty, not score

A 322 needs edges no route has used (fact 113). So the quantity worth
maximising is edges outside the known pool, and score is a poor proxy for it:

```
the three 321s                     0-7 novel edges  (some lie ENTIRELY inside the known pool)
320s from the recombination lane  30-32 novel edges, 17-19 novel boxes
```

**A 320 reaching thirty edges beyond the known world is worth more than a 321
sitting inside it.** During the campaign the most valuable lane was killed for
scoring 320 while producing three times the novelty of the 321s preferred over
it. Rank and seed lanes by novelty.

### A verdict arrives in under two seconds or never

Over the first 259 runs: 60 conclusive, **59 of those 60 returned in under two
seconds**, no verdict ever exceeded 120 s — and **33 thread-hours went into runs
that returned nothing** (fact 84). One exploration class reached 124 runs and 0
verdicts before anyone noticed.

Everything conclusive here is decided in presolve, and presolve gets stronger
with constraints rather than with seconds. **Budget distinct probes, not
duration.** The aggregate is invisible in any single log — every run looks
reasonable on its own — which is why it went unnoticed for so long.

### The model is not the bottleneck

The box model, the restricted-case model and the group-quotient model all wall
in the same place. Hardness is conserved across every reformulation; it lives in
the conjunction of ordering and box-consistency, and it follows the problem into
each new encoding. Raw throughput does not help either: unpruned search
saturates by 10^7 expansions and the next tenfold bought nothing, with 10^8
fractionally *worse* (fact 22). **The algorithm is wrong, not slow.**

### The search is walking a corridor, not exploring a tree

Splitting a stuck region on its most constrained open group and recursing went
nine levels deep in 29 probes, and **every level had exactly one surviving
child**, the rest INFEASIBLE in under a second. That is a consequence of a group
order determining the box path (fact 23): forcing the scarce groups one at a
time leaves exactly one viable member each time.

## 5. The one shape all four mistakes shared

Recorded because it repeated and cost more than any single bug.

1. A divergence ladder's covering claim was false — the encoding banned a box
   everywhere when the argument needed it banned only as a first step, so
   "every slice INFEASIBLE" proved nothing (fact 106). Each individual
   INFEASIBLE was still true.
2. Proof counts were read off a file listing three times instead of off the
   graph, wrong in both directions at once (fact 110).
3. Six search lanes ran cold for an hour because every lane demanded a group
   its own hint did not claim, so the solver discarded the hint. A valid parent
   reached 319 in one second; the cold lanes needed thirteen minutes to reach
   305.
4. The most valuable lane was killed for scoring 320 while producing three
   times the novelty of the 321s preferred over it.

Every one is the same error: **assuming a property instead of measuring it** —
that the slices covered, that the counts were complete, that the hints applied,
that the score tracked value. On this instance the measurement is nearly always
a cheap graph query, and it nearly always disagrees.

## 6. Where the wall actually is

Two results locate it better than anything else here.

**A walk claiming all 322 groups exists** — edge-legal from `START` to `FINISH`,
324 entries, violating exactly one rule by claiming one group twice. Across all
52 such composites there are 104 excision sites and **not one has the edge that
would make the deletion legal** (fact 128, fact 130).

**The graph has zero 2-path freedom** — of 184,432 connected box pairs, every
one is joined by exactly one midpoint (fact 129). So one-box substitution is
impossible anywhere on this map, and the smallest repair primitive with any
freedom at all is a 2-for-2 swap.

Between them: the answer is one box away, and the one-box move does not exist.

## 7. What a fresh attempt should try first

Two methods were designed during the campaign and never started. Both are
better bets than more of what was already run.

**Exact decomposition by graph cuts.** The map is spatial, so the graph should
have small edge cuts — narrow passages few edges cross. A route crosses any cut
a bounded number of times, so a k-edge cut turns the global problem into an
enumeration over crossing patterns, each case a smaller exact solve. Compute
minimum cuts separating the unexplored region from the explored one, and each
hard group's member region from the rest. **This is the only candidate that can
end the question in either direction** — a 322, or a completed impossibility
proof.

**The per-entry-box novelty sweep.** 113 of `g1972812849`'s 117 entry boxes lie
on no route ever produced, and 16 of its 21 members have never been visited
(fact 130). That turns "explore the dark territory" into 113 decidable
questions: for each unvisited entry box, require it and maximise. Each run
either produces a high scorer through dark territory or prunes that box from
every future 322. The runs are independent, so this parallelises freely — but
the cut analysis should choose the territory first. This is the workhorse, not
the compass.

**One more thing worth doing that is not compute.** unbeaten.at's $200 bounty on
this map has a discussion thread. Bounty hunters may hold partial routes nobody
has published, and partial routes are exactly the recombination fuel this
campaign ran short of.

---

[THE-PROBLEM.md](THE-PROBLEM.md) is the instance and its rules.
[FACTS.md](FACTS.md) holds the evidence behind every numbered claim above.
