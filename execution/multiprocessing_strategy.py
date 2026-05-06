"""Parallel #2 — Multiprocessing execution strategy.

Two distinct phases are parallelised across separate OS processes:

  Phase 1 — I/O  : Every API client runs in its own worker process so all
                   network calls happen simultaneously.
                   T_fetch ≈ max(T_api1, ..., T_apiN)

  Phase 2 — CPU  : Restaurant scoring is distributed across all available
                   CPU cores using Pool.map.
                   T_score ≈ T_score_sequential / N_cpus

Deduplication and ranking are kept sequential because they are
order-sensitive or trivially fast.

NOTE: Helper functions (_call_client, _score_restaurant) must be defined at
module level (not as methods or lambdas) so that Python's pickle can
serialise them when dispatching to worker processes.
"""

import os
import time
from multiprocessing import Pool
from typing import List, Optional, Tuple

from api_clients.base import BaseAPIClient
from execution.base import ExecutionStrategy
from models import Query, Restaurant, ScoredRestaurant


# ── Module-level picklable worker functions ───────────────────────────────────

def _call_client(
    packed: Tuple,
) -> Tuple[List[Restaurant], float, Optional[str]]:
    """Worker: call one API client and return (results, duration, error)."""
    client, query = packed
    t0 = time.perf_counter()
    try:
        results = client.search(query)
        return results, time.perf_counter() - t0, None
    except Exception as exc:
        return [], time.perf_counter() - t0, str(exc)


def _score_restaurant(packed: Tuple) -> ScoredRestaurant:
    """Worker: score a single restaurant using the provided scorer."""
    restaurant, query, scorer = packed
    return scorer.score(restaurant, query)


# ── Strategy class ────────────────────────────────────────────────────────────

class MultiprocessingStrategy(ExecutionStrategy):
    """Process-level parallelism for both I/O and CPU phases (Parallel #2).

    Args:
        collector: TimingCollector shared by this run.
        num_workers: Pool size. Defaults to os.cpu_count().
    """

    def __init__(self, collector, num_workers: Optional[int] = None):
        super().__init__(collector)
        self.num_workers = num_workers or os.cpu_count() or 4

    @property
    def mode_name(self) -> str:
        return "multiprocessing"

    def execute(
        self,
        query: Query,
        clients: List[BaseAPIClient],
        scorer: object,
    ) -> List[ScoredRestaurant]:
        # ── Phase 1: Fetch APIs in parallel worker processes ──────────────
        n_fetch = min(len(clients), self.num_workers)
        fetch_start = time.perf_counter()
        with Pool(processes=n_fetch) as pool:
            fetch_results = pool.map(
                _call_client, [(c, query) for c in clients]
            )
        # fetch_end not recorded separately; individual durations used below.

        all_restaurants: List[Restaurant] = []
        for client, (restaurants, duration, error) in zip(clients, fetch_results):
            # All workers started at approximately the same wall-clock moment
            # (fetch_start). We reconstruct individual end times as
            # fetch_start + measured_duration for the Gantt chart.
            self.collector.record(
                f"api_{client.name}",
                fetch_start,
                fetch_start + duration,
                count=len(restaurants),
                **({"error": error} if error else {}),
            )
            if error:
                print(f"  [WARN] {client.name} failed: {error}")
            else:
                all_restaurants.extend(restaurants)

        # ── Phase 2: Deduplication (sequential — order-sensitive) ─────────
        start = time.perf_counter()
        deduped = scorer.deduplicate(all_restaurants)
        end = time.perf_counter()
        self.collector.record(
            "deduplication", start, end,
            before=len(all_restaurants), after=len(deduped),
        )

        # ── Phase 3: Parallel scoring ─────────────────────────────────────
        score_start = time.perf_counter()
        with Pool(processes=self.num_workers) as pool:
            scored: List[ScoredRestaurant] = pool.map(
                _score_restaurant,
                [(r, query, scorer) for r in deduped],
            )
        score_end = time.perf_counter()
        self.collector.record("scoring", score_start, score_end, count=len(scored))

        # ── Phase 4: Ranking ──────────────────────────────────────────────
        start = time.perf_counter()
        ranked = sorted(scored, key=lambda x: x.score, reverse=True)
        end = time.perf_counter()
        self.collector.record("ranking", start, end, count=len(ranked))

        return ranked
