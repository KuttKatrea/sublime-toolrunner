import functools
import logging
import sys
from typing import Callable, TypeVar, cast

from . import util

_logger = logging.getLogger(f"{__package__}.{__name__}")

T = TypeVar("T", bound=Callable)


def notify_on_error(error_msg: str = "Unhandled error"):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                fn(*args, **kwargs)
            except Exception as ex:
                _logger.exception(error_msg, exc_info=ex)
                util.notify(str(ex))

        return wrapper

    return decorator


def forget_modules():
    _logger.info("Deleting submodules")
    deletekeys = []
    for key in sys.modules:
        if key.startswith(__package__):
            deletekeys.append(key)

    for key in deletekeys:
        del sys.modules[key]
