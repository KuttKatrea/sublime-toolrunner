import logging
from functools import partial
from typing import Any, Optional, Union

import sublime
import sublime_plugin

from .lib import commands, debug, manager, mapper, settings, util

logging.basicConfig(level=logging.DEBUG)

_logger = logging.getLogger("ToolRunner")


class ToolRunner(sublime_plugin.WindowCommand):
    def run(
        self,
        tool: Union[str, None] = None,
        group: Union[str, None] = None,
        profile: Union[str, None] = None,
        default_profile: bool = False,
        input_source: Optional[str] = None,
        output: Optional[dict] = None,
        params: Optional[dict] = None,
    ):
        try:
            commands.run(
                self,
                tool,
                group,
                profile,
                default_profile,
                input_source,
                output,
                params,
            )
        except Exception as ex:
            _logger.exception("Error running", exc_info=ex)
            util.notify(str(ex))


class ToolRunnerCancelCurrent(sublime_plugin.WindowCommand):
    def run(self):
        manager.cancel_command_for_view_id(self.window.active_view().id())


class ToolRunnerFocusOutput(sublime_plugin.WindowCommand):
    def run(self):
        commands.focus_output(self)


class ToolRunnerFocusSource(sublime_plugin.WindowCommand):
    def run(self):
        commands.focus_source(self)


class ToolRunnerSwitchDefaultProfile(sublime_plugin.WindowCommand):
    def __init__(self, *args, **kwargs):
        super(ToolRunnerSwitchDefaultProfile, self).__init__(*args, **kwargs)

        self.groups = []

        self.group_selected = None
        self.selected_profile_name = None

        self.profile_list = []

    def run(self, profile_group=None, profile=None):
        _logger.info("Switching command for profile group: %s", str(profile_group))
        if profile_group is None:
            self.ask_group_and_switch_profile()
            return

        self.group_selected = profile_group

        if profile is None:
            self.switch_profile()
            return

        self.selected_profile_name = profile

        self.set_group_profile()

    def ask_group_and_switch_profile(self):
        self.groups = [
            group["name"]
            for group in settings.get_groups()
        ]

        if len(self.groups) <= 0:
            sublime.error_message("There are no groups configured")
            return

        def on_ask_group_done(selected_index):
            if selected_index < 0:
                return

            self.group_selected = self.groups[selected_index]

            if selected_index > -1:
                self.switch_profile()

        def show_panel():
            self.window.show_quick_panel(
                self.groups,
                on_ask_group_done,
                0,
                0,
                None,
            )

        sublime.set_timeout(show_panel, 0)

    def switch_profile(self):
        profiles = settings.get_profiles(self.group_selected)

        self.profile_list = [
            profile["name"] for profile in profiles
        ]

        def on_ask_profile(selected_index):
            if selected_index > -1:
                self.selected_profile_name = self.profile_list[selected_index]
                self.set_group_profile()

        def show_panel():
            self.window.show_quick_panel(self.profile_list, on_ask_profile, 0, 0, None)

        sublime.set_timeout(show_panel, 0)

    def set_group_profile(self):
        current_settings = settings.get_setting("default_profiles", {})
        current_settings[self.group_selected] = self.selected_profile_name
        settings.set_setting("default_profiles", current_settings)


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
        if not key.startswith("toolrunner."):
            return None

        settings_key = key[len("toolrunner.") :]
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
        commands.on_pre_close_view(self, view)
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
        _logger.exception("Error when loading settings", exc_info=ex)

    try:
        debug.forget_modules()
    except Exception as ex:
        _logger.exception("Error when unloading modules", exc_info=ex)

    _logger.info("Plugin Loaded")


def plugin_unloaded():
    try:
        settings.on_unloaded()
    except Exception as ex:
        _logger.exception("Error when unloading settings", exc_info=ex)

    try:
        debug.forget_modules()
    except Exception as ex:
        _logger.exception("Error when unloading modules", exc_info=ex)

    _logger.info("Plugin Unloaded")
