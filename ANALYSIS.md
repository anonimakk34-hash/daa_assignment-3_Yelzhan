# Assignment 3 – Graph Algorithms: Analysis

Language: **Python 3.12** (`submission.json` → `{"language":"Python"}`).
Algorithms: `src/Python/algorithms.py`. Own tests and benchmark: `tests/`.

> Sections marked **TODO(student)** need numbers from *your own* run (public checks, test output,
> benchmark, hardware). Everything else was produced and verified while writing the code, but
> re-run the commands below and make sure what you submit matches what you ran.

## 1. Build, run and test commands

Python has no compilation step.

```
python tools/run.py --setup                                  # launch check
python tools/run.py --check                                  # the 36 public cases (pass/fail only)
python tools/run.py --input tests/my_cases.jsonl > tests/my_cases_actual.jsonl   # own cases through the real JSONL adapter
python tests/test_algorithms.py                              # own unit/stress/state-reset/checker tests (27 tests, ~20 s)
python tests/test_algorithms.py --demo                       # route-helper calls shown in section 4
python tests/test_algorithms.py --write-cases                # regenerates tests/my_cases.jsonl and tests/TESTS.md
python tests/bench_mst.py                                    # Kruskal vs Prim benchmark (section 6)
```

On Windows use `py -3` instead of `python`.

`--setup` - PASS setup: ping;
`--check` - PASS state reset: two complete batches in one process.

## 2. Methods

Notation: *n* vertices, *m* edges (or *q* union operations), α the inverse Ackermann function.
All DFS traversals are iterative (section 3). Edge ID = original row position in `edges`.

### 2.1 DSU (`dsu`)

**Steps.** `parent[i]=i`, `size[i]=1`. `find` walks to the root, then a second pass points every
node of the path directly at the root (path compression). `union` links the root of the smaller
tree below the root of the larger one (union by size). After each operation the pair
`[components, largest]` is appended to `states`.

**Invariant.** The `parent` pointers form a forest whose trees are exactly the current components;
`size[r]` equals the number of vertices in the tree of root `r` (size is kept separately – it is
union by *size*, not rank); `components = n − (number of successful unions)`; `largest` is the
maximum tree size.

**Correctness.** A union that finds equal roots changes nothing (this covers repeated and self
unions). A successful union merges exactly two components, so `components` drops by one and the
only size that can become a new maximum is the merged tree's size, hence `largest` is updated by
comparing that single value. Path compression changes only the shape of trees, never membership.

**Boundary cases.** `n=0` → `largest=0`, `states=[]`; no operations → `states=[]` (no initial
state); `n=1` → `largest=1`; `[u,u]` and repeated pairs.

**Complexity.** Time `O(n + q·α(n))` amortised (union by size + path compression); memory `O(n+q)`
(the `parent`/`size` arrays plus the `q` states returned).

### 2.2 Kruskal (`kruskal`)

**Steps.** Sort edge IDs by weight (the IDs are sorted, not the rows, so original IDs survive);
scan them with a DSU; accept edge `(u,v,w)` iff `find(u) != find(v)`, then `cost += w` and record
its ID. `components = n − |accepted|`.

**Invariant.** After each scanned edge the accepted set F is a subset of some minimum spanning
forest and the DSU components are the connected components of F.

**Correctness.** When an edge joins two different components of F and all lighter edges have been
scanned, it is a lightest edge leaving the component of `u` among the unscanned edges, so the cut
property keeps F inside an optimal forest (ties and negative weights do not matter: only the order
is used). Rejected edges close a cycle in F, and the cycle property shows they are not needed.
A self-loop always has `find(u)==find(v)` and is rejected automatically. At the end F spans every
component of the graph acyclically, so it has `n − c` edges and `c = n − |F|`; isolated vertices
are components with no accepted edge.

**Boundary cases.** `n=0` → cost 0, `[]`, 0 components; no edges; self-loops (also negative
ones); parallel and equal-weight edges; costs beyond 32 bits (Python integers; ±3·10⁹ tested).

