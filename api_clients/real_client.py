"""Real API clients for Geoapify, Overpass (OpenStreetMap), and Foursquare."""

import requests
from typing import List

from models import Query, Restaurant
from api_clients.base import BaseAPIClient
from api_clients.mock_client import _haversine_km, _resolve_coords
import config


# --- Geoapify category mapping ---
GEOAPIFY_FOOD_CATEGORIES = {
    "seafood": "catering.restaurant.seafood",
    "italian": "catering.restaurant.italian",
    "romanian": "catering.restaurant",
    "fast food": "catering.fast_food",
    "japanese": "catering.restaurant.japanese",
    "french": "catering.restaurant.french",
    "steakhouse": "catering.restaurant.steak_house",
    "vegetarian": "catering.restaurant.vegetarian",
    "pizza": "catering.restaurant.pizza",
    "sushi": "catering.restaurant.sushi",
}

# --- Foursquare category IDs ---
FOURSQUARE_FOOD_CATEGORIES = {
    "seafood": "13338",
    "italian": "13236",
    "romanian": "13263",
    "fast food": "13145",
    "japanese": "13263",
    "french": "13211",
    "steakhouse": "13383",
    "vegetarian": "13377",
    "pizza": "13064",
    "sushi": "13271",
}


def _extract_env_tags(name: str, categories: List[str]) -> List[str]:
    """Infer environment tags from name and categories."""
    tags = []
    name_lower = name.lower()
    cat_str = " ".join(categories).lower()
    combined = name_lower + " " + cat_str

    keyword_map = {
        "terrace": ["terrace", "terasa", "outdoor"],
        "garden": ["garden", "gradina"],
        "rooftop": ["rooftop", "sky"],
        "seaside": ["beach", "seaside", "port", "yacht", "marina"],
        "cozy": ["cozy", "bistro", "cafe"],
        "elegant": ["fine dining", "elegant", "premium"],
        "rustic": ["rustic", "traditional", "vechi"],
        "modern": ["modern", "lounge", "urban"],
        "central": ["central", "centru"],
        "historic": ["historic", "vechi", "old"],
    }
    for tag, keywords in keyword_map.items():
        if any(kw in combined for kw in keywords):
            tags.append(tag)
    return tags if tags else ["central"]


