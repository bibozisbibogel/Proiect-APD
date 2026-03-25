"""Data models for the Travel Companion restaurant finder."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Query:
    """User search query."""
    location: str
    food_types: List[str] = field(default_factory=list)
    environment: List[str] = field(default_factory=list)
    max_distance_km: float = 10.0
    latitude: Optional[float] = None
    longitude: Optional[float] = None


@dataclass
class Restaurant:
    """Raw restaurant data from an API source."""
    name: str
    source: str
    rating: float
    latitude: float
    longitude: float
    distance_km: float
    categories: List[str] = field(default_factory=list)
    price_level: int = 0
    environment_tags: List[str] = field(default_factory=list)
    review_count: int = 0
    address: str = ""


@dataclass
class ScoredRestaurant:
    """Restaurant with computed scores."""
    restaurant: Restaurant
    score: float
    score_breakdown: dict = field(default_factory=dict)


@dataclass
class PipelineResult:
    """Complete result of a pipeline execution."""
    restaurants: List[ScoredRestaurant]
    timing: object = None  # TimingCollector
    mode: str = "sequential"
    query: Optional[Query] = None
