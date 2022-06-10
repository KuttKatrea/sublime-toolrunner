import sublime_plugin

from .. import debug, settings


class ToolRunnerOpenSettings(sublime_plugin.WindowCommand):
    def run(
        self,
        scope=None,
        *args,
        **kwargs,
    ):
        debug.log_unused_args(*args, **kwargs)
        settings.open_settings(self.window, scope)
