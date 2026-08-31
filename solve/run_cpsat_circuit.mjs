#!/usr/bin/env node
import fs from 'node:fs';
import {
  CpModel,
  CpSolver,
  CpSolverStatus,
  LinearExpr,
} from '@ortools-node/cp-sat';

const [graphPath, outputPath, secondsArg = '600', seedArg = '1', sourceArg, targetArg] = process.argv.slice(2);
if (!graphPath || !outputPath) {
  console.error('usage: run_cpsat_circuit.mjs GRAPH.json OUTPUT.txt [seconds] [seed] [suffixSource suffixTarget]');
  process.exit(2);
}

const graph = JSON.parse(fs.readFileSync(graphPath, 'utf8'));
const nodes = graph.nodes;
const nodeById = new Map(nodes.map((n, i) => [n.id, {...n, index: i}]));
const goal = nodes.find(n => n.kind === 'goal');
const starts = nodes.filter(n => n.variant === 'START');
const virtual = nodes.length;
const model = new CpModel();
const optimize = process.env.CP_OPTIMIZE === '1';
model.name = 'haystack6-colored-directed-path';

const pairSeen = new Set();
const edgeVars = new Map();
const arcs = [];
for (const e of graph.edges) {
  const key = `${e.source},${e.target}`;
  if (pairSeen.has(key)) continue;
  pairSeen.add(key);
  const variable = model.newBoolVar(`e_${e.source}_${e.target}`);
  edgeVars.set(key, variable);
  arcs.push([nodeById.get(e.source).index, nodeById.get(e.target).index, variable]);
}
for (const start of starts) {
  const variable = model.newBoolVar(`spawn_${start.id}`);
  edgeVars.set(`-2,${start.id}`, variable);
  arcs.push([virtual, nodeById.get(start.id).index, variable]);
}
arcs.push([nodeById.get(goal.id).index, virtual, model.trueLiteral()]);

const skipsByGroup = new Map();
const skipVars = new Map();
for (const node of nodes) {
  if (node.id === goal.id) continue;
  const skip = model.newBoolVar(`skip_${node.id}`);
  skipVars.set(node.id, skip);
  arcs.push([nodeById.get(node.id).index, nodeById.get(node.id).index, skip]);
  if (!skipsByGroup.has(node.group)) skipsByGroup.set(node.group, []);
  skipsByGroup.get(node.group).push(skip);
}
if (skipsByGroup.size !== 322) throw new Error(`expected 322 groups, got ${skipsByGroup.size}`);
for (const skips of skipsByGroup.values()) {
  if (optimize) model.addGreaterOrEqual(LinearExpr.sum(skips), skips.length - 1);
  else model.addEquality(LinearExpr.sum(skips), skips.length - 1);
}
model.addCircuit(arcs);

// ─── controls the report documents but the shipped script never had ────────
//
// HAYSTACK6_PROBLEM_AND_SOLVER_STATUS.md §12 tabulates CP_FOCUS_GROUPS,
// CP_FOCUS_BONUS, CP_BASE_WEIGHT, CP_REQUIRE_GROUPS and CP_MIN_SCORE as if this
// file supported them; it does not, and §15 step 1 asks outright for
// CP_REQUIRE_NODES to be added. The report describes a newer script than the
// one it shipped. This block is that addition, written against the model
// already built above rather than as a rewrite of it.
//
// `skip` is per NODE and every group carries an at-most-one constraint, so
// `skip.not()` is "this box is on the route" and the sum of those over a
// group's members is that group's 0/1 claimed indicator. No new variables are
// needed for any of this.
const selected = id => skipVars.get(id).not();
const membersOf = new Map();
for (const node of nodes) {
  if (node.id === goal.id) continue;
  if (!membersOf.has(node.group)) membersOf.set(node.group, []);
  membersOf.get(node.group).push(node.id);
}
// The empty-string filter is load-bearing: ''.split(',') is [''], and
// Number('') is 0 rather than NaN, so an UNSET variable would otherwise read as
// "require group 0" and abort the run.
const idList = name => (process.env[name] || '')
  .split(',').map(s => s.trim()).filter(s => s !== '')
  .map(Number).filter(Number.isFinite);

