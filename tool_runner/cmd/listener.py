import logging
from typing import Any, Optional

import sublime
import sublime_plugin

from .. import mapper, settings

_logger = logging.getLogger(f"{__package__}.{__name__}")


class ToolRunnerListener(sublime_plugin.EventListener):
    def on_query_context(
        self,
        view: sublime.View,
        key: str,
        operator: "sublime.QueryOperator",
        operand: Any,
        match_all: bool,
    ) -> Optional[bool]:
        if not key.startswith("tool_runner."):
            return None

        settings_key = key[len("tool_runner.") :]
        setting_value = settings.get_setting(settings_key, None)

        _logger.info(
            "Checking setting: %s > %s %s %s (%s)",
            settings_key,
            setting_value,
            operator,
            operand,
            type(setting_value),
        )

        if operator == sublime.OP_EQUAL:
            return setting_value == operand

        if operator == sublime.OP_NOT_EQUAL:
            return setting_value != operand

        return None

    def on_pre_close(self, view):
        target_output_name = view.settings().get(
            mapper.TR_SETTING_TARGET_OUTPUT_ID, None
        )
        if target_output_name:
            mapper.close_panel(view.window(), target_output_name)

    def on_post_save(self, view):
        # _logger.info("Saved view: %s", view.id())
        # source_view = manager.get_source_view_for_target_view(view)
        # if source_view is None:
        # _logger.info("The view %s is not an output view", view.id())
        #    return

        # manager.remove_target_view(view)
        # view.set_scratch(False)
        # view.set_read_only(False)
        pass
