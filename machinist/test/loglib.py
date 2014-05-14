
__all__ = [
    "MessageType", "Logger",

    "LoggedAction", "LoggedMessage",

    "issuperset", "assertContainsFields", "validateLogging",
    ]

try:
    __import__("eliot")
except ImportError:
    MessageType = Logger = lambda *args, **kwargs: None

    LoggedAction = LoggedMessage = issuperset = assertContainsFields = None

    def validateLogging(validator):
        def passthrough(function):
            return function
        return passthrough
else:
    from eliot import MessageType, Logger
    from eliot.testing import (
        LoggedAction, LoggedMessage,
        issuperset, assertContainsFields, validateLogging,
    )
