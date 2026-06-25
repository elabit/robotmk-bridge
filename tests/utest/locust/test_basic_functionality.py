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

    def test_threshold_defaults_to_zero(self):
        self.assertEqual(self.handler._failure_threshold(), 0)

    def test_threshold_read_from_config(self):
        config = {**CONFIG, 'failure_percentage': '10'}
        self.assertEqual(LocustHandler(config)._failure_threshold(), 10)

    def test_threshold_capped_at_100(self):
        config = {**CONFIG, 'failure_percentage': '150'}
        self.assertEqual(LocustHandler(config)._failure_threshold(), 100)

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

    @patch('rmkbridge.utils.subprocess')
    def test_run_locust_raises_on_nonzero_when_check_enabled(self, mock_subprocess):
        mock_subprocess.run.return_value = Mock(returncode=1)
        with self.assertRaises(LocustHandlerException):
            self.handler.run_locust('output.csv', 'locust ...', check_return_code=True)

    @patch('rmkbridge.utils.subprocess')
    def test_run_locust_returns_result_file(self, mock_subprocess):
        mock_subprocess.run.return_value = Mock(returncode=0)
        result = self.handler.run_locust('output.csv', 'locust ...')
        self.assertTrue('output.csv' in result)

# TEST
