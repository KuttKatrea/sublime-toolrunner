import logging
import sys

_logger = logging.getLogger("ToolRunner:Debug")


def forget_modules():
    _logger.info("Deleting submodules")
    deletekeys = []
    for key in sys.modules:
        if key.startswith(__package__):
            deletekeys.append(key)

    for key in deletekeys:
        del sys.modules[key]
