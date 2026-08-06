"""P-00: process-wide performance counters for measurement baselines."""

from __future__ import annotations

from paint_controller.core.signal_wiring import SignalWiring
from paint_controller.utils.perf_counters import PERF, timed_section
from tests.test_signal_wiring import _make_ports


def setup_function() -> None:
    PERF.set_enabled(False)
    PERF.reset()


def teardown_function() -> None:
    PERF.set_enabled(False)
    PERF.reset()


def test_perf_counters_disabled_by_default_is_noop() -> None:
    assert PERF.enabled is False
    PERF.incr("status_tick")
    PERF.record_seconds("status_tick", 0.001)
    snap = PERF.snapshot()
    assert snap["enabled"] is False
    assert snap["counts"] == {}
    assert snap["timings"] == {}


def test_perf_counters_incr_and_timing_when_enabled() -> None:
    PERF.set_enabled(True)
    PERF.incr("frame_publish", 2)
    with timed_section("status_tick"):
        pass
    snap = PERF.snapshot()
    assert snap["enabled"] is True
    assert snap["counts"]["frame_publish"] == 2
    assert snap["timings"]["status_tick"]["count"] == 1.0
    assert snap["timings"]["status_tick"]["max_s"] >= 0.0
    assert PERF.count("frame_publish") == 2


def test_status_tick_records_counter_when_enabled() -> None:
    """Shipped SignalWiring._on_status_tick increments status_tick when PERF enabled."""
    PERF.set_enabled(True)
    ports = _make_ports()
    wiring = SignalWiring(ports)
    wiring.wire()
    ports.steam_deck_handler._current_state = {"buttons": {"switch": True}}
    wiring._on_status_tick()
    wiring._on_status_tick()
    assert PERF.count("status_tick") == 2
    # Real tick path still runs (e-stop/exit-hold order preserved).
    assert len(ports.bundle.exit_hold_handler.check_calls) == 2
