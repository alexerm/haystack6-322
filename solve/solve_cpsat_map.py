#!/usr/bin/env python3
# solve_cpsat_map.py — the covering route as an EXACT problem, straight on
# data/graph.json, so the answer is either a route or a proof that
# none exists. (an earlier room-level model (not shipped) is the older gate-instance variant and
# predates the corrected endgame graph.)
#
# The DFS (a DFS walker (not shipped)) walls at ~232/322 from both ends: its
# reachability prune checks each group independently, never jointly, and joint
# scarcity is exactly what this map is made of. CP-SAT reasons jointly.
#
# ENCODING — one circuit over the real graph, nothing reduced:
#   * every directed edge of the map graph is an arc
#   * every node also gets a self-loop = "not visited"
#   * a virtual depot closes the tour: depot -> each START, FINISH -> depot
#   * per link group: exactly one member is visited
#   * FINISH is visited
# A feasible circuit is then depot -> START -> ...322 checkpoints, one per
# group... -> FINISH -> depot, which is precisely the winning run. No chain or
# START is pre-committed — the arcs themselves force the endgame conveyor.
#
#   uv run --with ortools solve/solve_cpsat_map.py [--time 3600] [--workers 8]
#          [--out route-cpsat.json]
import argparse, json, sys, time

from ortools.sat.python import cp_model

ap = argparse.ArgumentParser()
ap.add_argument("--graph", default="data/graph.json")
ap.add_argument("--time", type=float, default=3600.0, help="solver limit, seconds")
ap.add_argument("--workers", type=int, default=8)
ap.add_argument("--out", default="route-cpsat.json")
ap.add_argument("--max", action="store_true",
                help="maximise groups claimed instead of demanding all 322: every "
                     "incumbent is a proven lower bound, the dual bound a proven "
                     "upper bound — the exact height of the wall")
ap.add_argument("--hint", default=None,
                help="route JSON from an earlier run (or its .incumbent) to warm-start from")
ap.add_argument("--force-small", type=int, default=0, metavar="N",
                help="under --max, still DEMAND every group with <= N members. The map is "
                     "bimodal: 17 groups have 1-4 members, the other 305 have 18-23. The "
                     "scarce ones are the whole puzzle, but --max scores them at 1 point "
                     "each, exactly like an abundant one, so it cheerfully trades away a "
                     "group that had a single reachable floor box. Such an incumbent is "
                     "dead the moment it passes that box — the 304-group route lost "
                     "g1192721329 at step 5 — and no suffix repair can revive it. Forcing "
                     "the scarce groups keeps every incumbent structurally completable.")
ap.add_argument("--core", action="store_true",
                help="with --repair: instead of demanding every group outright, assume "
                     "each is claimable and, on INFEASIBLE, report the unsat CORE — the "
                     "specific subset of groups that cannot jointly be completed after "
                     "the frozen prefix. Turns 'no completion exists' into names.")
ap.add_argument("--drop", default="", metavar="g1,g2",
                help="comma-separated group ids to NOT demand (at-most-once instead of "
                     "exactly-once). Manual unsat-core probing: --core's assumption "
                     "machinery loses the core when presolve proves infeasibility, so "
                     "instead we ask directly 'is it feasible without these groups?'")
ap.add_argument("--near", action="store_true",
                help="with --hint and no --max: demand all 322 groups HARD and "
                     "maximise how many of the hint route's arcs are reused. Any "
                     "feasible solution is a complete winner; the objective steers "
                     "search into the incumbent's neighbourhood, and the arcs a "
                     "solution drops are exactly the commitments that had to change "
                     "(constructive conflict-guided LNS, without the assumptions "
                     "API whose cores presolve eats).")
ap.add_argument("--ban-region", default="", metavar="R",
                help="comma-separated regions (e.g. 'floor 7') whose boxes are "
                     "banned (visit==0). A restriction: FEASIBLE transfers to the "
                     "full puzzle, INFEASIBLE does not.")
ap.add_argument("--chain", type=int, default=None, metavar="C",
                help="fix the endgame exit chain (0-7, from --chains file): every spire "
                     "box NOT on chain C is banned and every box ON it is forced. The "
                     "conveyor's 11 group claims become known from step 0, so presolve "
                     "propagates the reservation instead of discovering it at depth; the "
                     "8 fixed-chain instances partition the full problem.")
ap.add_argument("--chains", default="data/spire.json",
                help="finish-graph file carrying the chains array (for --chain)")
ap.add_argument("--repair", type=int, default=None, metavar="K",
                help="freeze the first K steps of --hint's route and solve only the rest: "
                     "from the K-th checkpoint, claim EVERY remaining group, end at the "
                     "Finish. The strandedness analysis says the fatal decisions sit in "
                     "the last third of a route, so rewriting a suffix window is a far "
                     "smaller problem than the full map — minutes, not hours. Feasible "
                     "-> a complete stitched route; infeasible -> freeze less.")
