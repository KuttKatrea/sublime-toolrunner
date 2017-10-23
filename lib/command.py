import sublime

import re
import subprocess
import datetime
import os
import tempfile
from os import path
from threading import Thread

from . import settings
from . import manager
from . import debug
from . import util
from .tool import Tool


class Command(object):
    def __init__(self, source_window, command_arguments):
        self._source_window = source_window
        self._source_view = source_window.active_view()
        self._target_view = None

        self._command_arguments = command_arguments

        self._running = False
        self._cancelled = False

        self._tool = None

        self._desc = None

        self._process = None

        self._input_text = None
        self._input_file = None
        self._output_file = None

    def run_tool(self, tool_id):
        debug.log("Running command for tool: ",
                  tool_id, self._command_arguments)

        if self._create_tool(tool_id) is None:
            self._notify("There is no tool named %s" % tool_id)
            return

        self._desc = self._tool.name

        self._tool.set_command_arguments(self._command_arguments)

        self._run_thread()

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

        debug.log("Running command for profile: ",
                  group_descriptor, profile_descriptor)

        tool_id = profile_descriptor.get("tool", group_descriptor.get("tool"))

        if self._create_tool(tool_id) is None:
            self._notify("There is no tool named: %s" % tool_id)
            return

        self._desc = "%s/%s" % (
            selected_group, selected_profile)

        self._tool.set_command_arguments(
            group_descriptor, profile_descriptor, self._command_arguments)

        self._run_thread()

    def cancel(self, wait=False):
        self._cancelled = True
        self._process.terminate()
        if wait:
            self._main_thread.join()

    def _create_tool(self, tool_id):
        tool_config = settings.get_tool(tool_id)

        if tool_config is None:
            return None

        self._tool = Tool(**tool_config)

        return self._tool

    def _extract_input(self):
        input_source = self._tool.input_source

        if input_source is None:
            input_source = "auto-file"

        if input_source not in set(['selection', 'auto-line', 'line',
                                    'auto-block', 'block', 'auto-file',
                                    'file', 'none']):
            raise ValueError("Input source invalid")

        if input_source == 'none':
            self._input_text = ''
            return ''

        active_view = self._source_view

        input_text = ''

        current_selection = active_view.sel()

        if input_source in set(['selection', 'auto-file',
                                'auto-block', 'auto-line']):
            if len(current_selection) > 0:
                for partial_selection in current_selection:
                    input_text += active_view.substr(partial_selection)

        if input_source != 'selection' and input_text == '':
            region = None
            if input_source in set(['line', 'auto-line']):
                region = active_view.line(current_selection[0])

            if input_source in set(['block', 'auto-block']):
                region = active_view.expand_by_class(
                    current_selection[0],
                    sublime.CLASS_EMPTY_LINE
                )

            if input_source in set(['file', 'auto-file']):
                region = sublime.Region(0, active_view.size())

            input_text = active_view.substr(region)

        if input_text != "" and input_text[-1] != '\n':
            input_text += '\n'

        self._input_text = input_text
        return input_text

    def _create_temp_input_file(self):
        input = self._tool.input
        input_text = self._input_text

        opts = dict(delete=False)

        opts["prefix"] = 'toolrunner.'

        if input.file_suffix is not None:
            opts["suffix"] = input.file_suffix

        with tempfile.NamedTemporaryFile(**opts) as tmpfile:
            tmpfile.write(bytes(input_text, input.codec))
            input_file = tmpfile.name

        self._input_file = input_file

        debug.log("Created input file: %s" % input_file)

        return input_file

    def _create_temp_output_file(self):
        with tempfile.NamedTemporaryFile(
                delete=False, prefix='toolrunner-') as tmpfile:
            self._output_file = tmpfile.name

        debug.log("Created output file: %s" % self._output_file)

        return self._output_file

    def _run_thread(self):
        self._main_thread = Thread(target=self._begin_run)
        self._main_thread.start()

    def _begin_run(self):
        tool = self._tool

        self._extract_input()

        input_text = self._input_text

        if input_text == "" and not tool.input.allow_empty:
            self._notify("This tool does not allow empty input")
            return

        self._create_command_line()
        debug.log("Using Command Line: %s" % self._command_array)

        self._create_working_directory()
        debug.log("Using Working Directory: %s" % self._working_directory)

        if tool.output.mode != 'none':
            manager.cancel_command_for_source_view(self._source_view, True)

        self._execution_cancelled = False

        self.starttime = datetime.datetime.now()

        self._notify("Running...")

        self._run_process()

        if self._process is None:
            self._notify("Executable not found")
            return

        if tool.output.mode != 'none':
            manager.set_current_command_for_source_view(
                self._source_view, self)

        self._begin_write()
        self._running = True

        self._thread = Thread(target=self._command_monitor_worker)
        self._thread.start()

    def _command_monitor_worker(self):
        '''
        This must be called in it's own thread as it will block while
        the process is running, and while the process is reading the
        output
        '''
        tool = self._tool
        process = self._process

        self._read_thread = None

        if tool.output.mode == 'pipe':
            def outputreader():
                while True:
                    if self._cancelled:
                        break
                    outstring = process.stdout.readline().decode(
                        tool.output.codec, "replace").replace('\r', '')
                    if outstring == "":
                        break
                    self.write(outstring)

            self._read_thread = Thread(target=outputreader)
            self._read_thread.start()

        self._process.wait()
        self._lock = True

        if self._read_thread is not None:
            self._read_thread.join()

        self._end_run()

    def _end_run(self):
        tool = self._tool
        if tool.output.mode == 'none':
            return

        self.endtime = datetime.datetime.now()
        timedelta = self.endtime - self.starttime

        self._write_output()

        if self._cancelled:
            self.write("\n:: Execution cancelled ::\n")

        self.write('\n:: End at %s ::\n' % self.endtime)

        self._target_view.sel().clear()
        self._target_view.sel().add(self._current_cursor_position)

        begin = self._current_cursor_position.begin()

        if self._cancelled:
            self._notify("Cancelled at %s seconds" % timedelta.total_seconds())
        else:
            self._notify("Complete on %s seconds" % timedelta.total_seconds())

        l = self._target_view.text_to_layout(begin)
        self._target_view.set_viewport_position(l)

        manager.set_current_command_for_source_view(self._source_view, None)

        self._clean()

        manager.ensure_visible_view(self._target_view)

    def _create_window(self):
        tool = self._tool

        self._source_window = self._source_view.window()

        self._target_view = manager.create_target_view_for_source_view(
            self._source_view, self._tool.results.mode)

        panelname = ':: ToolRunner Output (%s) ::' % (self._source_view.buffer_id())
        self._target_view.set_name(panelname)

        self._target_view.set_read_only(tool.results.read_only)
        self._target_view.set_scratch(tool.results.scratch)
        self._target_view.set_syntax_file(
            util.expand(tool.results.syntax_file, self._source_view)
        )

        self._target_view.settings().set('line_numbers', False)
        self._target_view.settings().set('translate_tabs_to_spaces', False)

        manager.ensure_visible_view(self._target_view)

    def write(self, text):
        if self._target_view is None or self._target_view.window() is None:
            return
            # self._create_window()

        read_only = self._target_view.is_read_only()

        if read_only:
            self._target_view.set_read_only(False)

        self._target_view.run_command("append", {"characters": text})

        if read_only:
            self._target_view.set_read_only(True)

    def _notify(self, msg):
        util.notify(msg, desc=self._desc, source=self._source_view,
                    target=self._target_view)

    def _create_command_line(self):
        tool = self._tool

        command_array = tool.get_command_array()

        for i in range(len(command_array)):
            input_re = re.escape(r'$[toolrunner_input_file]')
            if re.search(input_re, command_array[i]):
                if tool.input.mode == "tmpfile-path":
                    command_array[i] = re.sub(
                        input_re,
                        self._create_temp_input_file(),
                        command_array[i]
                    )

            if command_array[i] == '$[toolrunner_input_text]':
                if tool.input.mode == "cmdline":
                    command_array[i] = self._input_text

            if command_array[i] == '$[toolrunner_output_file]':
                if tool.output.mode == "tmpfile-path":
                    command_array[i] = self._create_temp_output_file()

        self._command_array = command_array

    # Create partial data
    def _create_working_directory(self):
        working_directory = None

        filename = self._source_view.file_name()
        project = self._source_window.project_file_name()
        folders = self._source_window.folders()

        if project is not None:
            working_directory = path.dirname(project)
        elif len(folders) > 0:
            working_directory = folders[0]
        elif filename is not None:
            working_directory = path.dirname(filename)
        else:
            working_directory = os.environ.get(
                'HOME', os.environ.get('USERPROFILE'))

        self._working_directory = working_directory

    def _run_process(self):
        tool = self._tool

        startupinfo = None
        process = None
        stdin = None
        stdout = None
        stderr = None

        if sublime.platform() == "windows":
            if tool.output.mode != 'none':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.CREATE_NEW_CONSOLE
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        if tool.output.mode != 'none':
            stdin = subprocess.PIPE

        if tool.output.mode == "tmpfile-pipe":
            self._create_temp_output_file()
            stdout = open(self._output_file, 'wb+')
            stderr = subprocess.STDOUT
        elif tool.output.mode == "none":
            pass
        else:
            stdout = subprocess.PIPE
            stderr = subprocess.STDOUT

        try:
            process = subprocess.Popen(
                self._command_array,
                stdin=stdin,
                stdout=stdout,
                stderr=stderr,
                shell=tool.shell,
                startupinfo=startupinfo,
                cwd=self._working_directory,
            )

        except FileNotFoundError as e:
            debug.log("Error: ", e)
            return

        self._stdout = stdout if process.stdout is None else process.stdout

        if tool.input.mode == 'pipe':
            process.stdin.write(
                self._input_text.encode(tool.input.codec, "replace"))

        if process.stdin is not None:
            process.stdin.close()

        self._process = process

    def _begin_write(self):
        tool = self._tool

        if tool.output.mode == 'none':
            return

        self._create_window()

        self._target_view.run_command("move_to", {"to": "eof"})

        current_cursor_position = self._target_view.sel()[0]
        current_line = self._target_view.line(current_cursor_position)

        if current_cursor_position.a > current_line.a:
            self.write('\n')

        if current_cursor_position.a != 0:
            self.write('\n')
            current_cursor_position = sublime.Region(
                current_cursor_position.a+1, current_cursor_position.a+1)

        self._current_cursor_position = current_cursor_position

        self._target_view.sel().clear()
        self._target_view.sel().add(current_cursor_position)

        self.write(':: Start at %s ::\n' % self.starttime)

        self._target_view.run_command("move_to", {"to": "eof"})

    def _write_output(self):
        if self._output_file:
            with open(self._output_file, mode='r',
                      encoding=self._tool.output.codec) as tmpfile:
                outlines = [line.replace('\r\n', '\n') for line in tmpfile]
                # debug.log(outstring)
            self.write(outlines)

    def _clean(self):
        if self._input_file:
            debug.log("Eliminando: %s" % self._input_file)
            os.unlink(self._input_file)

        if self._output_file:
            debug.log("Eliminando: %s" % self._output_file)
            os.unlink(self._output_file)
