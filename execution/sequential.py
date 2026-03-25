"""Sequential execution strategy — baseline for performance comparison."""

import time
from typing import List

from models import Query, Restaurant, ScoredRestaurant
from timing import TimingCollector
from api_clients.base import BaseAPIClient
from execution.base import ExecutionStrategy


class SequentialStrategy(ExecutionStrategy):
    """Executes all pipeline stages sequentially.

    T_total = T_api1 + T_api2 + ... + T_apiN + T_dedup + T_score + T_rank
    """

    @property
    def mode_name(self) -> str:
        return "sequential"

    def execute(self, query: Query, clients: List[BaseAPIClient],
                scorer: object) -> List[ScoredRestaurant]:
        all_restaurants: List[Restaurant] = []

        # --- Fetch: call each API one by one ---
        for client in clients:
            start = time.perf_counter()
            try:
                results = client.search(query)
            except Exception as e:
                end = time.perf_counter()
                self.collector.record(
                    f"api_{client.name}", start, end, count=0, error=str(e)
                )
                print(f"  [WARN] {client.name} failed: {e}")
                continue
            end = time.perf_counter()
            self.collector.record(
                f"api_{client.name}", start, end, count=len(results)
            )
            all_restaurants.extend(results)

        # --- Deduplication ---
        start = time.perf_counter()
        deduped = scorer.deduplicate(all_restaurants)
        end = time.perf_counter()
        self.collector.record("deduplication", start, end,
                              before=len(all_restaurants), after=len(deduped))

        # --- Scoring ---
        start = time.perf_counter()
        scored = scorer.score_all(deduped, query)
        end = time.perf_counter()
        self.collector.record("scoring", start, end, count=len(scored))

        # --- Ranking ---
        start = time.perf_counter()
        ranked = sorted(scored, key=lambda x: x.score, reverse=True)
        end = time.perf_counter()
        self.collector.record("ranking", start, end, count=len(ranked))

        return ranked