// CP_REQUIRE_NODES — pin specific physical representatives. This is what makes
// an exact branch partition possible: our graph has six groups with exactly two
// members, so pinning one of each splits the 322 problem into 64 branches that
// between them hold every route. The sibling is banned implicitly by the
// group's own at-most-one constraint.
const requireNodes = idList('CP_REQUIRE_NODES');
if (requireNodes.length) {
  for (const id of requireNodes) {
    const skip = skipVars.get(id);
    if (!skip) throw new Error(`CP_REQUIRE_NODES: ${id} is not a node in this graph`);
    model.addEquality(skip, 0);
  }
  console.error(`require-nodes: ${requireNodes.length} pinned — ${requireNodes.join(' ')}`);
}

const requireGroups = idList('CP_REQUIRE_GROUPS');
if (requireGroups.length) {
  for (const g of requireGroups) {
    const members = membersOf.get(g);
    if (!members) throw new Error(`CP_REQUIRE_GROUPS: ${g} is not a group in this graph`);
    model.addEquality(LinearExpr.sum(members.map(selected)), 1);
  }
  console.error(`require-groups: ${requireGroups.length} demanded — ${requireGroups.join(' ')}`);
}

const allSelected = [...skipVars.keys()].map(selected);

if (process.env.CP_MIN_SCORE) {
  const floor = Number(process.env.CP_MIN_SCORE);
  if (!optimize) throw new Error('CP_MIN_SCORE needs CP_OPTIMIZE=1; the exact model already demands all 322');
  model.addGreaterOrEqual(LinearExpr.sum(allSelected), floor);
  console.error(`min-score: at least ${floor} groups`);
}

if (optimize) {
  // The cardinality-dominant objective of §9.3: base*claimed + bonus*focused,
  // with base > bonus*|focus| so a tie-break can never outrank one real group.
  // §9.1 records what happens without that discipline — big bonuses duly force
  // the hard groups in, by sacrificing raw score, while the weighted objective
  // still rises. A run that improves its number by getting worse teaches
  // nothing, so the inequality is enforced here rather than left to the caller.
  const focusGroups = idList('CP_FOCUS_GROUPS');
  const focusLits = focusGroups.flatMap(g => (membersOf.get(g) || []).map(selected));
  if (focusLits.length) {
    const bonus = Number(process.env.CP_FOCUS_BONUS || 1);
    const cap = bonus * focusGroups.length;
    const base = Number(process.env.CP_BASE_WEIGHT || cap + 1);
    if (base <= cap) {
      throw new Error(`CP_BASE_WEIGHT=${base} <= CP_FOCUS_BONUS*|focus|=${cap}: a tie-break `
        + `could outrank a real group. Use > ${cap}, or leave CP_BASE_WEIGHT unset for ${cap + 1}.`);
    }
    model.maximize(LinearExpr.weightedSum(
      [...allSelected, ...focusLits],
      [...allSelected.map(() => base), ...focusLits.map(() => bonus)],
    ));
    console.error(`objective: ${base}*claimed + ${bonus}*focused over ${focusGroups.length} focus group(s)`);
  } else {
    model.maximize(LinearExpr.sum(allSelected));
  }
}

if (sourceArg !== undefined || targetArg !== undefined) {
  if (sourceArg === undefined || targetArg === undefined) throw new Error('both suffix source and target are required');
  const source = Number(sourceArg), target = Number(targetArg);
  let u = source, v = target;
  while (true) {
    const variable = edgeVars.get(`${u},${v}`);
    if (!variable) throw new Error(`missing fixed suffix edge ${u}->${v}`);
    model.addEquality(variable, 1);
    if (v === goal.id) break;
    const next = graph.edges.filter(e => e.source === v && (e.target === goal.id || nodeById.get(e.target)?.region === 'spire'));
    if (next.length !== 1) throw new Error(`non-deterministic suffix at ${v}`);
    u = v;
    v = next[0].target;
  }
}

if (process.env.CP_PREFIX_SNAPSHOT) {
  const snapshot = JSON.parse(fs.readFileSync(process.env.CP_PREFIX_SNAPSHOT, 'utf8'));
  const limit = Number(process.env.CP_PREFIX_LIMIT || snapshot.prefixRoute.length);
  const prefix = snapshot.prefixRoute.slice(0, limit);
  const fixed = [[-2, prefix[0]]];
  for (let i = 0; i + 1 < prefix.length; i++) fixed.push([prefix[i], prefix[i + 1]]);
  if (process.env.CP_NEXT_NODE) fixed.push([prefix.at(-1), Number(process.env.CP_NEXT_NODE)]);
  for (const [a, b] of fixed) {
    const variable = edgeVars.get(`${a},${b}`);
    if (!variable) throw new Error(`missing fixed prefix edge ${a}->${b}`);
    model.addEquality(variable, 1);
  }
  console.error(`fixed prefix=${prefix.length} next=${process.env.CP_NEXT_NODE || 'free'}`);
}