ap.add_argument("--entry-cuts", default=None, metavar="F",
                help="cuts JSON from `python3 an entry-cut generator (not shipped)`. For each listed "
                     "group set T it demands that the route enter T from outside at "
                     "least minEntries times. SOUND: the route's claims of T split "
                     "into maximal consecutive runs, each entered from outside (step 1 "
                     "is a START and the last step is the Finish, neither in T), and "
                     "minEntries is the exact minimum number of realizable runs that "
                     "partition T. Implied by the model but NOT propagated by it — the "
                     "solver models 'claim each group once' and has no way to see that "
                     "some sets force several separate visits.")
ap.add_argument("--plain-count", type=int, default=None, metavar="N",
                help="exactly N of the 25 gateless boxes (a plain CPBox, zero spawn "
                     "transform) are claimed. THE SKELETON'S INFORMATION WITHOUT ITS "
                     "COST: the author's 9 sub-250ms gaps mean 9 groups are claimed "
                     "through their gateless member, and our own 315 independently "
                     "claims exactly 9 too, so the count is a structural invariant "
                     "rather than a fact about one route. One constraint over 26 "
                     "booleans, no position variables -- the MTZ encoding --skeleton "
                     "needs adds 40k constraints and strands presolve.")
ap.add_argument("--skeleton", default=None, metavar="F",
                help="NOT SHIPPED: needs the per-position candidate table, which prunes the middle of the route by ~1% (6368 -> 6309 candidates) and is not worth its 7 MB. "
                     "Adds position variables and pins what the author's own waypoint "
                     "times already fix: the 9 steps that must leave a plain CPBox, the "
                     "conveyor's last 12 positions (with --chain), and a per-node "
                     "position domain cut by the observed gap durations. FEASIBLE "
                     "transfers to the full puzzle; INFEASIBLE only rules out routes "
                     "that share the author's waypoint timing.")
ap.add_argument("--skeleton-narrow", action="store_true",
                help="additionally cut each node's position domain by the observed gap "
                     "durations. UNSOUND — the drop-derived minimum times it relies on "
                     "are too slow (a whole START claim measures 0.937 s against a "
                     "1.263 s bare 7 m fall), so it can exclude legal edges. Off by "
                     "default; needs the fall model rebuilt on measured trigger "
                     "geometry first.")
# ---- the recombination controls (added 2026-08-08, fact 81) ---------------
# These four exist because an external solver walked 315 -> 319 with them and
# we had no way to reproduce the method. See docs/haystack-322-campaign.md §1-2.
ap.add_argument("--focus", default="", metavar="g1,g2",
                help="comma-separated group ids to PREFER, as a tie-break only. With "
                     "--max the objective becomes `W*claimed + B*focused`, and W is "
                     "chosen so that claiming one more ordinary group always beats "
                     "every possible focus gain combined. That discipline is the whole "
                     "point: the external run that reached 319 first tried large focus "
                     "bonuses, which duly forced the hard groups in — by sacrificing "
                     "raw score, while the weighted objective still went up. A run that "
                     "can improve its objective by getting worse teaches you nothing. "
                     "Feed this the accumulated omissions of every route so far.")
ap.add_argument("--focus-bonus", type=int, default=1, metavar="B",
                help="weight per focused group (default 1)")
ap.add_argument("--base-weight", type=int, default=None, metavar="W",
                help="weight per claimed group. Default and recommended: "
                     "B*|focus| + 1, computed automatically. A W at or below "
                     "B*|focus| lets a tie-break outrank a real group and is rejected.")
ap.add_argument("--require-groups", default="", metavar="g1,g2",
                help="comma-separated group ids that MUST be claimed. Under --max these "
                     "would otherwise be traded away. No-op in exact mode, where every "
                     "group is demanded already.")
ap.add_argument("--require-nodes", default="", metavar="id1,id2",
                help="comma-separated BOX ids that must be visited. This is what makes "
                     "an exact branch partition possible: pinning one representative of "
                     "a 2-member group bans the other through that group's own "
                     "constraint, so a set of pins over k such groups splits the problem "
                     "into 2^k independent branches that between them cover every route. "
                     "All INFEASIBLE => no route exists; any FEASIBLE => the route.")
ap.add_argument("--min-score", type=int, default=None, metavar="N",
                help="hard lower bound on claimed groups. Turns 'optimise and see' into "
                     "'beat this or prove you cannot'.")
