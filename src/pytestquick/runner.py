"""
src/pytestquick/runner.py

Pytest command construction, coverage scoping, and execution helpers.
"""

from __future__ import annotations

import importlib.util
import shlex
import subprocess
import sys
from pathlib import Path

from .logging import LogColors, log


def require_pytest_cov() -> None:
    """
    Verify that pytest-cov is installed.

    Raises:
        RuntimeError: If pytest-cov is unavailable in the active environment.
    """
    if importlib.util.find_spec("pytest_cov") is not None:
        return

    msg = (
        "Coverage is enabled by default, but pytest-cov is not installed.\n\n"
        "Install or update pytestquick with its dependencies, or run:\n\n"
        "  pyquicktest --no-coverage"
    )
    raise RuntimeError(msg)


def discover_src_package(project_root: Path) -> str | None:
    """
    Discover a single import package beneath a project's ``src`` directory.

    Args:
        project_root:
            Directory from which pytestquick is being run.

    Returns:
        The package name when exactly one package is discovered, otherwise
        ``None``.
    """
    src_dir = project_root / "src"

    if not src_dir.is_dir():
        return None

    packages = sorted(
        path
        for path in src_dir.iterdir()
        if path.is_dir()
        and not path.name.startswith(".")
        and (path / "__init__.py").is_file()
    )

    if len(packages) != 1:
        return None

    return packages[0].name


def _source_filename(test_file: Path) -> str:
    """Return the likely source filename for a test file."""
    stem = test_file.stem

    if stem.startswith("test_"):
        stem = stem.removeprefix("test_")

    return f"{stem}.py"


def _module_name(source_file: Path) -> str:
    """Convert a project-relative Python source path into an import name."""
    module_path = source_file.with_suffix("")
    parts = list(module_path.parts)

    if parts and parts[0] == "src":
        parts = parts[1:]

    if parts and parts[-1] == "__init__":
        parts = parts[:-1]

    return ".".join(parts)


def _source_candidates(
    test_file: Path,
    project_root: Path,
) -> list[Path]:
    """Build likely source-file candidates for a selected test file."""
    parts = test_file.parts
    source_name = _source_filename(test_file)
    candidates: list[Path] = []

    if "tests" in parts:
        tests_index = len(parts) - 1 - parts[::-1].index("tests")
        source_parts = parts[:tests_index]
        nested_parts = parts[tests_index + 1 : -1]

        if source_parts:
            source_root = Path(*source_parts)

            if nested_parts:
                candidates.append(
                    source_root.joinpath(
                        *nested_parts,
                        source_name,
                    )
                )

            candidates.append(source_root / source_name)
        else:
            src_package = discover_src_package(project_root)

            if src_package is not None:
                source_root = Path("src") / src_package

                if nested_parts:
                    candidates.append(
                        source_root.joinpath(
                            *nested_parts,
                            source_name,
                        )
                    )

                candidates.append(source_root / source_name)

            if nested_parts:
                candidates.append(Path(*nested_parts) / source_name)

            candidates.append(Path(source_name))

        return candidates

    if test_file.name.startswith("test_"):
        candidates.append(test_file.with_name(source_name))

    return candidates


def _matching_source_module(
    test_file: Path,
    project_root: Path,
) -> str | None:
    """Return the import name of the matching source file when one exists."""
    for candidate in _source_candidates(
        test_file,
        project_root,
    ):
        if (project_root / candidate).is_file():
            return _module_name(candidate)

    return None


def _fallback_coverage_scope(  # noqa: PLR0911
    path: Path,
    project_root: Path,
) -> str:
    """Return a broader coverage scope when no source file can be inferred."""
    parts = path.parts

    if "tests" in parts:
        tests_index = len(parts) - 1 - parts[::-1].index("tests")
        source_parts = parts[:tests_index]

        if source_parts:
            return Path(*source_parts).as_posix()

        src_package = discover_src_package(project_root)

        if src_package is not None:
            return src_package

        return "."

    if path.suffix == ".py":
        parent = path.parent

        if parent != Path():
            return parent.as_posix()

        src_package = discover_src_package(project_root)

        if src_package is not None:
            return src_package

        return "."

    return path.as_posix()


def infer_coverage_scope(
    test_target: str,
    project_root: Path | None = None,
) -> str:
    """
    Infer the source scope that should be measured for a pytest target.

    A single test file, class, method, or pytest node prefers the matching
    source module. For example, ``tests/test_runner.py`` can map to
    ``pytestquick.runner``.

    An application or package directory remains a directory-wide coverage
    target.

    When no matching source file can be found, pytestquick falls back to the
    containing package or application.

    Args:
        test_target:
            Resolved pytest target, optionally including a pytest node ID.

        project_root:
            Project root used for source discovery. Defaults to the current
            working directory.

    Returns:
        A path or importable module suitable for pytest-cov's ``--cov`` option.
    """
    root = project_root or Path.cwd()

    path_text, _, _ = test_target.partition("::")
    path = Path(path_text)

    if path.suffix == ".py":
        source_module = _matching_source_module(
            path,
            root,
        )

        if source_module is not None:
            return source_module

    return _fallback_coverage_scope(
        path,
        root,
    )


def build_command(
    test_target: str,
    args: list[str],
    *,
    coverage: bool = True,
) -> list[str]:
    """
    Build the command used to execute pytest.

    Coverage is enabled by default and reports branch coverage plus missing
    lines directly in the terminal.

    Supported pytestquick options:

    * ``--list`` shows collected tests without coverage.
    * ``--grep`` runs tests matching a keyword.

    All remaining arguments are forwarded to pytest.

    Args:
        test_target:
            Pytest target, such as a file, directory, class, method,
            or node ID.

        args:
            Additional pytestquick or pytest arguments.

        coverage:
            Whether pytest-cov coverage reporting should be enabled.

    Returns:
        The complete subprocess command.

    Raises:
        RuntimeError:
            If coverage is enabled but pytest-cov is unavailable.

        ValueError:
            If ``--grep`` is supplied without a pattern.
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

    pytest_args = [
        "-rs",
        test_target,
        "--disable-warnings",
    ]

    if "--grep" in remaining_args:
        index = remaining_args.index("--grep")

        if index + 1 >= len(remaining_args):
            msg = "Missing argument for --grep."
            raise ValueError(msg)

        pattern = remaining_args[index + 1]
        del remaining_args[index : index + 2]

        pytest_args.extend(
            [
                "-k",
                pattern,
            ]
        )

    if coverage:
        require_pytest_cov()

        coverage_scope = infer_coverage_scope(test_target)

        pytest_args.extend(
            [
                f"--cov={coverage_scope}",
                "--cov-branch",
                "--cov-report=term-missing",
            ]
        )

    return [
        sys.executable,
        "-m",
        "pytest",
        *pytest_args,
        *remaining_args,
    ]


def run_test(
    test_target: str,
    args: list[str],
    *,
    coverage: bool = True,
) -> int:
    """
    Run pytest against a specific target.

    Args:
        test_target:
            Pytest target, such as a file, directory, class, method,
            or node ID.

        args:
            Additional pytestquick or pytest arguments.

        coverage:
            Whether terminal coverage reporting should be enabled.

    Returns:
        The exact exit status returned by pytest.

    Raises:
        RuntimeError:
            If an execution dependency is unavailable.

        ValueError:
            If a pytestquick option is invalid.
    """
    command = build_command(
        test_target,
        args,
        coverage=coverage,
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
    "discover_src_package",
    "infer_coverage_scope",
    "require_pytest_cov",
    "run_test",
]
