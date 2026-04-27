# GitHub Copilot Instructions — Robotmk Bridge

## Project Overview

**Robotmk Bridge** (`robotframework-robotmk-bridge`) is a Python package, Robot Framework library, and CLI tool that converts third-party test tool results into Robot Framework XML output so they can be monitored by [Checkmk](https://checkmk.com) via [Robotmk](https://robotmk.org).

- PyPI name: `robotframework-robotmk-bridge`
- Package import name: `rmkbridge`
- Version file: `src/rmkbridge/version.py`
- Python ≥ 3.10 required; tested against 3.10, 3.11, 3.12
- Robot Framework 6.x supported (RF 7+ support is planned; `robotframework<7.0.0,>=6.0.0`)

## Repository Layout

```
src/rmkbridge/          # All package source code
tests/utest/            # pytest unit tests (mirroring src structure)
tests/atest/            # Robot Framework acceptance tests
tests/resources/        # Shared XML fixtures, dummy handlers
tasks.py                # invoke task runner
requirements.txt        # Runtime + dev dependencies
setup.py                # Package metadata / install config
.github/workflows/      # CI: matrix-test-full.yml, release.yml
handler_result_specification.md  # JSON schema for handler return values
DEVGUIDE.md             # Step-by-step guide for writing custom handlers
```

Source code lives exclusively in `src/rmkbridge/`. There is a parallel `build/` mirror that is generated output — never edit files there.

## Architecture & Key Concepts

### Two Usage Modes

1. **Library + Listener mode** — Import `rmkbridge.RobotmkBridgeLibrary` in a `.robot` file and run with `--listener rmkbridge.listener`. The listener post-processes the output XML, injecting third-party results.
2. **CLI mode** — `python -m rmkbridge` converts result files directly without Robot Framework.

### Handler Pattern

Every supported tool is represented by a **Handler** class:

| File | Class | Trigger keyword | Tag |
|------|-------|----------------|-----|
| `src/rmkbridge/junit.py` | `JUnitHandler` | `run_junit` | `rmkbridge-junit` |
| `src/rmkbridge/gatling.py` | `GatlingHandler` | `run_gatling` | `rmkbridge-gatling` |
| `src/rmkbridge/zap.py` | `ZAProxyHandler` | `run_zap` | `rmkbridge-zap` |

All handlers extend `rmkbridge.BaseHandler` (`src/rmkbridge/base_handler.py`) and must implement:

- A **trigger keyword** method (e.g. `run_junit(self, result_file, command, ...)`): runs the external tool, returns the result file path.
- `parse_results(self, result_file)`: reads the result file and returns a `RobotmkBridgeSuiteDict`.

### Handler Registration (config.yml)

Handlers are registered in `src/rmkbridge/config.yml`. The dict key must be the importable module name:

```yaml
rmkbridge.junit:
  handler: JUnitHandler
  keyword: run_junit
  tags:
    - rmkbridge-junit
rmkbridge.zap:
  handler: ZAProxyHandler
  keyword: run_zap
  tags: rmkbridge-zap
  accepted_risk_level: 2
  required_confidence_level: 1
```

External/custom handlers append to this config with:

```bash
python -m rmkbridge --add-config path/to/handler_config.yml
python -m rmkbridge --reset-config   # restore to shipped defaults
```

### Handler Result Schema (`RobotmkBridgeSuiteDict`)

Defined with `TypedDict` + `pydantic` validation in `src/rmkbridge/rmkbridge_handler_result.py`. The top-level return value of `parse_results` must conform to:

```
RobotmkBridgeSuiteDict
  name (required str)
  tags, setup, teardown, metadata, suites, tests (optional)
  suites: List[RobotmkBridgeSuiteDict]    # recursive
  tests:  List[RobotmkBridgeTestCaseDict]
    name (required str)
    keywords (required List[RobotmkBridgeKeywordDict])
      pass (required bool)   # NB: 'pass' is a Python keyword — use TypedDict functional form
      name (required str)
      elapsed, tags, messages, teardown, keywords (optional)
```

Regenerate the published JSON schema with `invoke update_rmkbridge_schema`.

### Core Classes

- `RobotmkBridgeCore` — shared base; lazy-loads config and handlers.
- `RobotmkBridgeLibrary` — Robot Framework library; exposes handler trigger keywords to `.robot` files.
- `RobotmkBridgeListener` / `listener` — RF listener; hooks `end_suite` to inject converted results. Aliased as `rmkbridge.listener`.
- `BaseHandler` — abstract base for all handlers; handles keyword wrapping into setup/teardown, argument validation, tag injection.

### Error Hierarchy (`src/rmkbridge/errors.py`)

Each handler has its own `<Tool>HandlerException`. Shared exceptions:

- `RobotmkBridgeException`
- `InvalidConfigurationException`
- `ResultFileNotFoundException` / `ResultFileIsNotAFileException`
- `SubprocessException` — raised by `run_command_line` utility
- `MismatchArgumentException`
- `InvalidRobotmkBridgeResultException`

## Development Workflow

### Environment Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### Task Runner (invoke)

```bash
invoke utest          # pytest unit tests
invoke atest          # Robot Framework acceptance tests
invoke test           # both
invoke coverage       # pytest + HTML coverage report (htmlcov/)
invoke doc            # regenerate docs/ with robot.libdoc
invoke build          # build wheel
invoke clean          # remove build artefacts
```

### Running Tests Manually

```bash
# Unit tests
PYTHONPATH=src pytest tests/utest -q --disable-warnings

# Acceptance tests (invoke handles PYTHONPATH + config setup automatically)
invoke atest
```

Acceptance tests require `PYTHONPATH` to include both `src/` and `tests/resources/my_dummy_handlers/`.

### Code Style

- Formatter: **Black** (pinned `black==25.11`)
- Run: `black src/ tests/`

## Writing a New Handler

1. Create `src/rmkbridge/<tool>.py`; subclass `BaseHandler`.
2. Implement `run_<tool>(self, result_file, command, ...)` and `parse_results(self, result_file)`.
3. Add an entry to `src/rmkbridge/config.yml`.
4. Add unit tests under `tests/utest/<tool>/`.
5. Return a valid `RobotmkBridgeSuiteDict` from `parse_results`.
6. Raise `<Tool>HandlerException` (add it to `errors.py`) for tool-specific failures.
7. Optionally expose extra CLI flags by overriding `cli()` in the handler.

See `DEVGUIDE.md` for a full worked example (Locust handler).

## CI / Release

- CI matrix tests Python 3.10/3.11/3.12 × Robot Framework 3.2/4.1/5.0/6.1 on Linux and Windows.
- Releases are managed by [release-please](https://github.com/googleapis/release-please) (`release-please-config.json`).
- The version string lives only in `src/rmkbridge/version.py` and is tagged with `# x-release-please-version`.

## Conventions

- **Never edit files under `build/`** — they are generated copies.
- Config YAML key = importable module path (e.g. `rmkbridge.junit`).
- The `pass` field in `RobotmkBridgeKeywordDict` must be set using the functional `TypedDict` form because `pass` is a Python keyword.
- `PYTHONPATH` must include `src/` for all local runs — the package uses `src/`-layout.
- Dummy handlers used in tests live in `tests/resources/my_dummy_handlers/` and follow the same handler contract as production handlers.
