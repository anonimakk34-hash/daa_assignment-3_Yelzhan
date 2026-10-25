"""Assignment 3 - graph algorithms (Python 3.12+).

Pure functions: every call builds its own local data structures, so there is no
state that could leak from one request to the next (see ANALYSIS.md, "State reset").
Every DFS is iterative with an explicit stack and a per-vertex neighbour pointer,
so deep graphs (n = 100000 chain) cannot overflow the call stack.

Row formats: DSU operations [u, v]; SCC/topo edges [u, v]; weighted edges [u, v, w].
Edge ID = original position of the row in `edges`.
"""
from functools import wraps
from heapq import heapify, heappop, heappush


def _request_or_args(*keys):
    """The course stubs are called as f(request) with a dict; my tests call f(n, ...).
    Accept both: if the first argument is a dict, unpack the named fields from it."""
    def deco(fn):
        @wraps(fn)
        def wrapper(first, *args):
            if isinstance(first, dict):
                return fn(*(first[k] for k in keys))
            return fn(first, *args)
        return wrapper
    return deco


# --------------------------------------------------------------------------- DSU
class _DSU:
    """Disjoint-set union: path compression + union by size."""

    __slots__ = ("parent", "size")

    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n

    def find(self, x):
        p = self.parent
        root = x
        while p[root] != root:          # pass 1: locate the root
            root = p[root]
        while p[x] != root:             # pass 2: point every node on the path at the root
            p[x], x = root, p[x]
        return root

    def union(self, a, b):
        """Merge the sets of a and b. Return the new root, or -1 if already together."""
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return -1
        if self.size[ra] < self.size[rb]:   # attach the smaller tree below the larger
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        return ra


@_request_or_args("n", "operations")
def dsu(n, operations):
    d = _DSU(n)
    components = n
    largest = 1 if n > 0 else 0
    states = []
    for u, v in operations:
        root = d.union(u, v)
        if root != -1:
            components -= 1
            if d.size[root] > largest:
                largest = d.size[root]
        states.append([components, largest])
    return {"states": states}


# ----------------------------------------------------------------- Kruskal / Prim
@_request_or_args("n", "edges")
def kruskal(n, edges):
    order = sorted(range(len(edges)), key=lambda i: edges[i][2])  # stable, IDs preserved
    d = _DSU(n)
    cost = 0
    edge_ids = []
    for i in order:
        u, v, w = edges[i]
        if d.union(u, v) != -1:         # a self-loop has find(u) == find(v): never accepted
            cost += w
            edge_ids.append(i)
    return {"cost": cost, "edge_ids": edge_ids, "components": n - len(edge_ids)}


@_request_or_args("n", "edges")
def prim(n, edges):
    adj = [[] for _ in range(n)]
    for i, (u, v, w) in enumerate(edges):
        if u != v:                      # self-loops can never be in a forest
            adj[u].append((w, i, v))
            adj[v].append((w, i, u))
    visited = [False] * n
    cost = 0
    edge_ids = []
    components = 0
    for s in range(n):                  # restart in every component
        if visited[s]:
            continue
        components += 1
        visited[s] = True
        heap = list(adj[s])
        heapify(heap)
        while heap:
            w, i, v = heappop(heap)     # cheapest edge leaving the visited part (lazy deletion)
            if visited[v]:
                continue
            visited[v] = True
            cost += w
            edge_ids.append(i)
            for item in adj[v]:
                if not visited[item[2]]:
                    heappush(heap, item)
    return {"cost": cost, "edge_ids": edge_ids, "components": components}


# --------------------------------------------------------------------------- SCC
def _dfs_finish_order(n, adj):
    """Iterative DFS over the whole graph; vertices in order of finishing."""
    visited = [False] * n
    ptr = [0] * n                       # next neighbour index to examine for each vertex
    order = []
    for s in range(n):
        if visited[s]:
            continue
        visited[s] = True
        stack = [s]
        while stack:
            u = stack[-1]
            nbrs = adj[u]
            i = ptr[u]
            if i < len(nbrs):
                ptr[u] = i + 1
                v = nbrs[i]
                if not visited[v]:
                    visited[v] = True
                    stack.append(v)
            else:
                stack.pop()
                order.append(u)
    return order


