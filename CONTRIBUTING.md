# Contributing to pytestquick

Thank you for your interest in contributing to `pytestquick`.

Contributions are welcome, including bug reports, documentation improvements, tests, and focused feature proposals.

`pytestquick` is intentionally a small command-line utility. Contributions should preserve its primary purpose: quickly discovering the pytest target a developer is most likely working on and delegating execution to pytest.

It should make pytest faster to use, not replace pytest.

## Development Setup

Clone the repository:

```bash
git clone https://github.com/fifoa-labs/pytestquick.git
cd pytestquick
```

Install the development environment:

```bash
uv sync
```

This project uses `uv` for dependency and environment management.

## Development Commands

The repository provides a `Makefile` for common development tasks.

Run the test suite:

```bash
make test
```

Run formatting:

```bash
make format
```

Run linting:

```bash
make lint
```

Run static type checking:

```bash
make typecheck
```

Run coverage validation:

```bash
make coverage
```

Before submitting a release-related change, run the complete validation suite:

```bash
make release-check
```

All checks should pass before a pull request is submitted.

## Project Scope

`pytestquick` focuses on pytest target discovery and command construction.

The package may determine an appropriate pytest target from inputs such as:

* Explicit test files
* Pytest node IDs
* Application or package directories
* Test classes
* Test methods
* The most recently modified test file

It then delegates test execution to pytest.

`pytestquick` should not become:

* A replacement for pytest
* A separate testing framework
* A custom test collector
* A test execution engine
* A general-purpose task runner
* A large project-management CLI

Features should make the normal pytest development loop faster while preserving pytest's existing behavior.

## Pytest Delegation

Pytest remains responsible for collecting and executing tests.

Whenever practical, `pytestquick` should construct an appropriate pytest invocation and allow pytest to perform the actual work.

Avoid duplicating functionality that pytest already provides unless doing so is necessary for target discovery or the `pytestquick` user experience.

Changes should not silently alter the semantics of the underlying pytest execution.

## Target Discovery

Target discovery is one of the package's most important behaviors.

Changes to discovery should be:

* Deterministic
* Predictable
* Easy to explain
* Well tested
* Conservative about ambiguous inputs

A convenience heuristic should not unexpectedly override an explicit user choice.

Explicit targets should take precedence over inferred targets.

When changing discovery behavior, include tests covering both the intended case and relevant competing or ambiguous cases.

## Command Construction

Generated pytest commands should remain transparent.

Users should be able to understand what `pytestquick` is executing.

Avoid hidden behavior that significantly changes pytest execution without making that behavior apparent to the user.

When adding pytest arguments or defaults, consider how they interact with:

* Project-level pytest configuration
* User-supplied pytest arguments
* Explicit targets
* Coverage behavior
* Different project layouts

## Coverage

Coverage is intentionally part of the normal `pytestquick` development workflow.

Changes to coverage behavior should remain predictable and should avoid assuming a single Python project layout.

When modifying automatic coverage scope selection, include tests for the relevant project and test layouts.

## Compatibility

Changes should preserve the Python versions supported by the project.

The authoritative compatibility information is maintained in `pyproject.toml` and the CI configuration.

Do not introduce dependencies on newer Python features without updating the declared compatibility policy and CI matrix.

## Dependencies

Keep runtime dependencies minimal.

New dependencies should only be introduced when they provide substantial value that cannot reasonably be achieved with Python's standard library or existing project dependencies.

Please discuss significant new runtime dependencies before submitting a pull request that introduces them.

## Code Quality

Contributions should:

* Follow the existing project structure and conventions
* Include type annotations where appropriate
* Pass Ruff formatting and linting
* Pass mypy type checking
* Preserve deterministic behavior
* Keep CLI behavior understandable
* Avoid unnecessary abstractions
* Keep the public API intentional and small

Prefer straightforward implementations over complex machinery for minor convenience features.

## Tests

Behavior changes should include tests.

Bug fixes should normally include a regression test demonstrating the problem being fixed.

New features should include tests covering expected behavior, edge cases, and relevant failure conditions.

The project maintains full statement and branch coverage. Contributions should preserve that standard.

Do not add meaningless tests solely to satisfy a coverage percentage. Tests should verify useful behavior and important branches.

## CLI Changes

Treat command-line interface changes as public API changes.

Existing commands, options, exit behavior, and commonly relied-upon output should not be changed casually.

When proposing a CLI change, consider:

* Backward compatibility
* Shell scripting
* Exit codes
* Existing pytest arguments
* Error messages
* Terminal output
* Whether the behavior remains intuitive without reading extensive documentation

Breaking CLI changes should be deliberate and clearly documented.

## Documentation

Changes to user-facing behavior should include corresponding documentation updates.

When adding or changing CLI functionality, update the README or other relevant documentation with concise examples.

Documentation should explain what `pytestquick` adds while making it clear when behavior comes directly from pytest.

## Pull Requests

Keep pull requests focused.

A pull request should ideally address one bug, feature, refactor, or documentation concern.

Before submitting a pull request:

1. Update your branch from `main`.
2. Run formatting.
3. Run linting.
4. Run type checking.
5. Run the complete test suite.
6. Confirm coverage remains at the required level.
7. Update documentation when user-facing behavior changes.
8. Review your diff for unrelated changes.

Please provide a clear pull request description explaining:

* What changed
* Why the change is needed
* Any important design decisions
* How the change was tested

Large architectural or CLI changes should generally be discussed before substantial implementation work begins.

## Backward Compatibility

Avoid unnecessary breaking changes.

If a contribution changes existing public behavior, explain the compatibility impact in the pull request.

Breaking changes should be deliberate, documented, and appropriate for the project's release strategy.

## Security Issues

Please do not report security vulnerabilities through public issues or pull requests.

Follow the instructions in `SECURITY.md` for responsible security reporting.

## Code of Conduct

Participation in this project is governed by the repository's `CODE_OF_CONDUCT.md`.

By participating, you are expected to follow those guidelines.

## License

By contributing to `pytestquick`, you agree that your contributions will be licensed under the same license as the project.

Thank you for helping improve `pytestquick`.