ap.add_argument("--ban-nodes", default="", metavar="id,id",
                help="comma-separated BOX ids that must NOT be visited. With --repair "
                     "this expresses 'follow the hint for K steps, then do something "
                     "ELSE', which is the slice the divergence partition is built from: "
                     "every route either equals the hint or first differs from it at "
                     "exactly one step, so the slices are disjoint and together cover "
                     "every route there is. Each slice inherits the frozen prefix, and "
                     "a frozen prefix is what makes presolve decide things in zero "
                     "seconds — see fact 84.")
ap.add_argument("--all-different-circuit", action="store_true",
                help="add the all-different propagator over the circuit's successor "
                     "variables. NOT our idea: the external bundle that produced the "
                     "319 and the 321 sets it unconditionally, and its model is "
                     "otherwise the same encoding on the same graph with the same "
                     "OR-Tools. Treat it as the reference implementation's answer "
                     "rather than a knob to sweep.")
ap.add_argument("--probing-level", type=int, default=None, metavar="N",
                help="cp_model_probing_level. OR-Tools defaults to 2; the same bundle "
                     "forces 0. On a 40k-boolean circuit, probing costs real seconds "
                     "of presolve for propagation the circuit constraint mostly "
                     "already has.")
ap.add_argument("--seed", type=int, default=None, metavar="N",
                help="CP-SAT random seed. Without it, two runs of the same model with "
                     "the same worker count explore the same way and a portfolio of "
                     "repeated attempts is just one attempt billed several times.")
ap.add_argument("--lns", action="store_true",
                help="run the large-neighbourhood portfolio instead of the default "
                     "search. The external 319 came out of a routing-neighbourhood "
                     "repair about 40 s into an LNS-only run warm-started from a 317.")
ap.add_argument("--lns-difficulty", type=float, default=0.35, metavar="X",
                help="initial fraction of the incumbent an LNS neighbourhood releases")
ap.add_argument("--lns-limit", type=float, default=0.2, metavar="X",
                help="initial deterministic budget per LNS subproblem")
args = ap.parse_args()
if args.repair is not None and not args.hint:
    ap.error("--repair needs --hint (the route whose prefix is being kept)")

G = json.load(open(args.graph))
nodes = G["nodes"]
by_id = {n["id"]: n for n in nodes}
finish = next(n for n in nodes if n["variant"] == "FINISH")
starts = [n for n in nodes if n["variant"] == "START"]
TOTAL_GROUPS = len({n["group"] for n in nodes if n["id"] != finish["id"]})

# ---- repair mode: keep a prefix, re-solve the suffix exactly ---------------
prefix = []
if args.repair is not None:
    H = json.load(open(args.hint))
    hr = [s["cp"] for s in H["route"]]
    if not 0 < args.repair <= len(hr):  # == len: keep it all, extend from the end
        sys.exit(f"--repair {args.repair} out of range for a {len(hr)}-step route")
    prefix = hr[:args.repair]
    L = prefix[-1]
    if by_id[L].get("region") == "spire" and by_id[L]["variant"] != "START":
        sys.exit(f"step {args.repair - 1} is already inside the spire — freeze less")
    claimed_prefix = {by_id[i]["group"] for i in prefix}
    # the suffix may only use checkpoints whose group the prefix left unclaimed
    keep = {n["id"] for n in nodes
            if n["group"] not in claimed_prefix or n["id"] in (L, finish["id"])}
    nodes = [n for n in nodes if n["id"] in keep]
    starts = [by_id[L]]  # the tour resumes where the prefix stopped
    print(f"repair: keeping {len(prefix)} steps ({len(claimed_prefix)} groups) of "
          f"{args.hint}; suffix must claim the remaining "
          f"{TOTAL_GROUPS - len(claimed_prefix)} groups from "
          f"{by_id[L].get('variant') or 'CP'}#{L}", flush=True)

groups = {}
for n in nodes:
    if n["id"] != finish["id"]:
        groups.setdefault(n["group"], []).append(n["id"])
print(f"{args.graph}: {len(nodes)} nodes, {len(G['edges'])} edges, "
      f"{len(groups)} groups, {len(starts)} start point(s)", flush=True)

# contiguous indices for add_circuit; the depot is index 0
idx = {n["id"]: i + 1 for i, n in enumerate(nodes)}
DEPOT = 0

m = cp_model.CpModel()
visit = {n["id"]: m.new_bool_var(f"v{n['id']}") for n in nodes}
arcs = []
for n in nodes:  # self-loop active <=> skipped
    arcs.append((idx[n["id"]], idx[n["id"]], visit[n["id"]].negated()))
for e in G["edges"]:  # only edges between surviving nodes (repair drops some)
    if e["source"] != e["target"] and e["source"] in idx and e["target"] in idx:
        arcs.append((idx[e["source"]], idx[e["target"]],
                     m.new_bool_var(f"a{e['source']}_{e['target']}")))
for s in starts:  # the run begins at one of the 4 START pits
    arcs.append((DEPOT, idx[s["id"]], m.new_bool_var(f"dep_{s['id']}")))