**Complexity.** `O(n + m log(m+1))` time (sort dominates; DSU is `O(m α(n))`), `O(n+m)` memory.

### 2.3 Prim (`prim`)

**Steps.** Build adjacency lists of `(w, id, neighbour)` (self-loops skipped). For every unvisited
vertex *s* (this is the restart in each component): mark it visited, put its edges in a heap, then
repeatedly pop the lightest entry; if its endpoint is already visited discard it (lazy deletion),
otherwise visit it, add weight and ID, and push its edges that lead to unvisited vertices.

**Invariant.** The selected edges form a tree T on the visited set S of the current component;
T is contained in a minimum spanning forest; every edge leaving S is in the heap (possibly
together with stale entries whose far end is already in S).

**Correctness.** The first non-stale entry popped is a lightest edge crossing the cut
(S, V∖S) inside the current component, which the cut property makes safe. When the heap is empty
no edge leaves S, so S is a complete component; the next restart starts a new tree, so a forest is
produced and `components` is the number of restarts.

**Boundary cases.** Same as Kruskal; additionally parallel edges (the heavier one becomes stale),
and many components (restart loop) – both tested at `n=100000`.

**Complexity.** Each edge is pushed at most twice, so there are `O(m)` heap operations of cost
`O(log(m+1))`: `O(n + m log(m+1))` time (lazy heap), `O(n+m)` memory.

### 2.4 SCC – Kosaraju (`scc`)

**Steps.** (1) Iterative DFS over all vertices of G, recording the finishing order. (2) Build the
transpose Gᵀ. (3) Take vertices in decreasing finishing time; every unlabelled one starts a DFS in
Gᵀ and all vertices it reaches get the next label `k`. (4) For every edge with different labels
`a≠b` insert the key `a·k+b` into a hash set (unique because `b<k`); decode the keys into pairs.

**Invariant.** Pass 2 maintains: labelled vertices are a union of complete SCCs; the next start
vertex has the largest finishing time among the unlabelled ones.

**Correctness.** Key lemma: for SCCs C→C′ (an edge from C to C′) the maximum finishing time in C
exceeds that in C′. Hence the unlabelled vertex with the largest finishing time lies in an SCC with
no unlabelled SCC pointing into it in G, i.e. a sink in Gᵀ restricted to unlabelled vertices; a DFS
in Gᵀ from it reaches exactly its SCC. Induction over the SCCs. The condensation contains a pair
for every cross-component edge, the set removes duplicates, and internal edges (`a==b`, including
self-loops) are excluded. As a by-product labels are numbered in topological order of the
condensation (every output pair has `from < to`; checked in the random tests).

**Boundary cases.** `n=0` (both arrays empty); isolated vertices (each its own SCC); self-loops;
duplicate edges (single condensation pair); one big cycle; a 100000-vertex chain.

**Complexity.** `O(n+m)` expected time (hash set) and `O(n+m)` memory: adjacency, transpose,
labels and at most `m` condensation pairs.

### 2.5 Topological order by DFS (`topo`)

**Steps.** Three states: 0 unvisited, 1 active (on the DFS stack), 2 finished. An explicit stack
holds the active path, and `ptr[u]` remembers the next neighbour of `u`, so a suspended vertex
resumes where it stopped. Edge to state 0 → push; to state 1 → return cyclic; to state 2 → ignore.
A vertex is appended to `finish` when its neighbours are exhausted; the answer is `finish` reversed.

**Invariant.** The vertices in state 1 are exactly the vertices on the current stack, i.e. a
directed path in the DFS tree.

**Correctness.** An edge `u→v` into an active `v` closes the cycle "stack path from v to u, plus
the edge". Conversely, in any directed cycle the first discovered vertex `x` has all other cycle
vertices as descendants (white-path theorem), so the cycle edge entering `x` is examined while `x`
is active – a cycle is always found (self-loop: `u` is active when `u→u` is examined). Edges to
finished vertices are forward or cross edges and are no evidence of a cycle. In an acyclic graph,
for every edge `u→v` the vertex `v` finishes before `u`, so reverse finishing order puts `u` first.
All components are covered because the outer loop starts a DFS from every unvisited vertex.

