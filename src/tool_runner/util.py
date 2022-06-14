import logging
import re
import uuid
from os import path
from typing import Optional

import sublime

from . import settings

_logger = logging.getLogger(f"{__package__}.{__name__}")


def expand(value: Optional[str], view: sublime.View) -> Optional[str]:
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
    except AttributeError:

        def repl(match):
            replacement = vars.get(match.group(1), None)

            if replacement is None:
                default = match.group(2)
                if default is not None:
                    return expand_variables(default, vars)

            return replacement

        return re.sub(r"\${([\w-]+)(?:[^}]*)?}", repl, str)


def extract_variables(view):
    win = view.window()
    try:
        return win.extract_variables()
    except AttributeError:
        filename = view.file_name()
        folder, basename = (
            path.split(filename) if filename is not None else (None, None)
        )

        base, ext = path.splitext(basename) if basename is not None else (None, None)

        project = win.project_file_name()
        pfolder, pbasename = (
            path.split(project) if project is not None else (None, None)
        )
        basep, baseext = (
            path.splitext(path.basename(project))
            if project is not None
            else (None, None)
        )

        return {
            "packages": sublime.packages_path(),
            "platform": sublime.platform(),
            "file": filename,
            "file_path": folder,
            "file_name": basename,
            "file_base_name": base,
            "file_extension": ext,
            "folder": folder,
            "project": project,
            "project_path": pfolder,
            "project_name": pbasename,
            "project_base_name": basep,
            "project_extension": baseext,
        }


def notify(
    msg: str,
    desc: Optional[str] = None,
    source: Optional[sublime.View] = None,
    target: Optional[sublime.View] = None,
):
    if desc is None:
        desc = "ToolRunner"
    else:
        desc = "ToolRunner[%s]" % desc

    message = "%s: %s" % (desc, msg)

    _logger.info("Notifying: %s", message)

    if source is None:
        source = sublime.active_window().active_view()

    assert source

    source.set_status("toolrunner", message)

    status_id = str(uuid.uuid4())

    source.settings().set("tr-status-id", status_id)
    sublime.set_timeout_async(create_clear_status_at_callback(source, status_id), 5000)

    if target is not None:
        target.set_status("toolrunner", message)
        source.settings().set("tr-status-id", status_id)
        sublime.set_timeout_async(
            create_clear_status_at_callback(target, status_id), 5000
        )


def create_clear_status_at_callback(source: sublime.View, status_id: str):
    def clear_status_at():
        _logger.info("Clearing status: %s", status_id)
        if source.settings().get("tr-status-id", None) == status_id:
            source.erase_status("toolrunner")
            source.settings().erase("tr-status-id")

    return clear_status_at


def merge_maps_as_new(*maps: Optional[dict]) -> dict:
    _logger.info("Merging: %s", maps)
    result = {}

    for item in maps:
        if item:
            result.update(item)

    return result
