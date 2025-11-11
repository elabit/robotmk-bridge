from unittest import TestCase
from unittest.mock import MagicMock

from rmkbridge.base_handler import BaseHandler
from ..helpers import get_config


class TestSetSuiteTags(TestCase):
    def setUp(self):
        self.object = BaseHandler(get_config()['rmkbridge.junit'])

        self.suite = MagicMock()
        self.suite.set_tags = MagicMock()
        self.tags = (MagicMock(), MagicMock())

    def test_tags_are_set(self):
        self.object._set_suite_tags(self.suite, *self.tags)
        self.suite.set_tags.assert_called_once_with(self.tags)
