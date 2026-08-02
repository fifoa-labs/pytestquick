"""
src/pytestquick/__main__.py

Module entry point for ``python -m pytestquick``.
"""

from __future__ import annotations

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
