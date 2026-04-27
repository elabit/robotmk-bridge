# Contributing to Robotmk Bridge

Thank you for your interest in contributing! This guide explains how to set up the development environment and run the test suite.

## Prerequisites

- **Python 3.10 or newer** — the project is tested against Python 3.10, 3.11, and 3.12
- **pip**
- **git**

## Fork and Clone

1. Navigate to [https://github.com/elabit/robotmk-bridge](https://github.com/elabit/robotmk-bridge) and click **Fork**.
2. Clone your fork locally:

```bash
git clone https://github.com/<your-username>/robotmk-bridge.git
cd robotmk-bridge
```

## Set Up the Virtual Environment

Create and activate a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
```

## Install Dependencies

Install all runtime and development dependencies, then install the package itself in editable mode:

```bash
pip install -r requirements.txt
pip install -e .
```

`requirements.txt` includes both the runtime dependencies (e.g. `robotframework`, `junitparser`, `PyYAML`, `pydantic`) and all development tools (e.g. `pytest`, `invoke`, `coverage`, `black`).

Installing with `-e .` (editable mode) means that changes you make in `src/rmkbridge/` take effect immediately without reinstalling.

## Task Runner — `invoke`

The project uses [`invoke`](https://www.pyinvoke.org/) as its task runner. All common development activities are wrapped as `invoke` tasks defined in `tasks.py`.

List all available tasks:

```bash
invoke --list
```

| Task | Description |
|------|-------------|
| `invoke install` | Clean build artefacts and reinstall dependencies |
| `invoke utest` | Run the unit test suite with `pytest` |
| `invoke atest` | Run the Robot Framework acceptance test suite |
| `invoke test` | Run unit tests followed by acceptance tests |
| `invoke coverage` | Run tests and generate an HTML coverage report |
| `invoke doc` | Generate the Robot Framework library documentation |
| `invoke build` | Build a distributable wheel |
| `invoke clean` | Remove build artefacts, dist, `.tox`, and HTML reports |

## Running the Tests

### Unit Tests

Unit tests live under `tests/utest/`. Run them with:

```bash
invoke utest
```

To limit execution to specific tests, pass `-t` / `--test` (can be repeated):

```bash
invoke utest --test test_junit --test test_zap
```

You can also run `pytest` directly; just make sure `src/` is on `PYTHONPATH`:

```bash
PYTHONPATH=src pytest tests/utest -q --disable-warnings
```

### Acceptance Tests

Acceptance tests are Robot Framework suites under `tests/atest/`. Run them with:

```bash
invoke atest
```

Pass extra Robot Framework command-line arguments via `--rf`:

```bash
invoke atest --rf "--loglevel DEBUG"
```

### Full Test Suite

```bash
invoke test
```

This runs `utest` first and then `atest`.

### Coverage Report

```bash
invoke coverage
```

An HTML report is written to `htmlcov/index.html`.

## Code Style

The project uses [Black](https://black.readthedocs.io/) for formatting (pinned to `black==25.11`). Format your changes before committing:

```bash
black src/ tests/
```

## Project Layout

```
src/rmkbridge/      # Package source code
tests/utest/        # pytest unit tests
tests/atest/        # Robot Framework acceptance tests
tests/resources/    # Shared test fixtures and dummy handlers
tasks.py            # invoke task definitions
requirements.txt    # Runtime + dev dependencies
setup.py            # Package metadata
```

## Writing a Custom Handler

If you want to contribute a new handler (e.g. for a new third-party test tool), see [DEVGUIDE.md](DEVGUIDE.md) for a step-by-step walkthrough, including:

1. Extending `rmkbridge.BaseHandler` and implementing `parse_results` and a trigger keyword.
2. Making your module discoverable via `PYTHONPATH` or as an installable package.
3. Registering the handler with `python -m rmkbridge --add-config path/to/handler_config.yml`.
4. Returning results conforming to the [handler result specification](handler_result_specification.md).

## Generating Library Documentation

To regenerate the Robot Framework library docs under `docs/`:

```bash
invoke doc
```

## Commit workflow

This project uses [release please](https://github.com/googleapis/release-please-action) to maintain the Changelog and Releases. 

Resources: 

- https://elixirschool.com/blog/managing-releases-with-release-please
- https://github.com/googleapis/release-please/blob/main/docs/manifest-releaser.md
- https://medium.com/@nicolaslelievre/automating-dbt-package-versioning-with-release-please-97ebe0ce9809

Notes: 

- Use feature branches
- Write commit messages which follow the [https://www.conventionalcommits.org/en/v1.0.0/]{Conventional Commit Standard}
  - `fix(bridge)`: correct xml escaping => patch
  - `feat(gatling)`: aggregate requests per scenario => minor
  - `chore(ci)`: speed up mkp packaging => major
- push to feature branch 
- On Github, create PR, merge to main
- RP creates Release PR => merge => Release is created
- Run the MKP workflow (currently not possible to run after the Release workflow) => MKPs are built and added to the release. 



## Submitting Changes

1. Create a feature branch from `main`:

```bash
git checkout -b feature/my-change
```

2. Make your changes, add tests, and ensure the full test suite passes:

```bash
invoke test
```

3. Push your branch and open a pull request against `elabit/robotmk-bridge:main`.
