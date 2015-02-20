import sublime

from . import settings
from . import debug

_target_views_by_source_id = dict()
_sources_by_target_id = dict()
_command_for_source_view = dict()

def cancel_command_for_source_view(view):
    command = get_current_command_for_source_view(view)
    if command is not None:
        debug.log("Cancelling command")
        command.cancel()
    else:
        debug.log("No command to cancel")

def create_target_view_for_source_view(view, type):
    source_id = str(view.id())

    if source_id not in _target_views_by_source_id:
        if type == 'buffer':
            new_view = view.window().new_file()
        else:
            vid = 'toolrunner-output:' + source_id
            new_view = view.window().create_output_panel(vid)
            new_view.settings().set('toolrunner-output-id', vid)

        target_id = str(new_view.id())
        debug.log("Created view with id %s" % target_id)

        _target_views_by_source_id[source_id] = new_view
        _sources_by_target_id[target_id] = source_id
        debug.log(_target_views_by_source_id, _sources_by_target_id)

    return _target_views_by_source_id[source_id]

def get_source_view_for_target_view(view):
    target_id = str(view.id())

    return _sources_by_target_id.get(target_id)

def get_target_view_for_source_view(view):
    source_id = str(view.id())
    return _target_views_by_source_id.get(source_id)

def get_current_command_for_source_view(view):
    view_id = str(view.id())

    if view_id not in _command_for_source_view:
        if view_id in _target_views_by_source_id:
            view_id = str(_target_views_by_source_id[view_id].id())
        else:
            return None

    if view_id in _command_for_source_view:
        return _command_for_source_view[view_id]

    return None

def set_current_command_for_source_view(target_view, command):
    view_id = str(target_view.id())

    if command is None:
        _command_for_source_view.pop(view_id,None)
    else:
        _command_for_source_view[view_id] = command

def remove_source_view(view):
    vid = str(view.id())
    targetid = _target_views_by_source_id.pop(vid, None)
    if targetid != None:
        targetid = targetid.id()
    debug.log("Forgetting as source %s => %s" % (vid, targetid))
    _sources_by_target_id.pop(targetid, None)

def remove_target_view(view):
    vid = str(view.id())
    sourceid = _sources_by_target_id.pop(vid, None)
    debug.log("Forgetting as target %s => %s" % (sourceid, vid))
    _target_views_by_source_id.pop(sourceid, None)

def focus_view(target_view):
    active_window = sublime.active_window()
    active_view = active_window.active_view()
    active_group = active_window.active_group()

    panel_id = target_view.settings().get('toolrunner-output-id')

    if panel_id is None:
        target_window = target_view.window()
        
        target_window.focus_view(target_view)
        target_group = target_window.active_group()

        if active_window != target_window or active_group != target_group:
            active_window.focus_view(active_view)

    else:
        active_window.run_command('show_panel', {'panel': 'output.' + panel_id})
