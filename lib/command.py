import sublime

import subprocess
import datetime
import os
import re
import tempfile
from functools import partial
from os import path
from threading import Thread, Event

from . import settings
from . import manager
from . import debug
from .tool import Tool

class Command(object):
    def __init__(self, source_window, command_arguments):
        self._source_window = source_window
        self._source_view = source_window.active_view()
        self._command_arguments = command_arguments
        self._target_view = None
        self._cancelled = False

    def run_tool(self, tool_id):
        debug.log("Running command for tool: ", tool_id, self._command_arguments)

        tool = self._create_tool(tool_id)

        if tool is None:
            debug.log("There is no tool named %s" % tool_id)
            return

        tool.set_command_arguments(self._command_arguments)

        self._launch(tool)

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

        tool_id =profile_descriptor.get("tool", group_descriptor.get("tool"))

        tool = self._create_tool(tool_id)

        debug.log("Passing command arguments:", self._command_arguments)

        tool.set_command_arguments(group_descriptor, profile_descriptor, self._command_arguments)

        self._launch(tool)

    def cancel(self):
        self._cancelled = True
        self.process.terminate()

    def _launch(self, tool):
        self._thread = Thread(target=partial(self._do_run_tool, tool))
        self._thread.start()

    def _create_tool(self, tool_id):
        tool_config = settings.get_tool(tool_id)

        if tool_config is None:
            return None

        tool = Tool(**tool_config)

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

    def create_temp_input_file(self, input):
        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            tmpfile.write(bytes(self.input_text, input.codec))
            self.input_file = tmpfile.name

        debug.log(self.input_file)
        return self.input_file

    def create_temp_output_file(self, output):
        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            self.output_file = tmpfile.name
        debug.log(self.output_file)
        return self.output_file

    def _do_run_tool(self, tool):
        manager.cancel_command_for_source_view(self._source_view)

        self._execution_cancelled = False

        input_text = self._get_input(tool.input_source)
        self.input_text = input_text

        debug.log("Using input text: \n---%s\n---" % input_text)

        if input_text == "" and not tool.input.allow_empty:
            debug.log("This tool does not allow empty input")
            return

        command_array = tool.get_command_array()

        if tool.input.mode in set(("manual", "none")):
            def repfunc(match):
                varname = match.group(1)
                debug.log(varname)
                if varname == 'input-file':
                    return self.create_temp_input_file(tool.input)

                if varname == 'output-file':
                    return self.create_temp_output_file(tool.output)

                return match.group(0)

            for i in range(len(command_array)):
                command_array[i] = re.sub(r'\${([\w-]+)}', repfunc, command_array[i]);

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

        debug.log(tool)

        self.create_window(tool.output)

        manager.set_current_command_for_source_view(self._target_view, self)

        self._target_view.run_command("move_to", {"to": "eof"})

        current_cursor_position = self._target_view.sel()[0]
        current_line = self._target_view.line(current_cursor_position)

        self._target_view.sel().clear()
        self._target_view.sel().add(current_cursor_position)

        if tool.input.mode == 'pipe':
            process.stdin.write(input_text.encode(tool.input.codec, "replace"))

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

        if self.output_file:
            with open(self.output_file, mode='r', encoding=tool.output.codec) as tmpfile:
                for line in tmpfile:
                    outstring = line.replace('\r\n', '\n')
                    debug.log(outstring)
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
        self._target_view.set_read_only(output.read_only)
        self._target_view.set_scratch(output.scratch)
        self._target_view.set_syntax_file(settings.expand(output.syntax_file))

        self._target_view.settings().set('line_numbers', False)
        self._target_view.settings().set('translate_tabs_to_spaces', False)
        #self._target_view.settings().set('tab_size', 8)
        manager.focus_view(self._target_view)

    def write(self, text):
        read_only = self._target_view.is_read_only()

        if read_only:
            self._target_view.set_read_only(False)

        self._target_view.run_command("append", {"characters": text})

        if read_only:
            self._target_view.set_read_only(True)

