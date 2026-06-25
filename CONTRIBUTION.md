# Contributing to Robotmk Bridge

Thank you for your interest in contributing! 

This guide explains how to set up the development environment and run the test suite.
If you want to **contribute** a new handler (e.g. for a new third-party test tool), see [HANDLER-DEVGUIDE.md](HANDLER-DEVGUIDE.md)


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

### Robot Framework version

`requirements.txt` pins `robotframework<7`, so the default local development environment uses **Robot Framework 6**.
RF7 compatibility is tested exclusively in CI via the matrix (see `.github/workflows/matrix-test-full.yml`), which installs RF6 first via `requirements.txt` and then overrides it with the specific matrix version:

```bash
pip install -r requirements.txt          # installs RF6 as default
pip install robotframework==7.x.x        # overrides to the matrix version
```

If you want to develop or debug against RF7 locally, override the version manually after the initial install:

```bash
pip install -r requirements.txt
pip install "robotframework>=7.0"
pip install -e .
```

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

---


## Generating Library Documentation

To regenerate the Robot Framework library docs under `docs/`:

```bash
invoke doc
```

---
## Submitting Changes

### Step 1 — Create a feature branch

Always branch off `main`:

```bash
git checkout main && git pull
git checkout -b feat/my-change   # or fix/my-change, docs/my-change, …
```

### Step 2 — Write Conventional Commits

This project uses [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) because the release automation reads your commit messages to determine the next version and generate the changelog automatically.

The format is:

```
<type>(<scope>): <short description>
```

| Type | When to use | Version bump |
|------|-------------|-------------|
| `feat` | New feature or behaviour | **minor** (`0.1.0 → 0.2.0`) |
| `fix` | Bug fix | **patch** (`0.1.0 → 0.1.1`) |
| `perf` | Performance improvement | patch |
| `deps` | Dependency update | patch |
| `docs` | Documentation only | none |
| `chore` | Maintenance, CI, tooling | none |
| `test` | Tests only | none |
| `feat!` or `BREAKING CHANGE` footer | Breaking API change | **major** (`0.1.0 → 1.0.0`) |

Examples:

```
fix(junit): correct XML escaping for special characters
feat(gatling): aggregate requests per scenario
docs(readme): add quickstart example
chore(ci): pin Python version in release matrix
```

### Step 3 — Make your changes and verify

Run the full test suite before pushing:

```bash
invoke test
```

Format your code:

```bash
black src/ tests/
```

### Step 4 — Push and open a Pull Request

```bash
git push -u origin feat/my-change
```

Then open a Pull Request on GitHub targeting `main`.  
Once the PR is reviewed and merged, your changes land on `main`.

---

## How Releases Work

This project uses [release-please](https://github.com/googleapis/release-please-action) to automate versioning and publishing. You never manually update version numbers or the changelog.

```
your feat/fix PR merged into main
          │
          ▼
release-please bot opens (or updates) a "chore: release X.Y.Z" PR
  ├── bumps version in src/rmkbridge/version.py
  ├── bumps version in setup.py
  ├── bumps .release-please-manifest.json
  └── updates CHANGELOG.md with your commits grouped by type
          │
 you review and merge the Release PR when ready to ship
          │
          ▼
release-please creates a Git tag + GitHub Release
          │
          ▼
CI runs tests (Python 3.12 × Robot Framework 6.1.1)
          │  all green
          ▼
package is published to PyPI automatically
```

**Key points:**

- release-please keeps exactly **one** open Release PR at a time. Every new merge into `main` updates that PR rather than creating a new one.
- You control *when* a release happens by deciding when to merge the Release PR. You can batch multiple features/fixes into a single release by merging them all before merging the Release PR.
- Never edit `src/rmkbridge/version.py`, `setup.py`, or `CHANGELOG.md` manually — release-please owns those files.

**Further reading:**

- [release-please manifest releaser docs](https://github.com/googleapis/release-please/blob/main/docs/manifest-releaser.md)
- [Managing releases with release-please](https://elixirschool.com/blog/managing-releases-with-release-please)
