import sublime
import sublime_plugin
from .toolrunner.settings import ToolRunnerSettings
from .toolrunner.command import ToolRunnerCommandManager
from .toolrunner.views import ToolRunnerViewManager

settings = ToolRunnerSettings(__package__)
command_manager = ToolRunnerCommandManager(settings)
view_manager = ToolRunnerViewManager(settings)

class ToolRunner(sublime_plugin.WindowCommand):
    def run(self,source='auto-line'):
        if source not in set(['selection', 'auto-line', 'line','auto-block','block', 'auto-file','file']):
            return

        textcommand = ''

        active_view = sublime.active_window().active_view()

        command_manager.cancel_command_for_source_view(view)

        cancel_command_for_view(active_view)

        current_selection = active_view.sel()

        if source in set(['selection', 'auto-file', 'auto-block', 'auto-line']):
            if len(current_selection) > 0:
                for partial_selection in current_selection:
                    textcommand += active_view.substr(partial_selection)

        if source != 'selection' and textcommand == '':
            region = None
            if source in set(['line', 'auto-line']):
                region = active_view.line(current_selection[0])

            if source in set(['block','auto-block']):
                region = active_view.expand_by_class(
                    current_selection[0],
                    sublime.CLASS_EMPTY_LINE
                )

            if source in set(['file', 'auto-file']):
                region = sublime.Region(0, active_view.size())
        
            textcommand = active_view.substr(region)

        if textcommand == '':
            return

        command = ToolRunnerHelper.getConnectionCommand(
            textcommand, active_view)

        if command is None:
            sublime.status_message(
                "ToolRunner: Invalid connection selected", True)
            return

        command.run()

class ToolRunnerCancelRunningQuery(sublime_plugin.WindowCommand):
    def run(self):
        active_view = sublime.active_window().active_view()
        cancel_command_for_view(active_view)

class ToolRunnerSwitchDefaultProfile(sublime_plugin.WindowCommand):
    def run(self):
        connection_list = ToolRunnerHelper.getConnectionList()
        quick_panel_items = [single_connection['name'] for single_connection in connection_list]  # noqa

        self.connection_list = connection_list
        self.window.show_quick_panel(
            quick_panel_items, self.onDone, 0, 0, None)

    def onDone(self, selected_index):
        selected_connection_name = self.connection_list[selected_index]['name']
        ToolRunnerHelper.setSetting(
            'current_connection', selected_connection_name)

class ToolRunnerOpenSettings(sublime_plugin.WindowCommand):
    def __init__(self, *args,**kwargs):
        
        sublime_plugin.WindowCommand.__init__(self, *args, **kwargs)

        self.ask_scope_items = [
            ["Default","Default settings"],
            ["User","Normal user settings"],
            ["OS", "Settings specific to this machine OS"],
            ["Host", "Settings specific to this machine"],
        ]

    def run(self, scope=None):
        if scope is None:
            self.ask_scope_and_open_settings()
        else:
            self.do_open_settings(scope)
        
    def ask_scope_and_open_settings(self):
        self.window.show_quick_panel(self.ask_scope_items,self.on_ask_scope_done, 0, 0, None)

    def on_ask_scope_done(self, selected_index):
        if selected_index < 0: return
        scope = self.ask_scope_items[selected_index][0].lower()
        self.do_open_settings(scope)

    def do_open_settings(self, scope):
        self.window.run_command("open_file", {"file": settings.getSettingsFilePath(scope)})

class ToolRunnerListener(sublime_plugin.EventListener):
    def on_close(self, view):
        view_manager.remove(view)
