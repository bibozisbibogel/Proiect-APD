"""Parallel #1 — Async I/O execution strategy.

All API calls are dispatched simultaneously via asyncio + ThreadPoolExecutor.
Since the existing clients use blocking `requests`, each call runs in its own
thread; asyncio.gather() waits for all of them concurrently.

T_total ≈ max(T_api1, T_api2, ..., T_apiN) + T_dedup + T_score + T_rank
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Tuple

from api_clients.base import BaseAPIClient
from execution.base import ExecutionStrategy
from models import Query, Restaurant, ScoredRestaurant


class AsyncStrategy(ExecutionStrategy):
    """Concurrent I/O via asyncio + thread pool (Parallel #1).

    Each API client's blocking .search() call is offloaded to a thread so
    all requests are in-flight at the same time. Post-fetch stages (dedup,
    score, rank) remain sequential because they are cheap CPU work.
    """

    @property
    def mode_name(self) -> str:
        return "async"

    # ------------------------------------------------------------------ #
    # Public interface                                                     #
    # ------------------------------------------------------------------ #

    def execute(
        self,
        query: Query,
        clients: List[BaseAPIClient],
        scorer: object,
    ) -> List[ScoredRestaurant]:
        # --- Fetch: all APIs concurrently ---
        fetch_results = asyncio.run(self._fetch_all(query, clients))

        all_restaurants: List[Restaurant] = []
        for client, (restaurants, t_start, t_end, error) in zip(clients, fetch_results):
            self.collector.record(
                f"api_{client.name}",
                t_start,
                t_end,
                count=len(restaurants),
                **({"error": error} if error else {}),
            )
            if error:
                print(f"  [WARN] {client.name} failed: {error}")
            else:
                all_restaurants.extend(restaurants)

        # --- Deduplication ---
        start = time.perf_counter()
        deduped = scorer.deduplicate(all_restaurants)
        end = time.perf_counter()
        self.collector.record(
            "deduplication", start, end,
            before=len(all_restaurants), after=len(deduped),
        )

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

    # ------------------------------------------------------------------ #
    # Internal async helpers                                              #
    # ------------------------------------------------------------------ #

    async def _fetch_all(
        self,
        query: Query,
        clients: List[BaseAPIClient],
    ) -> List[Tuple]:
        """Launch one thread per client and await all results."""
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers=len(clients)) as executor:
            tasks = [
                loop.run_in_executor(executor, self._fetch_one, client, query)
                for client in clients
            ]
            return await asyncio.gather(*tasks)

    def _fetch_one(
        self,
        client: BaseAPIClient,
        query: Query,
    ) -> Tuple[List[Restaurant], float, float, Optional[str]]:
        """Blocking fetch wrapper — called inside a thread."""
        start = time.perf_counter()
        try:
            results = client.search(query)
            return results, start, time.perf_counter(), None
        except Exception as exc:
            return [], start, time.perf_counter(), str(exc)
