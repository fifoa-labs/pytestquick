"""
src/pytestquick/cli.py

Command-line interface and pytest target routing for pytestquick.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import TYPE_CHECKING

from pytestquick import __version__

from .discovery import (
    find_app_dir,
    find_latest_test_file,
    find_test_class,
    find_test_method,
    looks_like_path,
    relative_pytest_path,
)
from .logging import LogColors, log
from .runner import run_test

if TYPE_CHECKING:
    from collections.abc import Sequence


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        prog="pytestquick",
        description=(
            "Run the pytest target you are actually working on, "
            "with coverage by default."
        ),
        epilog="""\
Examples:
  pytestquick
      Run the most recently modified test file with coverage.

  pytestquick billing
      Run tests beneath the billing application with coverage.

  pytestquick TestInvoice
      Run a test class from the most recently modified matching test file.

  pytestquick test_total
      Run a test method or function.

  pytestquick tests/test_models.py
      Run an explicit test file.

  pytestquick tests/test_models.py::TestInvoice::test_total
      Run an explicit pytest node.

  pytestquick --no-coverage
      Run without coverage.

  pytestquick billing -vv -x
      Forward normal pytest arguments unchanged.
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show the installed version and exit.",
    )

    parser.add_argument(
        "--coverage",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Show branch coverage and missing lines in the terminal (default: enabled)."
        ),
    )

    parser.add_argument(
        "target",
        nargs="?",
        metavar="TARGET",
        help=(
            "Application directory, test file, test class, test method, or pytest node."
        ),
    )

    return parser


def report_selection(kind: str, target: str) -> None:
    """Report the target selected for execution."""
    log.info(
        "%s✓%s %s",
        LogColors.SUCCESS,
        LogColors.RESET,
        kind,
    )
    log.info("  %s", target)


def resolve_explicit_target(
    target: str,
    project_root: Path,
) -> str:
    """Normalize an explicit filesystem path or pytest node."""
    path_part, separator, node_part = target.partition("::")
    path = Path(path_part)

    if not path.exists():
        return target

    relative = relative_pytest_path(
        path.resolve(),
        project_root.resolve(),
    )

    if separator:
        return f"{relative}::{node_part}"

    return relative


def resolve_target(
    target: str | None,
    project_root: Path,
) -> tuple[str, str]:
    """
    Resolve a CLI target into a pytest target and description.

    Returns:
        A tuple containing the pytest target and target type.

    Raises:
        FileNotFoundError: If the requested target cannot be resolved.
    """
    if target is None:
        latest = find_latest_test_file(project_root)
        return (
            relative_pytest_path(latest, project_root),
            "Latest modified test file",
        )

    if "::" in target or looks_like_path(target):
        return (
            resolve_explicit_target(target, project_root),
            "Explicit pytest target",
        )

    if target.startswith("test_"):
        node = find_test_method(target, project_root)

        if node is None:
            msg = (
                f"Could not locate test method: {target}\nSearched from: {project_root}"
            )
            raise FileNotFoundError(msg)

        return node, "Test method"

    if target.startswith("Test"):
        node = find_test_class(target, project_root)

        if node is None:
            msg = (
                f"Could not locate test class: {target}\nSearched from: {project_root}"
            )
            raise FileNotFoundError(msg)

        return node, "Test class"

    app_dir = find_app_dir(target, project_root)

    if app_dir is not None:
        return (
            relative_pytest_path(app_dir, project_root),
            "Application directory",
        )

    msg = f"Could not locate target: {target}\nSearched from: {project_root}"
    raise FileNotFoundError(msg)


def main(argv: Sequence[str] | None = None) -> int:
    """
    Run the pytestquick command-line interface.

    Args:
        argv:
            Optional argument sequence. When omitted, argparse reads the
            process command-line arguments.

    Returns:
        The exit status returned by pytest, or ``1`` when discovery or
        command construction fails.
    """
    parser = build_parser()
    namespace, pytest_args = parser.parse_known_args(argv)

    project_root = Path.cwd()

    try:
        test_target, selection_kind = resolve_target(
            namespace.target,
            project_root,
        )

        report_selection(
            selection_kind,
            test_target,
        )

        return run_test(
            test_target,
            pytest_args,
            coverage=namespace.coverage,
        )

    except (
        FileNotFoundError,
        OSError,
        RuntimeError,
        ValueError,
    ) as exc:
        log.error(
            "%sError:%s %s",
            LogColors.ERROR,
            LogColors.RESET,
            exc,
        )
        return 1


__all__ = [
    "build_parser",
    "main",
    "report_selection",
    "resolve_explicit_target",
    "resolve_target",
]
