import logging
import re
from typing import Any, Dict, List, Optional

import sublime

from . import better_settings


class ToolRunnerSettings:
    def __init__(self):
        self.tool_list = []


_tool_map: Dict[str, Dict[str, "sublime.Value"]] = {}
_tool_list: List[Dict[str, "sublime.Value"]] = []

_plugin_loaded = False
_on_plugin_loaded_callbacks = list()

basepackage = re.sub(r"\.lib$", "", __package__)

_settings = better_settings.load_for(basepackage, "ToolRunner")

_logger = logging.getLogger(__package__)

_settings = None


def settings() -> better_settings._BetterSettings:
    global _settings
    if not _settings:
        _settings = better_settings.load_for(basepackage, "ToolRunner")
    return _settings


def get_setting(setting_name, default=None) -> Any:
    return settings().get(setting_name, default)


def set_setting(setting_name, setting_value):
    settings().set(better_settings.SCOPE_HOST_OS, setting_name, setting_value)
    settings().save()


def get_groups():
    groups = (
        settings().get_scoped(better_settings.SCOPE_HOST_OS, "user_groups", []) or []
    )
    groups += settings().get_scoped(better_settings.SCOPE_HOST, "user_groups") or []
    groups += settings().get_scoped(better_settings.SCOPE_OS, "user_groups") or []
    groups += settings().get_scoped(better_settings.SCOPE_DEFAULT, "user_groups") or []

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
    project_tool_overrides = (
        sublime.active_window()
        .project_data()
        .get("tool_runner", {})
        .get("tool_overrides", {})
    )
    if tool_id in project_tool_overrides:
        return project_tool_overrides[tool_id]

    return settings().get("user_tool_overrides", {}).get(tool_id)


def _build_tool_list():
    global _tool_map, _tool_list

    _tool_map = {}
    _tool_list = []

    for settings_set in (
        settings().get_scoped(better_settings.SCOPE_HOST_OS, "user_tools", []),
        settings().get_scoped(better_settings.SCOPE_HOST, "user_tools", []),
        settings().get_scoped(better_settings.SCOPE_OS, "user_tools", []),
        settings().get_scoped(better_settings.SCOPE_DEFAULT, "user_tools", []),
        settings().get_scoped(better_settings.SCOPE_DEFAULT, "default_tools", []),
    ):
        for tool_item in settings_set:
            name = tool_item.get("name")
            cmd = tool_item.get("cmd")

            if name:
                key = name
            elif cmd and len(cmd) > 0:
                key = cmd[0]
                tool_item["name"] = key

            if not key:
                _logger.info("Tool has no valid name: %s", tool_item)
                continue

            if not tool_item.get("cmd"):
                tool_item["cmd"] = [key]

            # key = key.lower()

            if key not in _tool_map:
                override_cmd = get_override(tool_item["name"])
                if override_cmd is not None:
                    tool_item["cmd"] = override_cmd

                _tool_map[key] = tool_item
                _tool_list.append(tool_item)


def on_loaded():
    global _plugin_loaded

    if _plugin_loaded:
        _logger.info("Plugin already loaded")
        return

    _logger.info("Registering Settings Callbacks")

    if _on_plugin_loaded_callbacks is not None:
        for callback in _on_plugin_loaded_callbacks:
            callback()

    _plugin_loaded = True
    del _on_plugin_loaded_callbacks[:]


def on_unloaded():
    del _on_plugin_loaded_callbacks[:]


def register_on_plugin_loaded(callback):
    if _plugin_loaded:
        callback()
    else:
        _on_plugin_loaded_callbacks.append(callback)


def open_settings(window, scope):
    settings().open_settings(window, scope)


def get_scopes_mapping() -> dict:
    scopes_mapping = {}
    for settings_map in (
        settings().get_scoped(
            better_settings.SCOPE_DEFAULT, "default_scopes_mapping", {}
        ),
        settings().get_scoped(better_settings.SCOPE_DEFAULT, "user_scopes_mapping", {}),
        settings().get_scoped(better_settings.SCOPE_OS, "user_scopes_mapping", {}),
        settings().get_scoped(better_settings.SCOPE_HOST, "user_scopes_mapping", {}),
        settings().get_scoped(better_settings.SCOPE_HOST_OS, "user_scopes_mapping", {}),
    ):
        if settings_map:
            scopes_mapping.update(settings_map)

    return scopes_mapping


def get_extensions_mapping():
    scopes_mapping = {}
    for settings_map in (
        settings().get_scoped(
            better_settings.SCOPE_DEFAULT, "default_extensions_mapping", {}
        ),
        settings().get_scoped(
            better_settings.SCOPE_DEFAULT, "user_extensions_mapping", {}
        ),
        settings().get_scoped(better_settings.SCOPE_OS, "user_extensions_mapping", {}),
        settings().get_scoped(
            better_settings.SCOPE_HOST, "user_extensions_mapping", {}
        ),
        settings().get_scoped(
            better_settings.SCOPE_HOST_OS, "user_extensions_mapping", {}
        ),
    ):
        scopes_mapping.update(settings_map)

    return scopes_mapping


def get_default_profile(group: str):
    default_profiles = get_setting("default_profiles", default=dict())
    return default_profiles.get(group, None)
