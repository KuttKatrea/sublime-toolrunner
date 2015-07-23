import sublime

from os import path
import re

from . import debug
from . import settings

def expand(value, view):
    if value is None:
        return None

    variables = {}
    variables.update(extract_variables(view))
    variables.update({"package": settings.basepackage})
    expanded = expand_variables(value, variables)

    return expanded

def expand_variables(str, vars):
    try:
        return sublime.expand_variables(str, vars)
    except AttributeError as e:
        def repl(match):
            replacement = vars.get(match.group(1), None)

            if replacement is None:
                default = match.group(2)
                if default is not None:
                    return expand_variables(default,vars)

            return replacement

        return re.sub(r'\${([\w-]+)(?:[^}]*)?}', repl, str)

def extract_variables(view):
    win = view.window()
    try:
        return win.extract_variables()
    except AttributeError as e:
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


def notify(msg, desc=None, source=None, target=None):
    if desc is None:
        desc = 'ToolRunner'
    else:
        desc = 'ToolRunner[%s]' % desc

    debug.log(msg)

    if source is None:
        source = sublime.active_window().active_view()

    source.set_status(
        "toolrunner", "%s: %s" % (desc, msg))

    if target is not None:
        target.set_status(
            "toolrunner", "%s: %s" % (desc, msg))
