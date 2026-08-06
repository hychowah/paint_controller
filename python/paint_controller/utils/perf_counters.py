"""Lightweight process-wide performance counters for Qt main-path budgets (P-00).

Debug/measurement hooks only — not a product API and not a mega-Backend.
Thread-safe increments; snapshots are plain dicts for tests and optional HUD later.
Disabled by default (``enabled=False``) so production pays only a single bool check.
"""

from __future__ import annotations

import threading
import time
from typing import Any


class PerfCounters:
    """Named integer counters + optional timing samples (seconds)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._enabled = False
        self._counts: dict[str, int] = {}
        self._timing_sum_s: dict[str, float] = {}
        self._timing_count: dict[str, int] = {}
        self._timing_max_s: dict[str, float] = {}

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        with self._lock:
            self._enabled = bool(enabled)

    def reset(self) -> None:
        with self._lock:
            self._counts.clear()
            self._timing_sum_s.clear()
            self._timing_count.clear()
            self._timing_max_s.clear()

    def incr(self, name: str, amount: int = 1) -> None:
        if not self._enabled:
            return
        with self._lock:
            self._counts[name] = self._counts.get(name, 0) + int(amount)

    def record_seconds(self, name: str, duration_s: float) -> None:
        if not self._enabled:
            return
        d = float(duration_s)
        if d < 0:
            d = 0.0
        with self._lock:
            self._timing_sum_s[name] = self._timing_sum_s.get(name, 0.0) + d
            self._timing_count[name] = self._timing_count.get(name, 0) + 1
            prev = self._timing_max_s.get(name, 0.0)
            if d > prev:
                self._timing_max_s[name] = d

    def count(self, name: str) -> int:
        with self._lock:
            return int(self._counts.get(name, 0))

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            timings: dict[str, dict[str, float]] = {}
            for name, n in self._timing_count.items():
                if n <= 0:
                    continue
                total = self._timing_sum_s.get(name, 0.0)
                timings[name] = {
                    "count": float(n),
                    "sum_s": total,
                    "avg_s": total / n,
                    "max_s": self._timing_max_s.get(name, 0.0),
                }
            return {
                "enabled": self._enabled,
                "counts": dict(self._counts),
                "timings": timings,
            }


# Process-wide singleton used by hot paths when measurement is enabled.
PERF = PerfCounters()


class timed_section:
    """Context manager: record wall time under ``name`` when PERF is enabled."""

    __slots__ = ("_name", "_t0")

    def __init__(self, name: str) -> None:
        self._name = name
        self._t0 = 0.0

    def __enter__(self) -> timed_section:
        if PERF.enabled:
            self._t0 = time.perf_counter()
        return self

    def __exit__(self, *exc: object) -> None:
        if PERF.enabled:
            PERF.record_seconds(self._name, time.perf_counter() - self._t0)
