# Travel Companion — AI Restaurant Finder

## Overview

**Travel Companion** is an AI-powered restaurant recommendation system that aggregates data from multiple real external APIs (Geoapify, OpenStreetMap/Overpass, Foursquare) and ranks results using a configurable weighted scoring algorithm.

The core goal is to **implement and compare three execution strategies** — sequential, async I/O, and multiprocessing — measuring the performance impact of parallelism on a real multi-API aggregation workload.

---

## Execution Modes

### 1. Sequential (S6 — baseline)

All stages execute one after another. Each API call blocks until the response arrives.

```
T_total = T_api1 + T_api2 + T_api3 + T_dedup + T_score + T_rank
```

### 2. Parallel #1 — Async I/O (`--mode async`)

All API calls are dispatched simultaneously using `asyncio` + `ThreadPoolExecutor`. Since existing clients use blocking `requests`, each call runs in its own thread; `asyncio.gather()` waits for all of them concurrently.

```
T_total ≈ max(T_api1, T_api2, T_api3) + T_dedup + T_score + T_rank
```

### 3. Parallel #2 — Multiprocessing (`--mode multiprocessing`)

Two separate phases are parallelised using `multiprocessing.Pool`:

- **I/O phase**: each API client runs in a separate OS worker process
- **CPU phase**: restaurant scoring distributed across all available CPU cores

```
T_total ≈ max(T_api_i) + T_dedup + T_score_seq/N_cpus + T_rank
```

---

## Performance Results (Real APIs, 3 runs × 6 queries)

| Mode | 1 API | 2 APIs | 3 APIs | Speedup (3 APIs) |
|------|-------|--------|--------|------------------|
| Sequential (measured) | 0.69 s | 9.05 s | 8.73 s | 1.00× |
| Async (theoretical) | 0.69 s | ~8.35 s | ~7.40 s | ~1.18× |
| Multiprocessing (theoretical) | ~0.85 s | ~8.50 s | ~7.55 s | ~1.16× |

> Overpass/OSM dominates (~7-8 s per call) due to shared public infrastructure variability. Local processing (dedup, scoring, ranking) is negligible (<1 ms).

---

## Architecture

### Strategy Pattern

All three modes share the same `ExecutionStrategy` interface:

```python
class ExecutionStrategy(ABC):
    def execute(self, query, clients, scorer) -> List[ScoredRestaurant]: ...
    def mode_name(self) -> str: ...
```

`run_pipeline()` works with any strategy — adding a new mode requires zero changes to the orchestrator.

### Data Sources

| Source | API | Notes |
|--------|-----|-------|
| Geoapify Places | `api.geoapify.com/v2/places` | Category filter, fast (~0.7 s) |
| OpenStreetMap Overpass | `overpass-api.de/api/interpreter` | Free, no key, variable latency |
| Foursquare Places | `places-api.foursquare.com/places/search` | Bearer token, fast (~0.6 s) |

### Scoring Formula

```
score = 0.30 × S_rating + 0.25 × S_distance + 0.30 × S_food + 0.15 × S_environment
```

where each component is normalized to [0, 1]. Deduplication removes restaurants with the same name within 100 m, keeping the higher-rated version.

---

## Project Structure

```
ProiectAPD/
├── main.py                     # CLI entry point (--mode flag)
├── experiments.py              # Batch benchmark runner (all 3 modes)
├── pipeline.py                 # Orchestrator: connects strategy, clients, scorer
├── models.py                   # Query, Restaurant, ScoredRestaurant, PipelineResult
├── scoring.py                  # Scoring formula + deduplication
├── timing.py                   # TimingCollector, TimingRecord
├── config.py                   # API keys (from .env), weights, defaults
│
├── api_clients/
│   ├── base.py                 # Abstract BaseAPIClient
│   ├── real_client.py          # GeoapifyClient, OverpassClient, FoursquareClient
│   └── mock_client.py          # MockGooglePlaces, MockFoursquare, MockTripAdvisor
│
├── execution/
│   ├── base.py                 # Abstract ExecutionStrategy
│   ├── sequential.py           # SequentialStrategy  (S6 baseline)
│   ├── async_strategy.py       # AsyncStrategy       (Parallel #1)
│   └── multiprocessing_strategy.py  # MultiprocessingStrategy (Parallel #2)
│
├── report/
│   ├── report.tex              # LaTeX report (sequential only, S6)
│   └── experiment_results.csv  # Timing data from experiments
│
├── Proiect_APD_Complet.tex     # Full project LaTeX report (all 3 modes)
├── Proiect_APD_VariantaSecventiala.pdf  # S6 report (compiled)
└── requirements.txt
```

---

## Usage

### Installation

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in your API keys
```

### Search (CLI)

```bash
# Sequential (default)
python main.py --location "Constanta" --food "seafood" --environment "seaside" --apis 2

# Async I/O
python main.py --location "Constanta" --food "seafood" --mode async --apis 3

# Multiprocessing
python main.py --location "Bucharest" --food "italian" --mode multiprocessing --apis 3
```

#### CLI Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--location` | (required) | City name |
| `--food` | `""` | Food types, comma-separated |
| `--environment` | `""` | Environment prefs, comma-separated |
| `--max-distance` | 10.0 | Max radius in km |
| `--apis` | 2 | Number of API sources (1–3) |
| `--top-k` | 10 | Number of results to display |
| `--mode` | `sequential` | `sequential` \| `async` \| `multiprocessing` |

### Benchmark All Modes

```bash
# Full benchmark: all 3 modes × all API counts × 6 queries × 3 runs
python experiments.py \
    --modes "sequential,async,multiprocessing" \
    --runs-per-query 3 \
    --api-counts "1,2,3" \
    --output report/experiment_results.csv
```

The script exports a CSV with per-stage timing and prints a speedup table vs sequential baseline.

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12 |
| Async I/O | `asyncio`, `concurrent.futures.ThreadPoolExecutor` |
| CPU parallelism | `multiprocessing.Pool` |
| HTTP clients | `requests` (synchronous) |
| Architecture | Strategy Pattern |
| Timing | `time.perf_counter()` via `TimingCollector` |
| Config | `python-dotenv` |
| Docs | LaTeX (`Proiect_APD_Complet.tex`) |

---

## Test Machine

| Spec | Value |
|------|-------|
| CPU | AMD Ryzen 7 7745HX (8 cores / 16 threads) |
| RAM | 16 GB |
| OS | Linux 6.6.87.2 WSL2 |
| Python | 3.12.3 |
| Fork method | `fork` (Linux default) |

---

## Key Technical Decisions

**Why `ThreadPoolExecutor` for Async, not `aiohttp`?**  
Existing `requests`-based clients work without rewriting. Each blocking `.search()` runs in its own thread; `asyncio.gather()` provides the concurrency model. Result is functionally identical to native async.

**Why are `_call_client` / `_score_restaurant` module-level functions?**  
`multiprocessing.Pool.map()` pickles function references. Lambda expressions and bound methods are not picklable — module-level functions are.

**Why is deduplication kept sequential?**  
The dedup algorithm is order-sensitive (it tracks `seen` state) and runs in <1 ms — parallelizing it would add overhead without benefit.

---

## Conclusion

This project demonstrates the trade-offs between three execution models on a real I/O-bound workload:

- **Sequential**: simple, correct, sufficient for single-API scenarios
- **Async I/O**: best choice for multi-API I/O-bound workloads; low overhead, achieves `T ≈ max(T_api_i)`
- **Multiprocessing**: eliminates GIL entirely; best when CPU scoring becomes significant (large restaurant sets); higher overhead makes it less attractive for the current workload where scoring is <1 ms
