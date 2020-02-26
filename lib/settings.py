import platform
import re

import better_settings
import sublime

from . import debug

_tool_list = None
_tool_map = None

_plugin_loaded = False
_on_plugin_loaded_callbacks = list()
_settings = None


def get_setting(setting_name, default=None):
    return _settings.get(setting_name, default)


def set_setting(setting_name, setting_value):
    _settings.set(better_settings.SCOPE_HOST, setting_name, setting_value)
    _settings.save()


def get_groups():
    groups = _settings.get_hostplatform_setting("user_groups", [])
    groups += _settings.get_host_setting("user_groups", [])
    groups += _settings.get_platform_setting("user_groups", [])
    groups += _settings.get_user_setting("user_groups", [])

    return groups


def get_profiles(profile_group):
    groups = get_groups()

    for group in groups:
        if group["name"] == profile_group:
            return group["profiles"]

    return []


def get_tools():
    _build_tool_list()
    return _tool_list


def get_tool(tool_id):
    _build_tool_list()
    return _tool_map.get(tool_id.lower(), None)


def get_override(tool_id):
    return _settings.get("user_tool_overrides", {}).get(tool_id)


def _build_tool_list():
    global _tool_map, _tool_list

    _tool_map = {}
    _tool_list = []

    for settings_set in (
        _settings.get_hostplatform_setting("user_tools", []),
        _settings.get_host_setting("user_tools", []),
        _settings.get_platform_setting("user_tools", []),
        _settings.get_user_setting("user_tools", []),
        _settings.get_user_setting("default_tools", []),
    ):
        for tool_item in settings_set:
            key = tool_item.get("name", tool_item.get("cmd"))

            if key is None:
                debug.log("Tool has no cmd: ", tool_item)
                continue

            tool_item["name"] = key

            key = key.lower()

            if key not in _tool_map:
                override_cmd = get_override(tool_item["name"])
                if override_cmd is not None:
                    tool_item["cmd"] = override_cmd

                _tool_map[key] = tool_item
                _tool_list.append(tool_item)


def on_loaded():
    global _plugin_loaded
    global _settings

    if _plugin_loaded:
        debug.log("Plugin already loaded")
        return

    basepackage = re.sub(r"\.lib$", "", __package__)

    _settings = better_settings.load_for(basepackage, "ToolRunner")

    on_debug_change()

    debug.log("Registering Settings Callbacks")

    _settings.add_on_change("debug", on_debug_change)

    if _on_plugin_loaded_callbacks is not None:
        for callback in _on_plugin_loaded_callbacks:
            callback()

    _plugin_loaded = True
    del _on_plugin_loaded_callbacks[:]


def on_unloaded():
    _settings.clear_on_change("debug")
    del _on_plugin_loaded_callbacks[:]


def on_debug_change():
    debug.enabled = _settings.get("debug")


def register_on_plugin_loaded(callback):
    if _plugin_loaded:
        callback()
    else:
        _on_plugin_loaded_callbacks.append(callback)


def open_settings(window, scope):
    _settings.open_settings(window, scope)
