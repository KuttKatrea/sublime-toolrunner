import sublime_plugin

from .. import mapper, util


class ToolRunnerFocusSource(sublime_plugin.WindowCommand):
    def run(self):
        target_window = self.window
        target_view = target_window.active_view()
        source_view_id = target_view.settings().get(
            mapper.TR_SETTING_SOURCE_VIEW_ID, None
        )

        if source_view_id is None:
            util.notify("This view is not an output")

        for view in target_window.views():
            if str(view.id()) == source_view_id:
                target_window.focus_view(view)
                return
