# Own test cases

Inputs: `tests/my_cases.jsonl` (one request per line). Run:

```
python tools/run.py --input tests/my_cases.jsonl > tests/my_cases_actual.jsonl
python tests/test_algorithms.py
```

Each case below has a hand-derived justification; the *actual* column comes from `algorithms.py` and was accepted by the independent checkers in `tests/checkers.py`. For non-unique answers (marked *) validity, not equality, is what is checked.

## dsu spec example

- input: `{"task":"dsu","n":4,"operations":[[0,1],[1,2],[0,2],[3,3]]}`
- expected (by hand): 0-1 gives {0,1}; 1-2 gives {0,1,2}; 0-2 and 3-3 change nothing.
- actual: `{"states":[[3,2],[2,3],[2,3],[2,3]]}`

## dsu n=0

- input: `{"task":"dsu","n":0,"operations":[]}`
- expected (by hand): No vertices, no operations: states is empty, no initial state.
- actual: `{"states":[]}`

## dsu n=1 self union

- input: `{"task":"dsu","n":1,"operations":[[0,0]]}`
- expected (by hand): Single vertex stays one component of size 1.
- actual: `{"states":[[1,1]]}`

## dsu no operations

- input: `{"task":"dsu","n":5,"operations":[]}`
- expected (by hand): Zero operations means zero states (the initial state is not reported).
- actual: `{"states":[]}`

## dsu merges of equal-size trees

- input: `{"task":"dsu","n":6,"operations":[[0,1],[2,3],[1,2],[4,5],[3,4]]}`
- expected (by hand): {01}:5,2 ; {23}:4,2 ; {0123}:3,4 ; {45}:2,4 ; all six:1,6.
- actual: `{"states":[[5,2],[4,2],[3,4],[2,4],[1,6]]}`

## mst spec example [kruskal]

- input: `{"task":"kruskal","n":4,"edges":[[0,1,4],[1,2,2],[0,2,3]]}`
- expected (by hand): Take weights 2 and 3 (ids 1,2); weight 4 closes a cycle; vertex 3 is isolated.
- actual*: `{"cost":5,"edge_ids":[1,2],"components":2}`

## mst spec example [prim]

- input: `{"task":"prim","n":4,"edges":[[0,1,4],[1,2,2],[0,2,3]]}`
- expected (by hand): Take weights 2 and 3 (ids 1,2); weight 4 closes a cycle; vertex 3 is isolated.
- actual*: `{"cost":5,"edge_ids":[2,1],"components":2}`

## mst n=0 [kruskal]

- input: `{"task":"kruskal","n":0,"edges":[]}`
- expected (by hand): Empty graph: cost 0, 0 components.
- actual*: `{"cost":0,"edge_ids":[],"components":0}`

## mst n=0 [prim]

- input: `{"task":"prim","n":0,"edges":[]}`
- expected (by hand): Empty graph: cost 0, 0 components.
- actual*: `{"cost":0,"edge_ids":[],"components":0}`

## mst only isolates [kruskal]

- input: `{"task":"kruskal","n":3,"edges":[]}`
- expected (by hand): No edges: 3 components, cost 0.
- actual*: `{"cost":0,"edge_ids":[],"components":3}`

## mst only isolates [prim]

- input: `{"task":"prim","n":3,"edges":[]}`
- expected (by hand): No edges: 3 components, cost 0.
- actual*: `{"cost":0,"edge_ids":[],"components":3}`

## mst loops and parallel edges [kruskal]

- input: `{"task":"kruskal","n":3,"edges":[[0,0,-5],[0,1,2],[0,1,1],[1,2,1]]}`
- expected (by hand): Negative self-loop must be ignored; cheaper parallel edge (id 2) wins: 1+1.
- actual*: `{"cost":2,"edge_ids":[2,3],"components":1}`

## mst loops and parallel edges [prim]

- input: `{"task":"prim","n":3,"edges":[[0,0,-5],[0,1,2],[0,1,1],[1,2,1]]}`
- expected (by hand): Negative self-loop must be ignored; cheaper parallel edge (id 2) wins: 1+1.
- actual*: `{"cost":2,"edge_ids":[2,3],"components":1}`

## mst negative weights [kruskal]

