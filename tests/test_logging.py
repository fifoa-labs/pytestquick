"""
tests/test_logging.py

Tests for pytestquick logging helpers.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pytestquick.logging import LogColors, log

if TYPE_CHECKING:
    import pytest


def test_log_colors_define_expected_ansi_sequences() -> None:
    """Terminal colors should expose stable ANSI escape sequences."""
    assert LogColors.INFO == "\x1b[34m"
    assert LogColors.SUCCESS == "\x1b[32m"
    assert LogColors.ERROR == "\x1b[31m"
    assert LogColors.RESET == "\x1b[0m"


def test_package_logger_uses_expected_name() -> None:
    """The shared package logger should use the pytestquick namespace."""
    assert log.name == "pytestquick"


def test_package_logger_allows_info_messages() -> None:
    """The package logger should not filter normal informational output."""
    assert log.isEnabledFor(logging.INFO)


def test_package_logger_emits_info_message(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Informational messages should be emitted through the shared logger."""
    with caplog.at_level(logging.INFO, logger="pytestquick"):
        log.info("Running pytest target")

    assert "Running pytest target" in caplog.messages


def test_package_logger_formats_parameterized_message(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Parameterized logging should render values correctly."""
    with caplog.at_level(logging.INFO, logger="pytestquick"):
        log.info(
            "%sRunning:%s %s",
            LogColors.SUCCESS,
            LogColors.RESET,
            "tests/test_models.py",
        )

    assert caplog.messages == [
        (f"{LogColors.SUCCESS}Running:{LogColors.RESET} tests/test_models.py"),
    ]
