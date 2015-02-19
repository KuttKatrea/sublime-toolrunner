import sublime

import platform
import re
from os import path

from . import debug

basepackage = re.sub(r"\.lib$", "", __package__)

host_settings = None
platform_settings = None
user_settings = None

_tool_list = None
_tool_map = None

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

def get_host_setting(setting_name, default=None):
    return host_settings.get(setting_name, default)

def get_platform_setting(setting_name, default=None):
    return platform_settings.get(setting_name, default)

def get_user_setting(setting_name, default=None):
    return user_settings.get(setting_name, default)

def set_setting(setting_name, settingValue):
    host_settings.set(setting_name, settingValue)
    sublime.save_settings(get_host_settings_filename())

def expand(value):
    if value is None:
        return None

    variables = {}
    variables.update(extract_variables())
    variables.update({"package": basepackage})

    debug.log("Expanding: %s with %s" % (value, variables))
    expanded = expand_variables(value, variables)

    debug.log("Expanded: %s" % expanded)

    return expanded

def expand_variables(str, vars):
    try:
        return sublime.expand_variables(str, vars)
    except AttributeError as e:
        def repl(match):
            debug.log("Replacing: ", match)
            return vars.get(match.group(1), match.group(0))

        return re.sub(r'\${(\w+)}', repl, str)

def extract_variables():
    try:
        return sublime.extract_variables()
    except AttributeError as e:
        win = sublime.active_window()
        view = win.active_view()

        filename = view.file_name()
        folder, basename = path.split(filename) if filename is not None else (None, None)
        base, ext = path.splitext(basename) if filename is not None else (None, None)

        project = win.project_file_name()
        pfolder, pbasename = path.split(project) if project is not None else (None, None)
        basep, baseext = path.splitext(path.basename(project)) if project is not None else (None, None)

        return {
            'packages': sublime.packages_path(),
            'platform': sublime.platform(),
            'file': filename,
            'file_path': folder,
            'file_name': basename,
            'file_base_name': base,
            'file_extension': ext,
            'folder': folder,
            'project': project,
            'project_path': pfolder,
            'project_name': pbasename,
            'project_base_name': basep,
            'project_extension': baseext
        }

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
    _build_tool_list()
    return _tool_list

def get_tool(tool_id):
    _build_tool_list()
    return _tool_map.get(tool_id, None)

def get_override(tool_id):
    return get_setting('user_tool_overrides',{}).get(tool_id)

def _build_tool_list():
    global _tool_map, _tool_list

    _tool_map = {}
    _tool_list = []

    for settings_set in (
          get_host_setting('user_tools', []), get_platform_setting('user_tools', []),
          get_user_setting('user_tools', []), get_user_setting('default_tools', []) ):
        for tool_item in settings_set:
            debug.log("Checking: ", tool_item)
            key = tool_item.get('name', tool_item.get('cmd'))
            
            if key is None:
                debug.log("Tool has no cmd: ", tool_item)
                continue

            tool_item["name"] = key

            if key not in _tool_map:
                override_cmd = get_override(key)
                if override_cmd is not None:
                    tool_item['cmd'] = override_cmd

                _tool_map[key] = tool_item
                _tool_list.append(tool_item)

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

    debug.log(extract_variables())

def on_unloaded():
    if host_settings is not None:
        host_settings.clear_on_change('debug')
    
    if platform_settings is not None:
        platform_settings.clear_on_change('debug')

    if user_settings is not None:
        user_settings.clear_on_change('debug')

def on_debug_change():
    debug.enabled = get_setting('debug')
