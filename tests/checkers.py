"""Independent semantic checkers for the non-unique answers of Assignment 3.

They deliberately do NOT import algorithms.py: every reference (BFS, brute force,
Bellman-Ford, Kahn) is a different method from the one under test.
Each check_* raises Invalid with a message when the answer is not valid.
"""
from collections import deque
from itertools import combinations


class Invalid(Exception):
    pass


def _is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def _need(cond, msg):
    if not cond:
        raise Invalid(msg)


# ---------------------------------------------------------------- references
def component_count(n, edges):
    """Connected components of an undirected graph by BFS."""
    adj = [[] for _ in range(n)]
    for e in edges:
        adj[e[0]].append(e[1])
        adj[e[1]].append(e[0])
    seen = [False] * n
    c = 0
    for s in range(n):
        if seen[s]:
            continue
        c += 1
        seen[s] = True
        q = deque([s])
        while q:
            u = q.popleft()
            for v in adj[u]:
                if not seen[v]:
                    seen[v] = True
                    q.append(v)
    return c


class _Tiny:
    """Minimal union-find used only for verification."""

    def __init__(self, n):
        self.p = list(range(n))

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a == b:
            return False
        self.p[a] = b
        return True


def mst_bruteforce(n, edges):
    """Optimum forest cost by trying every subset of n-c non-loop edges (tiny graphs only)."""
    c = component_count(n, edges)
    need = n - c
    cand = [i for i, e in enumerate(edges) if e[0] != e[1]]
    best = None
    for subset in combinations(cand, need):
        t = _Tiny(n)
        if all(t.union(edges[i][0], edges[i][1]) for i in subset):
            s = sum(edges[i][2] for i in subset)
            if best is None or s < best:
                best = s
    return (0 if need == 0 else best), c


def reach_matrix(n, edges):
    adj = [[] for _ in range(n)]
    for e in edges:
        adj[e[0]].append(e[1])
    reach = []
    for s in range(n):
        seen = [False] * n
        seen[s] = True
        q = deque([s])
        while q:
            u = q.popleft()
            for v in adj[u]:
                if not seen[v]:
                    seen[v] = True
                    q.append(v)
        reach.append(seen)
    return reach


def kahn_is_acyclic(n, edges):
    indeg = [0] * n
    adj = [[] for _ in range(n)]
    for e in edges:
        adj[e[0]].append(e[1])
        indeg[e[1]] += 1
    q = deque(v for v in range(n) if indeg[v] == 0)
    done = 0
    while q:
        u = q.popleft()
        done += 1
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    return done == n


def dag_distances_kahn(n, edges, source):
    """Reference distances for an acyclic graph, computed along Kahn's order."""
    indeg = [0] * n
    out = [[] for _ in range(n)]
    for u, v, w in edges:
        out[u].append((v, w))
        indeg[v] += 1
    dist = [None] * n
    dist[source] = 0
    q = deque(v for v in range(n) if indeg[v] == 0)
    while q:
        u = q.popleft()
        for v, w in out[u]:
            if dist[u] is not None and (dist[v] is None or dist[u] + w < dist[v]):
                dist[v] = dist[u] + w
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    return dist


def dag_distances_bellman_ford(n, edges, source):
    """Second, unrelated reference (valid because a DAG has no negative cycle)."""
    dist = [None] * n
    dist[source] = 0
    for _ in range(max(n - 1, 1)):
        changed = False
        for u, v, w in edges:
            if dist[u] is not None and (dist[v] is None or dist[u] + w < dist[v]):
                dist[v] = dist[u] + w
                changed = True
        if not changed:
            break
    return dist


# ------------------------------------------------------------------ checkers
def check_dsu(n, operations, res, expected=None):
    """States compared with a naive relabelling simulation (or a given expected list)."""
    _need("states" in res, "missing 'states'")
    states = res["states"]
    _need(len(states) == len(operations), "wrong number of states")
    label = list(range(n))
    exp = []
    for u, v in operations:
        a, b = label[u], label[v]
        if a != b:
            label = [a if x == b else x for x in label]
        counts = {}
        for x in label:
            counts[x] = counts.get(x, 0) + 1
        exp.append([len(counts), max(counts.values()) if counts else 0])
    if expected is not None:
        _need(expected == exp, "hand-written expectation disagrees with the simulation")
    _need([list(s) for s in states] == exp, "states differ from the reference")