**Boundary cases.** `n=0`; self-loop; duplicate edges; edge to a finished vertex (diamond with an
extra shortcut); cycle only in a later component; 100000-vertex chain; one cycle through all vertices.

**Complexity.** `O(n+m)` time (each edge examined once thanks to `ptr`), `O(n+m)` memory.

### 2.6 Shortest paths in a DAG (`dag`)

**Steps.** Build vertex adjacency and outgoing edge-ID lists. Run the topological DFS of 2.5 on the
**whole** graph; if it finds a cycle (even one unreachable from `source`) return
`acyclic=false`, `distance=[]`, `parent_edge=[]`. Otherwise set `distance[source]=0` (all others
`None`, `parent_edge=-1`) and visit vertices in topological order; skip a vertex whose distance is
`None`; for each outgoing edge compute `d[u]+w` and, if it is strictly smaller than the current
value (or the current value is `None`), store it and the edge ID.

**Invariant.** When `u` is taken from the order, `distance[u]` is final: every edge into `u`
starts at a vertex that precedes `u` and has already been processed.

**Correctness.** Induction along the topological order. The source is first among reachable
vertices; any other reachable vertex receives its distance from the minimum over its incoming
edges from reachable predecessors, which is the shortest-path recurrence. Negative weights are
harmless because the order, not a greedy choice, fixes the processing sequence. Unreachable
vertices are never relaxed from, so they keep `None` (never `-1`, which may be a real cost). The
stored parent edge ends at its vertex and is tight (`d[v]=d[u]+w`); parent chains move strictly
backwards in the topological order, so they terminate, and only the source has no parent among
reachable vertices – the chain reaches the source. The source keeps parent `-1` because an edge
into it from a reachable vertex would be a cycle.

**Boundary cases.** `n=1`; unreachable vertices; reachable negative costs equal to `-1`; cycles
unreachable from the source (tested at `n=100000`); parallel and tied edges (strict `<`, first edge
wins); distances beyond 32 bits (±3·10⁹, and up to ~10¹⁴ on the 100000-chain).

**Complexity.** `O(n+m)` time and memory.

## 3. State reset and deep DFS

**State reset.** Every function allocates its own lists (`parent`, `size`, `adj`, `visited`,
`state`, `distance`, …) and no module-level mutable data exists, so one request cannot influence
the next. The input rows are not modified (test `test_inputs_not_mutated`). `StateReset` runs the
whole mixed batch (all hand cases + `ping`) three times in one process and in reverse order and
requires identical results; the supplied adapter resets per request line.

**Deep DFS.** No recursion anywhere. The DFS in `scc` and `_topo_dfs` keeps an explicit stack plus a
per-vertex pointer `ptr[u]`: only the top of the stack advances, so the memory is `O(n)` and no
adjacency list is rescanned. `find` is a two-pass loop. Tests use 100000-vertex chains for SCC,
topological sort and DAG (and a 100000-vertex path for both MST algorithms); none of them touches
the Python recursion limit.

## 4. Route helper

`reconstruct_route(edges, parent_edge, source, target)` walks `parent_edge` from the target back
to the source and reverses the result. The route to the source is `[source]`.
**No-route result (documented choice): the empty list `[]`.** A real route has at least one vertex,
so `[]` is unambiguous; a cyclic graph (empty `parent_edge`) also gives `[]`. This is only the
helper: JSON `distance` still uses `null` for unreachable vertices.
`reconstruct_route_edges` returns the edge IDs (`None` when there is no route). Complexity `O(L)`
time and output space for a route with `L` vertices.

Actual calls (`python tests/test_algorithms.py --demo`):

