"""Own tests for Assignment 3 (run from the repository root).

    python tests/test_algorithms.py                 # all tests (unittest, no extra packages)
    python tests/test_algorithms.py --demo          # print the route-helper calls used in ANALYSIS.md
    python tests/test_algorithms.py --write-cases   # regenerate tests/my_cases.jsonl and tests/TESTS.md
    python tools/run.py --input tests/my_cases.jsonl > tests/my_cases_actual.jsonl   # real JSONL adapter

Expected answers in HAND_CASES are derived by hand (justification strings), never copied
from the program's output. Non-unique answers are judged by tests/checkers.py (validity,
not equality), and the checkers themselves are tested with alternative valid answers
and invalid witnesses.
"""
import copy
import json
import os
import random
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "src", "Python"))

import algorithms as A          # noqa: E402
import checkers as C            # noqa: E402

W = 10 ** 9


def solve(req):
    """Tiny dispatcher mirroring the JSONL adapter (task name -> function)."""
    t = req["task"]
    if t == "ping":
        return {"status": "ready"}
    if t == "dsu":
        return A.dsu(req["n"], req["operations"])
    if t in ("kruskal", "prim"):
        return getattr(A, t)(req["n"], req["edges"])
    if t in ("scc", "topo"):
        return getattr(A, t)(req["n"], req["edges"])
    if t == "dag":
        return A.dag(req["n"], req["edges"], req["source"])
    raise ValueError(t)


def verify(req, res, expect=None):
    """Semantic check of one result; `expect` holds hand-derived facts."""
    expect = expect or {}
    t = req["task"]
    if t == "dsu":
        C.check_dsu(req["n"], req["operations"], res, expect.get("states"))
    elif t in ("kruskal", "prim"):
        C.check_mst(req["n"], req["edges"], res, expect.get("cost"), expect.get("components"))
    elif t == "scc":
        C.check_scc(req["n"], req["edges"], res, expect.get("partition"))
    elif t == "topo":
        C.check_topo(req["n"], req["edges"], res)
        if "acyclic" in expect:
            assert res["acyclic"] is expect["acyclic"]
    elif t == "dag":
        C.check_dag(req["n"], req["edges"], req["source"], res, expect.get("distance"))
        if "acyclic" in expect:
            assert res["acyclic"] is expect["acyclic"]


# ----------------------------------------------------------------- hand cases
# (name, request, why the expected answer is right, expected facts)
def _mst(name, n, edges, why, cost, comps):
    return [(f"{name} [{t}]", {"task": t, "n": n, "edges": edges}, why,
             {"cost": cost, "components": comps}) for t in ("kruskal", "prim")]


HAND_CASES = []
HAND_CASES += [
    ("dsu spec example", {"task": "dsu", "n": 4, "operations": [[0, 1], [1, 2], [0, 2], [3, 3]]},
     "0-1 gives {0,1}; 1-2 gives {0,1,2}; 0-2 and 3-3 change nothing.",
     {"states": [[3, 2], [2, 3], [2, 3], [2, 3]]}),
    ("dsu n=0", {"task": "dsu", "n": 0, "operations": []},
     "No vertices, no operations: states is empty, no initial state.", {"states": []}),
    ("dsu n=1 self union", {"task": "dsu", "n": 1, "operations": [[0, 0]]},
     "Single vertex stays one component of size 1.", {"states": [[1, 1]]}),
    ("dsu no operations", {"task": "dsu", "n": 5, "operations": []},
     "Zero operations means zero states (the initial state is not reported).", {"states": []}),
    ("dsu merges of equal-size trees",
     {"task": "dsu", "n": 6, "operations": [[0, 1], [2, 3], [1, 2], [4, 5], [3, 4]]},
     "{01}:5,2 ; {23}:4,2 ; {0123}:3,4 ; {45}:2,4 ; all six:1,6.",
     {"states": [[5, 2], [4, 2], [3, 4], [2, 4], [1, 6]]}),
]
HAND_CASES += _mst("mst spec example", 4, [[0, 1, 4], [1, 2, 2], [0, 2, 3]],
                   "Take weights 2 and 3 (ids 1,2); weight 4 closes a cycle; vertex 3 is isolated.", 5, 2)
