"""Direct tests for runtime-adjacent service slices used by TD-030."""

from __future__ import annotations

import importlib


class _FakeQtSignal:
    def __init__(self) -> None:
        self.connected = []
        self.disconnected = []

    def connect(self, callback) -> None:
        self.connected.append(callback)

    def disconnect(self, callback) -> None:
        self.disconnected.append(callback)


class _FakeScreen:
    def __init__(self, name: str, x: int, y: int, width: int, height: int, refresh_rate: float = 60.0):
        self._name = name
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self._refresh_rate = refresh_rate

    def name(self) -> str:
        return self._name

    def manufacturer(self) -> str:
        return "Valve"

    def model(self) -> str:
        return "Deck"

    def serialNumber(self) -> str:
        return self._name

    def size(self):
        width = self._width
        height = self._height
        return type("Size", (), {"width": lambda self: width, "height": lambda self: height})()

    def refreshRate(self) -> float:
        return self._refresh_rate

    def geometry(self):
        x = self._x
        y = self._y
        width = self._width
        height = self._height
        return type(
            "Geometry",
            (),
            {
                "x": lambda self: x,
                "y": lambda self: y,
                "width": lambda self: width,
                "height": lambda self: height,
            },
        )()

    def devicePixelRatio(self) -> float:
        return 1.0


class _FakeApp:
    def __init__(self, screens):
        self._screens = list(screens)
        self.screenAdded = _FakeQtSignal()
        self.screenRemoved = _FakeQtSignal()
        self.primaryScreenChanged = _FakeQtSignal()

    def screens(self):
        return list(self._screens)

    def primaryScreen(self):
        return self._screens[0] if self._screens else None


class _FakeQGuiApplication:
    _app: _FakeApp | None = None

    @classmethod
    def instance(cls):
        return cls._app

    @classmethod
    def primaryScreen(cls):
        return cls._app.primaryScreen() if cls._app is not None else None


def test_screen_manager_reports_virtual_desktop_and_cleans_up(qt_app, monkeypatch) -> None:
    module = importlib.import_module("paint_controller.services.screen_manager")
    screens = [
        _FakeScreen("builtin", 0, 0, 1280, 800),
        _FakeScreen("external", 1280, 0, 1920, 1080),
    ]
    fake_app = _FakeApp(screens)
    _FakeQGuiApplication._app = fake_app
    monkeypatch.setattr(module, "QGuiApplication", _FakeQGuiApplication)

    manager = module.ScreenManager(
        node=type("Node", (), {"get_logger": lambda self: type("Logger", (), {"info": lambda self, _msg: None})()})()
    )

    assert manager.get_screen_count() == 2
    assert manager.get_primary_screen_name() == "builtin"
    assert manager.get_virtual_desktop_size() == (3200, 1080)
    assert manager.get_screen_info_string(1).startswith("Screen 1")

    monitor_timer = manager._monitor_timer
    manager.cleanup()

    assert monitor_timer.isActive() is False
    assert fake_app.screenAdded.disconnected == [manager._on_screen_added]
    assert fake_app.screenRemoved.disconnected == [manager._on_screen_removed]
    assert fake_app.primaryScreenChanged.disconnected == [manager._on_primary_screen_changed]


def test_base_top_view_transformer_scales_output_and_uses_cached_maps(monkeypatch) -> None:
    module = importlib.import_module("paint_controller.services.base_top_view_service")
    transformer = module.BaseTopViewTransformer(config_path="/does/not/exist.json")

    compute_calls = []
    monkeypatch.setattr(
        transformer,
        "_compute_remap_tables",
        lambda: compute_calls.append((transformer.output_width, transformer.output_height)),
    )

    transformer.initialize_for_resolution(960, 540)

    assert transformer._input_width == 960
    assert transformer._input_height == 540
    assert transformer.output_width == 500
    assert transformer.output_height == 500
    assert compute_calls == [(500, 500)]