@_request_or_args("n", "edges")
def scc(n, edges):
    adj = [[] for _ in range(n)]
    radj = [[] for _ in range(n)]       # transpose graph
    for u, v in edges:
        adj[u].append(v)
        radj[v].append(u)
    order = _dfs_finish_order(n, adj)   # pass 1 on G

    comp = [-1] * n
    k = 0
    for s in reversed(order):           # pass 2 on G^T, decreasing finish time
        if comp[s] != -1:
            continue
        comp[s] = k
        stack = [s]
        while stack:
            u = stack.pop()
            for v in radj[u]:
                if comp[v] == -1:
                    comp[v] = k
                    stack.append(v)
        k += 1

    seen = set()                        # hash-based deduplication of cross pairs
    for u, v in edges:
        a, b = comp[u], comp[v]
        if a != b:
            seen.add(a * k + b)
    condensation = [[x // k, x % k] for x in seen]   # order is unrestricted: no sort needed
    return {"component": comp, "condensation": condensation}


# ------------------------------------------------------------------ topological
def _topo_dfs(n, adj):
    """Three-state DFS (0 unvisited, 1 active, 2 finished).

    Returns a topological order (reverse finish order) or None if a directed cycle exists.
    """
    state = [0] * n
    ptr = [0] * n
    finish = []
    for s in range(n):
        if state[s]:
            continue
        state[s] = 1
        stack = [s]
        while stack:
            u = stack[-1]
            nbrs = adj[u]
            i = ptr[u]
            if i < len(nbrs):
                ptr[u] = i + 1
                v = nbrs[i]
                sv = state[v]
                if sv == 0:
                    state[v] = 1
                    stack.append(v)
                elif sv == 1:           # edge to an active vertex = back edge = cycle
                    return None
                # sv == 2: edge to a finished vertex, not a cycle
            else:
                state[u] = 2
                stack.pop()
                finish.append(u)
    finish.reverse()
    return finish


@_request_or_args("n", "edges")
def topo(n, edges):
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
    order = _topo_dfs(n, adj)
    if order is None:
        return {"acyclic": False, "order": []}
    return {"acyclic": True, "order": order}


# -------------------------------------------------------------------- DAG paths
@_request_or_args("n", "edges", "source")
def dag(n, edges, source):
    adj = [[] for _ in range(n)]        # neighbour vertices, for the cycle check
    out = [[] for _ in range(n)]        # outgoing edge IDs, for relaxation
    for i, (u, v, w) in enumerate(edges):
        adj[u].append(v)
        out[u].append(i)
    order = _topo_dfs(n, adj)           # checks the WHOLE graph, not just what source reaches
    if order is None:
        return {"acyclic": False, "distance": [], "parent_edge": []}

    distance = [None] * n               # None = unreachable (never -1: it can be a real cost)
    parent_edge = [-1] * n
    distance[source] = 0
    for u in order:
        du = distance[u]
        if du is None:                  # never relax out of an unreachable vertex
            continue
        for i in out[u]:
            _, v, w = edges[i]
            nd = du + w
            dv = distance[v]
            if dv is None or nd < dv:   # strict '<': first of several tied edges wins
                distance[v] = nd
                parent_edge[v] = i
    return {"acyclic": True, "distance": distance, "parent_edge": parent_edge}


# ----------------------------------------------------------------- route helper
def reconstruct_route_edges(edges, parent_edge, source, target):
    """Edge IDs of the selected route source -> target, in travel order.

    [] for target == source (zero edges); None when there is no route.
    """
    if not parent_edge:                 # cyclic graph: dag() returned empty arrays
        return None
    if target == source:
        return []
    route = []
    v = target
    for _ in range(len(parent_edge)):   # a valid parent chain has fewer than n edges
        e = parent_edge[v]
        if e == -1 or edges[e][1] != v:  # unreachable target, or a parent not ending at v
            return None
        route.append(e)
        v = edges[e][0]
        if v == source:
            route.reverse()
            return route
    return None


def reconstruct_route(edges, parent_edge, source, target):
    """Vertex sequence source -> ... -> target built from `parent_edge`.

    The route to the source itself is [source].
    NO-ROUTE RESULT (documented choice): an empty list []. A real route always
    contains at least one vertex, so [] can never be confused with a valid answer.
    """
    ids = reconstruct_route_edges(edges, parent_edge, source, target)
    if ids is None:
        return []
    return [source] + [edges[e][1] for e in ids]
