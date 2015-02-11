import sublime
import sublime_plugin
from .toolrunner.settings import ToolRunnerSettings
from .toolrunner.command import ToolRunnerCommandManager
from .toolrunner.views import ToolRunnerViewManager
from .toolrunner.debug import log

settings = ToolRunnerSettings(__package__)
output_view_manager = ToolRunnerViewManager(settings)
command_manager = ToolRunnerCommandManager(settings, output_view_manager)

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
        command_manager.cancel_command_for_source_view(
            self.window.active_view()
        )

class ToolRunnerFocusOutput(sublime_plugin.WindowCommand):
    pass

class ToolRunnerSwitchDefaultProfile(sublime_plugin.WindowCommand):
    def run(self, profile_group=None):
        log("Switching command for profile group: " + str(profile_group))
        if profile_group is None:
            self.ask_group_and_switch_profile()
        else:
            self.switch_profile(profile_group)

    def ask_group_and_switch_profile(self):
        self.groups = [ group['name'] for group in settings.getGroups() ]
        log(repr(self.groups))
        self.window.show_quick_panel(self.groups, self.on_ask_group_done, 0, 0, None)

    def on_ask_group_done(self, selected_index):
        group_selected = self.groups[selected_index]

        if selected_index > -1:
            def on_switch_profile_async():
                self.switch_profile(group_selected)
            sublime.set_timeout_async(on_switch_profile_async, 0)

    def switch_profile(self, profile_group):
        self.profile_group = profile_group
        self.profile_list = [ profile["name"] for profile in settings.getProfiles(profile_group) ]

        log(self.profile_group, self.profile_list)

        self.window.show_quick_panel(self.profile_list, self.on_ask_profile, 0, 0, None)

    def on_ask_profile(self, selected_index):

        if selected_index > -1:
            selected_profile_name = self.profile_list[selected_index]
            current_settings = settings.getSetting('default_profiles', {})
            current_settings[self.profile_group] = selected_profile_name
            settings.setSetting('default_profiles', current_settings)

        self.profile_list = None
        self.groups = None


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
        output_view_manager.remove(view)

    def on_save(self, view):
        output_settings = output_view_manager.getSettings(view)

        if output_settings.keep_reusing_after_save: return

        output_view_manager.remove(view)
