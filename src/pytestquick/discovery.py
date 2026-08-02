"""
src/pytestquick/discovery.py

Test-file and pytest-target discovery helpers.
"""

from __future__ import annotations

import re
from pathlib import Path


def is_test_file(path: Path) -> bool:
    """
    Return whether a path looks like a pytest test module.

    Supported patterns:
    - files named ``test_*.py``
    - Python files anywhere inside a ``tests`` directory
    """
    return (
        path.is_file()
        and path.suffix == ".py"
        and (path.name.startswith("test_") or "tests" in path.parts)
    )


def find_all_test_files(start_dir: Path) -> list[Path]:
    """
    Return all pytest-style test files under a directory.

    Results are returned in deterministic path order.
    """
    return sorted(path for path in start_dir.rglob("*.py") if is_test_file(path))


def find_test_files_under_dir(root: Path) -> list[Path]:
    """
    Return all pytest-style test files under a specific directory.

    Results are returned in deterministic path order.
    """
    return find_all_test_files(root)


def find_latest_test_file(start_dir: Path) -> Path:
    """
    Return the most recently modified test file in a project.

    Raises:
        FileNotFoundError: If no test files are found.
    """
    test_files = find_all_test_files(start_dir)

    if not test_files:
        msg = f"No test files found under: {start_dir}"
        raise FileNotFoundError(msg)

    return max(
        test_files,
        key=lambda path: (path.stat().st_mtime_ns, str(path)),
    )


def relative_pytest_path(file_path: Path, base_dir: Path) -> str:
    """
    Convert a path to a pytest-friendly project-relative path.

    Paths outside the project root are returned unchanged.
    """
    resolved_file = file_path.resolve()
    resolved_base = base_dir.resolve()

    try:
        return str(resolved_file.relative_to(resolved_base))
    except ValueError:
        return str(resolved_file)


def find_app_dir(app_name: str, start_dir: Path) -> Path | None:
    """
    Find the most appropriate application directory by folder name.

    Preference is given to the shallowest matching directory that contains
    tests. If no matching directory contains tests, the shallowest matching
    directory is returned.
    """
    candidates = sorted(
        (
            path
            for path in start_dir.rglob(app_name)
            if path.is_dir() and path.name == app_name
        ),
        key=lambda path: (len(path.parts), str(path)),
    )

    if not candidates:
        return None

    candidates_with_tests = [
        path for path in candidates if find_test_files_under_dir(path)
    ]

    if candidates_with_tests:
        return candidates_with_tests[0]

    return candidates[0]


def looks_like_path(value: str) -> bool:
    """
    Return whether a CLI value appears to be a filesystem path.

    A value is considered path-like when it contains a path separator, ends in
    ``.py``, or resolves to an existing filesystem entry.
    """
    return (
        "/" in value or "\\" in value or value.endswith(".py") or Path(value).exists()
    )


def find_test_method(method_name: str, start_dir: Path) -> str | None:
    """
    Find a test method in the most recently modified test file.

    Returns:
        A pytest node ID, or ``None`` when no matching method is found.
    """
    latest_file = find_latest_test_file(start_dir)
    relative_path = relative_pytest_path(latest_file, start_dir)

    current_class: str | None = None

    for raw_line in latest_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        class_match = re.match(r"class\s+(\w+)(?:\(.*\))?:", line)
        if class_match:
            current_class = class_match.group(1)
            continue

        if re.match(rf"(?:async\s+)?def\s+{re.escape(method_name)}\b", line):
            if current_class is not None:
                return f"{relative_path}::{current_class}::{method_name}"

            return f"{relative_path}::{method_name}"

    return None


def find_test_class(class_name: str, start_dir: Path) -> str | None:
    """
    Find a test class in the most recently modified test file.

    Returns:
        A pytest node ID, or ``None`` when no matching class is found.
    """
    latest_file = find_latest_test_file(start_dir)
    relative_path = relative_pytest_path(latest_file, start_dir)

    class_pattern = re.compile(
        rf"class\s+{re.escape(class_name)}(?:\(.*\))?:",
    )

    for raw_line in latest_file.read_text(encoding="utf-8").splitlines():
        if class_pattern.match(raw_line.strip()):
            return f"{relative_path}::{class_name}"

    return None


__all__ = [
    "find_all_test_files",
    "find_app_dir",
    "find_latest_test_file",
    "find_test_class",
    "find_test_files_under_dir",
    "find_test_method",
    "is_test_file",
    "looks_like_path",
    "relative_pytest_path",
]
