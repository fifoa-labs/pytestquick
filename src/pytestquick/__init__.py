"""
src/pytestquick/__init__.py

Public package metadata for pytestquick.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pytestquick")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "__version__",
]