if (process.env.CP_HINT_ROUTE) {
  const tokens = fs.readFileSync(process.env.CP_HINT_ROUTE, 'utf8').trim().split(/\s+/).map(Number);
  const route = tokens.slice(1);
  const chosen = new Set(route.slice(0, -1));
  for (const [id, skip] of skipVars) model.addHint(skip, !chosen.has(id));
  const path = [-2, ...route];
  for (let i = 0; i + 1 < path.length; i++) {
    const variable = edgeVars.get(`${path[i]},${path[i + 1]}`);
    if (!variable) throw new Error(`hint route missing edge ${path[i]}->${path[i + 1]}`);
    model.addHint(variable, true);
  }
  console.error(`hint route score=${tokens[0]} nodes=${route.length}`);
}

const validation = model.validate();
if (validation) throw new Error(`invalid CP-SAT model: ${validation}`);
console.error(`model nodes=${nodes.length + 1} groups=${skipsByGroup.size} arcs=${arcs.length} bools=${arcs.length - 1}`);
console.error(model.modelStats());

const solver = new CpSolver();
solver.parameters.maxTimeInSeconds = Number(secondsArg);
solver.parameters.numSearchWorkers = Number(process.env.CP_WORKERS || 8);
solver.parameters.randomSeed = Number(seedArg);
solver.parameters.logSearchProgress = process.env.CP_QUIET !== '1';
solver.parameters.useAllDifferentForCircuit = true;
solver.parameters.cpModelProbingLevel = Number(process.env.CP_PROBING_LEVEL || 0);
if (process.env.CP_LNS_ONLY === '1') {
  solver.parameters.useLnsOnly = true;
  solver.parameters.diversifyLnsParams = true;
  solver.parameters.solutionPoolSize = 8;
  solver.parameters.alternativePoolSize = 4;
  solver.parameters.lnsInitialDifficulty = Number(process.env.CP_LNS_DIFFICULTY || 0.35);
  solver.parameters.lnsInitialDeterministicLimit = Number(process.env.CP_LNS_LIMIT || 0.2);
}
solver.logCallback = line => {
  if (/^(Starting|Presolve|CpSolverResponse|#|\s*status:|\s*conflicts:|\s*branches:)/.test(line))
    process.stderr.write(line.endsWith('\n') ? line : `${line}\n`);
};

const status = await solver.solve(model);
console.error(`status=${solver.statusName(status)} wall=${solver.wallTime.toFixed(2)}s conflicts=${solver.numConflicts} branches=${solver.numBranches}`);
if (status !== CpSolverStatus.FEASIBLE && status !== CpSolverStatus.OPTIMAL) process.exit(status === CpSolverStatus.INFEASIBLE ? 20 : 1);

const successor = new Map();
for (const [key, variable] of edgeVars) {
  if (!solver.booleanValue(variable)) continue;
  const [a, b] = key.split(',').map(Number);
  successor.set(a, b);
}
const route = [];
let u = -2;
const seen = new Set([u]);
while (u !== goal.id) {
  u = successor.get(u);
  if (u === undefined || seen.has(u)) throw new Error('selected circuit did not decode to a path');
  seen.add(u);
  route.push(u);
}
const groups = new Set();
if ((!optimize && route.length !== 323) || nodeById.get(route[0]).variant !== 'START') throw new Error(`bad route length/start: ${route.length}`);
for (let i = 0; i + 1 < route.length; i++) {
  const n = nodeById.get(route[i]);
  if (groups.has(n.group)) throw new Error(`duplicate group at ${i}`);
  groups.add(n.group);
  if (!pairSeen.has(`${route[i]},${route[i + 1]}`)) throw new Error(`missing edge at ${i}`);
}
if (!optimize && groups.size !== 322) throw new Error(`only ${groups.size} groups`);
fs.writeFileSync(outputPath, `${groups.size}\n${route.join(' ')}\n`);
console.error(`${groups.size === 322 ? 'COMPLETE' : 'INCUMBENT'} VALIDATED score=${groups.size} route=${outputPath}`);
