import sublime_plugin

from .. import debug


class ToolRunnerCancelCurrent(sublime_plugin.WindowCommand):
    def run(
        self,
        *args,
        **kwargs,
    ):
        debug.log_unused_args(*args, **kwargs)
        # manager.cancel_command_for_view_id(self.window.active_view().id())
        pass
