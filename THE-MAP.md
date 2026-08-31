# THE MAP

How Haystack 6 works, for someone who wants to drive it.

This document assumes you play Trackmania and have never modelled the map. You
do not need [THE-PROBLEM.md](THE-PROBLEM.md) to read it.

---

## 1. What the map is

[Haystack 6](https://trackmania.exchange/maps/323677) by **FruitSesh** looks
like a mountain of inflatable mats. It is not a driving challenge and it is not
a track-building puzzle. Parsing the file shows where the map actually lives:

| | count | role |
|---|---|---|
| blocks | 8,344 | two kinds only, floor and grass remover — pure scenery |
| items | 52,616 | the haystack: mats and tubes, decoration |
| **checkpoint boxes** | **6,396** | the puzzle |

Every one of those 6,396 boxes is a checkpoint you can drive into. The author
time is 15:11.615. Nobody has ever finished it: no record on Nadeo's
leaderboard, and on TMX no replay, no award and no world record (fact 132,
re-checked 2026-08-31). There is a standing $200 bounty for beating the author
time, sponsored by Wizord.tv.

One person has completed it: FruitSesh, validating the build before release.
The 323 waypoint timestamps from that run are embedded in the released map, and
they prove a complete route exists on exactly this build (fact 132). The run
is execution, not exploration — 323 moves in 911 seconds, speeding up 8% from
start to finish. He knew the route before he drove it
(fact 17).

## 2. The mechanic — you do not drive from box to box, you are teleported

The rule the whole map is built on:

> **You always respawn at the exact checkpoint box you physically touched.**

So drive into a box, then respawn. You do not reappear where you were. You
reappear at *that box's* spawn point, which is somewhere else entirely.

The offset is baked into each box's item file, and the variant name is the only
thing that distinguishes them — the meshes are identical:

| variant | where it sends you |
|---|---|
| `FW` | one room forward |
| `FWSide` | forward and sideways |
| `Up` | up one floor |
| `Down` | down one floor |
| `_U` | a small lift, 7 m, same room |
| `A`–`H` | a long portal jump out of the hub |
| `START` | drops you from the spawn platform into the hub |
| `End*`, plain `CP` | roughly in place — **these are the traps** |

Pick the wrong box and you are thrown into the hay with nothing gained. Pick
the right one and you advance one step. That is the entire game.

## 3. The lattice — 1,176 rooms on a 32 m grid

Sliced by height, the boxes sit on **six floors** at y = 64, 96, 128, 160, 192
and 224, about 1,000 boxes each. Within a floor they repeat in a square
formation, one cluster per 32 m cell.

So the world is a 3-D grid of **1,176 rooms**, and `room = floor(position / 32)`
on each axis. Each room holds a square of mixed box types. A room is the unit
you think in: you arrive in one, and the boxes there are your menu.

## 4. Link groups — why this is a routing puzzle and not a tour

This is the one idea to hold on to.

Of the 6,396 boxes, 6,395 carry a `LinkedCheckpoint` property, and those
collapse into **322 distinct link ids**. In Trackmania, linked checkpoints that
share an id count as a single checkpoint: **touching any one member clears the
whole group.**

So the win condition is not "visit 6,395 boxes". It is:

> **Clear all 322 groups, then reach the Goal.**

Group sizes run from 2 members to 23. That is what makes this hard. Every step
is a choice of *which member* of a group to spend, and spending the wrong
member puts you in the wrong room for everything after it. The author time of
911.6 s over 322 groups is about 2.8 s per group, which is exactly the cost of
one respawn — so the intended run wastes almost nothing.

The route shape, measured: 1 `START` + 3 hub + 307 floor steps + 11 spire +
Finish = 323 steps (fact 20). The opening and the last twelve steps are nearly
forced. **All the difficulty is in the 307 middle steps**, where the average
room offers 5.369 onward moves.

## 5. Forced landings — most of the map is not a choice

You materialise at an exact point. If a box happens to sit on that point, you
drive into it whether you meant to or not. It becomes your only successor, and
the room's other boxes are unreachable until it has fired.

This is containment, not proximity: the spawn puts the car *inside* the box
holding the next checkpoint, which fires on landing (fact 7). It is geometric
and rare — 119 of 6,299 landings — but where it happens it removes the choice
entirely.

The archetype is a `_U` room. The `_U` sits at the room centre, 1 m above the
deck, and every gate landing in the room drops you within 4.1 m of it. So
entering a `_U` room forces the `_U`, it lifts you 7 m, and only *then* do you
choose a pit.

## 6. The start and the hub

**The start chamber** sits at (768, 768) at y = 160. Four `START` pits stand in
a diamond around the spawn gate. The opening is a choice of one of four, and it
is fully symmetric: all four drop you on the hub, and each burns its own
group's two portals, leaving six usable portals whichever you pick (fact 3).

**The hub** is one drivable platform, four cells wide, at y ≈ 115. It carries 24
boxes in eight stations, arranged as an octagon. Each station is a column of
three:

```
  CP @116     a small group, 3-4 members
  CP @115     a large group, 20-23 members
  portal@114  A-H — the gate that teleports you out
```

You drive off the platform edge, fall through both checkpoints, and land on the
portal. **The portals are the only way out**, and all eight land on floor 2. So
one hub visit claims three groups and ejects you.

## 7. The endgame — the Spire

Verified in game on 2026-07-22. Everything below is what the map does, not what
a model predicts.

**The endgame is a conveyor. You choose where to get on, and after that nothing
is a choice until you cross the finish line.**

```
  24 doors  ────►  8 chain heads  ────►  1 Finish

  head → ring → ring → corner → vertical ─┐
                                           ├─ 5 shared middle → CP#104 → FINISH
  head → ring → ring → corner → vertical ─┘
```

62 nodes, 61 edges. Exactly eight have nothing feeding them; exactly one has no
way onward. Every chain is twelve boxes long.

**Three platforms.** The Spire occupies the 2×2 room block at x, z ∈ [736, 800)
— the only place on the map where the one-pit-per-room pattern breaks. The
upper deck sits at y = 167, the middle at y = 143, the lower at y = 135. Upper
and lower are exact mirrors: landing on one or the other makes no difference to
what you can reach.

**Getting on.** 24 checkpoints outside the Spire teleport you onto a deck — 12
onto the upper, 12 onto the lower. Each door drops you 1.0–4.1 m from a ring
cell, inside the forced-landing radius, so the entry is forced like every other
step. And every one of the 24 lands on a **chain head**, the far end of a run,
never part-way along. Three doors per head, eight heads, perfectly symmetric.

**The trap.** The four `START` pits sit at the upper ring height, so anything
that picks entries by height sweeps them in. Driving into one respawns you at
y = 115 on the hub deck — straight back out of the Spire. They are not entries.

**After that it is forced.** Every respawn drops you inside a box sealed on all
sides by mats, so you take its checkpoint on landing, which respawns you again.
Across all 61 steps the true successor sits 1.0–5.1 m away and the next nearest
candidate is at least 6.1 m. There is no ambiguity anywhere and no step where
you get to steer.

**What it costs.** The Spire holds 66 boxes in 49 groups, but one visit claims
only 11 groups plus the goal, and you get exactly one visit. So the endgame is
**not** a coverage bottleneck and the choice of chain is close to free.

## 8. The one structural fact a router can use

`g67` — whose only member is `CP#104` — exists nowhere else on the map, and all
eight chains pass through it. There is exactly one edge into the Finish on the
whole map.

So **`g67` is provably the last group of any valid route.** Whatever else you
work out, you know where it ends.

---

Next: [THE-PROBLEM.md](THE-PROBLEM.md) states the map as a graph, with the best
route anyone has found. [FACTS.md](FACTS.md) is the evidence behind every
numbered claim above.
