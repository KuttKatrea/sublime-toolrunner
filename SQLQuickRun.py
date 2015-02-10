import sublime
import sublime_plugin
import subprocess
import platform
import datetime

class SqlQuickRunHelper:
    @classmethod
    def getPlatformSettingsFilePath(cls):
        return cls.getSettingsFilePath(sublime.platform().capitalize())

    @classmethod
    def getHostSettingsFilePath(cls):
        return cls.getSettingsFilePath(platform.uname()[1])

    @classmethod
    def getSettingsFilePath(cls, special=None):
        special = " (" + special + ")" if special else ""
        return "".join(("SQLQuickRun", special, ".sublime-settings"))

    @classmethod
    def getSetting(cls, settingName, default=None):
        host_settings = sublime.load_settings(
            cls.getHostSettingsFilePath())

        user_settings = sublime.load_settings(
            cls.getSettingsFilePath())

        return host_settings.get(
            settingName, user_settings.get(settingName, default))

    @classmethod
    def setSetting(cls, settingName, settingValue):
        host_settings = sublime.load_settings(
            cls.getHostSettingsFilePath())

        # user_settings = sublime.load_settings(
        #     cls.getSettingsFilePath())

        host_settings.set(settingName, settingValue)

        sublime.save_settings(cls.getHostSettingsFilePath())

    @classmethod
    def getConnectionList(cls):
        return cls.getSetting('connections')

    @classmethod
    def getConnectionCommand(cls, sqltext, view):
        executable_list = cls.getSetting('executable')
        connection_list = cls.getConnectionList()
        current_connection_name = cls.getSetting('current_connection')

        current_connection = None

        for single_connection in connection_list:
            if single_connection['name'] == current_connection_name:
                current_connection = single_connection
                break

        if current_connection is None:
            return None

        executable = executable_list[current_connection['type']]

        return SqlQuickRunCommand(
            executable,
            current_connection,
            sqltext,
            view
        )


class SqlQuickRunCommand(object):
    def __init__(self, executable, connection, sqltext, view):
        self.view = view

        self.command_array = [ executable['cmd'] ]

        if 'arguments' in executable:
            for k,v in executable['arguments']:
                self.command_array.push(v)

        option_mapping = executable['options']
        flag_mapping = executable['flags']

        for param_key, param_value in connection['params'].items():
            if param_key in option_mapping:
                self.command_array += [option_mapping[param_key], param_value]

            if param_key in flag_mapping and param_value:
                self.command_array += [flag_mapping[param_key]]

        self.serverdesc = connection['desc'] if 'desc' in connection else connection['name']
        self.sqltext = sqltext
        self.input_codec = executable['codecs']['input']
        self.output_codec = executable['codecs']['output']

    def run(self):
        sublime.set_timeout_async(self.execute, 0)

    def execute(self):
        self.view.set_status("sqlquickrun", "SQLQuickRun: Running query on [%s]" % self.serverdesc)
        starttime = datetime.datetime.now()

        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        process = subprocess.Popen(
            self.command_array,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            startupinfo=startupinfo
        )

        output, error = process.communicate(input=bytes(self.sqltext, self.input_codec))

        outstring = output.decode(self.output_codec, "replace").replace('\r\n', '\n')
        errorstring = error.decode(self.output_codec, "replace").replace('\r\n', '\n')

        endtime = datetime.datetime.now()
        timedelta = endtime - starttime

        self.createWindow()
        self.panelview.run_command("move_to", {"to": "eof"})

        current_cursor_position = self.panelview.sel()[0]

        self.write(outstring)
        self.write(errorstring)
        self.write('\n')

        self.panelview.sel().clear()
        self.panelview.sel().add(current_cursor_position)
        self.panelview.show(current_cursor_position)
        self.panelview.set_status("sqlquickrun", "SQLQuickRun [%s]: Complete on %s seconds" % (self.serverdesc, timedelta.total_seconds()))
        self.view.set_status("sqlquickrun", "SQLQuickRun [%s]: Complete on %s seconds" % (self.serverdesc, timedelta.total_seconds()))

    def createWindow(self):
        self.window = self.view.window()

        self.panelview = view_manager.getViewForSource(self.view)
        self.panelname = 'SQLQuickRun Results: %s' % (self.view.buffer_id())
        self.panelview.set_name(self.panelname)

        #self.panelview = self.window.create_output_panel(self.panelname)
        self.panelview.set_scratch(True)
        self.panelview.set_syntax_file(
            'Packages/sublime-sqlquickrun/MSSQL Query Results.tmLanguage')
        self.panelview.settings().set('line_numbers', False)

        self.view.settings().set('sqlquickrun_panel_name', self.panelname)

        self.window.focus_view(self.panelview)

    def write(self, text):
        self.panelview.run_command("append", {"characters": text})

class SqlQuickRunOpenSettings(sublime_plugin.WindowCommand):
    def run(self, scope='default'):
        settingsFilePieces = self.getSettingPieces(scope)
        self.window.run_command("open_file", {
            "file": "${packages}/%0s/%1s" % settingsFilePieces
        })

    def getSettingPieces(self, scope):
        if scope == 'host':
            return ('User/', SqlQuickRunHelper.getHostSettingsFilePath())
        elif scope == 'user':
            return ('User/', SqlQuickRunHelper.getSettingsFilePath())
        elif scope == 'os':
            return ('User/', SqlQuickRunHelper.getPlatformSettingsFilePath())
        else:  # default
            return (__package__, SqlQuickRunHelper.getSettingsFilePath())


class SqlQuickRunSwitchConnection(sublime_plugin.WindowCommand):
    def run(self):
        connection_list = SqlQuickRunHelper.getConnectionList()
        quick_panel_items = [single_connection['name'] for single_connection in connection_list]  # noqa

        self.connection_list = connection_list
        self.window.show_quick_panel(
            quick_panel_items, self.onDone, 0, 0, None)

    def onDone(self, selected_index):
        selected_connection_name = self.connection_list[selected_index]['name']
        SqlQuickRunHelper.setSetting(
            'current_connection', selected_connection_name)


class SqlQuickRun(sublime_plugin.WindowCommand):
    def run(self):
        textcommand = ''
        active_view = sublime.active_window().active_view()
        current_selection = active_view.sel()

        if len(current_selection) > 0:
            for partial_selection in current_selection:
                textcommand += active_view.substr(partial_selection)

        if textcommand == '':
            fullregion = sublime.Region(0, active_view.size())
            textcommand = active_view.substr(fullregion)

        command = SqlQuickRunHelper.getConnectionCommand(
            textcommand, active_view)

        if command is None:
            sublime.status_message(
                "SQLQuickRun: Invalid connection selected", True)
            return

        command.run()


class SqlQuickRunListener(sublime_plugin.EventListener):
    def on_close(self, view):
        view_manager.remove(view)

class SqlQuickRunViewManager(object):
    def __init__(self):
        self.views_by_source_id = dict()
        self.sources_by_target_id = dict()

    def getViewForSource(self, view):
        source_id = str(view.id())

        if source_id not in self.views_by_source_id:
            new_view = view.window().new_file()

            self.views_by_source_id[source_id] = new_view
            self.sources_by_target_id[str(new_view.id())] = source_id

        return self.views_by_source_id[source_id]

    def remove(self, view):
        target_id = str(view.id())
        source_id = self.sources_by_target_id.pop(target_id, None)
        if source_id is not None:
            self.views_by_source_id.pop(str(source_id), None)

view_manager = SqlQuickRunViewManager()
