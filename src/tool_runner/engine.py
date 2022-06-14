import logging
import os
import subprocess
import sys
import tempfile
import threading
from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Literal, Optional, Protocol, TextIO, Union

TEMPFILE_PREFIX = "sttr_"

DEFAULT_INPUT_CODEC = "utf-8"  # 'cp850'
DEFAULT_OUTPUT_CODEC = "utf-8"  # 'cp850'

InputMode = Literal["pipe", "tmpfile-path", "cmdline", "none"]
OutputMode = Literal["pipe", "tmpfile-path", "tmpfile-pipe"]
ResultsMode = Literal["panel", "buffer"]

PlaceholderType = Literal["positional", "named", "flag"]
PlaceholderValue = Union[str, bool]

_logger = logging.getLogger(f"{__package__}.{__name__}")


@dataclass()
class Input:
    mode: InputMode = "pipe"
    allow_empty: bool = False
    file_suffix: str = ""
    codec: str = DEFAULT_INPUT_CODEC

    def is_file(self):
        return self.mode in {"tmpfile-path"}

    def is_pipe(self):
        return self.mode in {"pipe"}

    def is_commandline(self):
        return self.mode in {"cmdline"}


@dataclass()
class Output:
    mode: OutputMode = "pipe"
    codec: str = DEFAULT_OUTPUT_CODEC


@dataclass()
class Results:
    mode: ResultsMode = "panel"
    read_only: bool = False
    scratch: bool = True
    line_numbers: bool = False
    syntax_file: str = "Packages/${package}/lang/ToolRunner Output.tmLanguage"


@dataclass
class Placeholder:
    type: PlaceholderType
    argument: Optional[str] = None
    order: Optional[int] = None


@dataclass
class Tool:
    name: str
    cmd: List[str] = field(default_factory=list)
    arguments: List[str] = field(default_factory=list)
    shell: bool = False
    input: Input = field(default_factory=Input)
    output: Output = field(default_factory=Output)
    placeholders: Dict[str, Placeholder] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)


class InputProvider(Protocol):
    @abstractmethod
    def get_input_text(self) -> str:
        raise NotImplementedError()


class OutputProvider(Protocol):
    @abstractmethod
    def writeline(self, line: str):
        raise NotImplementedError()


@dataclass()
class Command:
    tool: Tool
    input_provider: InputProvider
    output_provider: OutputProvider
    placeholders_values: Dict[str, PlaceholderValue] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)
    platform: str = sys.platform
    cwd: str = os.getcwd()


def get_command_array(
    command: Command, input_file=None, input_text=None, output_file=None
):
    positional_arguments = []
    named_arguments = []
    flag_arguments = []

    if command.placeholders_values:
        for placeholder_key, placeholder_value in command.placeholders_values.items():
            param = command.tool.placeholders.get(placeholder_key, None)

            if param is None:
                raise Exception(
                    f"Tool {command.tool.name} doesn't have a parameter {placeholder_key}"
                )

            if param.type == "positional":
                positional_arguments.append(placeholder_value)
            elif param.type == "named":
                named_arguments.append(param.argument)
                named_arguments.append(placeholder_value)
            elif param.type == "flag":
                if placeholder_value:
                    flag_arguments.append(param.argument)

    full_command_template: List[str] = [] + command.tool.cmd + command.tool.arguments
    full_command = []

    for argument in full_command_template:
        if argument == "$[toolrunner_positional_arguments]":
            full_command += positional_arguments

        elif argument == "$[toolrunner_named_arguments]":
            full_command += named_arguments

        elif argument == "$[toolrunner_flag_arguments]":
            full_command += flag_arguments

        elif argument == "$[toolrunner_input_file]":
            full_command += [input_file]

        elif argument == "$[toolrunner_input_text]":
            full_command += [input_text]

        elif argument == "$[toolrunner_output_file]":
            full_command += [output_file]

        else:
            full_command.append(argument)

    return full_command


def get_command_input(command: Command):
    input_fd: TextIO
    input_file = None
    input_text = ""
    input_stream = b""

    if command.tool.input.is_file():
        (input_osd, input_file) = tempfile.mkstemp(
            prefix=TEMPFILE_PREFIX, suffix=command.tool.input.file_suffix
        )

        input_fd = os.fdopen(input_osd, mode="w", encoding=command.tool.input.codec)
        input_fd.write(command.input_provider.get_input_text())
        input_fd.close()

    if command.tool.input.is_pipe():
        input_stream = command.input_provider.get_input_text().encode(
            command.tool.input.codec
        )

    if command.tool.input.is_commandline():
        input_text = command.input_provider.get_input_text()

    return (
        input_file,
        input_text,
        input_stream,
    )


def get_command_output(command: Command):
    output_file = None
    output_fd = None

    if command.tool.output.mode == "tmpfile-path":
        (osd, output_file) = tempfile.mkstemp(prefix=TEMPFILE_PREFIX)
        output_fd = os.fdopen(osd, mode="r", encoding=command.tool.output.codec)

    return output_file, output_fd


def run_command(command: Command, on_exit_callback: Optional[Callable[[int], None]]):
    (input_file, input_text, input_stream) = get_command_input(command)
    (output_file, output_fd) = get_command_output(command)

    command_array = get_command_array(
        command=command,
        input_file=input_file,
        input_text=input_text,
        output_file=output_file,
    )
    _logger.info("Command to run: %s", command_array)

    environment = {}
    environment.update(os.environ)
    environment.update(command.tool.environment)
    environment.update(command.environment)

    startupinfo = None
    if command.platform == "windows":
        if command.output_provider is not None:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.CREATE_NEW_CONSOLE
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    try:
        tool_process = subprocess.Popen(
            args=command_array,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=environment,
            shell=command.tool.shell,
            startupinfo=startupinfo,
            cwd=command.cwd,
        )
    except FileNotFoundError as err:
        raise Exception(f"Executable not found: {err}")

    command.output_provider.writeline("> Process started\n")
    assert tool_process.stdin is not None

    _logger.info("Feeding input")

    tool_process.stdin.write(input_stream)
    tool_process.stdin.close()

    cancel_event = threading.Event()

    def subprocess_thread():
        assert tool_process.stdout is not None

        command.output_provider.writeline("> Reading stdout\n")
        while line := tool_process.stdout.readline():
            if cancel_event.is_set():
                pass
                ### ?? tool_process.stdout.close()
            command.output_provider.writeline(line.decode(command.tool.output.codec))
        tool_process.wait()
        command.output_provider.writeline("> Process finished\n")

        if on_exit_callback is not None:
            on_exit_callback(tool_process.returncode)

    # subprocess_thread()
    th = threading.Thread(target=subprocess_thread, daemon=True)
    th.start()
    # th.join()


def pipe_line(line: str, output_provider: OutputProvider):
    output_provider.writeline(line)
