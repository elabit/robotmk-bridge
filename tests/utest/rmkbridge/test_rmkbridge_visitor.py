from unittest import TestCase
from unittest.mock import Mock

from rmkbridge.rmkbridge import RobotmkBridgeVisitor
from rmkbridge import errors as rmkbridge_errors


class CustomUserException(Exception):
    pass


class TestRobotmkBridge(TestCase):
    def test_multiple_errors_are_reported(self):
        m = Mock()
        m.check_for_keyword.side_effect = [
            TypeError('different'),
            rmkbridge_errors.JUnitHandlerException('kinds of'),
            rmkbridge_errors.RobotmkBridgeException('exceptions'),
            CustomUserException('for fun and profit')
        ]
        oxy = RobotmkBridgeVisitor('fakedata')
        oxy._handlers = {
            'fake_handler': m,
            'another_fake': m,
            'third': m,
            'and fourth': m
        }

        with self.assertRaises(rmkbridge_errors.RobotmkBridgeException) as ex:
            oxy.visit_test(Mock())

        exception_message = str(ex.exception)
        for expected in ('different',
                         'kinds of',
                         'exceptions',
                         'for fun and profit'):
            self.assertIn(expected, exception_message)

    def test_single_exception_raised_directly(self):
        m = Mock()
        m.check_for_keyword.side_effect = [CustomUserException('single')]
        oxy = RobotmkBridgeVisitor('fakedata')
        oxy._handlers = {'fake_handler': m}

        with self.assertRaises(CustomUserException) as ex:
            oxy.visit_test(Mock())

        self.assertIn('single', str(ex.exception))
        self.assertEqual(oxy.data, 'fakedata')
