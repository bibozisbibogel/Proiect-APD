"""CLI entry point for the Travel Companion restaurant finder."""

import argparse

from models import Query
from timing import TimingCollector
from api_clients import GeoapifyClient, OverpassClient, FoursquareClient
from execution import SequentialStrategy
from scoring import Scorer
from pipeline import run_pipeline
import config


def parse_args():
    parser = argparse.ArgumentParser(
        description="Travel Companion — AI Restaurant Finder (Sequential)"
    )
    parser.add_argument("--location", required=True, help="City name (e.g. Constanta)")
    parser.add_argument("--food", default="", help="Food types, comma-separated (e.g. seafood,fish)")
    parser.add_argument("--environment", default="", help="Environment prefs, comma-separated (e.g. seaside,terrace)")
    parser.add_argument("--max-distance", type=float, default=config.MAX_DISTANCE_KM, help="Max distance in km")
    parser.add_argument("--apis", type=int, default=2, choices=[1, 2, 3], help="Number of API sources (1-3)")
    parser.add_argument("--top-k", type=int, default=config.TOP_K_RESULTS, help="Number of results to show")
    return parser.parse_args()


def build_clients(num_apis: int):
    """Create real API clients based on requested count."""
    available = [GeoapifyClient(), OverpassClient(), FoursquareClient()]
    return available[:num_apis]


def print_results(result):
    """Print ranked restaurants to stdout."""
    print(f"\n{'='*60}")
    print(f"  Travel Companion — Restaurant Recommendations")
    print(f"  Mode: {result.mode.upper()}")
    print(f"  Query: {result.query.location} | Food: {', '.join(result.query.food_types) or 'any'}")
    print(f"{'='*60}\n")

    for i, sr in enumerate(result.restaurants, 1):
        r = sr.restaurant
        print(f"  #{i:2d}  {r.name}")
        print(f"       Score: {sr.score:.4f}  |  Rating: {r.rating}/5  |  Distance: {r.distance_km:.1f}km")
        print(f"       Categories: {', '.join(r.categories)}")
        print(f"       Environment: {', '.join(r.environment_tags)}")
        print(f"       Source: {r.source}  |  Address: {r.address}")
        print(f"       Breakdown: {sr.score_breakdown}")
        print()

    result.timing.print_summary()


def main():
    args = parse_args()

    query = Query(
        location=args.location,
        food_types=[f.strip() for f in args.food.split(",") if f.strip()],
        environment=[e.strip() for e in args.environment.split(",") if e.strip()],
        max_distance_km=args.max_distance,
    )

    clients = build_clients(args.apis)
    collector = TimingCollector()
    strategy = SequentialStrategy(collector)
    scorer = Scorer()

    result = run_pipeline(query, strategy, clients, scorer, top_k=args.top_k)
    print_results(result)


if __name__ == "__main__":
    main()