arcs.append((idx[finish["id"]], DEPOT, m.new_bool_var("fin_dep")))
m.add_circuit(arcs)

m.add(visit[finish["id"]] == 1)

if args.ban_region:
    banned_regions = {r.strip() for r in args.ban_region.split(",")}
    nb = 0
    for n in nodes:
        if n.get("region") in banned_regions and n["variant"] not in ("START", "FINISH"):
            m.add(visit[n["id"]] == 0)
            nb += 1
    print(f"ban-region {sorted(banned_regions)}: {nb} boxes banned", flush=True)

if args.chain is not None:
    C = json.load(open(args.chains))
    chain = next(c for c in C["chains"] if c["id"] == args.chain)
    on_chain = set(chain["boxes"])  # includes CP#104 and FINISH (-1)
    banned = forced_boxes = 0
    for n in nodes:
        if n.get("region") != "spire" or n["variant"] in ("START", "FINISH"):
            continue
        if n["id"] in on_chain:
            m.add(visit[n["id"]] == 1)  # the conveyor claims every box it passes
            forced_boxes += 1
        else:
            m.add(visit[n["id"]] == 0)  # other chains' spire is closed
            banned += 1
    print(f"chain {chain['id']} (head {chain['head']}, {chain['deck']}): "
          f"{forced_boxes} spire boxes forced, {banned} banned", flush=True)
claimed_g = []
claimed_by_g = {}  # group id -> its "was claimed" literal, for --focus/--require
forced = 0
core_lit = {}  # assumption literal -> group id (only in --core mode)
dropped = {int(x) for x in args.drop.split(",") if x.strip()}
for g, members in groups.items():  # THE rule: a group is claimed at most once
    if g in dropped:  # probe mode: this group is optional
        m.add(sum(visit[i] for i in members) <= 1)
    elif args.core and args.repair is not None:
        # soft demand under an assumption, so infeasibility yields a core
        b = m.new_bool_var(f"g{g}")
        m.add(sum(visit[i] for i in members) == b)
        core_lit[b.index] = g
        m.add_assumption(b)
    # scarce groups are non-negotiable even when maximising — see --force-small
    elif args.max and len(members) > args.force_small:
        b = m.new_bool_var(f"g{g}")
        m.add(sum(visit[i] for i in members) == b)
        claimed_g.append(b)
        claimed_by_g[g] = b
    else:  # ...and for the full route, exactly once
        m.add(sum(visit[i] for i in members) == 1)
        forced += 1

# ---- hard inclusions, and the branch pins --------------------------------
#
# --require-nodes is the load-bearing one. Our graph has six groups with
# exactly two members, so pinning one member of each splits the exact 322
# problem into 64 branches that between them contain every possible route.
# Each branch propagates hard through add_circuit, and the branches are
# independent, which is what makes an unattended overnight sweep worth doing.
# The ban of the sibling is implicit: the group's own constraint is `sum == 1`
# (or `== b <= 1`), so forcing one member forces the rest to zero.
req_groups = {int(x) for x in args.require_groups.split(",") if x.strip()}
if req_groups:
    missing = req_groups - set(groups)
    if missing:
        sys.exit(f"--require-groups names {sorted(missing)}, not in this instance")
    for g in req_groups:
        if g in claimed_by_g:
            m.add(claimed_by_g[g] == 1)
        else:  # already demanded outright (exact mode, or --force-small)
            m.add(sum(visit[i] for i in groups[g]) == 1)
    print(f"require-groups: {len(req_groups)} group(s) demanded — "
          f"{sorted(req_groups)}", flush=True)

ban_nodes = [int(x) for x in args.ban_nodes.split(",") if x.strip()]
if ban_nodes:
    live = [i for i in ban_nodes if i in visit]
    for i in live:
        m.add(visit[i] == 0)
    print(f"ban-nodes: {len(live)} box(es) forbidden — "
          + " ".join(f"{i}({by_id[i].get('variant') or 'CP'})" for i in live)
          + (f"  ({len(ban_nodes) - len(live)} not in this instance)"
             if len(live) != len(ban_nodes) else ""), flush=True)

req_nodes = [int(x) for x in args.require_nodes.split(",") if x.strip()]
if req_nodes:
    absent = [i for i in req_nodes if i not in visit]
    if absent:  # a --repair prefix may have removed the box's whole group
        sys.exit(f"--require-nodes names {absent}, not in this instance")
    for i in req_nodes:
        m.add(visit[i] == 1)
    print(f"require-nodes: {len(req_nodes)} box(es) pinned — "
          + " ".join(f"{i}(g{by_id[i]['group']})" for i in req_nodes), flush=True)

