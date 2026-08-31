# Figures

Three pictures of the structures that decide this problem.

| figure | what it shows | used in |
|---|---|---|
| [`room-kinds.png`](room-kinds.png) | the five kinds of room, each drawn beside its graph | [THE-MAP.md](../THE-MAP.md) |
| [`endgame-conveyor.png`](endgame-conveyor.png) | 24 doors, 8 chains, 4 shared runs, one Finish | [README](../README.md), [THE-MAP.md](../THE-MAP.md) |
| [`contested-corridor.png`](contested-corridor.png) | the only bridge to the group no 321 claims | [THE-PROBLEM.md](../THE-PROBLEM.md) |

A **square** is a physical checkpoint box, drawn at its true position with its
real 6 m footprint. A **dot** is a node in the graph. Nothing in a figure is
schematic: every position, count and edge is read from
[`../data/graph.json`](../data/graph.json) and
[`../data/spire.json`](../data/spire.json).

## Keeping them honest

The figures are drawn by hand, so nothing stops them drifting from the data
except this:

```bash
python3 viz/check_figures.py
```

It asserts all 25 structural claims the three figures make — the corridor's
identical in-neighbourhoods, the conveyor's pair-merge, the room offsets, the
hub's fall chains, what each START destroys — and exits non-zero if any stops
holding. `./verify/check.sh` runs it too. **If it fails, the figure is wrong,
not the data.**

## One thing drawing them found

Nothing in the analysis had recorded it: **all 568 standard six-pit rooms use
the identical six offsets from the cell centre.**

```
FW (+1,+10)      FW (-1,-10)
FWSide (+10,+3)  FWSide (-10,-3)
Down (+7,-6)     Up (-7,+6)
```

A ring at 10 m in antipodal pairs, with zero variation anywhere on the map. The
earlier notes called it "a square formation"; it is a hexagon, and every room is
the same one. Learn one room and you have learned 568 of them.
