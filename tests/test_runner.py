"""
tests/test_runner.py

Tests for pytest command construction, coverage scoping, and execution.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest

from pytestquick import runner

if TYPE_CHECKING:
    from pathlib import Path


def write_file(path: Path, content: str = "") -> Path:
    """Create a file and any missing parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_require_pytest_cov_returns_when_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """pytest-cov availability should satisfy the dependency check."""
    find_spec = Mock(return_value=object())

    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        find_spec,
    )

    runner.require_pytest_cov()

    find_spec.assert_called_once_with("pytest_cov")


def test_require_pytest_cov_raises_when_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing pytest-cov should produce a useful installation error."""
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        Mock(return_value=None),
    )

    with pytest.raises(
        RuntimeError,
        match="pytest-cov is not installed",
    ):
        runner.require_pytest_cov()


def test_discover_src_package_returns_none_without_src_directory(
    tmp_path: Path,
) -> None:
    """Projects without a src directory should not yield a package."""
    assert runner.discover_src_package(tmp_path) is None


def test_discover_src_package_returns_single_package(
    tmp_path: Path,
) -> None:
    """A single import package beneath src should be discovered."""
    write_file(
        tmp_path / "src" / "pytestquick" / "__init__.py",
    )

    assert runner.discover_src_package(tmp_path) == "pytestquick"


def test_discover_src_package_ignores_nonpackages_and_hidden_directories(
    tmp_path: Path,
) -> None:
    """Only visible directories containing __init__.py should count."""
    write_file(
        tmp_path / "src" / "pytestquick" / "__init__.py",
    )
    write_file(
        tmp_path / "src" / ".hidden" / "__init__.py",
    )
    write_file(
        tmp_path / "src" / "not_a_package" / "module.py",
    )
    write_file(
        tmp_path / "src" / "README.txt",
    )

    assert runner.discover_src_package(tmp_path) == "pytestquick"


def test_discover_src_package_returns_none_for_multiple_packages(
    tmp_path: Path,
) -> None:
    """Ambiguous src layouts should not guess a coverage package."""
    write_file(
        tmp_path / "src" / "alpha" / "__init__.py",
    )
    write_file(
        tmp_path / "src" / "beta" / "__init__.py",
    )

    assert runner.discover_src_package(tmp_path) is None


def test_infer_coverage_scope_uses_matching_nested_source_file(
    tmp_path: Path,
) -> None:
    """A nested test file should cover its matching source module."""
    write_file(
        tmp_path / "fab" / "tasks" / "sync_envs" / "syncer.py",
    )

    result = runner.infer_coverage_scope(
        "fab/tasks/sync_envs/tests/test_syncer.py",
        tmp_path,
    )

    assert result == "fab.tasks.sync_envs.syncer"


def test_infer_coverage_scope_strips_pytest_node_suffix(
    tmp_path: Path,
) -> None:
    """A pytest node should still cover its matching source module."""
    write_file(
        tmp_path / "fab" / "tasks" / "sync_envs" / "transport.py",
    )

    result = runner.infer_coverage_scope(
        ("fab/tasks/sync_envs/tests/test_transport.py::TestTransport::test_send"),
        tmp_path,
    )

    assert result == "fab.tasks.sync_envs.transport"


def test_infer_coverage_scope_handles_nested_tests_subdirectories(
    tmp_path: Path,
) -> None:
    """Nested directories below tests should map to matching source paths."""
    write_file(
        tmp_path / "billing" / "services" / "invoice.py",
    )

    result = runner.infer_coverage_scope(
        "billing/tests/services/test_invoice.py",
        tmp_path,
    )

    assert result == "billing.services.invoice"


def test_infer_coverage_scope_handles_django_app_test_layout(
    tmp_path: Path,
) -> None:
    """A Django app test should map to its matching source module."""
    write_file(
        tmp_path / "atlas" / "appstore" / "pages" / "views" / "django" / "base.py",
    )

    result = runner.infer_coverage_scope(
        ("atlas/appstore/pages/views/django/tests/test_base.py"),
        tmp_path,
    )

    assert result == "atlas.appstore.pages.views.django.base"


def test_infer_coverage_scope_uses_matching_src_module_for_root_tests(
    tmp_path: Path,
) -> None:
    """Root tests should cover the matching module in a src layout."""
    write_file(
        tmp_path / "src" / "pytestquick" / "__init__.py",
    )
    write_file(
        tmp_path / "src" / "pytestquick" / "runner.py",
    )

    result = runner.infer_coverage_scope(
        "tests/test_runner.py",
        tmp_path,
    )

    assert result == "pytestquick.runner"


def test_infer_coverage_scope_falls_back_to_src_package(
    tmp_path: Path,
) -> None:
    """Root tests without a matching module should use the src package."""
    write_file(
        tmp_path / "src" / "pytestquick" / "__init__.py",
    )

    result = runner.infer_coverage_scope(
        "tests/test_unknown.py",
        tmp_path,
    )

    assert result == "pytestquick"


def test_infer_coverage_scope_falls_back_to_nested_package(
    tmp_path: Path,
) -> None:
    """Nested tests without a source match should use their application."""
    result = runner.infer_coverage_scope(
        "fab/tasks/sync_envs/tests/test_unknown.py",
        tmp_path,
    )

    assert result == "fab/tasks/sync_envs"


def test_infer_coverage_scope_uses_project_for_root_tests_without_package(
    tmp_path: Path,
) -> None:
    """Root tests should fall back to the project when no package is clear."""
    result = runner.infer_coverage_scope(
        "tests/test_unknown.py",
        tmp_path,
    )

    assert result == "."


def test_infer_coverage_scope_uses_matching_adjacent_source_file(
    tmp_path: Path,
) -> None:
    """A test beside its source file should cover that source module."""
    write_file(
        tmp_path / "runner.py",
    )

    result = runner.infer_coverage_scope(
        "test_runner.py",
        tmp_path,
    )

    assert result == "runner"


def test_infer_coverage_scope_uses_parent_for_source_python_file(
    tmp_path: Path,
) -> None:
    """A direct source file target should measure its containing directory."""
    result = runner.infer_coverage_scope(
        "fab/tasks/transport.py",
        tmp_path,
    )

    assert result == "fab/tasks"


def test_infer_coverage_scope_uses_directory_target_directly(
    tmp_path: Path,
) -> None:
    """Application directory targets should measure the whole directory."""
    result = runner.infer_coverage_scope(
        "fab/tasks",
        tmp_path,
    )

    assert result == "fab/tasks"


def test_infer_coverage_scope_uses_django_app_directory_directly(
    tmp_path: Path,
) -> None:
    """A Django app target should measure the whole selected app."""
    result = runner.infer_coverage_scope(
        "atlas/appstore/pages",
        tmp_path,
    )

    assert result == "atlas/appstore/pages"


def test_infer_coverage_scope_defaults_to_current_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Coverage source discovery should default to the current directory."""
    write_file(
        tmp_path / "src" / "pytestquick" / "__init__.py",
    )
    write_file(
        tmp_path / "src" / "pytestquick" / "runner.py",
    )
    monkeypatch.chdir(tmp_path)

    result = runner.infer_coverage_scope(
        "tests/test_runner.py",
    )

    assert result == "pytestquick.runner"


