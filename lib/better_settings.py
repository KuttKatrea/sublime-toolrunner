"""
Better settings management for Sublime Plugins.

This module allows a plugin to easily implement OS, Host and
OS/Host-level settings aside the normal user-level settings.

This allows to keep the settings file in the User package, so they can
be synced between machines using different OSes or with specific
configuration for each host without interfering between them.
"""
import logging
import platform
from collections import OrderedDict

import sublime

SCOPE_DEFAULT = "User"
SCOPE_OS = "OS"
SCOPE_HOST = "Host"
SCOPE_HOST_OS = "Host/OS"

ASK_SCOPE_ITEMS = [
    [SCOPE_DEFAULT, "Default user settings"],
    [SCOPE_OS, "Settings specific to this machine OS"],
    [SCOPE_HOST, "Settings specific to this machine"],
    [SCOPE_HOST_OS, "Settings specific to this machine on this OS"],
]

__DEBUG__ = False

_valid_scopes = {SCOPE_DEFAULT, SCOPE_OS, SCOPE_HOST, SCOPE_HOST_OS}
_logger = logging.getLogger(__name__)


class _BetterSettings(object):
    def __init__(self, default_settings_dir, scoped_settings):
        self.default_settings_dir = default_settings_dir
        self.scoped_settings = scoped_settings

    def get(self, setting_name, default=None):
        for item in self.scoped_settings.values():
            if item.settings.has(setting_name):
                return item.settings.get(setting_name)

        return default

    def get_scoped(self, scope, setting_name, default=None):
        _ensure_valid_scope(scope)
        return self.scoped_settings[scope].settings.get(setting_name, default)

    def set(self, scope, setting_name, setting_value):
        _ensure_valid_scope(scope)

        item = self.scoped_settings[scope]
        item.settings.set(setting_name, setting_value)

    def save(self):
        for item in self.scoped_settings.values():
            sublime.save_settings(item.filename)

    def add_on_change(self, event_name, callback):
        for item in self.scoped_settings.values():
            item.settings.add_on_change(event_name, callback)

    def clear_on_change(self, event_name):
        for item in self.scoped_settings.values():
            item.settings.clear_on_change(event_name)

    def open_settings(self, window, scope=None):
        def do_open_settings(selected_scope):
            default_path = _build_settings_file_path(
                self.default_settings_dir, self.scoped_settings[SCOPE_DEFAULT].filename
            )
            user_path = _build_settings_file_path(
                "User", self.scoped_settings[selected_scope].filename
            )

            _logger.info("Opening settings files: %s, %s", default_path, user_path)

            window.run_command(
                "edit_settings",
                {"base_file": default_path, "user_file": user_path, "default": "{}"},
            )

        def on_ask_scope_done(selected_index):
            if selected_index < 0:
                return

            selected_scope = ASK_SCOPE_ITEMS[selected_index][0]

            do_open_settings(selected_scope)

        def ask_scope_and_open_settings():
            window.show_quick_panel(ASK_SCOPE_ITEMS, on_ask_scope_done, 0, 0, None)

        if scope is None:
            ask_scope_and_open_settings()
        else:
            _ensure_valid_scope(scope)
            do_open_settings(scope)


class _ScopedSettings(object):
    def __init__(self, filename, settings):
        self.filename = filename
        self.settings = settings


def load_for(default_settings_dir, settings_name):
    def get_settings_filename(special=None):
        special = " (" + special + ")" if special else ""
        return "".join((settings_name, special, ".sublime-settings"))

    def load_scoped_settings(filename):
        return _ScopedSettings(filename, sublime.load_settings(filename))

    scoped_settings = OrderedDict()
    scoped_settings[SCOPE_HOST_OS] = load_scoped_settings(
        get_settings_filename(
            platform.uname()[1].lower() + " on " + sublime.platform().capitalize()
        )
    )
    scoped_settings[SCOPE_HOST] = load_scoped_settings(
        get_settings_filename(platform.uname()[1].lower())
    )

    scoped_settings[SCOPE_OS] = load_scoped_settings(
        get_settings_filename(sublime.platform().capitalize())
    )

    scoped_settings[SCOPE_DEFAULT] = load_scoped_settings(get_settings_filename())

    return _BetterSettings(default_settings_dir, scoped_settings)


def _ensure_valid_scope(scope):
    if scope not in _valid_scopes:
        raise Exception(
            "Invalid scope: %s (Valid scopes are %s)" % (scope, _valid_scopes)
        )


def _build_settings_file_path(directory, filename):
    return "${packages}/%0s/%1s" % (directory, filename)
