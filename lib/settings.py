import sublime

import platform
import re

from . import debug

basepackage = re.sub(r"\.lib$", "", __package__)

host_settings = None
platform_settings = None
user_settings = None

def get_platform_settings_filename():
    return get_settings_filename(sublime.platform().capitalize())

def get_host_settings_filename():
    return get_settings_filename(platform.uname()[1])

def get_settings_filename(special=None):
    special = " (" + special + ")" if special else ""
    return "".join(("ToolRunner", special, ".sublime-settings"))

def get_setting(setting_name, default=None):
    return host_settings.get(setting_name,
        platform_settings.get(setting_name,
        user_settings.get(setting_name, default)
        ))

def set_setting(setting_name, settingValue):
    host_settings.set(setting_name, settingValue)
    sublime.save_settings(get_host_settings_filename())

def get_settingsFilePath(scope):
    return "${packages}/%0s/%1s" % get_settingsPieces(scope)

def get_settingsPieces(scope):
    if scope == 'host':
        return ('User/', get_host_settings_filename())
    elif scope == 'user':
        return ('User/', get_settings_filename())
    elif scope == 'os':
        return ('User/', get_platform_settings_filename())
    else:  # default
        return (basepackage, get_settings_filename())

def get_groups():
    groups = get_setting('user_groups', [])
    groups += get_setting('os_groups', [])
    groups += get_setting('host_groups', [])

    return groups

def get_profiles(profile_group):
    groups = get_groups()

    for group in groups:
        if group["name"] == profile_group:
            return group["profiles"]

    return []

def get_tools():
    tools = {}
    tools.update(get_setting('default_tools'))
    tools.update(get_setting('user_tools'))
    tools.update(get_setting('os_tools'))
    tools.update(get_setting('host_tools'))
    return tools

def on_loaded():
    global host_settings, platform_settings, user_settings

    host_settings = sublime.load_settings(
        get_host_settings_filename())

    platform_settings = sublime.load_settings(
        get_platform_settings_filename())

    user_settings = sublime.load_settings(
        get_settings_filename())

    on_debug_change()

    debug.log('Registering Settings Callbacks')

    user_settings.add_on_change('debug', on_debug_change)
    platform_settings.add_on_change('debug', on_debug_change)
    host_settings.add_on_change('debug', on_debug_change)

def on_unloaded():
    if host_settings is not None:
        host_settings.clear_on_change('debug')
    
    if platform_settings is not None:
        platform_settings.clear_on_change('debug')

    if user_settings is not None:
        user_settings.clear_on_change('debug')

def on_debug_change():
    debug.enabled = get_setting('debug')
