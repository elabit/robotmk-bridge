from unittest import TestCase
from unittest.mock import ANY, Mock, patch

from rmkbridge.tosca_ext import ToscaExtHandler
from rmkbridge.errors import ToscaExtHandlerException
from ..helpers import RESOURCES_PATH

TOSCA_XML = RESOURCES_PATH / 'tosca-ext-report.xml'

CONFIG = {
    'handler': 'ToscaExtHandler',
    'keyword': 'run_tosca_ext',
    'tags': ['rmkbridge-tosca-ext'],
}


class ToscaExtBasicTests(TestCase):

    def setUp(self):
        self.handler = ToscaExtHandler(CONFIG)
        self.suite = self.handler.parse_results(TOSCA_XML)
        self.subsuite = self.suite['suites'][0]
        self.first_test = self.subsuite['tests'][0]

    def test_suite_name_from_execution_list(self):
        self.assertEqual(self.suite['name'], '001_Suite')

    def test_suite_has_one_subsuite(self):
        self.assertEqual(len(self.suite['suites']), 1)

    def test_subsuite_name_from_nodepath_folder(self):
        self.assertEqual(self.subsuite['name'], 'Web Smoketests')

    def test_subsuite_has_thirteen_tests(self):
        self.assertEqual(len(self.subsuite['tests']), 13)

    def test_first_test_name(self):
        self.assertEqual(self.first_test['name'], '001.TC001_Route_01')

    def test_all_tests_pass(self):
        for test in self.subsuite['tests']:
            for kw in test['keywords']:
                self.assertTrue(kw['pass'], f"Expected pass for {test['name']}: {kw['name']}")

    def test_first_test_has_49_keywords(self):
        # TF001 has 49 ExecutionXTestStepLog entries in the sample XML
        self.assertEqual(len(self.first_test['keywords']), 49)

    def test_keywords_have_elapsed(self):
        kw = self.first_test['keywords'][0]
        self.assertIn('elapsed', kw)
        self.assertGreater(kw['elapsed'], 0)

    def test_container_logs_excluded_from_keywords(self):
        # 39 ContainerLog entries exist in the sample; none should appear as keywords
        total_kw_count = sum(
            len(test['keywords'])
            for test in self.subsuite['tests']
        )
        self.assertEqual(total_kw_count, 455)

    @patch('rmkbridge.utils.subprocess')
    def test_run_tosca_ext_invokes_subprocess(self, mock_subprocess):
        mock_subprocess.run.return_value = Mock(returncode=0)
        self.handler.run_tosca_ext('output.xml', 'tcshell --run ...')
        mock_subprocess.run.assert_called_once_with(
            'tcshell --run ...', capture_output=True, shell=True, env=ANY
        )

    @patch('rmkbridge.utils.subprocess')
    def test_run_tosca_ext_raises_on_nonzero_when_check_enabled(self, mock_subprocess):
        mock_subprocess.run.return_value = Mock(returncode=1)
        with self.assertRaises(ToscaExtHandlerException):
            self.handler.run_tosca_ext('output.xml', 'tcshell ...', check_return_code=True)

    @patch('rmkbridge.utils.subprocess')
    def test_run_tosca_ext_returns_result_file(self, mock_subprocess):
        mock_subprocess.run.return_value = Mock(returncode=0)
        result = self.handler.run_tosca_ext('output.xml', 'tcshell ...')
        self.assertEqual(result, 'output.xml')
