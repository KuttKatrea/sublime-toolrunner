import sublime
import sublime_plugin
from functools import partial

from .lib import settings
from .lib import manager
from .lib import debug
from .lib.command import Command
from .lib import util


class ToolRunner(sublime_plugin.WindowCommand):
    def run(self, tool=None, group=None, profile=None, default_profile=False,
            **kwargs):
        command = Command(
            self.window,
            kwargs
        )

        if tool is not None:
            command.run_tool(tool)

        elif group is not None:

            if default_profile:
                profile = settings.get_setting('default_profiles').get(group)

            if profile is not None:
                command.run_profile(group, profile)
            else:
                self._ask_profile_and_run_command(
                    group,
                    partial(self._on_ask_profile_done, command)
                )

        else:
            self._ask_type_to_run(
                partial(self._on_ask_type_done, command)
            )

    def _ask_type_to_run(self, callback):
        self.window.show_quick_panel(["Tool", "Group"], callback, 0, 0, None)

    def _on_ask_type_done(self, command, selected_index):
        if selected_index == 0:
            sublime.set_timeout(partial(
                self._ask_tool_to_run,
                partial(self._on_ask_tool_done, command)
            ), 0)

        elif selected_index == 1:
            sublime.set_timeout(
                partial(
                    self._ask_group_and_profile_to_run,
                    partial(self._on_ask_group_done, command)
                ), 0
            )

    def _ask_tool_to_run(self, callback):
        tool_list = []
        tool_selection_list = []

        def_tool_list = settings.get_tools()

        if len(def_tool_list) <= 0:
            sublime.error_message("There are no tools configured")
            return

        debug.log("Creating Tools item list for Quick Panel", def_tool_list)

        for single_tool in def_tool_list:
            debug.log("Appending ", single_tool)
            tool_name = single_tool.get("name", single_tool.get("cmd"))
            tool_list.append(tool_name)

            desc = single_tool.get('desc')

            if desc is not None:
                tool_selection_list.append(desc + " (" + tool_name + ")")
            else:
                tool_selection_list.append(tool_name)

        callback = partial(callback, tool_list)

        self.window.show_quick_panel(tool_selection_list, callback, 0, 0, None)

    def _on_ask_tool_done(self, command, tool_list, selected_index):
        tool_selected = tool_list[selected_index]

        if selected_index > -1:
            command.run_tool(tool_selected)

    def _ask_group_and_profile_to_run(self, callback):
        group_list = [
            single_group['name'] for single_group in settings.get_groups()
        ]

        if len(group_list) <= 0:
            sublime.error_message("There are no groups configured")
        else:
            callback = partial(callback, group_list)

            self.window.show_quick_panel(group_list, callback, 0, 0, None)

    def _on_ask_group_done(self, command, group_list, selected_index):
        group_selected = group_list[selected_index]

        if selected_index >= 0:
            callback = partial(self._on_ask_profile_done, command)
            sublime.set_timeout(
                partial(
                    self._ask_profile_and_run_command,
                    group_selected, callback
                ), 0
            )

    def _ask_profile_and_run_command(self, group_selected, callback):
        profiles = settings.get_profiles(group_selected)

        if len(profiles) <= 0:
            sublime.error_message("This group has no profiles configured")
            return

        profile_list = [
            profile["name"] for profile in profiles
        ]

        self.window.show_quick_panel(
            profile_list,
            partial(callback, group_selected, profile_list),
            0, 0, None
        )

    def _on_ask_profile_done(self, command, group_selected, profile_list,
                             selected_index):
        if selected_index >= 0:
            selected_profile = profile_list[selected_index]
            command.run_profile(group_selected, selected_profile)


class ToolRunnerCancelCurrent(sublime_plugin.WindowCommand):
    def run(self):
        manager.cancel_command_for_view_id(
            self.window.active_view().id()
        )


