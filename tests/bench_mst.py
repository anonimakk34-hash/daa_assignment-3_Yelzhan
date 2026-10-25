"""Kruskal vs Prim on the SAME graphs at three sizes (run from the repository root).

    python tests/bench_mst.py                 # default seed 2026, 5 timed runs per method per size
    python tests/bench_mst.py --seed 7 --runs 7

Method
  * graphs: random tree on n vertices (guarantees a connected graph) plus extra random edges up
    to m; weights uniform in [-10^9, 10^9]; generated once per size from `random.Random(seed + n)`,
    so Kruskal and Prim receive the identical edge list;
  * before any timing, both results are validated (valid forest, equal cost and components);
  * warm-up: one untimed call per method per size;
  * timer: time.perf_counter(); garbage collector disabled during each timed call;
  * timing boundary: ONLY the call algorithms.kruskal(n, edges) / algorithms.prim(n, edges)
    on an already parsed in-memory edge list. Included: sorting + DSU (Kruskal), adjacency
    construction + heap work (Prim). Excluded: graph generation, JSON parsing/printing,
    validation, interpreter start-up. Python has no compilation step.
  * runs of the two methods are interleaved (K, P, K, P, ...) so drift affects both equally.
Prints a Markdown table to paste into ANALYSIS.md, plus the environment.
"""
import argparse
import gc
import os
import platform
import random
import statistics
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "src", "Python"))

import algorithms as A      # noqa: E402
import checkers as C        # noqa: E402

SIZES = [(1_000, 5_000), (10_000, 50_000), (100_000, 250_000)]
W = 10 ** 9


def make_graph(n, m, seed):
    rng = random.Random(seed + n)
    edges = [[rng.randrange(i), i, rng.randint(-W, W)] for i in range(1, n)]
    while len(edges) < m:
        edges.append([rng.randrange(n), rng.randrange(n), rng.randint(-W, W)])
    rng.shuffle(edges)
    return edges


def timed(fn, n, edges):
    gc.collect()
    gc.disable()
    t0 = time.perf_counter()
    fn(n, edges)
    dt = time.perf_counter() - t0
    gc.enable()
    return dt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--runs", type=int, default=5, help="timed runs per method per size (>= 3)")
    args = ap.parse_args()
    assert args.runs >= 3

    print(f"python {platform.python_version()} ({platform.python_implementation()}), "
          f"{platform.platform()}, {platform.processor() or platform.machine()}, "
          f"{os.cpu_count()} logical CPUs, timer=time.perf_counter, seed={args.seed}, "
          f"runs={args.runs}, warm-up=1 untimed call per method per size\n")
    rows = []
    for n, m in SIZES:
        edges = make_graph(n, m, args.seed)
        rk, rp = A.kruskal(n, edges), A.prim(n, edges)          # also serves as the warm-up
        C.check_mst(n, edges, rk)
        C.check_mst(n, edges, rp)
        assert rk["cost"] == rp["cost"] and rk["components"] == rp["components"], "methods disagree"
        tk, tp = [], []
        for _ in range(args.runs):
            tk.append(timed(A.kruskal, n, edges))
            tp.append(timed(A.prim, n, edges))
        rows.append((n, m, rk["cost"], rk["components"], tk, tp))

    fmt = lambda xs: ", ".join(f"{x:.4f}" for x in xs)
    print("| n | m | cost (both) | components | Kruskal timings (s) | Kruskal median (s) "
          "| Prim timings (s) | Prim median (s) | Prim / Kruskal |")
    print("|---:|---:|---:|---:|---|---:|---|---:|---:|")
    for n, m, cost, comps, tk, tp in rows:
        mk, mp = statistics.median(tk), statistics.median(tp)
        print(f"| {n} | {m} | {cost} | {comps} | {fmt(tk)} | {mk:.4f} | {fmt(tp)} | {mp:.4f} | {mp / mk:.2f} |")


if __name__ == "__main__":
    main()