def test_build_command_enables_coverage_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The default command should include terminal branch coverage."""
    require_pytest_cov = Mock()
    infer_coverage_scope = Mock(
        return_value="pytestquick.runner",
    )

    monkeypatch.setattr(
        runner,
        "require_pytest_cov",
        require_pytest_cov,
    )
    monkeypatch.setattr(
        runner,
        "infer_coverage_scope",
        infer_coverage_scope,
    )

    assert runner.build_command(
        "tests/test_runner.py",
        [],
    ) == [
        sys.executable,
        "-m",
        "pytest",
        "-rs",
        "tests/test_runner.py",
        "--disable-warnings",
        "--cov=pytestquick.runner",
        "--cov-branch",
        "--cov-report=term-missing",
    ]

    require_pytest_cov.assert_called_once_with()
    infer_coverage_scope.assert_called_once_with(
        "tests/test_runner.py",
    )


def test_build_command_uses_package_scope_for_directory_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A directory target should retain package-wide coverage."""
    monkeypatch.setattr(
        runner,
        "require_pytest_cov",
        Mock(),
    )
    monkeypatch.setattr(
        runner,
        "infer_coverage_scope",
        Mock(return_value="atlas/appstore/pages"),
    )

    assert runner.build_command(
        "atlas/appstore/pages",
        [],
    ) == [
        sys.executable,
        "-m",
        "pytest",
        "-rs",
        "atlas/appstore/pages",
        "--disable-warnings",
        "--cov=atlas/appstore/pages",
        "--cov-branch",
        "--cov-report=term-missing",
    ]


