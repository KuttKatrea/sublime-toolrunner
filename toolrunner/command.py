import sublime
import subprocess
import datetime

class ToolRunnerCommandManager(object):
    def __init__(self, settings):
        self.settings = settings

    def getConnectionCommand(self, sqltext, view):
        executable_list = self.settings.getSetting('executable')
        connection_list = self.settings.getConnectionList()
        current_connection_name = self.settings.getSetting('current_connection')

        current_connection = None

        for single_connection in connection_list:
            if single_connection['name'] == current_connection_name:
                current_connection = single_connection
                break

        if current_connection is None:
            return None

        executable = executable_list[current_connection['type']]

        return ToolRunnerCommand(
            executable,
            current_connection,
            sqltext,
            view
        )

    def cancel_command_for_view(source_view):
        command = view_manager.getCommandForView(source_view)
        if command is not None:
            command.cancel()

class ToolRunnerCommand(object):
    def __init__(self, executable, connection, sqltext, view):
        self.cancelled = False

        self.view = view

        self.command_array = [ executable['cmd'] ]

        if 'default_arguments' in executable:
            for v in executable['default_arguments']:
                self.command_array.append(v)

        argument_mapping = set(executable['arguments'])
        option_mapping = executable['options']
        flag_mapping = executable['flags']

        for param_key, param_value in connection['params'].items():
            if param_key in option_mapping:
                self.command_array += [ option_mapping[param_key], param_value ]

            if param_key in flag_mapping and param_value:
                self.command_array.append(flag_mapping[param_key])

        for param_key in argument_mapping:
            if param_key in connection['params']:
                self.command_array.append(connection['params'][param_key])

        self.serverdesc = connection['desc'] if 'desc' in connection else connection['name']
        self.sqltext = sqltext
        self.input_codec = executable['codecs']['input']
        self.output_codec = executable['codecs']['output']

    def run(self):
        sublime.set_timeout_async(self.execute, 0)

    def cancel(self):
        self.process.terminate()
        self.cancelled = True

    def execute(self):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        process = subprocess.Popen(
            self.command_array,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=False,
            startupinfo=startupinfo
        )

        self.process = process

        self.createWindow()

        view_manager.setCommandForView(self.panelview, self)

        self.panelview.run_command("move_to", {"to": "eof"})

        current_cursor_position = self.panelview.sel()[0]

        self.panelview.sel().clear()
        self.panelview.sel().add(current_cursor_position)

        process.stdin.write(bytes(self.sqltext + "\n", self.input_codec))
        process.stdin.close()

        starttime = datetime.datetime.now()
        self.view.set_status("toolrunner", "ToolRunner Source: Running query on [%s]" % self.serverdesc)
        self.panelview.set_status("toolrunner", "ToolRunner Target: Running query on [%s]" % self.serverdesc)

        while True:
            outstring = process.stdout.readline().decode(self.output_codec, "replace").replace('\r\n', '\n')
            if outstring == "": break
            self.write(outstring)

        endtime = datetime.datetime.now()
        timedelta = endtime - starttime

        if self.cancelled:
            self.write("\nQuery execution cancelled")

        self.write('\n')

        self.panelview.sel().clear()
        self.panelview.sel().add(current_cursor_position)
        self.panelview.show_at_center(current_cursor_position)

        if self.cancelled:
            self.panelview.set_status("toolrunner", "ToolRunner Target [%s]: Cancelled at %s seconds" % (self.serverdesc, timedelta.total_seconds()))
            self.view.set_status("toolrunner", "ToolRunner Source [%s]: Cancelled at %s seconds" % (self.serverdesc, timedelta.total_seconds()))
        else:
            self.panelview.set_status("toolrunner", "ToolRunner Target [%s]: Complete on %s seconds" % (self.serverdesc, timedelta.total_seconds()))
            self.view.set_status("toolrunner", "ToolRunner Source [%s]: Complete on %s seconds" % (self.serverdesc, timedelta.total_seconds()))

        view_manager.setCommandForView(self.panelview, None)

    def createWindow(self):
        self.window = self.view.window()

        self.panelview = view_manager.getViewForSource(self.view)
        self.panelname = 'ToolRunner Results: %s' % (self.view.buffer_id())
        self.panelview.set_name(self.panelname)

        #self.panelview = self.window.create_output_panel(self.panelname)
        self.panelview.set_scratch(True)
        self.panelview.set_syntax_file(
            'Packages/sublime-toolrunner/languages/MSSQL Query Results.tmLanguage')
        self.panelview.settings().set('line_numbers', False)

        self.view.settings().set('toolrunner_panel_name', self.panelname)

        self.window.focus_view(self.panelview)

    def write(self, text):
        self.panelview.run_command("append", {"characters": text})
