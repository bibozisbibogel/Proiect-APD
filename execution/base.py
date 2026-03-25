"""Abstract execution strategy interface (Strategy Pattern)."""

from abc import ABC, abstractmethod
from typing import List

from models import Query, ScoredRestaurant
from timing import TimingCollector
from api_clients.base import BaseAPIClient


class ExecutionStrategy(ABC):
    """Interface for execution backends.

    Implementations:
      - SequentialStrategy: calls APIs one by one (S6)
      - AsyncStrategy: concurrent I/O with asyncio (future)
      - MultiprocessingStrategy: CPU parallelism (future)
    """

    def __init__(self, collector: TimingCollector):
        self.collector = collector

    @abstractmethod
    def execute(self, query: Query, clients: List[BaseAPIClient],
                scorer: object) -> List[ScoredRestaurant]:
        """Run the full fetch -> parse -> score -> rank pipeline."""
        pass

    @property
    @abstractmethod
    def mode_name(self) -> str:
        """Name of this execution mode for reports."""
        pass
