import logging

import sublime

from . import settings

"""
sv = source view
svid = source view id
tv = target view
tvid = target view id
"""
_source_views_by_tvid = dict()
_target_views_by_svid = dict()
_svids_by_tvid = dict()
_command_for_source_view = dict()


_logger = logging.getLogger("ToolRunner:Manager")


def cancel_command_for_view_id(view_id, wait=False):
    command = get_current_command_for_source_view_id(view_id)

    if command is None:
        _logger.info("This source doesn't have a command")
        view_id = get_source_view_id_for_target_view_id(view_id)
        if view_id is not None:
            command = get_current_command_for_source_view_id(view_id)
        else:
            _logger.info("This target doesn't have a view")

    if command is not None:
        _logger.info("Cancelling command")
        command.cancel(wait)
    else:
        _logger.info("No command to cancel")


def cancel_command_for_source_view(source_view, wait=False):
    command = get_current_command_for_source_view(source_view)
    if command is not None:
        _logger.info("Cancelling command")
        command.cancel(wait)
    else:
        _logger.info("No command to cancel")


def create_target_view_for_source_view(view, type):
    source_id = str(view.id())

    if source_id not in _target_views_by_svid:
        if type == "buffer":
            new_view = _create_view_in_target_group(view)
        else:
            vid = "ToolRunner Output (%s)" % source_id
            new_view = view.window().create_output_panel(vid)
            new_view.settings().set("toolrunner-output-id", vid)
            new_view.settings().set("toolrunner-is-output", True)

        target_id = str(new_view.id())
        _logger.info("Created view with id %s for view %s", target_id, source_id)

        _target_views_by_svid[source_id] = new_view
        _source_views_by_tvid[target_id] = view
        _svids_by_tvid[target_id] = source_id

    _target_views_by_svid[source_id].set_name("ToolRunner Output for %s" % view.name())

    return _target_views_by_svid[source_id]


def _create_view_in_target_group(view):
    win = view.window()
    group, idx = win.get_view_index(view)

    target_group = settings.get_setting("output_tab_position")
    if target_group not in set(["top", "bottom", "left", "right"]):
        target = group
    else:
        layout = win.get_layout()

        x1 = 0
        y1 = 1
        x2 = 2
        y2 = 3

        origin_coords = layout["cells"][group]
        _logger.info(origin_coords)
        #  min_y = 0
        #  min_x = 0
        max_target = None
        min_target = None

        for idx in range(0, len(layout["cells"])):
            if idx == group:
                continue
            tgroup = layout["cells"][idx]

            if tgroup[y1] == origin_coords[y2]:
                _logger.info("Y-Matches: %s, %s", idx, tgroup)
                if tgroup[x1] >= origin_coords[x1]:
                    if max_target is None or tgroup[x1] < max_target:
                        _logger.info("X Max Matches: %s, %s", idx, tgroup)
                        max_target = idx
                if tgroup[x1] <= origin_coords[x1]:
                    if min_target is None or tgroup[x1] > min_target:
                        _logger.info("X Min Matches: %s, %s", idx, tgroup)
                        min_target = idx

        _logger.info("Target: %s, %s", max_target, min_target)

        target = max_target or min_target

        if target is None:
            cells = layout["cells"]

            new_cells = list()
            for cell in cells:
                new_cells.append(
                    [
                        layout["cols"][cell[x1]],
                        layout["rows"][cell[y1]],
                        layout["cols"][cell[x2]],
                        layout["rows"][cell[y2]],
                    ]
                )

            current_cell = new_cells[group]

            _logger.info("Cells: %s, %s", new_cells, current_cell)

            new_cell = list(current_cell)

            nc_height = (current_cell[y2] - current_cell[y1]) / 3
            dic_y = current_cell[y2] - nc_height

            new_cell[y1] = dic_y
            current_cell[y2] = dic_y

            new_cells.append(new_cell)

            layout["rows"].append(dic_y)
            rows = list(sorted(set(layout["rows"])))

            layout["rows"] = rows

            for cell in new_cells:
                cell[x1] = layout["cols"].index(cell[x1])
                cell[y1] = layout["rows"].index(cell[y1])
                cell[x2] = layout["cols"].index(cell[x2])
                cell[y2] = layout["rows"].index(cell[y2])

            _logger.info("New cells: %s", new_cells)

            layout["cells"] = new_cells

            target = len(new_cells) - 1

            win.set_layout(layout)

        if target is not None:
            win.focus_group(target)

    target_view = win.new_file()

    group, idx = win.get_view_index(view)

    win.focus_group(group)
    win.focus_view(view)

    return target_view


def get_source_view_id_for_target_view_id(view_id):
    view_id = str(view_id)
    return _svids_by_tvid.get(view_id)


def get_source_view_for_target_view(view):
    target_id = str(view.id())
    return _source_views_by_tvid.get(target_id)


def get_target_view_for_source_view(view):
    source_id = str(view.id())
    return _target_views_by_svid.get(source_id)


def get_current_command_for_source_view(view):
    view_id = str(view.id())
    return get_current_command_for_source_view_id(view_id)


def get_current_command_for_source_view_id(view_id):
    view_id = str(view_id)
    if view_id in _command_for_source_view:
        return _command_for_source_view.get(view_id)

    return None


def set_current_command_for_source_view(source_view, command):
    view_id = str(source_view.id())

    if command is None:
        _command_for_source_view.pop(view_id, None)
    else:
        _command_for_source_view[view_id] = command


def remove_source_view(view):
    source_id = str(view.id())

    target = _target_views_by_svid.pop(source_id, None)

    if target is None:
        _logger.info("No target to forget")
        return

    target_id = target.id()

    _logger.info("Forgetting as source %s => %s", source_id, target_id)

    _svids_by_tvid.pop(target_id, None)
    _source_views_by_tvid.pop(target_id, None)

    remove_panel(target)


def remove_target_view(view):
    vid = str(view.id())
    sourceid = _svids_by_tvid.pop(vid, None)
    _source_views_by_tvid.pop(vid, None)

    _logger.info("Forgetting as target %s => %s", sourceid, vid)
    tv = _target_views_by_svid.pop(sourceid, None)

    remove_panel(tv)


def remove_panel(tv: sublime.View):
    if not tv:
        return

    is_output = tv.settings().get("toolrunner-is-output")
    panel_id = tv.settings().get("toolrunner-output-id")
    win = tv.window()

    _logger.info("Target: %s, Is Output: %s", tv, is_output)
    if is_output:
        _logger.info("Removing panel %s", panel_id)

        try:
            win.destroy_output_panel(panel_id)
        except AttributeError:
            tv.run_command("close")


def ensure_visible_view(target_view, focus=False):
    active_window = sublime.active_window()

    panel_id = target_view.settings().get("toolrunner-output-id")
    use_panel = panel_id is not None

    _logger.info("Use panel: %s", use_panel)
    if use_panel:
        active_window.run_command("show_panel", {"panel": "output." + panel_id})

    target_window = target_view.window()
    if target_window is None:
        _logger.info("No window?")
        return

    target_group, group_index = target_window.get_view_index(target_view)
    target_window.set_view_index(target_view, target_group, group_index)

    if focus:
        target_window.focus_group(target_group)
        target_window.focus_view(target_view)
