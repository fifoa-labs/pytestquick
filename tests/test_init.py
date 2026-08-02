"""
tests/test_init.py

Tests for pytestquick package metadata and public exports.
"""

from __future__ import annotations

import importlib
import importlib.metadata
from typing import TYPE_CHECKING

import pytestquick

if TYPE_CHECKING:
    import pytest


def test_version_matches_installed_distribution() -> None:
    """Package metadata should expose the installed distribution version."""
    assert pytestquick.__version__ == importlib.metadata.version(
        "pytestquick",
    )


def test_version_falls_back_when_distribution_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Source imports without package metadata should use a safe fallback."""

    def raise_package_not_found(distribution_name: str) -> str:
        raise importlib.metadata.PackageNotFoundError(distribution_name)

    with monkeypatch.context() as context:
        context.setattr(
            importlib.metadata,
            "version",
            raise_package_not_found,
        )

        reloaded = importlib.reload(pytestquick)

        assert reloaded.__version__ == "0.0.0"

    importlib.reload(pytestquick)


def test_public_exports_are_explicit() -> None:
    """The package should expose only its intended public metadata."""
    assert pytestquick.__all__ == [
        "__version__",
    ]


def test_version_is_publicly_available() -> None:
    """The package version should be available from the top-level package."""
    assert isinstance(pytestquick.__version__, str)
    assert pytestquick.__version__
