"""Mock API clients with realistic delays and synthetic restaurant data."""

import random
import time
import math
from typing import List

import requests
from models import Query, Restaurant
from api_clients.base import BaseAPIClient
import config


# --- Synthetic data pools ---

CITY_COORDS = {
    "constanta": (44.1765, 28.6348),
    "bucharest": (44.4268, 26.1025),
    "cluj-napoca": (46.7712, 23.6236),
    "timisoara": (45.7489, 21.2087),
    "iasi": (47.1585, 27.6014),
    "brasov": (45.6427, 25.5887),
}

RESTAURANT_NAMES = {
    "google_places": [
        "La Mama", "Casa Doina", "Pescarus", "Restaurant Nunta",
        "Taverna Sarbului", "Trattoria Buongiorno", "Osaka Sushi",
        "La Placinte", "Restaurant Select", "Caru' cu Bere",
        "Hard Rock Cafe", "Shift Pub", "Beraria H", "Hanu' Berarilor",
        "Hanul lui Manuc", "Lacrimi si Sfinti", "Artist Cafe",
        "Energiea", "Mace Restaurant", "Zexe Braserie",
    ],
    "foursquare": [
        "Bistro de l'Arte", "Amvrosia Kitchen", "Salt Restaurant",
        "La Cantina", "Ristorante Momento", "Golden Falcon",
        "The Seafood Bar", "Panoramic Restaurant", "Green Hours",
        "Vatra Restaurant", "Dianei 4", "Kaiamo", "Fior di Latte",
        "Simbio", "Lente & Cafe", "Kane", "Grano Pizzeria",
        "The Jar", "Beca's Kitchen", "Brasserie Byzantium",
    ],
    "tripadvisor": [
        "Ancora Beach", "Reyna Restaurant", "Marty Restaurants",
        "Chez Liviu", "Casa Veche", "Restaurant Rustic",
        "Il Calcio", "Mesopotamia", "Dristor Kebab",
        "Sara Restaurant", "Baron", "New Montana",
        "Tudor's Fine Dining", "Provence", "Sardin Restaurant",
        "Orient Express", "Yacht Club", "Porto Restaurant",
        "Terasa Pescarus", "Golden Tulip",
    ],
}

FOOD_CATEGORIES = {
    "seafood": ["seafood", "fish", "ocean cuisine"],
    "italian": ["italian", "pizza", "pasta", "trattoria"],
    "romanian": ["romanian", "traditional", "local cuisine"],
    "fast food": ["fast food", "burgers", "street food"],
    "japanese": ["japanese", "sushi", "ramen", "asian"],
    "french": ["french", "bistro", "brasserie"],
    "steakhouse": ["steakhouse", "grill", "bbq"],
    "vegetarian": ["vegetarian", "vegan", "healthy"],
}

ENVIRONMENT_OPTIONS = ["seaside", "rooftop", "cozy", "garden", "central",
                       "terrace", "elegant", "rustic", "modern", "historic"]


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute distance between two coordinates in km."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _geocode(city_name: str):
    """Geocode a city name using Geoapify API. Returns (lat, lon) or None."""
    try:
        resp = requests.get(
            "https://api.geoapify.com/v1/geocode/search",
            params={
                "text": city_name,
                "type": "city",
                "limit": 1,
                "apiKey": config.GEOAPIFY_API_KEY,
            },
            timeout=10,
        )
        resp.raise_for_status()
        features = resp.json().get("features", [])
        if features:
            props = features[0]["properties"]
            return props["lat"], props["lon"]
    except Exception:
        pass
    return None


def _resolve_coords(query: Query):
    """Get coordinates from query or city name lookup."""
    if query.latitude is not None and query.longitude is not None:
        return query.latitude, query.longitude
    city_key = query.location.lower().strip()
    if city_key in CITY_COORDS:
        return CITY_COORDS[city_key]
    # Try geocoding via Geoapify
    coords = _geocode(query.location)
    if coords:
        return coords
    # Default to Bucharest
    return 44.4268, 26.1025


def _generate_restaurants(source: str, query: Query, count: int) -> List[Restaurant]:
    """Generate realistic synthetic restaurant data."""
    base_lat, base_lon = _resolve_coords(query)
    names = RESTAURANT_NAMES.get(source, RESTAURANT_NAMES["google_places"])
    restaurants = []

    for i in range(count):
        # Random offset within ~10km
        lat = base_lat + random.uniform(-0.05, 0.05)
        lon = base_lon + random.uniform(-0.05, 0.05)
        dist = _haversine_km(base_lat, base_lon, lat, lon)

        # Pick food categories - bias toward query food types
        if query.food_types and random.random() < 0.4:
            cats = list(query.food_types)
        else:
            cat_key = random.choice(list(FOOD_CATEGORIES.keys()))
            cats = FOOD_CATEGORIES[cat_key]

        # Pick environment tags - bias toward query preferences
        env_tags = []
        if query.environment and random.random() < 0.3:
            env_tags = list(query.environment)
        else:
            env_tags = random.sample(ENVIRONMENT_OPTIONS, k=random.randint(1, 3))

        restaurants.append(Restaurant(
            name=names[i % len(names)] + (f" #{i // len(names) + 1}" if i >= len(names) else ""),
            source=source,
            rating=round(random.uniform(2.5, 5.0), 1),
            latitude=lat,
            longitude=lon,
            distance_km=round(dist, 2),
            categories=cats,
            price_level=random.randint(1, 4),
            environment_tags=env_tags,
            review_count=random.randint(10, 2000),
            address=f"Str. {random.choice(['Mihai Eminescu', 'Ion Creanga', 'Stefan cel Mare', 'Nicolae Balcescu', 'Calea Victoriei'])} {random.randint(1, 200)}, {query.location}",
        ))

    return restaurants


class MockGooglePlaces(BaseAPIClient):
    """Simulates Google Places API with configurable delay."""

    @property
    def name(self) -> str:
        return "google_places"

    def search(self, query: Query) -> List[Restaurant]:
        delay = random.uniform(config.MOCK_API_DELAY_MIN, config.MOCK_API_DELAY_MAX)
        time.sleep(delay)
        return _generate_restaurants(
            "google_places", query, config.MOCK_RESTAURANTS_PER_SOURCE
        )


class MockFoursquare(BaseAPIClient):
    """Simulates Foursquare Places API with configurable delay."""

    @property
    def name(self) -> str:
        return "foursquare"

    def search(self, query: Query) -> List[Restaurant]:
        delay = random.uniform(config.MOCK_API_DELAY_MIN, config.MOCK_API_DELAY_MAX)
        time.sleep(delay)
        return _generate_restaurants(
            "foursquare", query, config.MOCK_RESTAURANTS_PER_SOURCE
        )


class MockTripAdvisor(BaseAPIClient):
    """Simulates TripAdvisor API with configurable delay."""

    @property
    def name(self) -> str:
        return "tripadvisor"

    def search(self, query: Query) -> List[Restaurant]:
        delay = random.uniform(config.MOCK_API_DELAY_MIN, config.MOCK_API_DELAY_MAX)
        time.sleep(delay)
        return _generate_restaurants(
            "tripadvisor", query, config.MOCK_RESTAURANTS_PER_SOURCE
        )
