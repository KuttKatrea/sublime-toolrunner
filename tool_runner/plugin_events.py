import logging

from . import debug

_logger = logging.getLogger(f"{__package__}.{__name__}")


def plugin_loaded():
    try:
        debug.forget_modules()
    except Exception as ex:
        _logger.exception("Error when unloading modules", exc_info=ex)

    _logger.info("Plugin Loaded")


def plugin_unloaded():
    try:
        debug.forget_modules()
    except Exception as ex:
        _logger.exception("Error when unloading modules", exc_info=ex)

    _logger.info("Plugin Unloaded")