# ---- a hard floor on the score -------------------------------------------
if args.min_score is not None:
    if not args.max:
        sys.exit("--min-score needs --max (the exact model already demands all 322)")
    need = args.min_score - forced
    if need > len(claimed_g):
        sys.exit(f"--min-score {args.min_score} is unreachable: only {len(claimed_g)} "
                 f"optional group(s) plus {forced} demanded outright")
    m.add(sum(claimed_g) >= need)
    print(f"min-score: at least {args.min_score}/{TOTAL_GROUPS} groups "
          f"({need} of the {len(claimed_g)} optional ones)", flush=True)
# ---- entry-count cuts: sets that force several separate visits ------------
#
# A group set can be a trap even when every member is individually easy to
# reach. What bites is how many of the set you can claim CONSECUTIVELY: if the
# longest run is 3 and the set has 7 members, the route must return to that set
# at least 3 times, each return needing a gateway box still unspent. The 315
# incumbent misses exactly such a set — its 7 groups admit only 18 realizable
# runs (7 singletons, 10 pairs, 1 triple), so 3 visits are forced, and it never
# scheduled them.
#
# Generate with: python3 an entry-cut generator (not shipped) --from-route <partial> --out F
if args.entry_cuts:
    EC = json.load(open(args.entry_cuts))
    grp_of = {n["id"]: n["group"] for n in nodes}
    rev_idx = {v: k for k, v in idx.items()}
    added = 0
    for cut in EC["cuts"]:
        T = set(cut["groups"])
        entering = [lit for a, b, lit in arcs
                    if a != b and b != DEPOT
                    and (a == DEPOT or grp_of.get(rev_idx.get(a)) not in T)
                    and grp_of.get(rev_idx.get(b)) in T]
        if entering:
            m.add(sum(entering) >= cut["minEntries"])
            added += 1
    print(f"entry cuts: {added} set(s) constrained; full trap set needs "
          f">= {EC['minEntries']} entries (longest run inside it is "
          f"{EC['longestRun']})", flush=True)

# ---- how many groups are claimed through a GATELESS box --------------------
#
# A plain CPBox has a zero spawn transform: fall in and nothing repositions you,
# so the step that LEAVES one shows up in the author's splits as a sub-250ms
# fall-through. He has exactly 9 such gaps, so exactly 9 of his 322 groups are
# claimed through their gateless member.
#
# Why this is worth having when --skeleton is not: --skeleton pins WHICH STEPS
# those are, which needs position variables, and the MTZ encoding that provides
# them adds ~40k constraints and leaves presolve grinding for 2700s without ever
# producing an incumbent. The COUNT needs no positions at all -- one linear
# constraint over 26 booleans.
#
# Soundness: 9 is not merely the author's number. best-315-partial.json, found
# independently by a solver that knew nothing about the waypoint times, also
# claims exactly 9. Two routes from unrelated derivations agreeing on the count
# is what makes it a structural invariant rather than a fact about one run.
# Still: this is a RESTRICTION, so an INFEASIBLE under it is not a proof about
# the map, and a FEASIBLE still goes through validate_route.ts.
if args.plain_count is not None:
    plain = [n["id"] for n in nodes
             if n["id"] != finish["id"]
             and sum((n["spawn"][k] - n["pos"][k]) ** 2 for k in range(3)) < 0.25]
    m.add(sum(visit[i] for i in plain) == args.plain_count)
    print(f"plain-CPBox count: exactly {args.plain_count} of {len(plain)} gateless "
          f"boxes claimed (no position variables)", flush=True)


