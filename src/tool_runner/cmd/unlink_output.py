import logging

import sublime_plugin

from .. import debug, mapper, settings, util

_logger = logging.getLogger(f"{__package__}.{__name__}")


class ToolRunnerUnlinkOutput(sublime_plugin.WindowCommand):
    def run(
        self,
        *args,
        **kwargs,
    ):
        debug.log_unused_args(*args, **kwargs)
        target_window = self.window
        target_view = target_window.active_view()
        assert target_view
        is_output = target_view.settings().get(mapper.TR_SETTING_IS_OUTPUT, None)

        if not is_output:
            util.notify("This view is not an output")
            return

        source_view_id = target_view.settings().get(mapper.TR_SETTING_SOURCE_VIEW_ID)
        _logger.info("Source view id, %s, %s", source_view_id, type(source_view_id))
        for view in target_window.views():
            if view.id() == source_view_id:
                _logger.info(
                    "OutputID: %s",
                    view.settings().get(mapper.TR_SETTING_TARGET_OUTPUT_ID, None),
                )
                view.settings().erase(mapper.TR_SETTING_TARGET_OUTPUT_ID)
                target_window.focus_view(view)
                return

        target_view.set_name(f"{target_view.name()} *Unlinked")