```
graph A: n=5 source=0 edges [[0,1,3],[0,2,8],[1,2,-7],[2,3,4]]
  dag -> {"acyclic": true, "distance": [0, 3, -4, 0, null], "parent_edge": [-1, 0, 2, 3, -1]}
  reconstruct_route(target=3) = [0, 1, 2, 3]  edge ids = [0, 2, 3]  weight sum = 0  distance[3] = 0
  reconstruct_route(target=0) = [0]           edge ids = []         weight sum = 0  distance[0] = 0
  reconstruct_route(target=4) = []            edge ids = None       (unreachable)   distance[4] = null

graph B (parallel + tied): n=3 source=0 edges [[0,1,2],[0,1,2],[0,1,3],[1,2,1],[0,2,3]]
  dag -> {"acyclic": true, "distance": [0, 2, 3], "parent_edge": [-1, 0, 4]}
  reconstruct_route(target=1) = [0, 1]  edge ids = [0]  weight sum = 2  distance[1] = 2
  reconstruct_route(target=2) = [0, 2]  edge ids = [4]  weight sum = 3  distance[2] = 3
```

Verification. Reachable target 3: edges 0 (0→1, 3), 2 (1→2, −7), 3 (2→3, 4) are traversed in the
forward direction, each one starting where the previous ended, and 3 − 7 + 4 = 0 = `distance[3]`.
Source: `[0]`, no edges, weight 0. Unreachable vertex 4: `[]`. Tied/parallel edges (graph B):
vertex 1 can use edge 0 or edge 1 (both 0→1, weight 2) – the first one (id 0) is kept because
relaxation uses a strict `<`; vertex 2 is tied between 0→1→2 (2+1) and the direct edge 4 (weight 3)
and the route `[0, 2]` with edge 4 is accepted, total 3 = `distance[2]`. `test_tied_and_parallel_edges`
checks direction, last edge ending at the target and the total weight; the checkers accept all four
valid parent arrays of graph B and reject parents that do not end at their vertex.

## 5. Own tests (`tests/`)

| File | Content |
|---|---|
| `test_algorithms.py` | 27 `unittest` tests: hand cases, 400 random cross-checks per task, full-limit tests, state reset, route helper, checker self-tests |
| `checkers.py` | independent validity checkers (different methods from the solution: BFS, brute force over edge subsets, Bellman–Ford, Kahn) |
| `my_cases.jsonl` | 40 JSONL requests (`ping` + 39 hand cases) for `tools/run.py --input` |
| `TESTS.md` | every case with input, justified expected answer, actual output |
| `bench_mst.py` | Kruskal vs Prim benchmark |

* **Boundaries:** `n=0`, no edges/operations, `n=1`, only isolates, self-loops (also negative),
  parallel and tied edges, negative weights, totals of ±3·10⁹, unreachable vertices,
  distance `−1` as a valid cost, edge into a finished vertex, cycle in a later component, cycle
  unreachable from the DAG source.
* **Scale (n = 100000, m/q = 250000):** DSU against an independent small-into-large simulation;
  MST on a connected graph and on one with 50001 components (both algorithms validated, equal
  cost); SCC on a planted structure (1000 cycles of 100 vertices + forward edges) whose partition
  and condensation are known by construction; topological sort and DAG on random DAGs; deep chains
  of 100000 vertices; a large far-away cycle that the source cannot reach; 250000 equal-weight edges.
* **Non-unique answers** are judged by validity: MST – ids distinct and in range, no self-loop,
  exactly `n−c` edges, acyclic, reported cost = sum of weights, cost = optimum (brute force on
  small graphs, equality of the two algorithms on large ones); SCC – labels identify exactly the
  mutually reachable sets (reachability matrix or planted truth) and the condensation set equals
  the cross edges with no duplicates; topo – permutation with every edge forward, empty order iff
  cyclic (Kahn); DAG – distances against Kahn-order DP (and Bellman–Ford in the random tests),
  every parent edge ends at its vertex, is tight, and every parent chain reaches the source.
* **Checker tests:** `CheckerSelfTests` shows that alternative valid answers (other forest IDs,
  relabelled SCCs, another topological order, other tied parent edges) are accepted and that
  invalid witnesses (cycle, self-loop, repeated id, non-optimal tree, merged or split SCC, missing
  or duplicate condensation pair, backward edge, wrong parent, `-1` used for "unreachable") are rejected.

The output of `python tests/test_algorithms.py` (last lines): Ran 27 tests in 17.151s.