# ---- skeleton: pin what the author's own waypoint times already fix -------
#
# The map records Race_AuthorRaceWaypointTimes — one timestamp per group the
# author claimed, ending on the Finish .
# A claimed box is inert and its pit has no working gate, so every move must
# land in an UNCLAIMED pit: the route is exactly `steps` long and waypoint k is
# move k. That rigid alignment is what makes the times usable as constraints.
#
# add_circuit has no notion of position, so this adds MTZ-style position
# variables (u[v] = the 1-based step at which v is visited, 0 if skipped) and
# pins three things onto them:
#
#   * gaps under 0.25 s are physically impossible for a respawn move, so the
#     step before each one left a plain CPBox — a box with a zero spawn
#     transform, of which the map has 26. Nine such gaps => nine exact facts.
#   * with --chain, the conveyor's 12 boxes occupy the last 12 positions.
#   * every other node gets its position domain cut to the steps whose observed
#     gap is at least as long as its cheapest incoming arc can possibly take.
#
# Generate the input with:
#   data/author-waypoints.json
if args.skeleton:
    W = json.load(open(args.skeleton))
    STEPS = W["steps"]
    rev = {v: k for k, v in idx.items()}  # contiguous index -> node id
    ft_nodes = [i for i in W["fallThroughNodes"] if i in idx]
    u = {n["id"]: m.new_int_var(0, STEPS, f"u{n['id']}") for n in nodes}

    for a, b, lit in arcs:
        if a == b or a == DEPOT or b == DEPOT:
            continue
        m.add(u[rev[b]] == u[rev[a]] + 1).only_enforce_if(lit)
    for a, b, lit in arcs:  # depot -> START opens at step 1; FINISH closes
        if a == DEPOT:
            m.add(u[rev[b]] == 1).only_enforce_if(lit)
    m.add(u[finish["id"]] == STEPS)
    for n in nodes:
        m.add(u[n["id"]] == 0).only_enforce_if(visit[n["id"]].negated())

    # A fall-through gap at waypoint p means the box left at step p-1 was a
    # plain CPBox. Positions are strictly increasing along the tour, so exactly
    # one visited node sits at p-1 and demanding >= 1 of the 26 is enough.
    pinned = 0
    for p in W["fallThroughWaypoints"]:
        if p - 1 < 1:
            continue
        lits = []
        for v in ft_nodes:
            b = m.new_bool_var(f"ft{v}@{p-1}")
            m.add(u[v] == p - 1).only_enforce_if(b)
            m.add(u[v] != p - 1).only_enforce_if(b.negated())
            lits.append(b)
        m.add(sum(lits) >= 1)
        pinned += 1

    fixed_chain = 0
    if args.chain is not None:
        boxes = chain["boxes"]
        first = STEPS - len(boxes) + 1
        for k, bx in enumerate(boxes):
            if bx in u:
                m.add(u[bx] == first + k)
                fixed_chain += 1

    # UNSOUND BY DEFAULT — off unless --skeleton-narrow is passed.
    #
    # This cuts each node's position domain to the steps whose observed gap is
    # at least as long as its cheapest incoming arc could take. That rests on
    # drop-derived minimum times, and in-game measurement showed those are too
    # SLOW: a complete START claim takes 0.937 s, less than the 1.263 s that a
    # 7 m free fall alone would need, so the waypoint fires well above the box
    # centre. Over-estimating an edge's minimum excludes LEGAL edges at fast
    # steps — the one direction a filter must never err in.
    #
    # The fall model has to be rebuilt on measured trigger geometry (and on
    # turn angle, which is the only geometric quantity on this map that varies)
    # before this is worth turning on. docs/haystack-author-waypoints.md §4a.
    narrowed = 0
    if args.skeleton_narrow:
        for sid, allowed in W["restrictedPositions"].items():
            v = int(sid)
            if v not in u or not allowed:
                continue
            m.add_linear_expression_in_domain(
                u[v], cp_model.Domain.from_values([0] + allowed))
            narrowed += 1

    print(f"skeleton: {STEPS}-step route, {pinned} fall-through step(s) pinned to the "
          f"{len(ft_nodes)} plain CPBoxes, {fixed_chain} conveyor position(s) fixed, "
          f"{narrowed} node position domain(s) narrowed by the observed gaps", flush=True)

base_weight = 1  # what one claimed group is worth in the objective
if args.max:
    # ---- the cardinality-dominant objective (fact 81) --------------------
    #
    # `W*claimed + B*focused` with W > B*|focus|. The inequality is the whole
    # mechanism: it makes every route of score k+1 outrank every route of
    # score k, whatever the focus set does, so the focus weights can only
    # break ties. Without it a run improves its objective while losing groups
    # and reports that as progress.
    focus = [int(x) for x in args.focus.split(",") if x.strip()]
    focus_lits = [claimed_by_g[g] for g in focus if g in claimed_by_g]
    if focus_lits:
        cap = args.focus_bonus * len(focus_lits)
        base_weight = args.base_weight if args.base_weight is not None else cap + 1
        if base_weight <= cap:
            sys.exit(f"--base-weight {base_weight} <= focus-bonus*|focus| = {cap}: a "
                     f"tie-break could outrank a real group. Use > {cap}, or omit "
                     f"--base-weight and let it be {cap + 1}.")
        m.maximize(base_weight * sum(claimed_g) + args.focus_bonus * sum(focus_lits))
        skipped = len(focus) - len(focus_lits)
        print(f"objective: {base_weight}*claimed + {args.focus_bonus}*focused over "
              f"{len(focus_lits)} focus group(s)"
              + (f" ({skipped} already demanded outright)" if skipped else ""),
              flush=True)
    else:
        if args.focus:
            print("focus: every named group is demanded outright already — "
                  "no tie-break to apply", flush=True)
        m.maximize(sum(claimed_g))
    print(f"objective: maximise {len(claimed_g)} groups; {forced} scarce group(s) "
          f"(<= {args.force_small} members) demanded outright", flush=True)

