import functools
import logging
import sys

from . import util

_logger = logging.getLogger(f"{__package__}.{__name__}")


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


def log_unused_args(*args, **kwargs):
    _logger.info("Unused parameters: %s, %s", args, kwargs)


def forget_modules():
    _logger.info("Deleting submodules")
    deletekeys = []
    for key in sys.modules:
        if key.startswith(__package__):
            deletekeys.append(key)

    for key in deletekeys:
        del sys.modules[key]