- input: `{"task":"kruskal","n":3,"edges":[[0,1,-4],[1,2,-3],[0,2,-10]]}`
- expected (by hand): Choose the two smallest weights, -10 and -4, they do not form a cycle.
- actual*: `{"cost":-14,"edge_ids":[2,0],"components":1}`

## mst negative weights [prim]

- input: `{"task":"prim","n":3,"edges":[[0,1,-4],[1,2,-3],[0,2,-10]]}`
- expected (by hand): Choose the two smallest weights, -10 and -4, they do not form a cycle.
- actual*: `{"cost":-14,"edge_ids":[2,0],"components":1}`

## mst total beyond 32 bits [kruskal]

- input: `{"task":"kruskal","n":4,"edges":[[0,1,1000000000],[1,2,1000000000],[2,3,1000000000],[0,3,1000000000]]}`
- expected (by hand): Any 3 of the 4 equal edges: 3*10^9 = 3000000000 > 2^31.
- actual*: `{"cost":3000000000,"edge_ids":[0,1,2],"components":1}`

## mst total beyond 32 bits [prim]

- input: `{"task":"prim","n":4,"edges":[[0,1,1000000000],[1,2,1000000000],[2,3,1000000000],[0,3,1000000000]]}`
- expected (by hand): Any 3 of the 4 equal edges: 3*10^9 = 3000000000 > 2^31.
- actual*: `{"cost":3000000000,"edge_ids":[0,1,2],"components":1}`

## mst negative total beyond 32 bits [kruskal]

- input: `{"task":"kruskal","n":4,"edges":[[0,1,-1000000000],[1,2,-1000000000],[2,3,-1000000000],[0,3,-1000000000]]}`
- expected (by hand): Any 3 of the 4 equal edges: -3000000000.
- actual*: `{"cost":-3000000000,"edge_ids":[0,1,2],"components":1}`

## mst negative total beyond 32 bits [prim]

- input: `{"task":"prim","n":4,"edges":[[0,1,-1000000000],[1,2,-1000000000],[2,3,-1000000000],[0,3,-1000000000]]}`
- expected (by hand): Any 3 of the 4 equal edges: -3000000000.
- actual*: `{"cost":-3000000000,"edge_ids":[0,1,2],"components":1}`

## mst two components [kruskal]

- input: `{"task":"kruskal","n":6,"edges":[[0,1,5],[1,2,1],[0,2,2],[3,4,7],[4,3,6]]}`
- expected (by hand): {0,1,2}: 1+2=3; {3,4}: 6 (parallel edge id 4); vertex 5 isolated -> 9, 3 components.
- actual*: `{"cost":9,"edge_ids":[1,2,4],"components":3}`

## mst two components [prim]

- input: `{"task":"prim","n":6,"edges":[[0,1,5],[1,2,1],[0,2,2],[3,4,7],[4,3,6]]}`
- expected (by hand): {0,1,2}: 1+2=3; {3,4}: 6 (parallel edge id 4); vertex 5 isolated -> 9, 3 components.
- actual*: `{"cost":9,"edge_ids":[2,1,4],"components":3}`

## scc spec example

- input: `{"task":"scc","n":4,"edges":[[0,1],[1,0],[1,2],[0,2],[2,3]]}`
- expected (by hand): 0<->1 are mutually reachable; 2 and 3 are not on a cycle. Cross pairs: {01}->{2}, {2}->{3}.
- actual*: `{"component":[0,0,1,2],"condensation":[[0,1],[1,2]]}`

## scc n=0

- input: `{"task":"scc","n":0,"edges":[]}`
- expected (by hand): Nothing to label.
- actual*: `{"component":[],"condensation":[]}`

## scc only isolates

- input: `{"task":"scc","n":3,"edges":[]}`
- expected (by hand): Three single-vertex SCCs and no condensation edges.
- actual*: `{"component":[2,1,0],"condensation":[]}`

## scc loop, duplicates

- input: `{"task":"scc","n":3,"edges":[[0,0],[0,1],[0,1],[1,2],[2,1]]}`
- expected (by hand): Loop is internal; {1,2} is a cycle; the duplicate 0->1 yields one condensation pair.
- actual*: `{"component":[0,1,1],"condensation":[[0,1]]}`

## scc one big cycle

- input: `{"task":"scc","n":4,"edges":[[0,1],[1,2],[2,3],[3,0]]}`
- expected (by hand): Every vertex reaches every other: one SCC, empty condensation.
- actual*: `{"component":[0,0,0,0],"condensation":[]}`