def test_build_command_disables_coverage_when_requested() -> None:
    """Coverage should be omitted when explicitly disabled."""
    assert runner.build_command(
        "tests/test_models.py",
        [],
        coverage=False,
    ) == [
        sys.executable,
        "-m",
        "pytest",
        "-rs",
        "tests/test_models.py",
        "--disable-warnings",
    ]


def test_build_command_forwards_pytest_arguments_with_coverage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Additional pytest arguments should follow coverage configuration."""
    monkeypatch.setattr(
        runner,
        "require_pytest_cov",
        Mock(),
    )
    monkeypatch.setattr(
        runner,
        "infer_coverage_scope",
        Mock(return_value="billing.models"),
    )

    assert runner.build_command(
        "billing/tests/test_models.py",
        ["-vv", "-x"],
    ) == [
        sys.executable,
        "-m",
        "pytest",
        "-rs",
        "billing/tests/test_models.py",
        "--disable-warnings",
        "--cov=billing.models",
        "--cov-branch",
        "--cov-report=term-missing",
        "-vv",
        "-x",
    ]


def test_build_command_forwards_pytest_arguments_without_coverage() -> None:
    """Plain pytest mode should continue forwarding arguments unchanged."""
    assert runner.build_command(
        "tests/test_models.py",
        ["-vv", "-x"],
        coverage=False,
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
    """List mode should collect tests without executing coverage."""
    assert runner.build_command(
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
    assert runner.build_command(
        "tests/test_models.py",
        [
            "--list",
            "--disable-warnings",
        ],
    ) == [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_models.py",
        "--collect-only",
        "-q",
        "--disable-warnings",
    ]


def test_build_command_list_mode_does_not_require_pytest_cov(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Collection-only mode should not require the coverage plugin."""
    require_pytest_cov = Mock()

    monkeypatch.setattr(
        runner,
        "require_pytest_cov",
        require_pytest_cov,
    )

    runner.build_command(
        "tests/test_models.py",
        ["--list"],
    )

    require_pytest_cov.assert_not_called()


def test_build_command_builds_keyword_command_with_coverage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The grep option should combine cleanly with focused coverage."""
    monkeypatch.setattr(
        runner,
        "require_pytest_cov",
        Mock(),
    )
    monkeypatch.setattr(
        runner,
        "infer_coverage_scope",
        Mock(return_value="billing.models"),
    )

    assert runner.build_command(
        "billing/tests/test_models.py",
        ["--grep", "invoice"],
    ) == [
        sys.executable,
        "-m",
        "pytest",
        "-rs",
        "billing/tests/test_models.py",
        "--disable-warnings",
        "-k",
        "invoice",
        "--cov=billing.models",
        "--cov-branch",
        "--cov-report=term-missing",
    ]


def test_build_command_builds_keyword_command_without_coverage() -> None:
    """Keyword selection should also work in plain pytest mode."""
    assert runner.build_command(
        "tests/test_models.py",
        ["--grep", "invoice"],
        coverage=False,
    ) == [
        sys.executable,
        "-m",
        "pytest",
        "-rs",
        "tests/test_models.py",
        "--disable-warnings",
        "-k",
        "invoice",
    ]


def test_build_command_removes_grep_arguments_before_forwarding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Custom grep arguments should not be forwarded twice."""
    monkeypatch.setattr(
        runner,
        "require_pytest_cov",
        Mock(),
    )
    monkeypatch.setattr(
        runner,
        "infer_coverage_scope",
        Mock(return_value="billing.models"),
    )

    assert runner.build_command(
        "billing/tests/test_models.py",
        [
            "-vv",
            "--grep",
            "invoice",
            "-x",
        ],
    ) == [
        sys.executable,
        "-m",
        "pytest",
        "-rs",
        "billing/tests/test_models.py",
        "--disable-warnings",
        "-k",
        "invoice",
        "--cov=billing.models",
        "--cov-branch",
        "--cov-report=term-missing",
        "-vv",
        "-x",
    ]


def test_build_command_raises_when_grep_pattern_is_missing() -> None:
    """A grep option without a pattern should fail clearly."""
    with pytest.raises(
        ValueError,
        match=r"Missing argument for --grep\.",
    ):
        runner.build_command(
            "tests/test_models.py",
            ["--grep"],
        )


