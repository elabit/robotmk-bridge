from unittest import TestCase
from rmkbridge.rmkbridge import RobotmkBridgeCore


class TestRobotmkBridgeInitialization(TestCase):
    def test_rmkbridge_core_initializes_without_loading_config(self):
        '''
        RobotmkBridgeCore and all it's subclasses lazy-load the configuration and,
        consequently, the handlers. This test makes sure that is not
        accidentally changed at some point
        '''
        core = RobotmkBridgeCore()
        self.assertEqual(core._config, None)
        self.assertEqual(core._handlers, None)