def check_mst(n, edges, res, expect_cost=None, expect_components=None):
    for key in ("cost", "edge_ids", "components"):
        _need(key in res, f"missing '{key}'")
    ids = res["edge_ids"]
    _need(all(_is_int(i) for i in ids), "edge_ids must be integers")
    _need(len(set(ids)) == len(ids), "repeated edge id")
    _need(all(0 <= i < len(edges) for i in ids), "edge id out of range")
    _need(all(edges[i][0] != edges[i][1] for i in ids), "self-loop selected")
    c = component_count(n, edges)
    _need(res["components"] == c, f"components {res['components']} != {c}")
    _need(len(ids) == n - c, f"forest must have n-c = {n - c} edges, got {len(ids)}")
    t = _Tiny(n)
    for i in ids:
        _need(t.union(edges[i][0], edges[i][1]), "selected edges contain a cycle")
    # n-c acyclic edges inside the graph's own components => spans every component
    cost = sum(edges[i][2] for i in ids)
    _need(res["cost"] == cost, f"reported cost {res['cost']} != sum of selected weights {cost}")
    if expect_cost is not None:
        _need(cost == expect_cost, f"cost {cost} != expected optimum {expect_cost}")
    if expect_components is not None:
        _need(c == expect_components, "hand-written component count disagrees")
    return cost


def check_mst_optimal_small(n, edges, res):
    opt, _ = mst_bruteforce(n, edges)
    check_mst(n, edges, res, expect_cost=opt)


def _canon_partition(labels):
    first = {}
    out = []
    for i, x in enumerate(labels):
        first.setdefault(x, i)
        out.append(first[x])
    return out


def check_scc(n, edges, res, truth_labels=None):
    for key in ("component", "condensation"):
        _need(key in res, f"missing '{key}'")
    comp, cond = res["component"], res["condensation"]
    _need(len(comp) == n, "component must have n labels")
    _need(all(_is_int(x) and x >= 0 for x in comp), "labels must be non-negative integers")
    if truth_labels is None:
        reach = reach_matrix(n, edges)
        truth = [min(v for v in range(n) if reach[u][v] and reach[v][u]) for u in range(n)]
    else:
        truth = _canon_partition(truth_labels)
    _need(_canon_partition(comp) == truth, "labels do not identify exactly the SCCs")
    expected = {(comp[u], comp[v]) for u, v, *_ in edges if comp[u] != comp[v]}
    got = [tuple(p) for p in cond]
    _need(len(set(got)) == len(got), "duplicate condensation pair")
    _need(set(got) == expected, "condensation pairs differ from the cross-component edges")


def check_topo(n, edges, res):
    acyclic = kahn_is_acyclic(n, edges)
    _need(res.get("acyclic") is acyclic, f"acyclic should be {acyclic}")
    if not acyclic:
        _need(res.get("order") == [], "order must be empty for a cyclic graph")
        return
    order = res["order"]
    _need(sorted(order) == list(range(n)), "order must contain every vertex exactly once")
    pos = [0] * n
    for i, v in enumerate(order):
        pos[v] = i
    for u, v, *_ in edges:
        _need(pos[u] < pos[v], f"edge {u}->{v} goes backwards")


def check_dag(n, edges, source, res, expect_distance=None):
    acyclic = kahn_is_acyclic(n, edges)
    _need(res.get("acyclic") is acyclic, f"acyclic should be {acyclic}")
    if not acyclic:
        _need(res.get("distance") == [] and res.get("parent_edge") == [],
              "cyclic graph needs empty distance and parent_edge")
        return
    dist, par = res["distance"], res["parent_edge"]
    _need(len(dist) == n and len(par) == n, "arrays must have length n")
    ref = dag_distances_kahn(n, edges, source)
    _need(dist == ref, "distances differ from the reference")
    if expect_distance is not None:
        _need(dist == expect_distance, "hand-written expectation disagrees")
    for v in range(n):
        if v == source:
            _need(dist[v] == 0 and par[v] == -1, "source needs distance 0, parent -1")
        elif dist[v] is None:
            _need(par[v] == -1, "unreachable vertex needs parent_edge -1")
        else:
            e = par[v]
            _need(_is_int(e) and 0 <= e < len(edges), f"vertex {v}: bad parent edge id")
            u, head, w = edges[e]
            _need(head == v, f"vertex {v}: parent edge {e} does not end at it")
            _need(dist[u] is not None and dist[u] + w == dist[v],
                  f"vertex {v}: parent edge {e} is not tight")
    # following parents must reach the source (memoised, so the whole check stays O(n))
    ok = [False] * n
    ok[source] = True
    for v in range(n):
        if dist[v] is None or ok[v]:
            continue
        path, x = [], v
        while not ok[x]:
            _need(len(path) <= n, f"parent chain of {v} does not reach the source")
            path.append(x)
            x = edges[par[x]][0]
        for y in path:
            ok[y] = True