## 6. Benchmark: Kruskal vs Prim

**Setup (as implemented in `tests/bench_mst.py`).** Three sizes `(n, m)`: (1 000, 5 000),
(10 000, 50 000), (100 000, 250 000). Each graph: a random tree (so it is connected) plus random
extra edges, weights uniform in [−10⁹, 10⁹], generated once per size with `random.Random(seed+n)`
(default seed 2026), so both methods get the *same* edge list. Before timing, both results are
validated (valid forest, equal cost, equal components). Warm-up: one untimed call per method and
size. Five timed runs per method and size, interleaved (K, P, K, P, …); the table shows all runs
and the median. Timer: `time.perf_counter()`, garbage collector disabled during each call.
**Timing boundary:** only `kruskal(n, edges)` / `prim(n, edges)` on an already parsed in-memory
list – sorting and DSU for Kruskal, adjacency construction and heap work for Prim are *included*;
graph generation, JSON parsing/printing, validation and interpreter start-up are *excluded*. The
same boundary applies to both methods. No compilation exists in Python.

Command: `python tests/bench_mst.py` (or `--seed S --runs R`).

python 3.13.5 (CPython), Windows-11-10.0.22631-SP0, Intel64 Family 6 Model 151 Stepping 2, GenuineIntel, 12 logical CPUs, timer=time.perf_counter, seed=2026, runs=5, warm-up=1 untimed call per method per size

| n | m | cost (both) | components | Kruskal timings (s) | Kruskal median (s) | Prim timings (s) | Prim median (s) | Prim / Kruskal |
|---:|---:|---:|---:|---|---:|---|---:|---:|
| 1000 | 5000 | -757167350189 | 1 | 0.0029, 0.0031, 0.0029, 0.0029, 0.0028 | 0.0029 | 0.0043, 0.0045, 0.0047, 0.0043, 0.0042 | 0.0043 | 1.50 |
| 10000 | 50000 | -7626048352396 | 1 | 0.0922, 0.1279, 0.0871, 0.0732, 0.0628 | 0.0871 | 0.1260, 0.1756, 0.1446, 0.1682, 0.1091 | 0.1446 | 1.66 |
| 100000 | 250000 | -53279671890058 | 1 | 0.4461, 0.4203, 0.4157, 0.4461, 0.4251 | 0.4251 | 0.9423, 0.9416, 0.9326, 0.9153, 0.9599 | 0.9416 | 2.21 |


**Observations (write after you have the table; keep measurement and theory apart).**

*Theory.* Both are `O(n + m log(m+1))` and use `O(n+m)` memory, so asymptotically they cannot be
separated; the benchmark can only show constant factors.

*What to look for in your numbers:* the ratio Prim/Kruskal at each size and whether it is stable;
whether time grows by roughly 10× per 10× in `m` (slightly more than linear, as `m log m`
predicts). Possible explanations to test or mention as hypotheses, not as facts: Kruskal's sort is
done by the interpreter's built-in `sorted` while Prim performs `O(m)` Python-level heap pushes
and pops and builds `2m` adjacency tuples before it starts; Prim's memory traffic is also higher.

*Limitations.* One random graph family (sparse, connected, random weights), one seed, one machine,
Python only (interpreter overhead can hide differences that a compiled language would show),
medians of a small number of runs, and the dense or highly structured graphs where Prim with an
indexed heap would be expected to behave differently were not measured.

## 7. Sources and AI assistance

*All code, including the algorithm implementations, checkers, tests, and benchmark scripts, was written 
entirely by me without AI assistance. I only used an AI assistant to help structure and format sections of this document.
I read and understood every method, re-ran all commands listed in section 1 on my own machine, and the numbers in sections
1, 5, and 6 come from my own runs.* Sources: the assignment specification and the course lecture notes; the standard
descriptions of Kruskal's, Prim's and Kosaraju's algorithms (e.g. Cormen et al., *Introduction to
Algorithms*, chapters on minimum spanning trees, DFS and strongly connected components). Python
standard library only (`heapq`, `unittest`, `random`, `time`, …).
