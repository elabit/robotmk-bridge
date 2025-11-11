from unittest import TestCase

from rmkbridge.base_handler import BaseHandler
from ..helpers import get_config

class TestBaseHandlerErrors(TestCase):
    def test_parse_results_raises_an_error(self):
        '''It is intentional that parse_results() raises an error.

        It should never be directly invoked from BaseHandler, as it should
        always be specific to implementing plugin.
        '''
        with self.assertRaises(NotImplementedError):
            BaseHandler(get_config()['rmkbridge.junit']).parse_results('whatever')
