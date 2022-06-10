import sublime_plugin

from .. import settings


class ToolRunnerCancelCurrent(sublime_plugin.WindowCommand):
    def run(self):
        # manager.cancel_command_for_view_id(self.window.active_view().id())
        pass
