"""Scoring and ranking logic for restaurants."""

from typing import List
from models import Query, Restaurant, ScoredRestaurant
import config


class Scorer:
    """Computes restaurant scores based on weighted criteria."""

    def __init__(
        self,
        w_rating: float = config.WEIGHT_RATING,
        w_distance: float = config.WEIGHT_DISTANCE,
        w_food_match: float = config.WEIGHT_FOOD_MATCH,
        w_environment: float = config.WEIGHT_ENVIRONMENT,
    ):
        self.w_rating = w_rating
        self.w_distance = w_distance
        self.w_food_match = w_food_match
        self.w_environment = w_environment

    def score(self, restaurant: Restaurant, query: Query) -> ScoredRestaurant:
        """Compute a weighted score for a single restaurant."""
        s_rating = restaurant.rating / 5.0

        max_dist = query.max_distance_km
        s_distance = max(0.0, 1.0 - (restaurant.distance_km / max_dist))

        s_food = self._match_ratio(
            query.food_types,
            restaurant.categories,
        )

        s_env = self._match_ratio(
            query.environment,
            restaurant.environment_tags,
        )

        total = (
            self.w_rating * s_rating
            + self.w_distance * s_distance
            + self.w_food_match * s_food
            + self.w_environment * s_env
        )

        return ScoredRestaurant(
            restaurant=restaurant,
            score=round(total, 4),
            score_breakdown={
                "rating": round(s_rating, 4),
                "distance": round(s_distance, 4),
                "food_match": round(s_food, 4),
                "environment": round(s_env, 4),
            },
        )

    def score_all(self, restaurants: List[Restaurant],
                  query: Query) -> List[ScoredRestaurant]:
        """Score all restaurants."""
        return [self.score(r, query) for r in restaurants]

    def deduplicate(self, restaurants: List[Restaurant]) -> List[Restaurant]:
        """Remove duplicate restaurants (same name within 100m)."""
        seen = []
        result = []
        for r in restaurants:
            is_dup = False
            for s in seen:
                if (r.name.lower() == s.name.lower()
                        and abs(r.latitude - s.latitude) < 0.001
                        and abs(r.longitude - s.longitude) < 0.001):
                    # Keep higher rating
                    if r.rating > s.rating:
                        result = [x for x in result if x is not s]
                        result.append(r)
                        seen = [x if x is not s else r for x in seen]
                    is_dup = True
                    break
            if not is_dup:
                seen.append(r)
                result.append(r)
        return result

    @staticmethod
    def _match_ratio(query_terms: List[str], item_terms: List[str]) -> float:
        """Compute fuzzy match ratio between query and item terms."""
        if not query_terms:
            return 1.0
        if not item_terms:
            return 0.0
        q_lower = {t.lower().strip() for t in query_terms}
        i_lower = {t.lower().strip() for t in item_terms}
        # Check substring matches
        matches = 0
        for q in q_lower:
            for i in i_lower:
                if q in i or i in q:
                    matches += 1
                    break
        return matches / len(q_lower)
