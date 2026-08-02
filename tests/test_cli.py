"""
tests/test_cli.py

Tests for pytestquick command-line parsing and target routing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest

from pytestquick import __version__, cli
from pytestquick.logging import LogColors

if TYPE_CHECKING:
    from pathlib import Path


def write_file(path: Path, content: str = "") -> Path:
    """Create a file and any missing parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_build_parser_uses_expected_program_name() -> None:
    """The parser should identify the installed command correctly."""
    parser = cli.build_parser()

    assert parser.prog == "pytestquick"


def test_build_parser_accepts_target() -> None:
    """The parser should accept an optional discovery target."""
    parser = cli.build_parser()

    namespace = parser.parse_args(
        [
            "tests/test_models.py",
        ],
    )

    assert namespace.target == "tests/test_models.py"


def test_build_parser_defaults_target_to_none() -> None:
    """The parser should allow execution without an explicit target."""
    parser = cli.build_parser()

    namespace = parser.parse_args([])

    assert namespace.target is None


def test_build_parser_displays_version(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The version option should report the installed package version."""
    parser = cli.build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--version"])

    assert exc_info.value.code == 0
    assert capsys.readouterr().out == f"pytestquick {__version__}\n"


def test_build_parser_help_contains_examples(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The help output should include practical usage examples."""
    parser = cli.build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--help"])

    assert exc_info.value.code == 0

    output = capsys.readouterr().out

    assert "Examples:" in output
    assert "pytestquick billing" in output
    assert "pytestquick TestInvoice" in output
    assert "pytestquick test_total" in output
    assert "pytestquick --coverage" in output


def test_report_selection_logs_kind_and_target(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Selection reporting should describe the resolved pytest target."""
    with caplog.at_level("INFO", logger="pytestquick"):
        cli.report_selection(
            "Latest modified test file",
            "tests/test_models.py",
        )

    assert caplog.messages == [
        (f"{LogColors.SUCCESS}✓{LogColors.RESET} Latest modified test file"),
        "  tests/test_models.py",
    ]


def test_resolve_explicit_target_returns_nonexistent_target_unchanged(
    tmp_path: Path,
) -> None:
    """A nonexistent explicit target should be delegated to pytest."""
    target = "tests/test_missing.py::test_example"

    assert cli.resolve_explicit_target(target, tmp_path) == target


def test_resolve_explicit_target_normalizes_existing_relative_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An existing relative test file should remain project-relative."""
    write_file(tmp_path / "tests" / "test_models.py")
    monkeypatch.chdir(tmp_path)

    result = cli.resolve_explicit_target(
        "tests/test_models.py",
        tmp_path,
    )

    assert result == "tests/test_models.py"


def test_resolve_explicit_target_normalizes_existing_absolute_file(
    tmp_path: Path,
) -> None:
    """An absolute path within the project should become relative."""
    test_file = write_file(
        tmp_path / "tests" / "test_models.py",
    )

    result = cli.resolve_explicit_target(
        str(test_file),
        tmp_path,
    )

    assert result == "tests/test_models.py"


def test_resolve_explicit_target_preserves_node_suffix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An existing pytest node should retain its class and method suffix."""
    write_file(tmp_path / "tests" / "test_models.py")
    monkeypatch.chdir(tmp_path)

    result = cli.resolve_explicit_target(
        "tests/test_models.py::TestInvoice::test_total",
        tmp_path,
    )

    assert result == ("tests/test_models.py::TestInvoice::test_total")


def test_resolve_target_selects_latest_test_file(
    tmp_path: Path,
) -> None:
    """No target should select the latest test beneath the search root."""
    write_file(tmp_path / "tests" / "test_models.py")

    result = cli.resolve_target(
        None,
        tmp_path,
    )

    assert result == (
        "tests/test_models.py",
        "Latest modified test file",
    )


def test_resolve_target_selects_explicit_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A path-like target should be handled as an explicit pytest target."""
    write_file(tmp_path / "tests" / "test_models.py")
    monkeypatch.chdir(tmp_path)

    result = cli.resolve_target(
        "tests/test_models.py",
        tmp_path,
    )

    assert result == (
        "tests/test_models.py",
        "Explicit pytest target",
    )


def test_resolve_target_selects_explicit_node(
    tmp_path: Path,
) -> None:
    """A pytest node should be recognized without filesystem discovery."""
    target = "tests/test_missing.py::test_example"

    result = cli.resolve_target(
        target,
        tmp_path,
    )

    assert result == (
        target,
        "Explicit pytest target",
    )


def test_resolve_target_selects_test_method(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A test method name should resolve through method discovery."""
    node = "tests/test_models.py::TestInvoice::test_total"
    find_test_method = Mock(return_value=node)

    monkeypatch.setattr(
        cli,
        "find_test_method",
        find_test_method,
    )

    result = cli.resolve_target(
        "test_total",
        tmp_path,
    )

    assert result == (
        node,
        "Test method",
    )
    find_test_method.assert_called_once_with(
        "test_total",
        tmp_path,
    )


def test_resolve_target_raises_when_test_method_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unresolved test method should produce a descriptive error."""
    monkeypatch.setattr(
        cli,
        "find_test_method",
        Mock(return_value=None),
    )

    with pytest.raises(FileNotFoundError) as exc_info:
        cli.resolve_target(
            "test_missing",
            tmp_path,
        )

    message = str(exc_info.value)

    assert "Could not locate test method: test_missing" in message
    assert f"Searched from: {tmp_path}" in message


def test_resolve_target_selects_test_class(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A test class name should resolve through class discovery."""
    node = "tests/test_models.py::TestInvoice"
    find_test_class = Mock(return_value=node)

    monkeypatch.setattr(
        cli,
        "find_test_class",
        find_test_class,
    )

    result = cli.resolve_target(
        "TestInvoice",
        tmp_path,
    )

    assert result == (
        node,
        "Test class",
    )
    find_test_class.assert_called_once_with(
        "TestInvoice",
        tmp_path,
    )


def test_resolve_target_raises_when_test_class_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unresolved test class should produce a descriptive error."""
    monkeypatch.setattr(
        cli,
        "find_test_class",
        Mock(return_value=None),
    )

    with pytest.raises(FileNotFoundError) as exc_info:
        cli.resolve_target(
            "TestMissing",
            tmp_path,
        )

    message = str(exc_info.value)

    assert "Could not locate test class: TestMissing" in message
    assert f"Searched from: {tmp_path}" in message


def test_resolve_target_selects_application_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A plain target should resolve as an application directory."""
    app_dir = tmp_path / "src" / "billing"
    find_app_dir = Mock(return_value=app_dir)

    monkeypatch.setattr(
        cli,
        "looks_like_path",
        Mock(return_value=False),
    )
    monkeypatch.setattr(
        cli,
        "find_app_dir",
        find_app_dir,
    )

    result = cli.resolve_target(
        "billing",
        tmp_path,
    )

    assert result == (
        "src/billing",
        "Application directory",
    )
    find_app_dir.assert_called_once_with(
        "billing",
        tmp_path,
    )


def test_resolve_target_raises_for_unknown_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unknown target should produce a descriptive error."""
    monkeypatch.setattr(
        cli,
        "looks_like_path",
        Mock(return_value=False),
    )
    monkeypatch.setattr(
        cli,
        "find_app_dir",
        Mock(return_value=None),
    )

    with pytest.raises(FileNotFoundError) as exc_info:
        cli.resolve_target(
            "missing",
            tmp_path,
        )

    message = str(exc_info.value)

    assert "Could not locate target: missing" in message
    assert f"Searched from: {tmp_path}" in message


def test_main_runs_latest_test_file_by_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No arguments should run the latest test beneath the current folder."""
    write_file(tmp_path / "tests" / "test_models.py")
    run_test = Mock(return_value=0)
    report_selection = Mock()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "run_test", run_test)
    monkeypatch.setattr(
        cli,
        "report_selection",
        report_selection,
    )

    result = cli.main([])

    assert result == 0
    report_selection.assert_called_once_with(
        "Latest modified test file",
        "tests/test_models.py",
    )
    run_test.assert_called_once_with(
        "tests/test_models.py",
        [],
    )


def test_main_runs_explicit_target_with_pytest_arguments(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unknown CLI options should be forwarded directly to pytest."""
    write_file(tmp_path / "tests" / "test_models.py")
    run_test = Mock(return_value=0)
    report_selection = Mock()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "run_test", run_test)
    monkeypatch.setattr(
        cli,
        "report_selection",
        report_selection,
    )

    result = cli.main(
        [
            "tests/test_models.py",
            "-vv",
            "-x",
        ],
    )

    assert result == 0
    report_selection.assert_called_once_with(
        "Explicit pytest target",
        "tests/test_models.py",
    )
    run_test.assert_called_once_with(
        "tests/test_models.py",
        ["-vv", "-x"],
    )


def test_main_accepts_custom_flag_without_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A custom runner option should work with latest-file discovery."""
    write_file(tmp_path / "tests" / "test_models.py")
    run_test = Mock(return_value=0)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "run_test", run_test)
    monkeypatch.setattr(
        cli,
        "report_selection",
        Mock(),
    )

    result = cli.main(["--coverage"])

    assert result == 0
    run_test.assert_called_once_with(
        "tests/test_models.py",
        ["--coverage"],
    )


def test_main_preserves_test_runner_exit_code(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The CLI should return the exact status produced by the runner."""
    write_file(tmp_path / "tests" / "test_models.py")
    run_test = Mock(return_value=5)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "run_test", run_test)
    monkeypatch.setattr(
        cli,
        "report_selection",
        Mock(),
    )

    result = cli.main([])

    assert result == 5


def test_main_returns_one_when_target_resolution_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A target-resolution error should return a failure status."""
    run_test = Mock(return_value=0)
    report_selection = Mock()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "run_test", run_test)
    monkeypatch.setattr(
        cli,
        "report_selection",
        report_selection,
    )

    result = cli.main(["missing"])

    assert result == 1
    report_selection.assert_not_called()
    run_test.assert_not_called()


@pytest.mark.parametrize(
    "exception",
    [
        FileNotFoundError("missing"),
        OSError("unreadable"),
        RuntimeError("coverage missing"),
        ValueError("invalid"),
    ],
)
def test_main_handles_expected_resolution_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    exception: Exception,
) -> None:
    """Expected discovery failures should return status one."""
    resolve_target = Mock(side_effect=exception)
    run_test = Mock(return_value=0)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        cli,
        "resolve_target",
        resolve_target,
    )
    monkeypatch.setattr(cli, "run_test", run_test)

    result = cli.main([])

    assert result == 1
    resolve_target.assert_called_once_with(
        None,
        tmp_path,
    )
    run_test.assert_not_called()
