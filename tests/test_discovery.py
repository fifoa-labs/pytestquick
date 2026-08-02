"""
tests/test_discovery.py

Tests for pytest target discovery helpers.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest

from pytestquick.discovery import (
    find_all_test_files,
    find_app_dir,
    find_latest_test_file,
    find_test_class,
    find_test_files_under_dir,
    find_test_method,
    is_test_file,
    looks_like_path,
    relative_pytest_path,
)

if TYPE_CHECKING:
    from pathlib import Path


def write_file(path: Path, content: str = "") -> Path:
    """Create a file and any missing parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("relative_path", "expected"),
    [
        ("test_models.py", True),
        ("app/test_services.py", True),
        ("tests/models.py", True),
        ("app/tests/services.py", True),
        ("models.py", False),
        ("tests/README.md", False),
    ],
)
def test_is_test_file(
    tmp_path: Path,
    relative_path: str,
    expected: bool,  # noqa: FBT001
) -> None:
    """Test pytest-style file detection."""
    path = write_file(tmp_path / relative_path)

    assert is_test_file(path) is expected


def test_is_test_file_returns_false_for_directory(tmp_path: Path) -> None:
    """Directories should not be treated as test modules."""
    directory = tmp_path / "tests"
    directory.mkdir()

    assert is_test_file(directory) is False


def test_find_all_test_files_returns_supported_files_in_path_order(
    tmp_path: Path,
) -> None:
    """Discovery should return supported test files deterministically."""
    first = write_file(tmp_path / "app" / "test_models.py")
    second = write_file(tmp_path / "app" / "tests" / "services.py")

    write_file(tmp_path / "app" / "models.py")
    write_file(tmp_path / "README.md")

    assert find_all_test_files(tmp_path) == sorted([first, second])


def test_find_test_files_under_dir_limits_discovery_to_root(
    tmp_path: Path,
) -> None:
    """Directory-scoped discovery should not include sibling applications."""
    app_test = write_file(tmp_path / "app" / "tests" / "test_models.py")
    write_file(tmp_path / "other" / "tests" / "test_other.py")

    assert find_test_files_under_dir(tmp_path / "app") == [app_test]


def test_find_latest_test_file_returns_newest_file(tmp_path: Path) -> None:
    """The latest modified test module should be selected."""
    older = write_file(tmp_path / "tests" / "test_old.py")
    newer = write_file(tmp_path / "tests" / "test_new.py")

    os.utime(older, ns=(1_000_000_000, 1_000_000_000))
    os.utime(newer, ns=(2_000_000_000, 2_000_000_000))

    assert find_latest_test_file(tmp_path) == newer


def test_find_latest_test_file_uses_path_as_tiebreaker(
    tmp_path: Path,
) -> None:
    """Equal timestamps should produce deterministic selection."""
    first = write_file(tmp_path / "tests" / "test_alpha.py")
    second = write_file(tmp_path / "tests" / "test_beta.py")

    timestamp = 2_000_000_000
    os.utime(first, ns=(timestamp, timestamp))
    os.utime(second, ns=(timestamp, timestamp))

    assert find_latest_test_file(tmp_path) == second


def test_find_latest_test_file_raises_when_no_tests_exist(
    tmp_path: Path,
) -> None:
    """An empty search root should fail clearly."""
    with pytest.raises(
        FileNotFoundError,
        match="No test files found under",
    ):
        find_latest_test_file(tmp_path)


def test_relative_pytest_path_returns_project_relative_path(
    tmp_path: Path,
) -> None:
    """Paths inside the project should be converted to relative form."""
    test_file = write_file(tmp_path / "tests" / "test_models.py")

    assert relative_pytest_path(test_file, tmp_path) == ("tests/test_models.py")


def test_relative_pytest_path_preserves_external_absolute_path(
    tmp_path: Path,
) -> None:
    """Paths outside the project should remain absolute."""
    project = tmp_path / "project"
    external = write_file(tmp_path / "external" / "test_models.py")
    project.mkdir()

    assert relative_pytest_path(external, project) == str(
        external.resolve(),
    )


def test_find_app_dir_prefers_shallow_candidate_with_tests(
    tmp_path: Path,
) -> None:
    """The shallowest matching application containing tests should win."""
    shallow = tmp_path / "src" / "billing"
    deep = tmp_path / "packages" / "nested" / "billing"

    write_file(shallow / "tests" / "test_models.py")
    write_file(deep / "tests" / "test_models.py")

    assert find_app_dir("billing", tmp_path) == shallow


