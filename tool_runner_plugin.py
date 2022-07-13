import logging

from .src.tool_runner import debug
from .src.tool_runner.cmd.focus_output import ToolRunnerFocusOutput
from .src.tool_runner.cmd.focus_source import ToolRunnerFocusSource
from .src.tool_runner.cmd.listener import ToolRunnerListener
from .src.tool_runner.cmd.main import ToolRunner
from .src.tool_runner.cmd.open_settings import ToolRunnerOpenSettings
from .src.tool_runner.cmd.switch_default_profile import ToolRunnerSwitchDefaultProfile
from .src.tool_runner.cmd.unlink_output import ToolRunnerUnlinkOutput

logging.basicConfig(level=logging.INFO)

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


assert ToolRunnerFocusOutput
assert ToolRunnerFocusSource
assert ToolRunnerListener
assert ToolRunner
assert ToolRunnerOpenSettings
assert ToolRunnerSwitchDefaultProfile
assert ToolRunnerUnlinkOutput
