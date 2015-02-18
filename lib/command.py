import sublime

import subprocess
import datetime
import os
from functools import partial
from os import path
from threading import Thread

from . import settings
from . import manager
from . import debug
from .tool import Tool

class Command(object):
    def __init__(self, source_window, command_arguments):
        self._source_window = source_window
        self._source_view = source_window.active_view()
        self._command_arguments = command_arguments
        self._tool = None

        self._target_view = None

        self._cancelled = False

    def run_tool(self, tool_id):
        debug.log("Running command for tool: ", tool_id)

        tool = self._create_tool(tool_id)

        debug.log("Passing command arguments:", self._command_arguments)

        tool.set_input_source(self._command_arguments.get("input_source"))

        tool.set_output(self._command_arguments.get("output"))

        tool.set_params_values(self._command_arguments.get("params"))

        self._tool = tool

        manager.cancel_command_for_source_view(self._source_view)

        debug.log("Launching thread")
        self._thread = Thread(target=partial(self._do_run_tool, tool))
        self._thread.start()

        '''
        sublime.set_timeout_async(
            partial(self._do_run_tool, tool), 0
        )
        '''

    def run_profile(self, selected_group, selected_profile):
        group_descriptor = None
        profile_descriptor = None

        group_list = settings.get_groups()
        
        for single_group in group_list:
            if single_group["name"] == selected_group:
                group_descriptor = single_group
                break

        for single_profile in group_descriptor["profiles"]:
            if single_profile["name"] == selected_profile:
                profile_descriptor = single_profile

        debug.log("Running command for profile: ", group_descriptor, profile_descriptor)

        tool_id =profile_descriptor.get("tool",
            group_descriptor.get("tool"))

        tool = self._create_tool(tool_id)

        debug.log("Passing command arguments:", self._command_arguments)

        tool.set_input_source(
            self._command_arguments.get("input_source",
               profile_descriptor.get("input_source",
                    group_descriptor.get("input_source"))))

        tool.set_output(
            self._command_arguments.get("output",
               profile_descriptor.get("output",
                    group_descriptor.get("output"))))

        tool.set_params_values(
            self._command_arguments.get("params",
               profile_descriptor.get("params",
                    group_descriptor.get("params"))))
        
        self._tool = tool

        manager.cancel_command_for_source_view(self._source_view)

        '''
        sublime.set_timeout_async(
            partial(self._do_run_tool, tool), 0
        )
        '''
        self._thread = Thread(target=partial(self._do_run_tool, tool))
        self._thread.start()

    def cancel(self):
        self._cancelled = True
        self.process.terminate()

    def _create_tool(self, tool_id):
        tool_config = settings.get_tool(tool_id)

        if tool_config is None:
            return None

        tool = Tool()

        tool.set_name(tool_config.get("name"))
        tool.set_cmd(tool_config.get("cmd"))
        tool.set_arguments(tool_config.get("arguments"))
        tool.set_input(tool_config.get("options", {}).get("input"))
        tool.set_output(tool_config.get("options", {}).get("output"))
        tool.set_params(tool_config.get("options", {}).get("params"))
        tool.set_input_source(tool_config.get("options", {}).get("input_source"))

        return tool

    def _get_input(self, input_source):
        if input_source is None:
            input_source = "auto-file"

        debug.log(input_source)

        if input_source not in set(['selection', 'auto-line', 'line','auto-block','block', 'auto-file','file', 'none']):
            raise ValueError("Input source invalid")

        if input_source == 'none':
            return ''

        active_view = self._source_view

        input_text = ''

        current_selection = active_view.sel()

        if input_source in set(['selection', 'auto-file', 'auto-block', 'auto-line']):
            if len(current_selection) > 0:
                for partial_selection in current_selection:
                    input_text += active_view.substr(partial_selection)

        if input_source != 'selection' and input_text == '':
            region = None
            if input_source in set(['line', 'auto-line']):
                region = active_view.line(current_selection[0])

            if input_source in set(['block','auto-block']):
                region = active_view.expand_by_class(
                    current_selection[0],
                    sublime.CLASS_EMPTY_LINE
                )

            if input_source in set(['file', 'auto-file']):
                region = sublime.Region(0, active_view.size())
        
            input_text = active_view.substr(region)

        if input_text != "" and input_text[-1] != '\n':
            input_text += '\n'

        return input_text

    def _do_run_tool(self, tool):
        self._execution_cancelled = False

        input_text = self._get_input(tool.input_source)

        if input_text == "" and not tool.input.allow_empty:
            debug.log("This tool does not allow empty input")
            return

        command_array = None
        if tool.input.mode in set(("manual", "none")):
            command_array = tool.get_command_array(input_text=input_text)
        else:
            command_array = tool.get_command_array()

        debug.log(command_array)

        working_directory = None

        file_ = self._source_view.file_name()
        project = self._source_window.project_file_name()
        
        if file_ is not None:
            working_directory = path.dirname(file_)
        elif project is not None:
            working_directory = path.dirname(project)
        else:
            working_directory = os.environ.get('HOME', os.environ.get('USER_PROFILE'))

        startupinfo = None
        if sublime.platform() == "windows":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= (subprocess.STARTF_USESHOWWINDOW | subprocess.CREATE_NEW_CONSOLE)

        try:
            process = subprocess.Popen(
                command_array,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=False,
                startupinfo=startupinfo,
                cwd=working_directory
            )
            self.process = process

        except FileNotFoundError as e:
            debug.log("Error: ", e)
            return

        self.create_window(tool.output)

        manager.set_current_command_for_source_view(self._target_view, self)

        self._target_view.run_command("move_to", {"to": "eof"})

        current_cursor_position = self._target_view.sel()[0]
        current_line = self._target_view.line(current_cursor_position)

        self._target_view.sel().clear()
        self._target_view.sel().add(current_cursor_position)

        if tool.input.mode == 'pipe':
            process.stdin.write(bytes(input_text, tool.input.codec))

        process.stdin.close()

        input_text = None

        starttime = datetime.datetime.now()

        tool_desc = tool.name

        self._source_view.set_status("toolrunner", "ToolRunner Source: Running query on [%s]" % tool_desc)
        self._target_view.set_status("toolrunner", "ToolRunner Target: Running query on [%s]" % tool_desc)

        debug.log(current_cursor_position)
        debug.log(current_line)

        if current_cursor_position.a > current_line.a:
            self.write('\n')

        if current_cursor_position.a != 0:
            self.write('\n')
            current_cursor_position = sublime.Region(current_cursor_position.a+1, current_cursor_position.a+1)

        self.write(':: ToolRunner :: Start at %s ::\n' % starttime)
        self._target_view.run_command("move_to", {"to": "eof"})

        while True: #self._cancelled is False:
            outstring = process.stdout.readline().decode(tool.output.codec, "replace").replace('\r\n', '\n')
            if outstring == "": break
            self.write(outstring)

        endtime = datetime.datetime.now()
        timedelta = endtime - starttime

        if self._cancelled:
            self.write("\nQuery execution cancelled\n")

        self.write('\n:: ToolRunner :: End at %s ::\n' % endtime)

        self._target_view.sel().clear()
        self._target_view.sel().add(current_cursor_position)
        self._target_view.show_at_center(current_cursor_position)

        if self._cancelled:
            self._target_view.set_status("toolrunner", "ToolRunner Target [%s]: Cancelled at %s seconds" % (tool_desc, timedelta.total_seconds()))
            self._source_view.set_status("toolrunner", "ToolRunner Source [%s]: Cancelled at %s seconds" % (tool_desc, timedelta.total_seconds()))
        else:
            self._target_view.set_status("toolrunner", "ToolRunner Target [%s]: Complete on %s seconds" % (tool_desc, timedelta.total_seconds()))
            self._source_view.set_status("toolrunner", "ToolRunner Source [%s]: Complete on %s seconds" % (tool_desc, timedelta.total_seconds()))

        manager.set_current_command_for_source_view(self._target_view, None)

    def create_window(self, output):
        self._source_window = self._source_view.window()

        self._target_view = manager.create_target_view_for_source_view(self._source_view, output.type)

        self.panelname = ':: ToolRunner Results: %s ::' % (self._source_view.buffer_id())
        self._target_view.set_name(self.panelname)

        #self._target_view = self._source_window.create_output_panel(self.panelname)
        self._target_view.set_scratch(True)

        self._target_view.set_syntax_file(settings.expand(output.syntax_file))

        self._target_view.settings().set('line_numbers', False)
        self._target_view.settings().set('translate_tabs_to_spaces', False)
        #self._target_view.settings().set('tab_size', 8)
        manager.focus_view(self._target_view)

    def write(self, text):
        self._target_view.run_command("append", {"characters": text})

