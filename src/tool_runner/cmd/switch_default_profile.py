import logging

import sublime
import sublime_plugin

from .. import debug, settings

_logger = logging.getLogger(f"{__package__}.{__name__}")


class ToolRunnerSwitchDefaultProfile(sublime_plugin.WindowCommand):
    def __init__(self, *args, **kwargs):
        super(ToolRunnerSwitchDefaultProfile, self).__init__(*args, **kwargs)

        self.groups = []

        self.group_selected = None
        self.selected_profile_name = None

        self.profile_list = []

    def run(
        self,
        profile_group=None,
        profile=None,
        *args,
        **kwargs,
    ):
        debug.log_unused_args(*args, **kwargs)
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
        self.groups = [group["name"] for group in settings.get_groups()]

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

        self.profile_list = [profile["name"] for profile in profiles]

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
