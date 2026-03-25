# Travel Companion – AI Restaurant Finder

## Overview

Travel Companion is an AI-powered application that recommends the best restaurant based on user preferences (location, food type, environment, distance, etc.).

The system aggregates data from multiple external APIs (e.g. Google Places, Yelp) and applies ranking algorithms to determine the most suitable restaurant.

The main goal of this project is to **analyze and compare sequential and parallel approaches** for multi-source data aggregation and processing.

---

## Project Objectives

- Build an intelligent restaurant recommendation system
- Integrate multiple external APIs for data collection
- Implement and compare:
  - Sequential execution
  - Parallel execution (async I/O)
  - Parallel execution (multi-processing / distributed)
- Measure performance improvements (execution time, speedup, scalability)
- Visualize execution flow and parallelism using frontend tools

---

## Key Features

- AI-based query understanding (user preferences)
- Multi-API restaurant search and aggregation
- Ranking system based on:
  - rating
  - distance
  - food match
  - environment (e.g. seaside view)
- Execution mode selection:
  - Sequential
  - Parallel #1 (Async)
  - Parallel #2 (Multiprocessing / Distributed)
- Performance metrics visualization:
  - execution time
  - speedup
  - task timeline (Gantt chart)

---

## System Architecture
User
↓
Frontend (Next.js, React)
↓
Backend (FastAPI)
↓
AI Agent (LangGraph / LangChain)
↓
Parallel Task Execution Layer
↙ ↓ ↘
Google Yelp Other APIs


---

## Technology Stack

### Backend
- Python
- FastAPI
- Uvicorn
- LangGraph / LangChain
- AsyncIO / Multiprocessing

### Frontend
- Next.js
- React
- Tailwind CSS
- gantt-task-react / vis-timeline (task visualization)
- Recharts (performance charts)

### Database
- Supabase (PostgreSQL)

---

## Execution Models

### 1. Sequential Execution

All tasks are executed one after another:

1. Call API #1
2. Wait for response
3. Call API #2
4. Wait for response
5. Process data
6. Rank restaurants

Execution time:
T = T1 + T2 + T3 + ...


---

### 2. Parallel Execution #1 (Async I/O)

API calls are executed concurrently using async programming:

- Multiple API requests are sent simultaneously
- System waits for all responses

Execution time:
T = max(T1, T2, T3)


Technologies:
- asyncio
- async HTTP clients (httpx)

---

### 3. Parallel Execution #2 (Multiprocessing / Distributed)

CPU-intensive tasks are parallelized:

- restaurant scoring
- review analysis
- ranking computation

Technologies:
- multiprocessing
- or distributed frameworks (optional: Ray / Dask)

---

## Performance Evaluation

The system measures and compares:

- Total execution time
- API response times
- Number of processed restaurants
- Speedup: Speedup = T_sequential / T_parallel


---

## Frontend Visualization

The frontend provides:

### 1. Execution Mode Selector
- Sequential
- Parallel (Async)
- Parallel (Multiprocessing)

### 2. Execution Metrics
- total execution time
- speedup
- number of APIs used

### 3. Task Timeline (Gantt Chart)
Visual representation of task execution:
- sequential vs parallel behavior
- task overlap

### 4. Performance Charts
- execution time vs number of tasks
- scalability graphs

### 5. Restaurant Results
- ranked list of recommended restaurants
- score breakdown

---

## Example Flow

1. User input:
Location: Constanta
Food: Seafood
Environment: Seaside


2. System:
- queries multiple APIs
- aggregates results
- computes ranking
- returns top restaurants

3. Frontend:
- displays results
- shows execution timeline
- compares performance modes

---

## Future Improvements

- Add more APIs (TripAdvisor, Foursquare)
- Improve AI agent decision-making
- Implement distributed execution (cluster)
- Add caching layer
- Real-time streaming of task progress

---

## Conclusion

This project demonstrates how parallel and distributed techniques can significantly improve performance in real-world applications involving:

- multiple external data sources
- large-scale data processing
- AI-based decision systems

It highlights the trade-offs between simplicity (sequential execution) and efficiency (parallel execution).

---