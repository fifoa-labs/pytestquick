"""
src/pytestquick/runner.py

Pytest command construction and execution helpers.
"""

from __future__ import annotations

import shlex
import subprocess
import sys

from .logging import LogColors, log


def build_command(
    test_target: str,
    args: list[str],
) -> list[str]:
    """
    Build the command used to execute pytest.

    Supported pytestquick options:

    * ``--list`` shows collected tests.
    * ``--grep`` runs tests matching a keyword.
    * ``--coverage`` runs pytest through coverage.

    All remaining arguments are forwarded to pytest.

    Args:
        test_target:
            Pytest target, such as a file, directory, class, method,
            or node ID.

        args:
            Additional pytestquick or pytest arguments.

    Returns:
        The complete subprocess command.
    """
    remaining_args = args.copy()

    if "--list" in remaining_args:
        remaining_args.remove("--list")

        return [
            sys.executable,
            "-m",
            "pytest",
            test_target,
            "--collect-only",
            "-q",
            *remaining_args,
        ]

    if "--grep" in remaining_args:
        index = remaining_args.index("--grep")

        if index + 1 >= len(remaining_args):
            msg = "Missing argument for --grep."
            raise ValueError(msg)

        pattern = remaining_args[index + 1]
        del remaining_args[index : index + 2]

        return [
            sys.executable,
            "-m",
            "pytest",
            test_target,
            "-k",
            pattern,
            "-rs",
            "--disable-warnings",
            *remaining_args,
        ]

    if "--coverage" in remaining_args:
        remaining_args.remove("--coverage")

        return [
            sys.executable,
            "-m",
            "coverage",
            "run",
            "-m",
            "pytest",
            test_target,
            *remaining_args,
        ]

    return [
        sys.executable,
        "-m",
        "pytest",
        "-rs",
        test_target,
        "--disable-warnings",
        *remaining_args,
    ]


def run_test(
    test_target: str,
    args: list[str],
) -> int:
    """
    Run pytest against a specific target.

    Args:
        test_target:
            Pytest target, such as a file, directory, class, method,
            or node ID.

        args:
            Additional pytestquick or pytest arguments.

    Returns:
        The exact exit status returned by pytest or coverage.
    """
    command = build_command(
        test_target,
        args,
    )

    log.info(
        "%s→ Running:%s",
        LogColors.SUCCESS,
        LogColors.RESET,
    )
    log.info(
        "  %s",
        shlex.join(command),
    )

    completed = subprocess.run(  # noqa: S603
        command,
        check=False,
    )

    return completed.returncode


__all__ = [
    "build_command",
    "run_test",
]
