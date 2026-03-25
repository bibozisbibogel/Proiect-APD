"""Timing instrumentation for pipeline stages."""

import time
import functools
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class TimingRecord:
    """Single timing measurement."""
    task_name: str
    start_time: float       # relative to pipeline start
    end_time: float          # relative to pipeline start
    duration_seconds: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class TimingCollector:
    """Collects timing records for one pipeline run."""

    def __init__(self):
        self.records: List[TimingRecord] = []
        self.pipeline_start: float = 0.0

    def start_pipeline(self):
        self.pipeline_start = time.perf_counter()
        self.records = []

    def record(self, task_name: str, start: float, end: float, **metadata):
        self.records.append(TimingRecord(
            task_name=task_name,
            start_time=start - self.pipeline_start,
            end_time=end - self.pipeline_start,
            duration_seconds=end - start,
            metadata=metadata,
        ))

    def total_time(self) -> float:
        if not self.records:
            return 0.0
        return self.records[-1].end_time

    def summary(self) -> Dict[str, float]:
        """Return dict of task_name -> duration."""
        return {r.task_name: r.duration_seconds for r in self.records}

    def to_csv_dict(self, run_id: int, query_label: str, mode: str,
                    num_apis: int, num_restaurants: int) -> Dict[str, Any]:
        """Flatten into a dict suitable for CSV export."""
        row: Dict[str, Any] = {
            "run_id": run_id,
            "query": query_label,
            "execution_mode": mode,
            "num_apis": num_apis,
            "num_restaurants": num_restaurants,
        }
        for r in self.records:
            row[f"time_{r.task_name}"] = round(r.duration_seconds, 6)
        row["time_total"] = round(self.total_time(), 6)
        return row

    def print_summary(self):
        """Print a human-readable timing summary."""
        print("\n--- Timing Summary ---")
        for r in self.records:
            meta = ""
            if r.metadata:
                meta = f"  ({', '.join(f'{k}={v}' for k, v in r.metadata.items())})"
            print(f"  {r.task_name:<25} {r.duration_seconds:.4f}s{meta}")
        print(f"  {'TOTAL':<25} {self.total_time():.4f}s")
        print("----------------------\n")


def timed_task(collector: TimingCollector, task_name: Optional[str] = None):
    """Decorator that records execution time of a function."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            name = task_name or func.__name__
            start = time.perf_counter()
            result = func(*args, **kwargs)
            end = time.perf_counter()
            collector.record(name, start, end)
            return result
        return wrapper
    return decorator
