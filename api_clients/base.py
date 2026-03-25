"""Abstract base class for restaurant API clients."""

from abc import ABC, abstractmethod
from typing import List
from models import Query, Restaurant


class BaseAPIClient(ABC):
    """Common interface for all restaurant data sources."""

    @abstractmethod
    def search(self, query: Query) -> List[Restaurant]:
        """Fetch restaurants matching the query. Blocking call."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable source name for timing reports."""
        pass
