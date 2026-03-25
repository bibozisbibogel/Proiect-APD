"""Pipeline orchestrator — connects strategy, clients, and scorer."""

import time
from typing import List

from models import Query, PipelineResult
from timing import TimingCollector
from api_clients.base import BaseAPIClient
from execution.base import ExecutionStrategy
from scoring import Scorer
import config


def run_pipeline(
    query: Query,
    strategy: ExecutionStrategy,
    clients: List[BaseAPIClient],
    scorer: Scorer,
    top_k: int = config.TOP_K_RESULTS,
) -> PipelineResult:
    """Execute the full restaurant search pipeline.

    Args:
        query: User search query.
        strategy: Execution strategy (sequential, async, multiprocessing).
        clients: List of API clients to query.
        scorer: Scoring engine.
        top_k: Number of top results to return.

    Returns:
        PipelineResult with ranked restaurants and timing data.
    """
    collector = strategy.collector
    collector.start_pipeline()

    start = time.perf_counter()
    ranked = strategy.execute(query, clients, scorer)
    end = time.perf_counter()
    collector.record("pipeline_total", start, end)

    return PipelineResult(
        restaurants=ranked[:top_k],
        timing=collector,
        mode=strategy.mode_name,
        query=query,
    )
