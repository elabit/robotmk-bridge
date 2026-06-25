# Handler Developer Guide

## What is a handler?

A handler is a Python module inside `src/rmkbridge/` that teaches rmkbridge how to run a third-party test tool and interpret its results. Every handler does exactly two things:

1. **Trigger keyword** (`run_<handler_name>`) — invoked to launch the external tool directly from Robot Framework and return the path to its output. 
2. **Result parser** (`parse_results`) — called automatically by rmkbridge to convert that output into a structure Robot Framework can display.

Note: For the [Robotmk Bridge Plugin](https://github.com/elabit/robotmk-bridge-plugin), the result parser is the important part. The trigger keyword is only used when you want to run the external tool directly from Robot Framework.

There are three built-in handlers: 

- [junit.py](src/rmkbridge/junit.py)
- [gatling.py](src/rmkbridge/gatling.py), and 
- [zap.py](src/rmkbridge/zap.py) 

## The result contract

`parse_results` must return a Python dict conforming to the [handler result specification](handler_result_specification.md). The required shape is:

```python
{
    'name': 'My Suite',          # top-level suite name
    'tags': ['my-tag'],          # optional; handler tags are usually set here
    'tests': [
        {
            'name': 'My Test',   # test case name
            'keywords': [
                {
                    'name': 'some step',   # keyword name
                    'pass': True,          # bool — the only real pass/fail signal
                    'messages': [],        # optional log lines shown in RF output
                }
            ]
        }
    ]
}
```

| Field      | Suite | Test case | Keyword |
|------------|-------|-----------|---------|
| `name`     | x     | x         | x       |
| `pass`     |       |           | x       |
| `keywords` |       | x         | (x)     |
| `tags`     | (x)   | (x)       | (x)     |
| `messages` |       |           | (x)     |
| `elapsed`  |       |           | (x)     |
| `setup`    | (x)   | (x)       |         |
| `teardown` | (x)   | (x)       | (x)     |
| `suites`   | (x)   |           |         |
| `tests`    | (x)   |           |         |
| `metadata` | (x)   |           |         |

`x` = required · `(x)` = optional

---

## Example: writing a Locust handler

We will write now a handler for [Locust](https://locust.io/), an open-source load testing tool.  
In Locust you describe user behaviour in Python, point it at a host, and it hammers it with simulated traffic.  
The results land in a CSV file that looks like this:

```
"Type","Name","Request Count","Failure Count",...
"GET","/",10,0,...
"POST","/",5,5,...
"GET","/item",24,0,...
"None","Aggregated",39,5,...
```

Each row is one endpoint. `Failure Count` (4th column) is the one we care about.

We will build the handler in three stages, adding a feature and a round of tests at each step.

### Before you start

If you haven't already, follow [CONTRIBUTION.md](CONTRIBUTION.md) to fork and clone the repo, then set up your environment:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Installing with `-e .` means changes in `src/rmkbridge/` take effect immediately — no reinstalling needed.

---

## Stage 1 — the basic functionality

### 1. Add an exception class

Open [src/rmkbridge/errors.py](src/rmkbridge/errors.py) and add one line alongside the other handler exceptions:

```python
class LocustHandlerException(Exception):
    pass
```

Raising your own exception type (instead of a bare `Exception`) makes stack traces self-documenting.

### 2. Create the handler module

Create `src/rmkbridge/locust.py`:

```python
import csv

from robot.api import logger

from .base_handler import BaseHandler
from .errors import LocustHandlerException, SubprocessException
from .utils import run_command_line, validate_path


class LocustHandler(BaseHandler):

    def run_locust(self, result_file, command, check_return_code=False, **env):
        '''Run the Locust load testing tool via ``command``.

        ``result_file`` is the path rmkbridge will read after Locust finishes.
        Craft your ``command`` to write its stats CSV to exactly that path
        (use Locust's ``--csv`` flag and derive the ``_stats.csv`` filename).

        ``command`` is a shell string executed in a subprocess.

        ``check_return_code`` — set to ``True`` while debugging to treat a
        non-zero exit code as a failure. Leave it off for normal use: Locust
        exits non-zero when requests fail, which would swallow real results.

        Extra keyword arguments are forwarded as environment variables to the
        subprocess.
        '''
        try:
            output = run_command_line(command, check_return_code, **env)
        except SubprocessException as e:
            raise LocustHandlerException(e)
        logger.info(output)
        logger.info(f'Result file: {result_file}')
        return result_file

    def parse_results(self, result_file):
        return self._transform_tests(validate_path(result_file).resolve())

    def _transform_tests(self, file):
        test_cases = []
        with open(file, newline='') as csvfile:
            for row in csv.DictReader(csvfile):
                if row['Type'] == 'None':
                    continue
                failure_count = int(row['Failure Count'])
                test_cases.append({
                    'name': f"{row['Type']} requests to {row['Name']}",
                    'keywords': [{
                        'name': f"{row['Type']} {row['Name']}",
                        'pass': failure_count == 0,
                        'messages': [f'{k}: {v}' for k, v in row.items()],
                    }],
                })
        return {
            'name': 'Locust Scenario',
            'tags': self._tags,
            'tests': test_cases,
        }
```

💡 Implementation details:

1. **Imports**: We import necessary modules, including `csv` for reading CSV files
2. **run_locust**: This method runs the Locust command in a subprocess and returns the path to the result file. It handles exceptions and logs output.
3. **parse_results**: This method reads the result file and transforms it into the required structure using `_transform_tests`.
4. **_transform_tests**: This method reads the CSV file, skips the aggregated row, and creates a list of test cases. Each test case contains the name, keywords, pass/fail status based on the failure count, and messages with details from the CSV


### 3. Register the handler

Add an entry to [src/rmkbridge/config.yml](src/rmkbridge/config.yml), where all handlers are registered, including optional tags and other configuration:

```yaml
rmkbridge.locust:
  handler: LocustHandler
  keyword: run_locust
  tags:
    - rmkbridge-locust
```

The key `rmkbridge.locust` must exactly match the importable module path (`import rmkbridge.locust`).

### 4. Write unit tests

With unit tests we can verify the handler works without actually running Locust. The tests will call `parse_results` on a sample CSV and check the output structure.

Create the test package `locust` under `tests/utest/` with two empty files:

```
tests/utest/locust/
    __init__.py
    test_basic_functionality.py
```

And add a sample CSV to `tests/resources/locust-example-stats.csv`:

```
"Type","Name","Request Count","Failure Count","Median Response Time","Average Response Time","Min Response Time","Max Response Time","Average Content Size","Requests/s","Failures/s","50%","66%","75%","80%","90%","95%","98%","99%","99.9%","99.99%","99.999%","100%"
"GET","/",10,0,72,75,66,89,2175,0.26,0.00,73,75,86,87,89,89,89,89,89,89,89,89
"POST","/",5,5,300,323,288,402,157,0.13,0.13,300,330,330,400,400,400,400,400,400,400,400,400
"GET","/item",24,0,80,79,67,100,2175,0.63,0.00,81,85,86,86,89,92,100,100,100,100,100,100
"None","Aggregated",39,5,81,109,66,402,1916,1.03,0.13,81,86,87,89,300,330,400,400,400,400,400,400
```

Now fill `tests/utest/locust/test_basic_functionality.py`:

```python
from unittest import TestCase
from unittest.mock import ANY, Mock, patch

from rmkbridge.locust import LocustHandler
from rmkbridge.errors import LocustHandlerException
from ..helpers import RESOURCES_PATH

LOCUST_CSV = RESOURCES_PATH / 'locust-example-stats.csv'

CONFIG = {
    'handler': 'LocustHandler',
    'keyword': 'run_locust',
    'tags': ['rmkbridge-locust'],
}


class LocustBasicTests(TestCase):

    def setUp(self):
        self.handler = LocustHandler(CONFIG)
        self.suite = self.handler.parse_results(LOCUST_CSV)

    def test_suite_has_four_cases(self):
        self.assertEqual(len(self.suite['tests']), 3)

    def test_get_request_passes_when_no_failures(self):
        # First row: GET / — zero failures
        self.assertTrue(self.suite['tests'][0]['keywords'][0]['pass'])

    def test_post_request_fails_when_failures_exist(self):
        # Second row: POST / — 5 failures
        self.assertFalse(self.suite['tests'][1]['keywords'][0]['pass'])

    @patch('rmkbridge.utils.subprocess')
    def test_run_locust_invokes_subprocess(self, mock_subprocess):
        mock_subprocess.run.return_value = Mock(returncode=0)
        self.handler.run_locust('output.csv', 'locust --headless ...')
        mock_subprocess.run.assert_called_once_with(
            'locust --headless ...', capture_output=True, shell=True, env=ANY
        )

    @patch('rmkbridge.utils.subprocess')
    def test_run_locust_raises_on_nonzero_when_check_enabled(self, mock_subprocess):
        mock_subprocess.run.return_value = Mock(returncode=1)
        with self.assertRaises(LocustHandlerException):
            self.handler.run_locust('output.csv', 'locust ...', check_return_code=True)

    @patch('rmkbridge.utils.subprocess')
    def test_run_locust_returns_result_file(self, mock_subprocess):
        mock_subprocess.run.return_value = Mock(returncode=0)
        result = self.handler.run_locust('output.csv', 'locust ...')
        self.assertEqual(result, 'output.csv')
```

💡 Implementation details:

1. **Setup**: We create a `LocustHandler` instance and parse the sample CSV file in the `setUp` method, so it's available for all tests.
2. ** Test Cases**: We define several test methods to verify the functionality of the handler:
   - `test_suite_has_four_cases`: Checks that the suite has three test cases (excluding the aggregated row).
   - `test_get_request_passes_when_no_failures`: Verifies that a GET request with zero failures passes.
   - `test_post_request_fails_when_failures_exist`: Verifies that a POST request with failures fails.
   - `test_run_locust_invokes_subprocess`: Mocks the subprocess call to ensure that `run_locust` invokes it correctly.
   - `test_run_locust_raises_on_nonzero_when_check_enabled`: Ensures that `run_locust` raises an exception when the subprocess returns a non-zero exit code and `check_return_code` is enabled.
   - `test_run_locust_returns_result_file`: Confirms that `run_locust` returns the expected result file path.

Run the suite from the project root:

```bash
pytest tests/utest/locust
```

All six tests should pass.

Bonus Tipp: IN VS Code, the test functions show little "play" buttons in the gutter. 

- Click one to run just that test, or click the "play" button at the top of the file to run all tests in that file.
- Hold the "Alt" key while clicking to run the test in debug mode, which lets you set breakpoints and inspect variables. **Very useful!**

---

## Stage 2 — configurable failure threshold

Failing the whole test when any single request fails is often too strict for load testing (when hundreds of requests are involved).  
=> A `failure_percentage` would be fine to define the maximum tolerable share of failed requests per endpoint!

### Update the handler

In `src/rmkbridge/locust.py`, replace `_transform_tests` and add `_failure_threshold`:

```python
    def _transform_tests(self, file):
        threshold = self._failure_threshold()
        test_cases = []
        with open(file, newline='') as csvfile:
            for row in csv.DictReader(csvfile):
                if row['Type'] == 'None':
                    continue
                failure_count = int(row['Failure Count'])
                request_count = int(row['Request Count'])
                actual_pct = (failure_count / request_count) * 100 if request_count > 0 else 0
                test_cases.append({
                    'name': f"{row['Type']} requests to {row['Name']}",
                    'keywords': [{
                        'name': f"{row['Type']} {row['Name']}",
                        'pass': actual_pct <= threshold,
                        'messages': [f'{k}: {v}' for k, v in row.items()],
                    }],
                })
        return {
            'name': 'Locust Scenario',
            'tags': self._tags,
            'tests': test_cases,
        }
    
    def _failure_threshold(self):
        pct = int(self._config.get('failure_percentage', 0))
        if pct > 100:
            logger.info('failure_percentage capped at 100')
            return 100
        return pct    
```

💡 Implementation details:

1. New function **_failure_threshold**: This method retrieves the `failure_percentage` from the handler's configuration, defaults to 0 if not set, and caps it at 100. It logs a message if the value exceeds 100.
2. Updated **_transform_tests**: The method now calculates the actual failure percentage for each request type and compares it against the threshold. The test case passes if the actual percentage is less than or equal to the threshold.

### Register the default failure threshold

Add the default `failure_percentage` in `src/rmkbridge/config.yml`:

```yaml
rmkbridge.locust:
  handler: LocustHandler
  keyword: run_locust
  tags:
    - rmkbridge-locust
  failure_percentage: 20
```

### Add tests

Add the following tests to `tests/utest/locust/test_basic_functionality.py`:

```python
    def test_threshold_defaults_to_zero(self):
        self.assertEqual(self.handler._failure_threshold(), 0)

    def test_threshold_read_from_config(self):
        config = {**CONFIG, 'failure_percentage': '10'}
        self.assertEqual(LocustHandler(config)._failure_threshold(), 10)

    def test_threshold_capped_at_100(self):
        config = {**CONFIG, 'failure_percentage': '150'}
        self.assertEqual(LocustHandler(config)._failure_threshold(), 100)
```

💡 Implementation details:

1. **test_threshold_defaults_to_zero**: Verifies that the default failure threshold is 0 when not specified in the configuration.
2. **test_threshold_read_from_config**: Checks that the failure threshold is correctly read from the configuration.
3. **test_threshold_capped_at_100**: Ensures that the failure threshold is capped at 100 if a higher value is provided in the configuration.


---

## Stage 3 — per-test override

A global threshold in `config.yml` is convenient, but load testing different parts of a system often calls for different tolerances. You can let the Robot Framework caller pass `failure_percentage` directly to `run_locust`, overriding the config value for that specific test case.

### Update `locust.py`

```python
    def run_locust(self, result_file, command, check_return_code=False, failure_percentage=None, **env):
        try:
            output = run_command_line(command, check_return_code, **env)
        except SubprocessException as e:
            raise LocustHandlerException(e)
        logger.info(output)
        logger.info(f'Result file: {result_file}')
        return result_file, failure_percentage

    def parse_results(self, result_file, failure_percentage=None):
        effective_threshold = failure_percentage if failure_percentage is not None else self._failure_threshold()
        threshold = min(effective_threshold, 100)
        return self._transform_tests(validate_path(result_file).resolve(), threshold)

    def _transform_tests(self, file, threshold):
        test_cases = []
        with open(file, newline='') as csvfile:
            for row in csv.DictReader(csvfile):
                if row['Type'] == 'None':
                    continue
                failure_count = int(row['Failure Count'])
                request_count = int(row['Request Count'])
                actual_pct = (failure_count / request_count) * 100 if request_count > 0 else 0
                test_cases.append({
                    'name': f"{row['Type']} requests to {row['Name']}",
                    'keywords': [{
                        'name': f"{row['Type']} {row['Name']}",
                        'pass': actual_pct <= threshold,
                        'messages': [f'{k}: {v}' for k, v in row.items()],
                    }],
                })
        return {
            'name': 'Locust Scenario',
            'tags': self._tags,
            'tests': test_cases,
        }
```

💡 Implementation details:

1. **run_locust**: Now returns a tuple `(result_file, failure_percentage)` to allow passing the threshold to `parse_results`.
2. **parse_results**: Accepts an optional `failure_percentage` argument. If provided, it overrides the configuration value for that specific test case. The effective threshold is capped at 100.
3. **_transform_tests**: Now takes the threshold as a parameter, allowing it to be set per test case.

### Add unit tests the failure percentage override

```python
    def test_parse_results_uses_parameter_over_config(self):
        # POST / has 100% failure rate; threshold=100 (param) overrides config 70 → should pass
        config = {**CONFIG, 'failure_percentage': '70'}
        handler = LocustHandler(config)
        suite = handler.parse_results(str(LOCUST_CSV), 100)
        post_test = suite['tests'][1]['keywords'][0]
        self.assertTrue(post_test['pass'])

    def test_parse_results_falls_back_to_config(self):
        # POST / has 100% failure rate; threshold=100 from config (param=None) → should pass
        config = {**CONFIG, 'failure_percentage': '100'}
        handler = LocustHandler(config)
        suite = handler.parse_results(str(LOCUST_CSV), None)
        post_test = suite['tests'][1]['keywords'][0]
        self.assertTrue(post_test['pass'])
```

💡 Implementation details:

1. **test_parse_results_uses_parameter_over_config**: Verifies that when a `failure_percentage` is provided as a parameter, it overrides the configuration value for that specific test case.
2. **test_parse_results_falls_back_to_config**: Ensures that when no `failure_percentage` parameter is provided, the handler falls back to using the configuration value.



---

## Checklist before opening a PR

- [ ] Handler at `src/rmkbridge/locust.py` — relative imports, subclasses `BaseHandler`
- [ ] `LocustHandlerException` added to `src/rmkbridge/errors.py`
- [ ] Entry added to `src/rmkbridge/config.yml` with key `rmkbridge.locust`
- [ ] Sample result file in `tests/resources/`
- [ ] Unit tests in `tests/utest/locust/` covering parse logic, subprocess mocking, and threshold behaviour
- [ ] `pytest tests/utest/` passes without errors or warnings
- [ ] `parse_results` output validated against [handler_result_specification.md](handler_result_specification.md)
- [ ] Add yout handler to the list of supported handlers in `README.md`

Once all boxes are ticked, push your branch and open a pull request. See [CONTRIBUTION.md](CONTRIBUTION.md) for the Git workflow.
