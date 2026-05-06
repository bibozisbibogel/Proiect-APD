"""Batch experiment runner — runs all three execution modes, collects timing, exports CSV."""

import argparse
import csv
import os
import time
from typing import List

from models import Query
from timing import TimingCollector
from api_clients import GeoapifyClient, OverpassClient, FoursquareClient
from execution import SequentialStrategy, AsyncStrategy, MultiprocessingStrategy
from scoring import Scorer
from pipeline import run_pipeline


EXPERIMENT_QUERIES = [
    Query(location="Constanta", food_types=["seafood"], environment=["seaside"]),
    Query(location="Bucharest", food_types=["italian", "pizza"], environment=["cozy"]),
    Query(location="Cluj-Napoca", food_types=["romanian", "traditional"], environment=[]),
    Query(location="Timisoara", food_types=["fast food"], environment=["central"]),
    Query(location="Iasi", food_types=["french"], environment=["elegant"]),
    Query(location="Brasov", food_types=["steakhouse"], environment=["rustic", "terrace"]),
]

ALL_MODES = ["sequential", "async", "multiprocessing"]


def query_label(q: Query) -> str:
    food = "+".join(q.food_types) if q.food_types else "any"
    return f"{q.location}/{food}"


def make_strategy(mode: str, collector: TimingCollector):
    if mode == "sequential":
        return SequentialStrategy(collector)
    if mode == "async":
        return AsyncStrategy(collector)
    if mode == "multiprocessing":
        return MultiprocessingStrategy(collector)
    raise ValueError(f"Unknown mode: {mode}")


def run_experiments(
    queries: List[Query],
    runs_per_query: int,
    api_counts: List[int],
    modes: List[str],
    output_path: str,
):
    """Run experiments for all modes and export results to CSV."""
    all_clients = [GeoapifyClient(), OverpassClient(), FoursquareClient()]
    scorer = Scorer()
    rows = []

    total_runs = len(queries) * len(api_counts) * len(modes) * runs_per_query
    run_counter = 0

    for mode in modes:
        for num_apis in api_counts:
            clients = all_clients[:num_apis]

            for query in queries:
                for run_id in range(1, runs_per_query + 1):
                    run_counter += 1
                    print(
                        f"  [{run_counter}/{total_runs}] "
                        f"mode={mode} apis={num_apis} "
                        f"query={query_label(query)} run={run_id}"
                    )

                    collector = TimingCollector()
                    strategy = make_strategy(mode, collector)

                    result = run_pipeline(query, strategy, clients, scorer)

                    row = collector.to_csv_dict(
                        run_id=run_id,
                        query_label=query_label(query),
                        mode=result.mode,
                        num_apis=num_apis,
                        num_restaurants=len(result.restaurants),
                    )
                    rows.append(row)

                    # Small delay between runs to avoid API rate limiting
                    time.sleep(1.0)

    # Export to CSV
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    all_keys: List[str] = []
    for row in rows:
        for key in row:
            if key not in all_keys:
                all_keys.append(key)

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_keys)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n  Exported {len(rows)} rows to {output_path}")
    print_summary(rows, api_counts, modes)


def print_summary(rows, api_counts, modes):
    """Print timing summary grouped by mode and num_apis."""
    print("\n" + "=" * 70)
    print("  EXPERIMENT SUMMARY")
    print("=" * 70)

    for mode in modes:
        for num_apis in api_counts:
            subset = [
                r for r in rows
                if r["execution_mode"] == mode and r["num_apis"] == num_apis
            ]
            if not subset:
                continue

            totals = [r.get("time_pipeline_total", 0) for r in subset]
            mean_t = sum(totals) / len(totals)
            variance = sum((t - mean_t) ** 2 for t in totals) / len(totals)
            stddev = variance ** 0.5

            print(f"\n  Mode: {mode:<16}  APIs: {num_apis}  Runs: {len(subset)}")
            print(f"    Mean total time : {mean_t:.4f}s")
            print(f"    Std deviation   : {stddev:.4f}s")
            print(f"    Min / Max       : {min(totals):.4f}s / {max(totals):.4f}s")

    # Speedup table vs sequential baseline
    print("\n" + "=" * 70)
    print("  SPEEDUP vs SEQUENTIAL (mean times)")
    print("=" * 70)
    for num_apis in api_counts:
        seq_rows = [
            r for r in rows
            if r["execution_mode"] == "sequential" and r["num_apis"] == num_apis
        ]
        if not seq_rows:
            continue
        seq_mean = sum(r.get("time_pipeline_total", 0) for r in seq_rows) / len(seq_rows)
        print(f"\n  APIs: {num_apis}  (sequential baseline: {seq_mean:.4f}s)")
        for mode in modes:
            par_rows = [
                r for r in rows
                if r["execution_mode"] == mode and r["num_apis"] == num_apis
            ]
            if not par_rows:
                continue
            par_mean = sum(r.get("time_pipeline_total", 0) for r in par_rows) / len(par_rows)
            speedup = seq_mean / par_mean if par_mean > 0 else float("inf")
            print(f"    {mode:<18} {par_mean:.4f}s  speedup={speedup:.2f}x")

    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Run timing experiments comparing all execution modes"
    )
    parser.add_argument(
        "--runs-per-query", type=int, default=3,
        help="Number of runs per query per mode (default: 3)",
    )
    parser.add_argument(
        "--api-counts", default="1,2,3",
        help="Comma-separated API counts to test (default: 1,2,3)",
    )
    parser.add_argument(
        "--modes", default=",".join(ALL_MODES),
        help=f"Comma-separated modes to test (default: {','.join(ALL_MODES)})",
    )
    parser.add_argument(
        "--output", default="report/experiment_results.csv",
        help="Output CSV path (default: report/experiment_results.csv)",
    )
    args = parser.parse_args()

    api_counts = [int(x.strip()) for x in args.api_counts.split(",")]
    modes = [m.strip() for m in args.modes.split(",") if m.strip() in ALL_MODES]

    print("=" * 70)
    print("  Travel Companion — Multi-Mode Timing Experiments")
    print("=" * 70)
    print(f"  Queries        : {len(EXPERIMENT_QUERIES)}")
    print(f"  Modes          : {modes}")
    print(f"  API counts     : {api_counts}")
    print(f"  Runs per query : {args.runs_per_query}")
    total = len(EXPERIMENT_QUERIES) * len(api_counts) * len(modes) * args.runs_per_query
    print(f"  Total runs     : {total}")
    print(f"  Output         : {args.output}")
    print("=" * 70 + "\n")

    run_experiments(EXPERIMENT_QUERIES, args.runs_per_query, api_counts, modes, args.output)


if __name__ == "__main__":
    main()
