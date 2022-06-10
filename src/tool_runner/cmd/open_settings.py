import sublime_plugin

from .. import settings


class ToolRunnerOpenSettings(sublime_plugin.WindowCommand):
    def run(self, scope=None):
        settings.open_settings(self.window, scope)
