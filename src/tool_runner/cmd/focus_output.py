import sublime_plugin

from .. import mapper, util


class ToolRunnerFocusOutput(sublime_plugin.WindowCommand):
    def run(self):
        source_view = self.window.active_view()

        target_view_name = source_view.settings().get(
            mapper.TR_SETTING_TARGET_OUTPUT_NAME, None
        )

        if target_view_name:
            mapper.show_panel(self.window, target_view_name)
        else:
            util.notify("This view don't have an output")
