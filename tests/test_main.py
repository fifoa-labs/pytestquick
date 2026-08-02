"""
tests/test_main.py

Tests for the pytestquick module entry point.
"""

from __future__ import annotations

import importlib
import runpy
import sys
from unittest.mock import Mock

import pytest

from pytestquick import cli


def remove_main_module(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Remove the entry-point module so it can be imported cleanly."""
    monkeypatch.delitem(
        sys.modules,
        "pytestquick.__main__",
        raising=False,
    )


def test_importing_main_module_does_not_run_cli(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Importing the entry-point module should not execute the CLI."""
    main = Mock(return_value=0)

    remove_main_module(monkeypatch)
    monkeypatch.setattr(cli, "main", main)

    importlib.import_module("pytestquick.__main__")

    main.assert_not_called()


def test_running_main_module_executes_cli(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Running ``python -m pytestquick`` should invoke the CLI."""
    main = Mock(return_value=0)

    remove_main_module(monkeypatch)
    monkeypatch.setattr(cli, "main", main)

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_module(
            "pytestquick.__main__",
            run_name="__main__",
        )

    assert exc_info.value.code == 0
    main.assert_called_once_with()


def test_running_main_module_preserves_exit_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The module entry point should preserve pytest's exit status."""
    main = Mock(return_value=5)

    remove_main_module(monkeypatch)
    monkeypatch.setattr(cli, "main", main)

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_module(
            "pytestquick.__main__",
            run_name="__main__",
        )

    assert exc_info.value.code == 5
    main.assert_called_once_with()