## topo spec example

- input: `{"task":"topo","n":4,"edges":[[0,2],[1,2],[2,3]]}`
- expected (by hand): No cycle; 0 and 1 precede 2, 2 precedes 3.
- actual*: `{"acyclic":true,"order":[1,0,2,3]}`

## topo n=0

- input: `{"task":"topo","n":0,"edges":[]}`
- expected (by hand): Empty graph is acyclic.
- actual*: `{"acyclic":true,"order":[]}`

## topo self-loop

- input: `{"task":"topo","n":2,"edges":[[1,1]]}`
- expected (by hand): A self-loop is a cycle.
- actual*: `{"acyclic":false,"order":[]}`

## topo edge to finished vertex

- input: `{"task":"topo","n":4,"edges":[[0,1],[0,2],[1,3],[2,3],[0,3]]}`
- expected (by hand): Edges into the already finished vertex 3 are forward/cross edges, not cycles.
- actual*: `{"acyclic":true,"order":[0,2,1,3]}`

## topo cycle in second component

- input: `{"task":"topo","n":5,"edges":[[0,1],[2,3],[3,4],[4,2]]}`
- expected (by hand): 2->3->4->2 is a cycle even though the first DFS tree is clean.
- actual*: `{"acyclic":false,"order":[]}`

## topo duplicate edges

- input: `{"task":"topo","n":2,"edges":[[0,1],[0,1]]}`
- expected (by hand): Parallel edges do not make a cycle.
- actual*: `{"acyclic":true,"order":[0,1]}`

## dag spec example

- input: `{"task":"dag","n":5,"source":0,"edges":[[0,1,3],[0,2,8],[1,2,-7],[2,3,4]]}`
- expected (by hand): d1=3; d2=min(8,3-7)=-4; d3=-4+4=0; vertex 4 unreachable.
- actual*: `{"acyclic":true,"distance":[0,3,-4,0,null],"parent_edge":[-1,0,2,3,-1]}`

## dag cycle unreachable from source

- input: `{"task":"dag","n":4,"source":0,"edges":[[0,1,1],[2,3,1],[3,2,1]]}`
- expected (by hand): 2<->3 is a cycle not reachable from 0; the whole graph must still be rejected.
- actual: `{"acyclic":false,"distance":[],"parent_edge":[]}`

## dag n=1

- input: `{"task":"dag","n":1,"source":0,"edges":[]}`
- expected (by hand): Only the source: distance [0], parent [-1].
- actual*: `{"acyclic":true,"distance":[0],"parent_edge":[-1]}`

## dag unreachable and -1 cost

- input: `{"task":"dag","n":4,"source":1,"edges":[[0,1,5],[1,2,-1],[0,3,2]]}`
- expected (by hand): From 1 only vertex 2 is reachable with the valid finite cost -1; 0 and 3 are unreachable (null).
- actual*: `{"acyclic":true,"distance":[null,0,-1,null],"parent_edge":[-1,-1,1,-1]}`

## dag parallel and tied edges

- input: `{"task":"dag","n":3,"source":0,"edges":[[0,1,2],[0,1,2],[0,1,3],[1,2,1],[0,2,3]]}`
- expected (by hand): d1=2 via id 0 or id 1; d2=3 via 1->2 (id 3) or directly (id 4): ties allowed.
- actual*: `{"acyclic":true,"distance":[0,2,3],"parent_edge":[-1,0,4]}`

## dag totals beyond 32 bits

- input: `{"task":"dag","n":4,"source":0,"edges":[[0,1,1000000000],[1,2,1000000000],[2,3,1000000000]]}`
- expected (by hand): Distances 10^9, 2*10^9, 3*10^9.
- actual*: `{"acyclic":true,"distance":[0,1000000000,2000000000,3000000000],"parent_edge":[-1,0,1,2]}`

## dag negative totals beyond 32 bits

- input: `{"task":"dag","n":4,"source":0,"edges":[[0,1,-1000000000],[1,2,-1000000000],[2,3,-1000000000]]}`
- expected (by hand): Distances -10^9, -2*10^9, -3*10^9.
- actual*: `{"acyclic":true,"distance":[0,-1000000000,-2000000000,-3000000000],"parent_edge":[-1,0,1,2]}`