class GeoapifyClient(BaseAPIClient):
    """Geoapify Places API client."""

    @property
    def name(self) -> str:
        return "geoapify"

    def search(self, query: Query) -> List[Restaurant]:
        lat, lon = _resolve_coords(query)
        radius_m = int(query.max_distance_km * 1000)

        # Build categories filter
        categories = "catering.restaurant"
        if query.food_types:
            mapped = []
            for ft in query.food_types:
                cat = GEOAPIFY_FOOD_CATEGORIES.get(ft.lower())
                if cat:
                    mapped.append(cat)
            if mapped:
                categories = ",".join(mapped)

        params = {
            "categories": categories,
            "filter": f"circle:{lon},{lat},{radius_m}",
            "limit": 20,
            "apiKey": config.GEOAPIFY_API_KEY,
        }

        resp = requests.get(
            "https://api.geoapify.com/v2/places",
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        restaurants = []
        for feat in data.get("features", []):
            props = feat.get("properties", {})
            r_lat = props.get("lat", lat)
            r_lon = props.get("lon", lon)
            dist = _haversine_km(lat, lon, r_lat, r_lon)

            cats = []
            for cat in props.get("categories", []):
                cats.append(cat.split(".")[-1])

            restaurants.append(Restaurant(
                name=props.get("name", "Unknown"),
                source="geoapify",
                rating=props.get("datasource", {}).get("raw", {}).get("rating", 0.0) or round(props.get("rank", {}).get("popularity", 3.0), 1),
                latitude=r_lat,
                longitude=r_lon,
                distance_km=round(dist, 2),
                categories=cats if cats else ["restaurant"],
                price_level=0,
                environment_tags=_extract_env_tags(
                    props.get("name", ""), cats
                ),
                review_count=0,
                address=props.get("formatted", props.get("address_line1", "")),
            ))

        return restaurants


class OverpassClient(BaseAPIClient):
    """OpenStreetMap Overpass API client (free, no key needed)."""

    OVERPASS_URLS = [
        "https://overpass-api.de/api/interpreter",
        "https://lz4.overpass-api.de/api/interpreter",
    ]

    @property
    def name(self) -> str:
        return "overpass_osm"

    def search(self, query: Query) -> List[Restaurant]:
        lat, lon = _resolve_coords(query)
        radius_m = int(query.max_distance_km * 1000)

        # Build cuisine filter if food types specified
        cuisine_filter = ""
        if query.food_types:
            cuisine_regex = "|".join(ft.lower() for ft in query.food_types)
            cuisine_filter = f'["cuisine"~"{cuisine_regex}",i]'

        overpass_query = (
            f'[out:json][timeout:15];'
            f'node["amenity"="restaurant"]{cuisine_filter}'
            f'  (around:{radius_m},{lat},{lon});'
            f'out body 20;'
        )

        # Try multiple Overpass mirrors
        last_err = None
        data = None
        for url in self.OVERPASS_URLS:
            try:
                resp = requests.post(
                    url,
                    data={"data": overpass_query},
                    timeout=20,
                )
                resp.raise_for_status()
                data = resp.json()
                break
            except requests.RequestException as e:
                last_err = e
                continue

        if data is None:
            raise last_err

        restaurants = []
        for elem in data.get("elements", []):
            tags = elem.get("tags", {})

            # Get coordinates (nodes have lat/lon directly, ways use center)
            if elem["type"] == "way":
                center = elem.get("center", {})
                r_lat = center.get("lat", lat)
                r_lon = center.get("lon", lon)
            else:
                r_lat = elem.get("lat", lat)
                r_lon = elem.get("lon", lon)

            dist = _haversine_km(lat, lon, r_lat, r_lon)
            name = tags.get("name", "Unknown")

            # Parse cuisine tags into categories
            cuisine_raw = tags.get("cuisine", "restaurant")
            cats = [c.strip() for c in cuisine_raw.split(";")]

            # Extract rating if available (stars tag)
            rating_str = tags.get("stars", "0")
            try:
                rating = float(rating_str)
            except ValueError:
                rating = 0.0

            # Build address from OSM tags
            addr_parts = []
            if tags.get("addr:street"):
                addr_parts.append(tags["addr:street"])
            if tags.get("addr:housenumber"):
                addr_parts.append(tags["addr:housenumber"])
            if tags.get("addr:city"):
                addr_parts.append(tags["addr:city"])
            address = ", ".join(addr_parts) if addr_parts else query.location

            # Environment from OSM tags
            env_tags = []
            if tags.get("outdoor_seating") == "yes":
                env_tags.append("terrace")
            if tags.get("indoor_seating") == "yes":
                env_tags.append("cozy")
            env_tags.extend(_extract_env_tags(name, cats))
            # Deduplicate
            env_tags = list(dict.fromkeys(env_tags))

            restaurants.append(Restaurant(
                name=name,
                source="overpass_osm",
                rating=rating,
                latitude=r_lat,
                longitude=r_lon,
                distance_km=round(dist, 2),
                categories=cats,
                price_level=0,
                environment_tags=env_tags,
                review_count=0,
                address=address,
            ))

        return restaurants


class FoursquareClient(BaseAPIClient):
    """Foursquare Places API client (new places-api.foursquare.com endpoints).

    Requires a Service Key (not the old fsq3... API key).
    Generate one at the Foursquare Developer Console.
    """

    @property
    def name(self) -> str:
        return "foursquare"

    def search(self, query: Query) -> List[Restaurant]:
        lat, lon = _resolve_coords(query)

        # New API uses text query instead of category IDs
        search_term = "restaurant"
        if query.food_types:
            search_term = " ".join(query.food_types) + " restaurant"

        headers = {
            "Authorization": f"Bearer {config.FOURSQUARE_API_KEY}",
            "Accept": "application/json",
            "X-Places-Api-Version": "2025-06-17",
        }
        params = {
            "ll": f"{lat},{lon}",
            "query": search_term,
            "limit": 20,
        }

        resp = requests.get(
            "https://places-api.foursquare.com/places/search",
            headers=headers,
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        restaurants = []
        for place in data.get("results", []):
            # New API has lat/lon at top level
            r_lat = place.get("latitude", lat)
            r_lon = place.get("longitude", lon)
            dist = _haversine_km(lat, lon, r_lat, r_lon)

            cats = [c.get("name", "") for c in place.get("categories", [])]

            loc = place.get("location", {})
            address = loc.get("formatted_address", loc.get("address", ""))

            restaurants.append(Restaurant(
                name=place.get("name", "Unknown"),
                source="foursquare",
                rating=0.0,
                latitude=r_lat,
                longitude=r_lon,
                distance_km=round(dist, 2),
                categories=cats if cats else ["restaurant"],
                price_level=0,
                environment_tags=_extract_env_tags(
                    place.get("name", ""), cats
                ),
                review_count=0,
                address=address,
            ))

        return restaurants