HAND_CASES += _mst("mst n=0", 0, [], "Empty graph: cost 0, 0 components.", 0, 0)
HAND_CASES += _mst("mst only isolates", 3, [], "No edges: 3 components, cost 0.", 0, 3)
HAND_CASES += _mst("mst loops and parallel edges", 3,
                   [[0, 0, -5], [0, 1, 2], [0, 1, 1], [1, 2, 1]],
                   "Negative self-loop must be ignored; cheaper parallel edge (id 2) wins: 1+1.", 2, 1)
HAND_CASES += _mst("mst negative weights", 3, [[0, 1, -4], [1, 2, -3], [0, 2, -10]],
                   "Choose the two smallest weights, -10 and -4, they do not form a cycle.", -14, 1)
HAND_CASES += _mst("mst total beyond 32 bits", 4,
                   [[0, 1, W], [1, 2, W], [2, 3, W], [0, 3, W]],
                   "Any 3 of the 4 equal edges: 3*10^9 = 3000000000 > 2^31.", 3 * W, 1)
HAND_CASES += _mst("mst negative total beyond 32 bits", 4,
                   [[0, 1, -W], [1, 2, -W], [2, 3, -W], [0, 3, -W]],
                   "Any 3 of the 4 equal edges: -3000000000.", -3 * W, 1)
HAND_CASES += _mst("mst two components", 6, [[0, 1, 5], [1, 2, 1], [0, 2, 2], [3, 4, 7], [4, 3, 6]],
                   "{0,1,2}: 1+2=3; {3,4}: 6 (parallel edge id 4); vertex 5 isolated -> 9, 3 components.", 9, 3)