print(f"model: {len(arcs)} arcs ({len(G['edges'])} real, {len(nodes)} skip, "
      f"{len(starts) + 1} depot) · {len(groups)} exactly-one constraints", flush=True)

rev = {v: k for k, v in idx.items()}

def extract_route(value):
    """Walk the chosen arcs depot->...->depot; `value` maps literal -> bool.
    In repair mode the frozen prefix is stitched back on, so what comes out is
    always a complete START -> FINISH route."""
    nxt = {}
    for a, b, lit in arcs:
        if a != b and value(lit):
            nxt[a] = b
    route_idx, at = [], nxt[DEPOT]
    while at != DEPOT:
        route_idx.append(at)
        at = nxt[at]
    suffix = [by_id[rev[i]] for i in route_idx]
    return [by_id[i] for i in prefix[:-1]] + suffix

def dump_route(route, path, status_name, total):
    claimed = {n["group"] for n in route if n["id"] != finish["id"]}
    json.dump({
        "meta": {"graph": args.graph, "solver": "solve/solve_cpsat_map.py",
                 "status": status_name, "won": len(claimed) == total,
                 "groupsClaimed": len(claimed), "groupsTotal": total,
                 "steps": len(route)},
        "route": [{"cp": n["id"], "variant": n.get("variant") or "CP",
                   "group": n["group"], "pos": n["pos"], "spawn": n["spawn"]}
                  for n in route],
    }, open(path, "w"), indent=1)
    return len(claimed)

# ---- repair mode: hint the SUFFIX from the same route ---------------------
#
# Repair used to give the solver nothing to start from: the prefix was frozen
# and the suffix searched cold. That is why the provable frontier collapsed —
# measured 2026-08-09, freezing the 321's first K steps and maximising the rest
# returned OPTIMAL 321 in under 2 s for every K from 200 to 260, and then at
# K=180 and K=160 returned a *worse-than-incumbent* 297 and 298, not because
# those prefixes are worse but because 120 s was not enough to rediscover a
# suffix it was never told about.
#
# The route's own remaining steps are a feasible completion of its own prefix,
# so hinting them costs nothing and hands the solver an incumbent of 321 to
# beat. Optimality proofs then have something to close the gap against.
if args.hint and args.repair is not None:
    H = json.load(open(args.hint))
    tail = [s["cp"] for s in H["route"]][args.repair - 1:]  # from the frozen end on
    arc_lit = {(a, b): lit for a, b, lit in arcs if a != b}
    live = [i for i in tail if i in visit]
    for n in nodes:
        m.add_hint(visit[n["id"]], n["id"] in set(live))
    pairs = [(idx[a], idx[b]) for a, b in zip(live, live[1:])
             if a in idx and b in idx]
    if live and live[-1] == finish["id"]:
        pairs.append((idx[finish["id"]], DEPOT))
    ok = 0
    for p in pairs:
        if p in arc_lit:
            m.add_hint(arc_lit[p], 1)
            ok += 1
    print(f"repair warm start: hinting the hint's own {len(live)}-step suffix, "
          f"{ok}/{len(pairs)} arcs — gives the solver a {len(live) - 1}-claim "
          f"incumbent to beat instead of starting cold", flush=True)

# warm start: hint every visited node and every consecutive arc of a prior route
if args.hint and args.repair is None:
    H = json.load(open(args.hint))
    hint_ids = [s["cp"] for s in H["route"]]
    arc_lit = {(a, b): lit for a, b, lit in arcs if a != b}
    hinted = set(hint_ids)
    for n in nodes:
        m.add_hint(visit[n["id"]], n["id"] in hinted)
    pairs = [(DEPOT, idx[hint_ids[0]])] + \
        [(idx[a], idx[b]) for a, b in zip(hint_ids, hint_ids[1:])]
    if hint_ids[-1] == finish["id"]:
        pairs.append((idx[finish["id"]], DEPOT))
    ok = sum(1 for p in pairs if p in arc_lit)
    # Hint every arc, not only the route's own — the ones it does not use are
    # hinted to 0. A partial hint is not a solution CP-SAT can start from, and
    # LNS in particular has nothing to ruin without a complete incumbent: an
    # earlier run hinted only the 321 used arcs, reported "6717 out of 40730
    # non fixed variables hinted", and produced no incumbent at all in 100 s.
    # keyed on the (from, to) pair, never on the variable: CpModel's variables
    # overload __eq__ to build constraints, so putting them in a set is asking
    # for trouble
    on = {p for p in pairs if p in arc_lit}
    for key, lit in arc_lit.items():
        m.add_hint(lit, 1 if key in on else 0)
    print(f"hint: {args.hint} — {len(hint_ids)} nodes, {ok}/{len(pairs)} arcs matched, "
          f"{len(arc_lit)} arc literals hinted", flush=True)
    if args.near:
        if args.max:
            sys.exit("--near needs the exact model: drop --max")
        kept = [arc_lit[p] for p in pairs if p in arc_lit]
        m.maximize(sum(kept))
        print(f"near mode: all {TOTAL_GROUPS} groups demanded, maximising reuse "
              f"of the hint's {len(kept)} arcs", flush=True)

