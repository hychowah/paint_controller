"""Shared QML warning assertions for startup smoke (TD-042)."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

# Default fatal fragments shared by all smoke surfaces.
DEFAULT_FATAL_QML_WARNING_FRAGMENTS: tuple[str, ...] = (
    "failed to load component",
    "no such file or directory",
    "is not a type",
    "required property",
)


def assert_no_fatal_qml_warnings(
    warnings: Sequence[str],
    *,
    extra_fragments: Iterable[str] = (),
    context: str = "",
) -> None:
    """Fail if any collected QML warning contains a fatal fragment."""
    fragments = tuple(DEFAULT_FATAL_QML_WARNING_FRAGMENTS) + tuple(extra_fragments)
    hits = [
        warning
        for warning in warnings
        if any(fragment in warning.lower() for fragment in fragments)
    ]
    if hits:
        prefix = f"{context}: " if context else ""
        raise AssertionError(f"{prefix}fatal QML warnings: {hits}\nall warnings: {list(warnings)}")