HAND_CASES += [
    ("scc spec example", {"task": "scc", "n": 4, "edges": [[0, 1], [1, 0], [1, 2], [0, 2], [2, 3]]},
     "0<->1 are mutually reachable; 2 and 3 are not on a cycle. Cross pairs: {01}->{2}, {2}->{3}.",
     {"partition": [0, 0, 2, 3]}),
    ("scc n=0", {"task": "scc", "n": 0, "edges": []}, "Nothing to label.", {"partition": []}),
    ("scc only isolates", {"task": "scc", "n": 3, "edges": []},
     "Three single-vertex SCCs and no condensation edges.", {"partition": [0, 1, 2]}),
    ("scc loop, duplicates",
     {"task": "scc", "n": 3, "edges": [[0, 0], [0, 1], [0, 1], [1, 2], [2, 1]]},
     "Loop is internal; {1,2} is a cycle; the duplicate 0->1 yields one condensation pair.",
     {"partition": [0, 1, 1]}),
    ("scc one big cycle", {"task": "scc", "n": 4, "edges": [[0, 1], [1, 2], [2, 3], [3, 0]]},
     "Every vertex reaches every other: one SCC, empty condensation.", {"partition": [0, 0, 0, 0]}),
    ("topo spec example", {"task": "topo", "n": 4, "edges": [[0, 2], [1, 2], [2, 3]]},
     "No cycle; 0 and 1 precede 2, 2 precedes 3.", {"acyclic": True}),
    ("topo n=0", {"task": "topo", "n": 0, "edges": []}, "Empty graph is acyclic.", {"acyclic": True}),
    ("topo self-loop", {"task": "topo", "n": 2, "edges": [[1, 1]]},
     "A self-loop is a cycle.", {"acyclic": False}),
    ("topo edge to finished vertex",
     {"task": "topo", "n": 4, "edges": [[0, 1], [0, 2], [1, 3], [2, 3], [0, 3]]},
     "Edges into the already finished vertex 3 are forward/cross edges, not cycles.", {"acyclic": True}),
    ("topo cycle in second component",
     {"task": "topo", "n": 5, "edges": [[0, 1], [2, 3], [3, 4], [4, 2]]},
     "2->3->4->2 is a cycle even though the first DFS tree is clean.", {"acyclic": False}),
    ("topo duplicate edges", {"task": "topo", "n": 2, "edges": [[0, 1], [0, 1]]},
     "Parallel edges do not make a cycle.", {"acyclic": True}),
    ("dag spec example",
     {"task": "dag", "n": 5, "source": 0, "edges": [[0, 1, 3], [0, 2, 8], [1, 2, -7], [2, 3, 4]]},
     "d1=3; d2=min(8,3-7)=-4; d3=-4+4=0; vertex 4 unreachable.",
     {"acyclic": True, "distance": [0, 3, -4, 0, None]}),
    ("dag cycle unreachable from source",
     {"task": "dag", "n": 4, "source": 0, "edges": [[0, 1, 1], [2, 3, 1], [3, 2, 1]]},
     "2<->3 is a cycle not reachable from 0; the whole graph must still be rejected.",
     {"acyclic": False}),
    ("dag n=1", {"task": "dag", "n": 1, "source": 0, "edges": []},
     "Only the source: distance [0], parent [-1].", {"acyclic": True, "distance": [0]}),
    ("dag unreachable and -1 cost",
     {"task": "dag", "n": 4, "source": 1, "edges": [[0, 1, 5], [1, 2, -1], [0, 3, 2]]},
     "From 1 only vertex 2 is reachable with the valid finite cost -1; 0 and 3 are unreachable (null).",
     {"acyclic": True, "distance": [None, 0, -1, None]}),
    ("dag parallel and tied edges",
     {"task": "dag", "n": 3, "source": 0,
      "edges": [[0, 1, 2], [0, 1, 2], [0, 1, 3], [1, 2, 1], [0, 2, 3]]},
     "d1=2 via id 0 or id 1; d2=3 via 1->2 (id 3) or directly (id 4): ties allowed.",
     {"acyclic": True, "distance": [0, 2, 3]}),
    ("dag totals beyond 32 bits",
     {"task": "dag", "n": 4, "source": 0, "edges": [[0, 1, W], [1, 2, W], [2, 3, W]]},
     "Distances 10^9, 2*10^9, 3*10^9.", {"acyclic": True, "distance": [0, W, 2 * W, 3 * W]}),
    ("dag negative totals beyond 32 bits",
     {"task": "dag", "n": 4, "source": 0, "edges": [[0, 1, -W], [1, 2, -W], [2, 3, -W]]},
     "Distances -10^9, -2*10^9, -3*10^9.", {"acyclic": True, "distance": [0, -W, -2 * W, -3 * W]}),
]


# -------------------------------------------------------------- random inputs
def rnd_graph(rng, n, m, weighted, lo=-9, hi=9):
    edges = []
    for _ in range(m):
        u, v = rng.randrange(n), rng.randrange(n)
        edges.append([u, v, rng.randint(lo, hi)] if weighted else [u, v])
    return edges


def rnd_dag_edges(rng, n, m, lo=-9, hi=9):
    perm = list(range(n))
    rng.shuffle(perm)
    edges = []
    for _ in range(m):
        a, b = sorted(rng.sample(range(n), 2))
        edges.append([perm[a], perm[b], rng.randint(lo, hi)])
    return edges


def timed(fn, *args):
    t0 = time.perf_counter()
    r = fn(*args)
    return r, time.perf_counter() - t0


# ------------------------------------------------------------------ the tests
class HandCases(unittest.TestCase):
    def test_hand_cases(self):
        for name, req, why, expect in HAND_CASES:
            with self.subTest(name):
                verify(req, solve(req), expect)

    def test_exact_dsu_and_unique_facts(self):
        # exact equality is only used where the answer is unique
        for name, req, why, expect in HAND_CASES:
            if req["task"] == "dsu":
                self.assertEqual(solve(req)["states"], expect["states"], name)
            if req["task"] == "dag" and "distance" in expect:
                self.assertEqual(solve(req)["distance"], expect["distance"], name)

    def test_ping(self):
        self.assertEqual(solve({"task": "ping"}), {"status": "ready"})


