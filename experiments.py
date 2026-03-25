"""Batch experiment runner — runs multiple queries, collects timing, exports CSV."""

import argparse
import csv
import os
import time
from typing import List

from models import Query
from timing import TimingCollector
from api_clients import GeoapifyClient, OverpassClient, FoursquareClient
from execution import SequentialStrategy
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


def query_label(q: Query) -> str:
    food = "+".join(q.food_types) if q.food_types else "any"
    return f"{q.location}/{food}"


def run_experiments(
    queries: List[Query],
    runs_per_query: int,
    api_counts: List[int],
    output_path: str,
):
    """Run experiments and export results to CSV."""
    all_clients = [GeoapifyClient(), OverpassClient(), FoursquareClient()]
    scorer = Scorer()
    rows = []

    total_runs = len(queries) * len(api_counts) * runs_per_query
    run_counter = 0

    for num_apis in api_counts:
        clients = all_clients[:num_apis]

        for query in queries:
            for run_id in range(1, runs_per_query + 1):
                run_counter += 1
                print(f"  [{run_counter}/{total_runs}] "
                      f"apis={num_apis} query={query_label(query)} run={run_id}")

                collector = TimingCollector()
                strategy = SequentialStrategy(collector)

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

    # Collect all column names
    all_keys = []
    for row in rows:
        for key in row:
            if key not in all_keys:
                all_keys.append(key)

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_keys)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n  Exported {len(rows)} rows to {output_path}")

    # Print summary statistics
    print_summary(rows, api_counts)


def print_summary(rows, api_counts):
    """Print summary statistics grouped by num_apis."""
    print("\n" + "=" * 60)
    print("  EXPERIMENT SUMMARY (Sequential Mode)")
    print("=" * 60)

    for num_apis in api_counts:
        api_rows = [r for r in rows if r["num_apis"] == num_apis]
        if not api_rows:
            continue

        totals = [r.get("time_pipeline_total", 0) for r in api_rows]
        mean_total = sum(totals) / len(totals)
        variance = sum((t - mean_total) ** 2 for t in totals) / len(totals)
        stddev = variance ** 0.5

        print(f"\n  APIs: {num_apis}")
        print(f"  Runs: {len(api_rows)}")
        print(f"  Mean total time:   {mean_total:.4f}s")
        print(f"  Std deviation:     {stddev:.4f}s")
        print(f"  Min total time:    {min(totals):.4f}s")
        print(f"  Max total time:    {max(totals):.4f}s")

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Run timing experiments for sequential execution"
    )
    parser.add_argument("--runs-per-query", type=int, default=5,
                        help="Number of runs per query (default: 5)")
    parser.add_argument("--api-counts", default="1,2,3",
                        help="Comma-separated API counts to test (default: 1,2,3)")
    parser.add_argument("--output", default="report/experiment_results.csv",
                        help="Output CSV path (default: report/experiment_results.csv)")
    args = parser.parse_args()

    api_counts = [int(x.strip()) for x in args.api_counts.split(",")]

    print("=" * 60)
    print("  Travel Companion — Sequential Timing Experiments")
    print("=" * 60)
    print(f"  Queries: {len(EXPERIMENT_QUERIES)}")
    print(f"  API counts: {api_counts}")
    print(f"  Runs per query: {args.runs_per_query}")
    print(f"  Total runs: {len(EXPERIMENT_QUERIES) * len(api_counts) * args.runs_per_query}")
    print(f"  Output: {args.output}")
    print("=" * 60 + "\n")

    run_experiments(EXPERIMENT_QUERIES, args.runs_per_query, api_counts, args.output)


if __name__ == "__main__":
    main()
