"""Configuration for the Travel Companion restaurant finder."""

import os
from dotenv import load_dotenv

load_dotenv()

# --- API Keys ---
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_PLACES_API_KEY", "")
YELP_API_KEY = os.getenv("YELP_FUSION_API_KEY", "")
FOURSQUARE_API_KEY = os.getenv("FOURSQUARE_PLACES_SERVICE_API_KEY", "")

# --- Scoring Weights ---
WEIGHT_RATING = 0.30
WEIGHT_DISTANCE = 0.25
WEIGHT_FOOD_MATCH = 0.30
WEIGHT_ENVIRONMENT = 0.15

# --- Defaults ---
MAX_DISTANCE_KM = 10.0
TOP_K_RESULTS = 10

# --- Mock Client Settings ---
MOCK_API_DELAY_MIN = 0.5   # seconds
MOCK_API_DELAY_MAX = 2.0   # seconds
MOCK_RESTAURANTS_PER_SOURCE = 15