class RandomCrossChecks(unittest.TestCase):
    N_ITER = 400

    def test_dsu(self):
        rng = random.Random(1)
        for _ in range(self.N_ITER):
            n = rng.randint(0, 9)
            ops = [[rng.randrange(n), rng.randrange(n)] for _ in range(rng.randint(0, 14))] if n else []
            C.check_dsu(n, ops, A.dsu(n, ops))

    def test_mst_against_bruteforce(self):
        rng = random.Random(2)
        for _ in range(self.N_ITER):
            n = rng.randint(0, 7)
            m = rng.randint(0, 9) if n else 0
            edges = rnd_graph(rng, n, m, True, -6, 6) if n else []
            rk, rp = A.kruskal(n, edges), A.prim(n, edges)
            C.check_mst_optimal_small(n, edges, rk)
            C.check_mst_optimal_small(n, edges, rp)
            self.assertEqual(rk["cost"], rp["cost"])
            self.assertEqual(rk["components"], rp["components"])

    def test_scc(self):
        rng = random.Random(3)
        for _ in range(self.N_ITER):
            n = rng.randint(0, 8)
            edges = rnd_graph(rng, n, rng.randint(0, 16), False) if n else []
            res = A.scc(n, edges)
            C.check_scc(n, edges, res)
            for a, b in res["condensation"]:        # Kosaraju from G numbers SCCs topologically
                self.assertLess(a, b)

    def test_topo(self):
        rng = random.Random(4)
        for _ in range(self.N_ITER):
            n = rng.randint(0, 8)
            edges = rnd_graph(rng, n, rng.randint(0, 12), False) if n else []
            C.check_topo(n, edges, A.topo(n, edges))
            if n >= 2:                              # guaranteed acyclic variant
                dag_edges = [[u, v] for u, v, _ in rnd_dag_edges(rng, n, rng.randint(0, 12))]
                res = A.topo(n, dag_edges)
                self.assertTrue(res["acyclic"])
                C.check_topo(n, dag_edges, res)

    def test_dag(self):
        rng = random.Random(5)
        for _ in range(self.N_ITER):
            n = rng.randint(1, 8)
            src = rng.randrange(n)
            edges = rnd_graph(rng, n, rng.randint(0, 12), True)          # may contain cycles
            C.check_dag(n, edges, src, A.dag(n, edges, src))
            if n >= 2:
                e2 = rnd_dag_edges(rng, n, rng.randint(0, 14))           # always acyclic
                res = A.dag(n, e2, src)
                self.assertTrue(res["acyclic"])
                C.check_dag(n, e2, src, res)
                self.assertEqual(res["distance"], C.dag_distances_bellman_ford(n, e2, src))


