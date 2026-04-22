"""Static regression checks for heavyweight QML page imports."""

from __future__ import annotations

from pathlib import Path
import re


_HEAVY_IMPORT_RULES = {
    "QtCharts": re.compile(r"\b(ChartView|LineSeries|ValueAxis|BarSeries|PieSeries|SplineSeries)\b"),
    "QtMultimedia": re.compile(r"\b(MediaPlayer|VideoOutput|Camera|AudioOutput|CaptureSession|MediaDevices|SoundEffect)\b"),
    "Qt5Compat.GraphicalEffects": re.compile(
        r"\b(DropShadow|OpacityMask|FastBlur|Glow|ColorOverlay|InnerShadow|RectangularGlow)\b"
    ),
}


def test_qml_pages_do_not_keep_unused_heavy_imports():
    repo_root = Path(__file__).resolve().parent.parent
    pages_dir = repo_root / "python" / "paint_controller" / "qml" / "pages"
    failures = []

    for qml_path in pages_dir.rglob("*.qml"):
        source = qml_path.read_text(encoding="utf-8")
        for module_name, usage_pattern in _HEAVY_IMPORT_RULES.items():
            import_pattern = re.compile(rf"^\s*import\s+{re.escape(module_name)}\s*$", re.MULTILINE)
            if import_pattern.search(source) and usage_pattern.search(source) is None:
                failures.append(f"{qml_path.relative_to(repo_root)} imports {module_name} but does not use it")

    assert not failures, "\n".join(failures)