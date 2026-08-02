# pytestquick

[![PyPI version](https://img.shields.io/pypi/v/pytestquick.svg)](https://pypi.org/project/pytestquick/)
[![Python versions](https://img.shields.io/pypi/pyversions/pytestquick.svg)](https://pypi.org/project/pytestquick/)
[![CI](https://github.com/fifoa-labs/pytestquick/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/fifoa-labs/pytestquick/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/fifoa-labs/pytestquick/branch/main/graph/badge.svg)](https://codecov.io/gh/fifoa-labs/pytestquick)
[![License](https://img.shields.io/pypi/l/pytestquick.svg)](https://github.com/fifoa-labs/pytestquick/blob/main/LICENSE)

A small command-line utility for quickly discovering and running pytest targets.

`pytestquick` discovers the pytest target you are most likely working on from
the current working directory and delegates execution directly to pytest. It
supports explicit test files, pytest node IDs, application directories, test
classes, test methods, and—when no target is supplied—the most recently
modified test file.

It intentionally focuses on pytest target discovery and command construction.
It does not replace pytest, introduce another test framework, or change how
pytest executes your tests.

* **PyPI:** https://pypi.org/project/pytestquick/
* **Source:** https://github.com/fifoa-labs/pytestquick
* **License:** MIT

## Installation

Install the latest release from PyPI:

```bash
pip install pytestquick
```

Or install it as an isolated command with uv:

```bash
uv tool install pytestquick
```

It can also be installed with pipx:

```bash
pipx install pytestquick
```

To install it directly into a project environment:

```bash
uv add --dev pytestquick
```

## Commands

The primary command is:

```bash
pytestquick
```

For convenience, `pyquicktest` is also installed as an alias:

```bash
pyquicktest
```

Both commands are equivalent.

## Quick example

Run `pytestquick` without a target to select the most recently modified test
file beneath the current working directory:

```console
$ pytestquick
✓ Latest modified test file
  tests/services/test_invoice.py

→ Running:
  /path/to/python -m pytest -rs tests/services/test_invoice.py --disable-warnings
```

`pytestquick` reports the selected target, shows the exact command being run,
and returns pytest's exit status unchanged.

## Usage

Run the most recently modified test file:

```console
pytestquick
```

Run all tests beneath an application or package directory:

```console
pytestquick billing
```

Run a test class from the most recently modified test file:

```console
pytestquick TestInvoice
```

Run a test method or function from the most recently modified test file:

```console
pytestquick test_total
```

Run a specific test file:

```console
pytestquick tests/test_models.py
```

Run an explicit pytest node:

```console
pytestquick tests/test_models.py::TestInvoice::test_total
```

Forward normal pytest arguments:

```console
pytestquick billing -vv -x
```

Collect and list tests:

```console
pytestquick --list
```

Filter tests by keyword:

```console
pytestquick --grep invoice
```

Run the selected tests through coverage:

```console
pytestquick --coverage
```

Display the installed version:

```console
pytestquick --version
```

## How discovery works

The current working directory defines the search scope.

Running:

```console
cd ~/Sites/project
pytestquick
```

searches beneath `~/Sites/project`.

Running from a subdirectory intentionally limits discovery to that subtree:

```console
cd ~/Sites/project/billing
pytestquick
```

`pytestquick` does not walk upward looking for a repository root, Git directory, or configuration file.

The directory where the command is run is the directory it searches.

A Python file is considered a test file when either:

* its name begins with `test_`
* it is located beneath a directory named `tests`

When multiple matching application directories exist, `pytestquick` prefers the shallowest one that contains tests.

## Target resolution

Targets are interpreted in this order:

1. An explicit pytest node or filesystem path
2. A test method beginning with `test_`
3. A test class beginning with `Test`
4. An application or package directory
5. The most recently modified test file when no target is supplied

Once a target is selected, `pytestquick` delegates execution to pytest.

> Find the right test. Let pytest do the rest.

## Special options

### List collected tests

```console
pytestquick --list
pytestquick billing --list
```

This runs pytest with `--collect-only`.

### Filter by keyword

```console
pytestquick --grep invoice
pytestquick billing --grep invoice
```

This translates to pytest's `-k` option.

### Run with coverage

```console
pytestquick --coverage
pytestquick billing --coverage
```

This runs the selected target through Python's `coverage` module.

## Pytest arguments

Arguments not handled by `pytestquick` are passed directly to pytest.

```console
pytestquick -vv
pytestquick -x
pytestquick billing -vv -x
pytestquick tests/test_models.py --tb=short
```

## Exit statuses

`pytestquick` returns the exact exit status produced by pytest or coverage.

This means it behaves correctly in:

* shell scripts
* editor integrations
* Docker containers
* continuous-integration environments

Target-discovery failures return exit status `1`.

## Why?

Because this gets old:

```console
pytest path/to/tests/test_really_long_filename.py::TestSomething::test_case
```

And this does not:

```console
pytestquick test_case
```

## Philosophy

`pytestquick` intentionally does one thing well.

It does not replace pytest.

It does not introduce another testing framework, configuration system, or plugin architecture.

It simply removes friction from running the test you are currently working on.

## Development

Install the development environment:

```console
uv sync --dev
```

Run the full test suite:

```console
make test
```

Run formatting, linting, type checking, and tests:

```console
make check
```

Run the complete release validation:

```console
make release-check
```

## License

`pytestquick` is released under the MIT License.