class FullLimits(unittest.TestCase):
    """n = 100000 and m / q = 250000: correctness and (printed) running time."""
    N, M = 100_000, 250_000

    def test_dsu_full(self):
        rng = random.Random(10)
        ops = [[rng.randrange(self.N), rng.randrange(self.N)] for _ in range(self.M)]
        res, dt = timed(A.dsu, self.N, ops)
        # independent reference: merge explicit member lists, small into large
        owner = list(range(self.N))
        members = {i: [i] for i in range(self.N)}
        comps, largest, exp = self.N, 1, []
        for u, v in ops:
            a, b = owner[u], owner[v]
            if a != b:
                if len(members[a]) < len(members[b]):
                    a, b = b, a
                for x in members[b]:
                    owner[x] = a
                members[a].extend(members.pop(b))
                comps -= 1
                largest = max(largest, len(members[a]))
            exp.append([comps, largest])
        self.assertEqual(res["states"], exp)
        print(f"\n  dsu n={self.N} q={self.M}: {dt:.2f}s", end="")

    def test_dsu_chain_full(self):
        ops = [[i, i + 1] for i in range(self.N - 1)] + [[0, self.N - 1]] * 1000
        res = A.dsu(self.N, ops)
        self.assertEqual(res["states"][self.N - 2], [1, self.N])
        self.assertEqual(res["states"][-1], [1, self.N])

    def _connected_graph(self, rng):
        edges = [[rng.randrange(i), i, rng.randint(-W, W)] for i in range(1, self.N)]   # random tree
        while len(edges) < self.M:
            edges.append([rng.randrange(self.N), rng.randrange(self.N), rng.randint(-W, W)])
        rng.shuffle(edges)
        return edges

    def test_mst_full_connected_and_disconnected(self):
        rng = random.Random(11)
        graphs = [(self.N, self._connected_graph(rng))]
        half = self.N // 2          # only the first half is wired: 1 + 50000 components
        e = [[rng.randrange(i), i, rng.randint(-W, W)] for i in range(1, half)]
        while len(e) < self.M:
            e.append([rng.randrange(half), rng.randrange(half), rng.randint(-W, W)])
        graphs.append((self.N, e))
        for n, edges in graphs:
            rk, tk = timed(A.kruskal, n, edges)
            rp, tp = timed(A.prim, n, edges)
            C.check_mst(n, edges, rk)
            C.check_mst(n, edges, rp)
            self.assertEqual(rk["cost"], rp["cost"])
            self.assertEqual(rk["components"], rp["components"])
            print(f"\n  mst n={n} m={len(edges)} comps={rk['components']}: "
                  f"kruskal {tk:.2f}s, prim {tp:.2f}s", end="")

    def test_mst_deep_path_and_heavy_ties(self):
        n = self.N
        edges = [[i, i + 1, W] for i in range(n - 1)]
        for r in (A.kruskal(n, edges), A.prim(n, edges)):
            C.check_mst(n, edges, r, expect_cost=(n - 1) * W, expect_components=1)
        tie = [[i % 1000, (i * 7 + 1) % 1000, 0] for i in range(self.M)]   # all weights equal
        for r in (A.kruskal(1000, tie), A.prim(1000, tie)):
            C.check_mst(1000, tie, r)

    def test_scc_full_planted(self):
        rng = random.Random(12)
        block, nblocks = 100, 1000
        edges = []
        label = [v // block for v in range(self.N)]
        for b in range(nblocks):                       # a directed cycle inside each block
            base = b * block
            for i in range(block):
                edges.append([base + i, base + (i + 1) % block])
        while len(edges) < self.M:                     # random edges only forwards between blocks
            a, b = sorted(rng.sample(range(nblocks), 2))
            edges.append([a * block + rng.randrange(block), b * block + rng.randrange(block)])
        rng.shuffle(edges)
        res, dt = timed(A.scc, self.N, edges)
        C.check_scc(self.N, edges, res, truth_labels=label)
        print(f"\n  scc n={self.N} m={len(edges)}: {dt:.2f}s", end="")

    def test_scc_deep_chain_and_big_cycle(self):
        n = self.N
        chain = [[i, i + 1] for i in range(n - 1)]
        C.check_scc(n, chain, A.scc(n, chain), truth_labels=list(range(n)))
        cyc = chain + [[n - 1, 0]]
        r = A.scc(n, cyc)
        C.check_scc(n, cyc, r, truth_labels=[0] * n)
        self.assertEqual(r["condensation"], [])

    def test_topo_full(self):
        rng = random.Random(13)
        n = self.N
        chain = [[i, i + 1] for i in range(n - 1)]
        r = A.topo(n, chain)
        self.assertEqual(r["order"], list(range(n)))                     # deep chain
        C.check_topo(n, chain, r)
        edges = [[u, v] for u, v, _ in rnd_dag_edges(rng, n, self.M)]
        res, dt = timed(A.topo, n, edges)
        self.assertTrue(res["acyclic"])
        C.check_topo(n, edges, res)
        print(f"\n  topo n={n} m={self.M}: {dt:.2f}s", end="")
        cyc = chain + [[n - 1, 0]]                                       # one long cycle
        self.assertEqual(A.topo(n, cyc), {"acyclic": False, "order": []})

    def test_dag_full(self):
        rng = random.Random(14)
        n = self.N
        chain = [[i, i + 1, rng.randint(-W, W)] for i in range(n - 1)]
        res = A.dag(n, chain, 0)
        C.check_dag(n, chain, 0, res)
        self.assertEqual(A.reconstruct_route(chain, res["parent_edge"], 0, n - 1), list(range(n)))
        edges = rnd_dag_edges(rng, n, self.M, -W, W)
        src = edges[0][0]
        res, dt = timed(A.dag, n, edges, src)
        self.assertTrue(res["acyclic"])
        C.check_dag(n, edges, src, res)
        print(f"\n  dag n={n} m={self.M}: {dt:.2f}s", end="")

    def test_dag_cycle_unreachable_from_source_at_scale(self):
        n = self.N
        edges = [[i, i + 1, 1] for i in range(n // 2 - 1)]               # source 0 reaches 0..n/2-1
        edges += [[n - 3, n - 2, 1], [n - 2, n - 1, 1], [n - 1, n - 3, 1]]   # far-away cycle
        res = A.dag(n, edges, 0)
        self.assertEqual(res, {"acyclic": False, "distance": [], "parent_edge": []})


class StateReset(unittest.TestCase):
    def test_repeated_mixed_requests_in_one_process(self):
        reqs = [r for _, r, _, _ in HAND_CASES] + [{"task": "ping"}]
        first = [copy.deepcopy(solve(r)) for r in reqs]
        for _ in range(2):                                   # same batch again, in same process
            self.assertEqual([solve(r) for r in reqs], first)
        for r, want in zip(reversed(reqs), reversed(first)):  # reversed order: no hidden carry-over
            self.assertEqual(solve(r), want)

    def test_inputs_not_mutated(self):
        for _, req, _, _ in HAND_CASES:
            before = copy.deepcopy(req)
            solve(req)
            self.assertEqual(req, before)


class CheckerSelfTests(unittest.TestCase):
    """The checkers must accept alternative valid answers and reject invalid witnesses."""

    def test_mst_accepts_alternatives(self):
        edges = [[0, 1, 1], [0, 1, 1], [1, 2, 3]]
        for ids in ([0, 2], [1, 2], [2, 0]):
            C.check_mst(3, edges, {"cost": 4, "edge_ids": ids, "components": 1}, expect_cost=4)

    def test_mst_rejects_invalid_witnesses(self):
        edges = [[0, 1, 1], [1, 2, 1], [0, 2, 5], [2, 2, -9]]
        good = {"cost": 2, "edge_ids": [0, 1], "components": 1}
        C.check_mst(3, edges, good, expect_cost=2)
        bad = [
            {"cost": 2, "edge_ids": [0, 1], "components": 2},            # wrong component count
            {"cost": 3, "edge_ids": [0, 1], "components": 1},            # cost != sum of weights
            {"cost": 2, "edge_ids": [0, 0], "components": 1},            # repeated id
            {"cost": 1, "edge_ids": [0], "components": 1},               # too few edges
            {"cost": -7, "edge_ids": [0, 3], "components": 1},           # uses a self-loop
            {"cost": 6, "edge_ids": [0, 2], "components": 1},            # valid tree, not optimal
            {"cost": 2, "edge_ids": [0, 9], "components": 1},            # id out of range
        ]
        for b in bad:
            with self.assertRaises(C.Invalid, msg=str(b)):
                C.check_mst(3, edges, b, expect_cost=2)
        cyc = [[0, 1, 1], [1, 2, 1], [2, 0, 1], [3, 4, 1]]               # 5 vertices, 2 components
        with self.assertRaises(C.Invalid):                                # right count, but a cycle
            C.check_mst(5, cyc, {"cost": 3, "edge_ids": [0, 1, 2], "components": 2})

    def test_scc_accepts_relabelling_rejects_wrong(self):
        edges = [[0, 1], [1, 0], [1, 2], [0, 2], [2, 3]]
        C.check_scc(4, edges, {"component": [5, 5, 7, 9], "condensation": [[5, 7], [7, 9]]})
        C.check_scc(4, edges, {"component": [9, 9, 1, 0], "condensation": [[1, 0], [9, 1]]})
        bad = [
            {"component": [5, 5, 5, 9], "condensation": [[5, 9]]},                         # merged SCCs
            {"component": [5, 6, 7, 9], "condensation": [[5, 6], [6, 5], [6, 7], [5, 7], [7, 9]]},  # split SCC
            {"component": [5, 5, 7, 9], "condensation": [[5, 7]]},                          # pair missing
            {"component": [5, 5, 7, 9], "condensation": [[5, 7], [5, 7], [7, 9]]},          # duplicate
            {"component": [5, 5, 7, 9], "condensation": [[5, 7], [7, 9], [5, 5]]},          # internal edge
            {"component": [5, 5, 7, 9], "condensation": [[5, 7], [7, 9], [9, 5]]},          # invented pair
        ]
        for b in bad:
            with self.assertRaises(C.Invalid, msg=str(b)):
                C.check_scc(4, edges, b)

    def test_topo_accepts_alternatives_rejects_wrong(self):
        edges = [[0, 2], [1, 2], [2, 3]]
        for order in ([0, 1, 2, 3], [1, 0, 2, 3]):
            C.check_topo(4, edges, {"acyclic": True, "order": order})
        for bad in ({"acyclic": True, "order": [2, 0, 1, 3]},       # edge 0->2 goes backwards
                    {"acyclic": True, "order": [0, 1, 2]},          # vertex missing
                    {"acyclic": True, "order": [0, 1, 2, 2]},       # repeated vertex
                    {"acyclic": False, "order": []}):               # claims a cycle that is not there
            with self.assertRaises(C.Invalid):
                C.check_topo(4, edges, bad)
        with self.assertRaises(C.Invalid):                           # cyclic graph must have empty order
            C.check_topo(2, [[0, 1], [1, 0]], {"acyclic": False, "order": [0, 1]})

    def test_dag_accepts_alternative_parents_rejects_wrong(self):
        edges = [[0, 1, 2], [0, 1, 2], [1, 2, 1], [0, 2, 3]]
        base = {"acyclic": True, "distance": [0, 2, 3]}
        for par in ([-1, 0, 2], [-1, 1, 2], [-1, 0, 3], [-1, 1, 3]):
            C.check_dag(3, edges, 0, dict(base, parent_edge=par))
        bad = [
            dict(base, parent_edge=[-1, 2, 2]),                       # edge 2 ends at 2, not at 1
            dict(base, parent_edge=[-1, 0, 0]),                       # edge 0 ends at 1, not at 2
            dict(base, parent_edge=[-1, 0, -1]),                      # reachable vertex without parent
            dict(base, parent_edge=[0, 0, 2]),                        # source must have parent -1
            {"acyclic": True, "distance": [0, 2, 4], "parent_edge": [-1, 0, 2]},   # wrong distance
            {"acyclic": True, "distance": [0, 2, None], "parent_edge": [-1, 0, -1]},  # reachable as null
            {"acyclic": False, "distance": [], "parent_edge": []},    # graph is acyclic
        ]
        for b in bad:
            with self.assertRaises(C.Invalid, msg=str(b)):
                C.check_dag(3, edges, 0, b)
        e2 = [[1, 2, 4]]                                              # vertex 2 reachable only from 1
        with self.assertRaises(C.Invalid):                            # -1 used as 'unreachable' distance
            C.check_dag(3, e2, 0, {"acyclic": True, "distance": [0, -1, -1], "parent_edge": [-1, -1, -1]})
        C.check_dag(3, e2, 0, {"acyclic": True, "distance": [0, None, None], "parent_edge": [-1, -1, -1]})


class RouteHelper(unittest.TestCase):
    EDGES = [[0, 1, 3], [0, 2, 8], [1, 2, -7], [2, 3, 4]]

    def setUp(self):
        self.res = A.dag(5, self.EDGES, 0)

    def test_reachable_source_unreachable(self):
        par = self.res["parent_edge"]
        self.assertEqual(A.reconstruct_route(self.EDGES, par, 0, 3), [0, 1, 2, 3])
        self.assertEqual(A.reconstruct_route_edges(self.EDGES, par, 0, 3), [0, 2, 3])
        self.assertEqual(sum(self.EDGES[e][2] for e in [0, 2, 3]), self.res["distance"][3])
        self.assertEqual(A.reconstruct_route(self.EDGES, par, 0, 0), [0])
        self.assertEqual(A.reconstruct_route(self.EDGES, par, 0, 4), [])

    def test_tied_and_parallel_edges(self):
        edges = [[0, 1, 2], [0, 1, 2], [0, 1, 3], [1, 2, 1], [0, 2, 3]]
        res = A.dag(3, edges, 0)
        ids = A.reconstruct_route_edges(edges, res["parent_edge"], 0, 2)
        route = A.reconstruct_route(edges, res["parent_edge"], 0, 2)
        self.assertIn(route, ([0, 1, 2], [0, 2]))
        self.assertEqual(sum(edges[e][2] for e in ids), res["distance"][2])   # total weight
        for a, e in zip(route, ids):
            self.assertEqual(edges[e][0], a)                                   # direction
        self.assertEqual(edges[ids[-1]][1], 2)

    def test_cyclic_graph_gives_no_route(self):
        res = A.dag(2, [[0, 1, 1], [1, 0, 1]], 0)
        self.assertEqual(A.reconstruct_route([[0, 1, 1], [1, 0, 1]], res["parent_edge"], 0, 1), [])


# ------------------------------------------------------ demo / file generation
def demo():
    print("Route-helper calls (edge ID = original row position)\n")
    ex = RouteHelper.EDGES
    r = A.dag(5, ex, 0)
    print("graph A: n=5 source=0 edges", ex)
    print("  dag ->", json.dumps(r))
    for t in (3, 0, 4):
        ids = A.reconstruct_route_edges(ex, r["parent_edge"], 0, t)
        cost = None if ids is None else sum(ex[e][2] for e in ids)
        print(f"  reconstruct_route(target={t}) = {A.reconstruct_route(ex, r['parent_edge'], 0, t)}"
              f"  edge ids = {ids}  weight sum = {cost}  distance[{t}] = {r['distance'][t]}")
    tie = [[0, 1, 2], [0, 1, 2], [0, 1, 3], [1, 2, 1], [0, 2, 3]]
    r = A.dag(3, tie, 0)
    print("\ngraph B (parallel + tied): n=3 source=0 edges", tie)
    print("  dag ->", json.dumps(r))
    for t in (1, 2):
        ids = A.reconstruct_route_edges(tie, r["parent_edge"], 0, t)
        print(f"  reconstruct_route(target={t}) = {A.reconstruct_route(tie, r['parent_edge'], 0, t)}"
              f"  edge ids = {ids}  weight sum = {sum(tie[e][2] for e in ids)}  distance[{t}] = {r['distance'][t]}")


def write_cases():
    lines = [json.dumps({"task": "ping"})]
    md = ["# Own test cases\n",
          "Inputs: `tests/my_cases.jsonl` (one request per line). Run:\n",
          "```\npython tools/run.py --input tests/my_cases.jsonl > tests/my_cases_actual.jsonl\n"
          "python tests/test_algorithms.py\n```\n",
          "Each case below has a hand-derived justification; the *actual* column comes from "
          "`algorithms.py` and was accepted by the independent checkers in `tests/checkers.py`. "
          "For non-unique answers (marked *) validity, not equality, is what is checked.\n"]
    for name, req, why, expect in HAND_CASES:
        res = solve(req)
        verify(req, res, expect)                 # never write a case the checkers reject
        lines.append(json.dumps(req, separators=(",", ":")))
        star = "*" if req["task"] in ("kruskal", "prim", "scc", "topo") or \
            (req["task"] == "dag" and res.get("acyclic")) else ""
        md.append(f"## {name}\n\n- input: `{json.dumps(req, separators=(',', ':'))}`\n"
                  f"- expected (by hand): {why}\n"
                  f"- actual{star}: `{json.dumps(res, separators=(',', ':'))}`\n")
    with open(os.path.join(HERE, "my_cases.jsonl"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(HERE, "TESTS.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"wrote {len(lines)} requests to tests/my_cases.jsonl and tests/TESTS.md")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
    elif "--write-cases" in sys.argv:
        write_cases()
    else:
        unittest.main(verbosity=2)
