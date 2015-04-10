import sublime

from . import settings
from . import debug
'''
sv = source view
svid = source view id
tv = target view
tvid = target view id
'''
_target_views_by_svid = dict()
_svids_by_tvid = dict()
_command_for_source_view = dict()

def cancel_command_for_view_id(view_id, wait=False):
    command = get_current_command_for_source_view_id(view_id)

    if command is None:
        debug.log('This source doesn\'t have a command')
        view_id = get_source_view_id_for_target_view_id(view_id)
        if view_id is not None:
            command = get_current_command_for_source_view_id(view_id)
        else:
            debug.log('This target doesn\'t have a view')

    if command is not None:
        debug.log("Cancelling command")
        command.cancel(wait)
    else:
        debug.log("No command to cancel")

def cancel_command_for_source_view(source_view, wait=False):
    command = get_current_command_for_source_view(source_view)
    if command is not None:
        debug.log("Cancelling command")
        command.cancel(wait)
    else:
        debug.log("No command to cancel")

def create_target_view_for_source_view(view, type):
    source_id = str(view.id())

    if source_id not in _target_views_by_svid:
        if type == 'buffer':
            new_view = view.window().new_file()
        else:
            vid = 'toolrunner-output:' + source_id
            new_view = view.window().create_output_panel(vid)
            new_view.settings().set('toolrunner-output-id', vid)

        target_id = str(new_view.id())
        debug.log("Created view with id %s" % target_id)

        _target_views_by_svid[source_id] = new_view
        _svids_by_tvid[target_id] = source_id

    return _target_views_by_svid[source_id]

def get_source_view_id_for_target_view_id(view_id):
    view_id = str(view_id)
    return _svids_by_tvid.get(view_id)

def get_source_view_for_target_view(view):
    target_id = str(view.id())

    return get_source_view_id_for_target_view_id(target_id)

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
        _command_for_source_view.pop(view_id,None)
    else:
        _command_for_source_view[view_id] = command

def remove_source_view(view):
    vid = str(view.id())
    targetid = _target_views_by_svid.pop(vid, None)
    if targetid != None:
        targetid = targetid.id()
    debug.log("Forgetting as source %s => %s" % (vid, targetid))
    _svids_by_tvid.pop(targetid, None)

def remove_target_view(view):
    vid = str(view.id())
    sourceid = _svids_by_tvid.pop(vid, None)
    debug.log("Forgetting as target %s => %s" % (sourceid, vid))
    _target_views_by_svid.pop(sourceid, None)

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
