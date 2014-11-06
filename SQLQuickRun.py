import sublime
import sublime_plugin
import subprocess
import os
import platform
import threading
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

        user_settings = sublime.load_settings(
            cls.getSettingsFilePath())
        
        host_settings.set(settingName, settingValue)

        sublime.save_settings(cls.getHostSettingsFilePath())

    @classmethod
    def getConnectionList(cls):
        return cls.getSetting('connections')

    @classmethod
    def getConnectionCommand(cls, sqltext, onDone,panelview,active_window, panelname):
        executable_list = cls.getSetting('executable')
        connection_list = cls.getConnectionList()
        current_connection_name = cls.getSetting('current_connection')

        #print(executable_list)
        #print(connection_list)
        #print(current_connection_name)

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
            onDone,
            panelview,
            active_window,
            panelname
        )


class SqlQuickRunCommand(object):
    def __init__(self, executable, connection, sqltext, onDone, panelview, active_window, panelname):
        self.command_array = [ executable ]

        option_mapping = {
            'server': '-S',
            'user': '-U',
            'password': '-P',
            'codepage': '-f',
        }

        for option_key, option_value in option_mapping.items():
            if option_key in connection:
                self.command_array += [ option_value, connection[option_key] ]

        self.sqltext = sqltext
        self.onDone = onDone
        self.panelview = panelview
        self.active_window = active_window
        self.panelname = panelname

    def run(self):
        startupinfo = subprocess.STARTUPINFO() 
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        process = subprocess.Popen(self.command_array, 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, shell=False, startupinfo=startupinfo)

        output, error = process.communicate(input=bytes(self.sqltext,'UTF-8'))

        outstring = output.decode('cp437', "replace").replace('\r','')
        errorstring = error.decode('cp437', "replace").replace('\r','')

        self.onDone(outstring + errorstring)

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
        quick_panel_items = [ single_connection['name'] for single_connection in connection_list ]
        
        self.connection_list = connection_list
        self.window.show_quick_panel(quick_panel_items, self.onDone, 0, 0, None)

    def onDone(self, selected_index):
        selected_connection_name = self.connection_list[selected_index]['name']
        #print(selected_connection_name)
        SqlQuickRunHelper.setSetting('current_connection', selected_connection_name)

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

        self.execute(active_view, textcommand)

    def execute(self, view, textcommand):
        active_window = sublime.active_window()
        panelname = 'sqlquickrun-%s' % ( active_window.active_view().buffer_id() )

        panelview = active_window.create_output_panel(panelname)
        panelview.set_scratch(True)
        panelview.set_read_only(False)

        command = SqlQuickRunHelper.getConnectionCommand(textcommand, self.onDone, panelview, active_window, panelname)

        if command is None:
            sublime.status_message("SQLQuickRun: Invalid connection selected")
            return

        self.active_window = active_window
        self.panelview = panelview
        self.panelname = panelname

        sublime.status_message("SQLQuickRun: Running query...")
        print("SQLQuickRun: Before Running %s" % ( datetime.datetime.now() ))

        sublime.set_timeout_async(command.run,0)

    def onDone(self, outstring):
        print("SQLQuickRun: Complete %s" % ( datetime.datetime.now() ))
        sublime.status_message("Writing resultset, please wait...")
        self.active_window.run_command('show_panel', {'panel': 'output.' + self.panelname})
        self.panelview.run_command('append', {'characters': outstring})
        self.panelview.set_read_only(True)
        sublime.status_message("Complete")

class SqlQuickRunListener(sublime_plugin.EventListener):
    def on_activated(self, view):
        active_window = sublime.active_window()
        panelname = 'sqlquickrun-%s' % ( view.buffer_id() )
        active_window.run_command('show_panel', {'panel': 'output.' + panelname})
