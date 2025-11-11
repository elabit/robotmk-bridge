''' IMPORTANT

RobotmkBridgeKeywordDict is defined like this since key `pass` is reserved
word in Python, and thus raises SyntaxError if defined like a class.
However, in the functional style you cannot refer to the TypedDict itself
recursively, like you can with with class style. Oh bother.

See more:
 - https://docs.python.org/3/library/typing.html?highlight=typeddict#typing.TypedDict
 - https://stackoverflow.com/a/72460065
'''

import functools

from typing import List, Dict
# TODO FIXME: Python 3.10 requires these to be imported from here
# Python 3.10 EOL is in 2026
from typing_extensions import TypedDict, Required

from pydantic import TypeAdapter, ValidationError

from .errors import InvalidRobotmkBridgeResultException

_KeywordBase = TypedDict('_KeywordBase', {'pass': Required[bool], 'name': Required[str]})
# define required fields in this one above
class RobotmkBridgeKeywordDict(_KeywordBase, total=False):
    elapsed:  float  # milliseconds
    tags:     List[str]
    messages: List[str]
    teardown: 'RobotmkBridgeKeywordDict'  # in RF, keywords do not have setup kw; just put it as first kw in `keywords`
    keywords: List['RobotmkBridgeKeywordDict']


class RobotmkBridgeTestCaseDict(TypedDict, total=False):
    name:     Required[str]
    keywords: Required[List[RobotmkBridgeKeywordDict]]
    tags:     List[str]
    setup:    RobotmkBridgeKeywordDict
    teardown: RobotmkBridgeKeywordDict


class RobotmkBridgeSuiteDict(TypedDict, total=False):
    name:     Required[str]
    tags:     List[str]
    setup:    RobotmkBridgeKeywordDict
    teardown: RobotmkBridgeKeywordDict
    metadata: Dict[str, str]
    suites:   List['RobotmkBridgeSuiteDict']
    tests:    List[RobotmkBridgeTestCaseDict]


def _change_validationerror_to_rmkbridge_exception(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            raise InvalidRobotmkBridgeResultException(e)
    return wrapper

@_change_validationerror_to_rmkbridge_exception
def validate_rmkbridge_suite(result_dict):
    return TypeAdapter(RobotmkBridgeSuiteDict).validate_python(result_dict)

@_change_validationerror_to_rmkbridge_exception
def validate_rmkbridge_test_case(test_case_dict):
    return TypeAdapter(RobotmkBridgeTestCaseDict).validate_python(test_case_dict)

@_change_validationerror_to_rmkbridge_exception
def validate_rmkbridge_keyword(keyword_dict):
    return TypeAdapter(RobotmkBridgeKeywordDict).validate_python(keyword_dict)
