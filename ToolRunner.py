import logging
import re
from functools import partial
from typing import Any, Literal, Optional, Union

import sublime
import sublime_plugin

from .lib import debug, manager, mapper, settings, util
from .lib.command import Command
from .lib.mapper import (
    InputSource,
    OutputTarget,
    ask_profile_and_run_command,
    ask_type_to_run,
    focus_output,
    run_profile,
    run_tool,
)

logging.basicConfig(level=logging.DEBUG)

_logger = logging.getLogger("ToolRunner")


class ToolRunner(sublime_plugin.WindowCommand):
    def run(
        self,
        tool: Union[str, None] = None,
        group: Union[str, None] = None,
        profile: Union[str, None] = None,
        default_profile: bool = False,
        input_source: InputSource = None,
        output: OutputTarget = None,
    ):
        return mapper.run(
            self, tool, group, profile, default_profile, input_source, output
        )


class ToolRunnerCancelCurrent(sublime_plugin.WindowCommand):
    def run(self):
        manager.cancel_command_for_view_id(self.window.active_view().id())


class ToolRunnerFocusOutput(sublime_plugin.WindowCommand):
    def run(self):
        focus_output(self)


class ToolRunnerFocusSource(sublime_plugin.WindowCommand):
    def run(self):
        mapper.focus_source(self)


class ToolRunnerSwitchDefaultProfile(sublime_plugin.WindowCommand):
    def run(self, profile_group=None):
        _logger.info("Switching command for profile group: %s", str(profile_group))
        if profile_group is None:
            self.ask_group_and_switch_profile()
        else:
            self.switch_profile(profile_group)

    def ask_group_and_switch_profile(self):
        self.groups = [group["name"] for group in settings.get_groups()]

        if len(self.groups) <= 0:
            sublime.error_message("There are no groups configured")
            return

        def on_ask_group_done(self, callback, selected_index):
            if selected_index < 0:
                return

            group_selected = self.groups[selected_index]

            if selected_index > -1:
                sublime.set_timeout(partial(callback, group_selected), 0)

        self.window.show_quick_panel(
            self.groups,
            partial(on_ask_group_done, self.switch_profile),
            0,
            0,
            None,
        )

    def switch_profile(self, profile_group):
        profiles = settings.get_profiles(profile_group)

        self.profile_group = profile_group
        self.profile_list = [profile["name"] for profile in profiles]
        self.window.show_quick_panel(self.profile_list, self.on_ask_profile, 0, 0, None)

    def on_ask_profile(self, selected_index):

        if selected_index > -1:
            selected_profile_name = self.profile_list[selected_index]
            current_settings = settings.get_setting("default_profiles", {})
            current_settings[self.profile_group] = selected_profile_name
            settings.set_setting("default_profiles", current_settings)

        self.profile_list = None
        self.groups = None


class ToolRunnerOpenSettings(sublime_plugin.WindowCommand):
    def run(self, scope=None):
        settings.open_settings(self.window, scope)


class ToolRunnerListener(sublime_plugin.EventListener):
    def on_query_context(
        self,
        view: sublime.View,
        key: str,
        operator: "sublime.QueryOperator",
        operand: Any,
        match_all: bool,
    ) -> Optional[bool]:
        if (
            key == "toolrunner.enable_default_tools_keymap"
            and operator == sublime.OP_EQUAL
        ):
            setting_value = settings.get_setting("enable_default_tools_keymap", False)
            _logger.info(
                "Setting: %s (%s), operand: %s (%s)",
                setting_value,
                type(setting_value),
                operand,
                type(operand),
            )
            return setting_value == operand

    def on_pre_close(self, view):
        mapper.on_pre_close_view(self, view)
        # manager.remove_source_view(view)
        # manager.remove_target_view(view)
        pass

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


def plugin_loaded():
    _logger.info("Plugin Loading")
    try:
        settings.on_loaded()
    except Exception as ex:
        _logger.exception("Error when loading settings")

    try:
        debug.forget_modules()
    except Exception as ex:
        _logger.exception("Error when unloading modules")

    _logger.info("Plugin Loaded")


def plugin_unloaded():
    try:
        settings.on_unloaded()
    except Exception as ex:
        _logger.exception("Error when unloading settings")

    try:
        debug.forget_modules()
    except Exception as ex:
        _logger.exception("Error when unloading modules")

    _logger.info("Plugin Unloaded")