def test_find_app_dir_prefers_candidate_containing_tests(
    tmp_path: Path,
) -> None:
    """A matching folder with tests should beat one without tests."""
    without_tests = tmp_path / "billing"
    with_tests = tmp_path / "src" / "billing"

    without_tests.mkdir(parents=True)
    write_file(with_tests / "tests" / "test_models.py")

    assert find_app_dir("billing", tmp_path) == with_tests


def test_find_app_dir_returns_shallow_candidate_without_tests(
    tmp_path: Path,
) -> None:
    """A matching folder may still be returned before tests are created."""
    shallow = tmp_path / "billing"
    deep = tmp_path / "src" / "billing"

    shallow.mkdir(parents=True)
    deep.mkdir(parents=True)

    assert find_app_dir("billing", tmp_path) == shallow


def test_find_app_dir_returns_none_for_unknown_app(
    tmp_path: Path,
) -> None:
    """Unknown application names should not resolve."""
    assert find_app_dir("missing", tmp_path) is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("tests/test_models.py", True),
        (r"tests\test_models.py", True),
        ("test_models.py", True),
        ("TestModels", False),
        ("billing", False),
    ],
)
def test_looks_like_path_for_nonexistent_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    value: str,
    expected: bool,  # noqa: FBT001
) -> None:
    """Path-like syntax should be recognized without requiring existence."""
    monkeypatch.chdir(tmp_path)

    assert looks_like_path(value) is expected


def test_looks_like_path_returns_true_for_existing_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Existing filesystem entries should be recognized as paths."""
    directory = tmp_path / "billing"
    directory.mkdir()
    monkeypatch.chdir(tmp_path)

    assert looks_like_path("billing") is True


def test_find_test_method_returns_class_method_node(
    tmp_path: Path,
) -> None:
    """A method inside a class should produce a full pytest node ID."""
    write_file(
        tmp_path / "tests" / "test_models.py",
        """
class TestInvoice:
    def test_total(self) -> None:
        pass
""".strip(),
    )

    assert find_test_method("test_total", tmp_path) == (
        "tests/test_models.py::TestInvoice::test_total"
    )


def test_find_test_method_returns_module_function_node(
    tmp_path: Path,
) -> None:
    """A module-level test should produce a function node ID."""
    write_file(
        tmp_path / "tests" / "test_models.py",
        """
def test_total() -> None:
    pass
""".strip(),
    )

    assert find_test_method("test_total", tmp_path) == (
        "tests/test_models.py::test_total"
    )


def test_find_test_method_supports_async_functions(
    tmp_path: Path,
) -> None:
    """Async test functions should be discoverable."""
    write_file(
        tmp_path / "tests" / "test_models.py",
        """
async def test_total() -> None:
    pass
""".strip(),
    )

    assert find_test_method("test_total", tmp_path) == (
        "tests/test_models.py::test_total"
    )


def test_find_test_method_returns_none_when_missing(
    tmp_path: Path,
) -> None:
    """Missing methods should not produce a node ID."""
    write_file(
        tmp_path / "tests" / "test_models.py",
        "def test_other() -> None:\n    pass\n",
    )

    assert find_test_method("test_total", tmp_path) is None


def test_find_test_class_returns_class_node(tmp_path: Path) -> None:
    """A matching class should produce a class-level pytest node ID."""
    write_file(
        tmp_path / "tests" / "test_models.py",
        """
class TestInvoice:
    def test_total(self) -> None:
        pass
""".strip(),
    )

    assert find_test_class("TestInvoice", tmp_path) == (
        "tests/test_models.py::TestInvoice"
    )


def test_find_test_class_supports_base_classes(tmp_path: Path) -> None:
    """Classes with base classes should be discoverable."""
    write_file(
        tmp_path / "tests" / "test_models.py",
        """
class TestInvoice(BaseTestCase):
    pass
""".strip(),
    )

    assert find_test_class("TestInvoice", tmp_path) == (
        "tests/test_models.py::TestInvoice"
    )


def test_find_test_class_returns_none_when_missing(
    tmp_path: Path,
) -> None:
    """Missing classes should not produce a node ID."""
    write_file(
        tmp_path / "tests" / "test_models.py",
        "class TestOther:\n    pass\n",
    )

    assert find_test_class("TestInvoice", tmp_path) is None
