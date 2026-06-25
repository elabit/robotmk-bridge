
class RobotmkBridgeException(Exception):
    pass


class SubprocessException(Exception):
    pass




class ResultFileNotFoundException(Exception):
    pass


class ResultFileIsNotAFileException(Exception):
    pass


class MismatchArgumentException(Exception):
    pass


class InvalidConfigurationException(Exception):
    pass


class InvalidRobotmkBridgeResultException(Exception):
    pass

# HANDLER EXCEPTIONS

class GatlingHandlerException(Exception):
    pass

class JUnitHandlerException(Exception):
    pass

class ZAProxyHandlerException(Exception):
    pass

class LocustHandlerException(Exception):
    pass