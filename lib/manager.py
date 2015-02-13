import sublime

from . import settings
from . import debug

_target_views_by_source_id = dict()
_sources_by_target_id = dict()
_command_for_source_view = dict()

def cancel_command_for_source_view(view):
    command = get_current_command_for_source_view(view)
    if command is not None:
        command.cancel()

def create_target_view_for_source_view(view):
    source_id = str(view.id())

    if source_id not in _target_views_by_source_id:
        new_view = view.window().new_file()

        _target_views_by_source_id[source_id] = new_view
        _sources_by_target_id[str(new_view.id())] = source_id

    return _target_views_by_source_id[source_id]

def get_source_view_for_target_view(view):
    target_id = view.id()

    if target_id in _sources_by_target_id:
        return _sources_by_target_id[target_id]

    return None

def get_target_view_for_source_view(view):
    source_id = view.id()

    if source_id in _target_views_by_source_id:
        return _target_views_by_source_id[source_id]

    return None

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

def remove_target_view(view):
    target_id = str(view.id())
    source_id = _sources_by_target_id.pop(target_id, None)

    if source_id is not None:
        debug.log("Forgetting view %s" % str(source_id))
        _target_views_by_source_id.pop(str(source_id), None)

