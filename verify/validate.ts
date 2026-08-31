#!/usr/bin/env bun
// validate_route.ts — an INDEPENDENT referee for any route file.
//
// Deliberately shares no code with any solver. It re-reads the graph and
// checks the rules from scratch, so a bug in a solver's own bookkeeping (or
// in how it extracts a tour from its model) cannot hide behind agreeing with
// itself. Every solver output should go through this before it is believed.
//
// THE RULES, as the game plays them:
//   1. every step follows a DIRECTED edge of the graph
//   2. the run begins at a START pit
//   3. the run ends by crossing the Finish
//   4. no link group is ever claimed twice
//   5. a winning run claims all 322 groups
//
// Exit: 0 valid and complete · 1 valid but partial · 2 ILLEGAL
//
//   bun verify/validate.ts <route.json> [--graph data/graph.json]
//   node --experimental-strip-types verify/validate.ts <route.json>
import { readFileSync } from "node:fs";

const arg = (f: string) => process.argv.includes(f) ? process.argv[process.argv.indexOf(f) + 1] : null;
const FILE = process.argv[2];
if (!FILE) { console.error("usage: validate.ts <route.json> [--graph data/graph.json]"); process.exit(2); }
const GRAPH = arg("--graph") ?? "data/graph.json";

const G = JSON.parse(readFileSync(GRAPH, "utf8"));
const R = JSON.parse(readFileSync(FILE, "utf8"));

const byId = new Map<number, any>(G.nodes.map((n: any) => [n.id, n]));
const edge = new Set<string>(G.edges.map((e: any) => `${e.source}>${e.target}`));
const finish = G.nodes.find((n: any) => n.variant === "FINISH");
// The Finish clears no group, so it is not one of the 322.
const allGroups = new Set<number>(G.nodes.map((n: any) => n.group));
allGroups.delete(finish.group);

// Accept both shapes we emit: {route:[{cp}]} and {steps:[{exit:{cp}}]}
const ids: number[] = R.route ? R.route.map((s: any) => s.cp)
  : R.steps ? R.steps.map((s: any) => s.exit.cp)
  : (() => { throw new Error(`${FILE} has neither .route nor .steps`); })();

const V = (id: number) => { const n = byId.get(id); return n ? `${n.variant || "CP"}#${id}` : `MISSING#${id}`; };
const problems: string[] = [];
const claimedAt = new Map<number, number>();

ids.forEach((id, i) => {
  const n = byId.get(id);
  if (!n) { problems.push(`step ${i}: checkpoint ${id} is not in ${GRAPH}`); return; }

  // 1. directed edges only — the direction is the whole point, a route that
  //    reads fine backwards is still not drivable
  if (i > 0 && !edge.has(`${ids[i - 1]}>${id}`)) {
    const back = edge.has(`${id}>${ids[i - 1]}`);
    problems.push(`step ${i}: no edge ${V(ids[i - 1])} -> ${V(id)}` +
      (back ? "  (the REVERSE edge exists — direction is flipped)" : ""));
  }

  // 4. one claim per group
  if (n.group !== finish.group) {
    if (claimedAt.has(n.group))
      problems.push(`step ${i}: group ${n.group} already claimed at step ${claimedAt.get(n.group)}` +
        ` by ${V(ids[claimedAt.get(n.group)!])}`);
    else claimedAt.set(n.group, i);
  }
});

// 2 & 3. the endpoints
const first = byId.get(ids[0]), last = byId.get(ids[ids.length - 1]);
if (first?.variant !== "START") problems.push(`starts at ${V(ids[0])}, not a START pit`);
if (last?.variant !== "FINISH") problems.push(`ends at ${V(ids[ids.length - 1])}, not the Finish`);

const missing = [...allGroups].filter((g) => !claimedAt.has(g));
const complete = missing.length === 0;

console.log(`${FILE}  (graph ${GRAPH})`);
console.log(`  ${ids.length} steps · ${claimedAt.size}/${allGroups.size} groups claimed` +
  ` · ${V(ids[0])} -> ${V(ids[ids.length - 1])}`);

if (problems.length) {
  console.log(`\n  ILLEGAL — ${problems.length} rule violation${problems.length === 1 ? "" : "s"}:`);
  for (const p of problems.slice(0, 20)) console.log(`    ${p}`);
  if (problems.length > 20) console.log(`    ... and ${problems.length - 20} more`);
  process.exit(2);
}

// A legal route: say what it is worth.
if (complete) {
  console.log(`\n  VALID AND COMPLETE — all ${allGroups.size} groups, each exactly once. This is a winning run.`);
  process.exit(0);
}
console.log(`\n  VALID but partial — ${missing.length} group${missing.length === 1 ? "" : "s"} never claimed.`);
// Where the gap is matters more than the count: it tells us which part of the
// map the search cannot fit in, which is what a repair pass has to target.
const where = new Map<string, number>();
for (const g of missing) {
  for (const r of new Set(G.nodes.filter((n: any) => n.group === g).map((n: any) => n.region)))
    where.set(r as string, (where.get(r as string) ?? 0) + 1);
}
console.log(`  unclaimed groups have members in: ` +
  [...where].sort((a, b) => b[1] - a[1]).map(([r, k]) => `${r} (${k})`).join(", "));
if (missing.length <= 25) console.log(`  missing: ${missing.join(", ")}`);
process.exit(1);