class Progress(cp_model.CpSolverSolutionCallback):
    """Every incumbent goes to disk immediately — a killed run loses nothing."""
    def __init__(self):
        super().__init__()
        self.t0 = time.time()
    def on_solution_callback(self):
        # COUNT the claimed groups rather than reading the objective. Under a
        # focus objective the objective is `W*claimed + B*focused` and dividing
        # it back out would be a guess; under any objective the count is what
        # the run is actually judged on. The forced groups are a given, so add
        # them back to report the honest route total.
        what = (f"{sum(self.value(b) for b in claimed_g) + forced}/{TOTAL_GROUPS} groups"
                if args.max
                else f"COMPLETE ROUTE reusing {int(self.objective_value)} hint arcs"
                if args.near else "solution")
        # the dual bound is in objective units; in group units it is the bound
        # divided by what one group is worth (1 when no focus set is in play)
        bound = (int(self.best_objective_bound) // base_weight + forced
                 if args.max else "-")
        print(f"  {time.time() - self.t0:6.0f}s  found {what} "
              f"(bound {bound})", flush=True)
        try:
            dump_route(extract_route(self.value), args.out + ".incumbent",
                       "INCUMBENT", TOTAL_GROUPS)
        except Exception as ex:  # never let bookkeeping kill the solve
            print(f"  (incumbent dump failed: {ex})", flush=True)

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = args.time
solver.parameters.num_workers = args.workers
solver.parameters.log_search_progress = True
if args.seed is not None:
    solver.parameters.random_seed = args.seed
    print(f"seed: {args.seed}", flush=True)
if args.all_different_circuit:
    solver.parameters.use_all_different_for_circuit = True
if args.probing_level is not None:
    solver.parameters.cp_model_probing_level = args.probing_level
if args.all_different_circuit or args.probing_level is not None:
    print(f"tuning: all_different_for_circuit="
          f"{bool(args.all_different_circuit)} probing_level="
          f"{args.probing_level if args.probing_level is not None else 'default(2)'}",
          flush=True)
if args.lns:
    # Ruin-and-recreate instead of one global search. Warm-started from a good
    # incumbent this is the productive mode: it releases a slice of the route
    # and repairs it exactly, which is how the external run's 319 appeared
    # ~40 s into an LNS-only solve. Pointless without --hint — there is no
    # incumbent to ruin.
    solver.parameters.use_lns_only = True
    solver.parameters.diversify_lns_params = True
    solver.parameters.solution_pool_size = 8
    solver.parameters.alternative_pool_size = 4
    solver.parameters.lns_initial_difficulty = args.lns_difficulty
    solver.parameters.lns_initial_deterministic_limit = args.lns_limit
    print(f"LNS-only portfolio: difficulty {args.lns_difficulty}, "
          f"deterministic limit {args.lns_limit}"
          + ("" if args.hint else "  — WARNING: no --hint, nothing to ruin"), flush=True)
status = solver.solve(m, Progress())
print(f"\nstatus: {solver.status_name(status)} after {solver.wall_time:.0f}s", flush=True)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    route = extract_route(solver.value)
    claimed = dump_route(route, args.out, solver.status_name(status), TOTAL_GROUPS)
    print(f"ROUTE: {len(route)} steps, {claimed}/{TOTAL_GROUPS} groups, "
          f"start {route[0]['id']}, ends at FINISH: {route[-1]['id'] == finish['id']}")
    print(f"wrote {args.out}")
elif status == cp_model.INFEASIBLE:
    if args.core and core_lit:
        core = [core_lit[i] for i in solver.sufficient_assumptions_for_infeasibility()
                if i in core_lit]
        print(f"UNSAT CORE — these {len(core)} group(s) cannot jointly be completed "
              f"after the frozen {len(prefix)}-step prefix:")
        for g in core:
            mem = [n for n in G["nodes"] if n["group"] == g]
            print(f"  g{g}: {len(mem)} members in "
                  f"{sorted({n.get('region') or '?' for n in mem})}")
    if args.repair is not None:
        print(f"repair INFEASIBLE: no completion exists after these {len(prefix)} "
              "steps — the fatal decision is inside the frozen prefix. Freeze less.")
    else:
        print("PROVEN INFEASIBLE: no route can claim all 322 groups exactly once. "
              "The wall is real, for every START and every chain at once.")
    sys.exit(2)
else:
    print("inconclusive within the time limit — neither route nor proof")
    sys.exit(3)
