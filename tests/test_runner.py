"""
tests/test_runner.py

Tests for pytest command construction and execution.
"""

from __future__ import annotations

import subprocess
import sys
from unittest.mock import Mock

import pytest

from pytestquick.runner import build_command, run_test


def test_build_command_builds_default_pytest_command() -> None:
    """The default command should use the active Python interpreter."""
    assert build_command(
        "tests/test_models.py",
        [],
    ) == [
        sys.executable,
        "-m",
        "pytest",
        "-rs",
        "tests/test_models.py",
        "--disable-warnings",
    ]


def test_build_command_forwards_pytest_arguments() -> None:
    """Additional pytest arguments should be forwarded unchanged."""
    assert build_command(
        "tests/test_models.py",
        ["-vv", "-x"],
    ) == [
        sys.executable,
        "-m",
        "pytest",
        "-rs",
        "tests/test_models.py",
        "--disable-warnings",
        "-vv",
        "-x",
    ]


def test_build_command_builds_collect_only_command() -> None:
    """The list option should collect tests without executing them."""
    assert build_command(
        "tests/test_models.py",
        ["--list"],
    ) == [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_models.py",
        "--collect-only",
        "-q",
    ]


def test_build_command_forwards_arguments_with_list_option() -> None:
    """Arguments accompanying list mode should still reach pytest."""
    assert build_command(
        "tests/test_models.py",
        ["--list", "--disable-warnings"],
    ) == [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_models.py",
        "--collect-only",
        "-q",
        "--disable-warnings",
    ]


def test_build_command_builds_keyword_command() -> None:
    """The grep option should translate to pytest's keyword selector."""
    assert build_command(
        "tests/test_models.py",
        ["--grep", "invoice"],
    ) == [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_models.py",
        "-k",
        "invoice",
        "-rs",
        "--disable-warnings",
    ]


def test_build_command_removes_grep_arguments_before_forwarding() -> None:
    """The custom grep arguments should not be forwarded twice."""
    assert build_command(
        "tests/test_models.py",
        ["-vv", "--grep", "invoice", "-x"],
    ) == [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_models.py",
        "-k",
        "invoice",
        "-rs",
        "--disable-warnings",
        "-vv",
        "-x",
    ]


def test_build_command_raises_when_grep_pattern_is_missing() -> None:
    """A grep option without a pattern should fail clearly."""
    with pytest.raises(
        ValueError,
        match=r"Missing argument for --grep\.",
    ):
        build_command(
            "tests/test_models.py",
            ["--grep"],
        )


def test_build_command_builds_coverage_command() -> None:
    """Coverage mode should execute pytest through coverage."""
    assert build_command(
        "tests/test_models.py",
        ["--coverage"],
    ) == [
        sys.executable,
        "-m",
        "coverage",
        "run",
        "-m",
        "pytest",
        "tests/test_models.py",
    ]


def test_build_command_forwards_arguments_with_coverage_option() -> None:
    """Arguments accompanying coverage should be forwarded to pytest."""
    assert build_command(
        "tests/test_models.py",
        ["--coverage", "-vv", "-x"],
    ) == [
        sys.executable,
        "-m",
        "coverage",
        "run",
        "-m",
        "pytest",
        "tests/test_models.py",
        "-vv",
        "-x",
    ]


def test_build_command_does_not_modify_supplied_arguments() -> None:
    """Building a command should not mutate the caller's argument list."""
    args = ["--grep", "invoice", "-vv"]

    build_command(
        "tests/test_models.py",
        args,
    )

    assert args == ["--grep", "invoice", "-vv"]


def test_list_option_takes_precedence_over_other_special_options() -> None:
    """List mode should win when multiple custom options are supplied."""
    assert build_command(
        "tests/test_models.py",
        ["--coverage", "--list"],
    ) == [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_models.py",
        "--collect-only",
        "-q",
        "--coverage",
    ]


def test_grep_option_takes_precedence_over_coverage() -> None:
    """Keyword mode should win over coverage when list mode is absent."""
    assert build_command(
        "tests/test_models.py",
        ["--coverage", "--grep", "invoice"],
    ) == [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_models.py",
        "-k",
        "invoice",
        "-rs",
        "--disable-warnings",
        "--coverage",
    ]


def test_run_test_executes_command_and_returns_exit_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The runner should preserve the subprocess exit status."""
    completed: subprocess.CompletedProcess[list[str]] = subprocess.CompletedProcess(
        args=[],
        returncode=5,
    )
    run_mock = Mock(return_value=completed)

    monkeypatch.setattr(
        subprocess,
        "run",
        run_mock,
    )

    result = run_test(
        "tests/test_models.py",
        ["-x"],
    )

    assert result == 5
    run_mock.assert_called_once_with(
        [
            sys.executable,
            "-m",
            "pytest",
            "-rs",
            "tests/test_models.py",
            "--disable-warnings",
            "-x",
        ],
        check=False,
    )


def test_build_command_raises_when_coverage_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Coverage mode should fail gracefully when coverage is unavailable."""
    monkeypatch.setattr(
        "importlib.util.find_spec",
        lambda _: None,
    )

    with pytest.raises(
        RuntimeError,
        match="Coverage support requires",
    ):
        build_command(
            "tests/test_models.py",
            ["--coverage"],
        )