class ToolRunnerFocusOutput(sublime_plugin.WindowCommand):
    def run(self):
        source_view = self.window.active_view()
        target_view = manager.get_target_view_for_source_view(source_view)
        if target_view is not None:
            manager.ensure_visible_view(target_view, focus=True)
        else:
            util.notify("This view don't have an output")


class ToolRunnerFocusSource(sublime_plugin.WindowCommand):
    def run(self):
        target_view = self.window.active_view()
        source_view = manager.get_source_view_for_target_view(target_view)
        if source_view is not None:
            manager.ensure_visible_view(source_view, focus=True)
        else:
            util.notify("This view is not an output")


class ToolRunnerSwitchDefaultProfile(sublime_plugin.WindowCommand):
    def run(self, profile_group=None):
        debug.log("Switching command for profile group: " + str(profile_group))
        if profile_group is None:
            self.ask_group_and_switch_profile()
        else:
            self.switch_profile(profile_group)

    def ask_group_and_switch_profile(self):
        self.groups = [group['name'] for group in settings.get_groups()]

        if len(self.groups) <= 0:
            sublime.error_message("There are no groups configured")
            return

        self.window.show_quick_panel(
            self.groups,
            partial(self.on_ask_group_done, self.switch_profile),
            0, 0, None)

    def on_ask_group_done(self, callback, selected_index):
        if selected_index < 0:
            return

        group_selected = self.groups[selected_index]

        if selected_index > -1:
            sublime.set_timeout(partial(callback, group_selected), 0)

    def switch_profile(self, profile_group):
        profiles = settings.get_profiles(profile_group)

        self.profile_group = profile_group
        self.profile_list = [profile["name"] for profile in profiles]
        self.window.show_quick_panel(
            self.profile_list, self.on_ask_profile, 0, 0, None)

    def on_ask_profile(self, selected_index):

        if selected_index > -1:
            selected_profile_name = self.profile_list[selected_index]
            current_settings = settings.get_setting('default_profiles', {})
            current_settings[self.profile_group] = selected_profile_name
            settings.set_setting('default_profiles', current_settings)

        self.profile_list = None
        self.groups = None


class ToolRunnerOpenSettings(sublime_plugin.WindowCommand):
    def __init__(self, *args, **kwargs):

        sublime_plugin.WindowCommand.__init__(self, *args, **kwargs)

        self.ask_scope_items = [
            ["Default", "Default settings"],
            ["User", "Normal user settings"],
            ["OS", "Settings specific to this machine OS"],
            ["Host", "Settings specific to this machine"],
            ["Host/OS", "Settings specific to this machine on this OS"],
        ]

    def run(self, scope=None):
        if scope is None:
            self.ask_scope_and_open_settings()
        else:
            self.do_open_settings(scope)

    def ask_scope_and_open_settings(self):
        self.window.show_quick_panel(
            self.ask_scope_items, self.on_ask_scope_done, 0, 0, None)

    def on_ask_scope_done(self, selected_index):
        if selected_index < 0:
            return

        scope = self.ask_scope_items[selected_index][0].lower()
        self.do_open_settings(scope)

    def do_open_settings(self, scope):
        self.window.run_command(
            "open_file",
            {"file": settings.get_settings_file_path(scope)}
        )


class ToolRunnerListener(sublime_plugin.EventListener):
    def on_close(self, view):
        manager.remove_source_view(view)
        manager.remove_target_view(view)

    def on_post_save(self, view):
        # debug.log("Saved view: %s" % view.id())
        source_view = manager.get_source_view_for_target_view(view)
        if source_view is None:
            # debug.log("The view %s is not an output view" % view.id())
            return

        manager.remove_target_view(view)
        view.set_scratch(False)
        view.set_read_only(False)


def plugin_loaded():
    debug.log("Plugin Loading")
    settings.on_loaded()
    debug.log("Plugin Loaded")
    if settings.get_setting('devel'):
        debug.forget_modules()


def plugin_unloaded():
    settings.on_unloaded()
    debug.log("Plugin Unloaded")
