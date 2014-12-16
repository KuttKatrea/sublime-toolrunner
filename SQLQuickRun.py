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

    def run(self):
        self.createWindow()
        self.showWindow()
        self.write("SQLQuickRun: Running query...", True)
        self.lock()

        print("SQLQuickRun: Before Running %s" % ( datetime.datetime.now() ))

        sublime.set_timeout_async(self.execute,0)


    def execute(self):
        startupinfo = subprocess.STARTUPINFO() 
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        process = subprocess.Popen(self.command_array, 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, shell=False, startupinfo=startupinfo)

        output, error = process.communicate(input=bytes(self.sqltext,'UTF-8'))

        outstring = output.decode('cp437', "replace").replace('\r','')
        errorstring = error.decode('cp437', "replace").replace('\r','')

        print("SQLQuickRun: Complete %s" % ( datetime.datetime.now() ))

        self.showWindow()

        self.unlock()
        self.clear()
        self.write(errorstring)
        self.write(outstring)
        self.lock()

        sublime.status_message("SQLQuickRun: Complete")

    def createWindow(self):
        self.window = self.view.window()

        self.panelname = 'sqlquickrun-%s' % ( self.view.buffer_id() )
        self.panelview = self.window.create_output_panel(self.panelname)
        self.panelview.set_scratch(True)
        self.panelview.set_syntax_file('Find Results')
        self.panelview.settings().set('line_numbers', False)

        self.view.settings().set('sqlquickrun_panel_name', self.panelname)

        self.unlock()
        self.clear()

    def showWindow(self):
        self.window.run_command('show_panel', {'panel': 'output.' + self.panelname})

    def lock(self):
        self.panelview.set_read_only(True)

    def unlock(self):
        self.panelview.set_read_only(False)     

    def clear(self):
        self.panelview.run_command("move_to", {"extend": False, "to": "bof"})
        self.panelview.run_command("move_to", {"extend": True, "to": "eof"})
        self.panelview.run_command("right_delete")

    def write(self, text, on_status=False):
        self.panelview.run_command("append", {"characters": text})

        if on_status:
            sublime.status_message(text)

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

        command = SqlQuickRunHelper.getConnectionCommand(textcommand, active_view)

        if command is None:
            sublime.status_message("SQLQuickRun: Invalid connection selected", True)
            return

        command.run()

class SqlQuickRunListener(sublime_plugin.EventListener):
    def on_activated(self, view):
        results_panel = view.settings().get("sqlquickrun_panel_name")

        if results_panel is not None:
            view.window().run_command('show_panel', {'panel': 'output.' + results_panel})
