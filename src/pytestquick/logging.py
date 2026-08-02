"""
src/pytestquick/logging.py

Logging helpers for pytestquick.
"""

from __future__ import annotations

import logging


class LogColors:
    """ANSI escape codes for colored terminal logging."""

    INFO = "\x1b[34m"
    SUCCESS = "\x1b[32m"
    ERROR = "\x1b[31m"
    RESET = "\x1b[0m"


logging.basicConfig(
    level=logging.INFO,
    format=f"{LogColors.INFO}[%(levelname)s] %(message)s{LogColors.RESET}",
)

log = logging.getLogger("pytestquick")
log.setLevel(logging.INFO)

__all__ = [
    "LogColors",
    "log",
]