def test_build_command_does_not_modify_supplied_arguments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Building a command should not mutate the caller's argument list."""
    args = [
        "--grep",
        "invoice",
        "-vv",
    ]

    monkeypatch.setattr(
        runner,
        "require_pytest_cov",
        Mock(),
    )
    monkeypatch.setattr(
        runner,
        "infer_coverage_scope",
        Mock(return_value="billing.models"),
    )

    runner.build_command(
        "billing/tests/test_models.py",
        args,
    )

    assert args == [
        "--grep",
        "invoice",
        "-vv",
    ]


def test_list_option_takes_precedence_over_grep() -> None:
    """List mode should win when multiple pytestquick options are supplied."""
    assert runner.build_command(
        "tests/test_models.py",
        [
            "--grep",
            "invoice",
            "--list",
        ],
    ) == [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_models.py",
        "--collect-only",
        "-q",
        "--grep",
        "invoice",
    ]


def test_run_test_executes_command_and_returns_exit_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The runner should execute the built command and preserve its status."""
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_models.py",
    ]
    build_command = Mock(return_value=command)

    completed: subprocess.CompletedProcess[list[str]] = subprocess.CompletedProcess(
        args=command,
        returncode=5,
    )
    run_mock = Mock(return_value=completed)

    monkeypatch.setattr(
        runner,
        "build_command",
        build_command,
    )
    monkeypatch.setattr(
        subprocess,
        "run",
        run_mock,
    )

    result = runner.run_test(
        "tests/test_models.py",
        ["-x"],
    )

    assert result == 5

    build_command.assert_called_once_with(
        "tests/test_models.py",
        ["-x"],
        coverage=True,
    )
    run_mock.assert_called_once_with(
        command,
        check=False,
    )


def test_run_test_forwards_disabled_coverage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The runner should pass the coverage preference to command building."""
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_models.py",
    ]
    build_command = Mock(return_value=command)

    completed: subprocess.CompletedProcess[list[str]] = subprocess.CompletedProcess(
        args=command,
        returncode=0,
    )

    monkeypatch.setattr(
        runner,
        "build_command",
        build_command,
    )
    monkeypatch.setattr(
        subprocess,
        "run",
        Mock(return_value=completed),
    )

    result = runner.run_test(
        "tests/test_models.py",
        [],
        coverage=False,
    )

    assert result == 0

    build_command.assert_called_once_with(
        "tests/test_models.py",
        [],
        coverage=False,
    )


def test_infer_coverage_scope_maps_init_test_to_package(
    tmp_path: Path,
) -> None:
    """A test for __init__.py should cover the package itself."""
    write_file(
        tmp_path / "src" / "pytestquick" / "__init__.py",
    )

    result = runner.infer_coverage_scope(
        "tests/test___init__.py",
        tmp_path,
    )

    assert result == "pytestquick"


def test_infer_coverage_scope_maps_nested_root_test_into_src_package(
    tmp_path: Path,
) -> None:
    """Nested root tests should map into the matching src package path."""
    write_file(
        tmp_path / "src" / "pytestquick" / "__init__.py",
    )
    write_file(
        tmp_path / "src" / "pytestquick" / "services" / "invoice.py",
    )

    result = runner.infer_coverage_scope(
        "tests/services/test_invoice.py",
        tmp_path,
    )

    assert result == "pytestquick.services.invoice"


def test_infer_coverage_scope_maps_nested_root_test_without_src_package(
    tmp_path: Path,
) -> None:
    """Nested root tests should consider an equivalent project path."""
    write_file(
        tmp_path / "services" / "invoice.py",
    )

    result = runner.infer_coverage_scope(
        "tests/services/test_invoice.py",
        tmp_path,
    )

    assert result == "services.invoice"


def test_infer_coverage_scope_falls_back_for_root_python_file_with_src_package(
    tmp_path: Path,
) -> None:
    """An unmatched root Python file should fall back to the src package."""
    write_file(
        tmp_path / "src" / "pytestquick" / "__init__.py",
    )

    result = runner.infer_coverage_scope(
        "helper.py",
        tmp_path,
    )

    assert result == "pytestquick"


def test_infer_coverage_scope_falls_back_for_root_python_file_without_package(
    tmp_path: Path,
) -> None:
    """An unmatched root Python file should fall back to the project."""
    result = runner.infer_coverage_scope(
        "helper.py",
        tmp_path,
    )

    assert result == "."
