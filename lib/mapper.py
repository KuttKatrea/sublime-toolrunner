import logging
import os.path
import re
from enum import Enum
from functools import partial
from typing import Dict, Literal, Optional, Union

import sublime
import sublime_plugin

from . import better_settings, engine, settings, util


class InputSource(str, Enum):
    NONE = "none"
    SELECTION = "selection"
    AUTO_LINE = "auto-line"
    LINE = "line"
    AUTO_BLOCK = "auto-block"
    BLOCK = "block"
    AUTO_FILE = "auto-file"
    FILE = "file"
    SCOPE = "scope"
    AUTO_SCOPE = "auto-scope"


OutputTarget = dict

command = None

basepackage = re.sub(r"\.lib$", "", __package__)
pluginname = "ToolRunner"

_logger = logging.getLogger("ToolRunner:Mapper")

TR_SETTING_TARGET_OUTPUT_NAME = "tr-target-output-name"
TR_SETTING_IS_OUTPUT = "tr-is-output"
TR_SETTING_OUTPUT_ID = "tr-output-id"
TR_SETTING_SOURCE_VIEW_ID = "tr-source-view-id"


def create_input_provider_from(source_view: sublime.View, input_source: InputSource):
    if input_source is None:
        input_source = InputSource.AUTO_FILE

    if input_source not in frozenset(
        {
            InputSource.NONE,
            "selection",
            "auto-line",
            "line",
            "auto-block",
            "block",
            "auto-file",
            "file",
        }
    ):
        raise ValueError("Input source invalid")

    if input_source == InputSource.NONE:
        return ""

    active_view = source_view

    input_text = ""
    source = InputSource.NONE

    current_selection = active_view.sel()
    syntax = active_view.syntax()
    ext = extract_extension(active_view.buffer().file_name())

    if input_source in {
        "selection",
        "auto-file",
        "auto-block",
        "auto-line",
        "auto-scope",
    }:
        if len(current_selection) > 0:
            for partial_selection in current_selection:
                input_text += active_view.substr(partial_selection)

            return InlineInputProvider(input_text, InputSource.SELECTION, syntax, ext)

    if input_source == InputSource.SELECTION:
        raise Exception("Nothing selected")

    if input_source in {InputSource.LINE, InputSource.AUTO_LINE}:
        source = InputSource.LINE
        region = active_view.line(current_selection[0])

    if input_source in {InputSource.BLOCK, InputSource.AUTO_BLOCK}:
        source = InputSource.BLOCK
        region = active_view.expand_by_class(
            current_selection[0], sublime.CLASS_EMPTY_LINE
        )

    if input_source in {InputSource.FILE, InputSource.AUTO_FILE}:
        source = InputSource.FILE
        region = sublime.Region(0, active_view.size())

    if input_source in {InputSource.SCOPE, InputSource.AUTO_SCOPE}:
        source = InputSource.SCOPE
        region = active_view.extract_scope(current_selection[0])

    if region is None:
        raise Exception("Invalid input-source: {}".format(input_source))

    input_text = active_view.substr(region)

    if input_text != "" and input_text[-1] != "\n":
        input_text += "\n"

    return InlineInputProvider(input_text, source, syntax, ext)


def run_tool(
    cmd: sublime_plugin.WindowCommand,
    tool_id: str,
    input_source: InputSource,
    output: OutputTarget,
    *args,
    **kwargs,
):
    _logger.debug("Ignoring parameters %s, %s", args, kwargs)

    input_provider = create_input_provider_from(cmd.window.active_view(), input_source)

    _logger.info("Input: %s", input_provider)

    tool_settings = settings.get_tool(tool_id)

    engine_tool = engine.Tool(
        name=tool_settings["name"],
        cmd=tool_settings["cmd"],
        input=engine.Input(**tool_settings.get("input", {})),
        output=engine.Output(**tool_settings.get("output", {})),
        placeholders=tool_settings.get("placeholders", {}),
    )

    engine_cmd = engine.Command(
        tool=engine_tool,
        input_provider=InlineInputProvider(input_provider),
        output_provider=create_output_provider(cmd, output),
        placeholders_values={},
        environment={"PYTHONUNBUFFERED": "1"},
        platform=sublime.platform(),
    )

    def callback():
        engine.run_command(engine_cmd)

    sublime.set_timeout_async(callback, 0)


def run_profile(
    cmd: sublime_plugin.WindowCommand,
    group: str,
    profile: str,
    input_source: InputSource,
):
    pass


def ask_profile_and_run_command(group: str):
    callback = partial(_on_ask_profile_done)


def ask_type_to_run(cmd: sublime_plugin.WindowCommand, group: str):
    def on_ask_type_done(selected_index):
        if selected_index == 0:
            sublime.set_timeout(
                partial(
                    self._ask_tool_to_run, partial(self._on_ask_tool_done, command)
                ),
                0,
            )

        elif selected_index == 1:
            sublime.set_timeout(
                partial(
                    self._ask_group_and_profile_to_run,
                    partial(self._on_ask_group_done, command),
                ),
                0,
            )

    cmd.window.show_quick_panel(["Tool", "Group"], on_ask_type_done, 0, 0, None)


def _ask_tool_to_run(self, callback):
    tool_list = []
    tool_selection_list = []

    def_tool_list = settings.get_tools()

    if len(def_tool_list) <= 0:
        sublime.error_message("There are no tools configured")
        return

    _logger.info("Creating Tools item list for Quick Panel: %s", def_tool_list)

    for single_tool in def_tool_list:
        _logger.info("Tool: %s", single_tool)
        tool_name = single_tool.get("name", single_tool.get("cmd"))
        tool_list.append(tool_name)

        desc = single_tool.get("desc")

        if desc is not None:
            tool_selection_list.append(desc + " (" + tool_name + ")")
        else:
            tool_selection_list.append(tool_name)

    callback = partial(callback, tool_list)

    self.window.show_quick_panel(tool_selection_list, callback, 0, 0, None)


def _on_ask_tool_done(self, command, tool_list, selected_index):
    tool_selected = tool_list[selected_index]

    if selected_index > -1:
        command.run_tool(tool_selected)


def _ask_group_and_profile_to_run(self, callback):
    group_list = [single_group["name"] for single_group in settings.get_groups()]

    if len(group_list) <= 0:
        sublime.error_message("There are no groups configured")
    else:
        callback = partial(callback, group_list)

        self.window.show_quick_panel(group_list, callback, 0, 0, None)


def _on_ask_group_done(self, command, group_list, selected_index):
    group_selected = group_list[selected_index]

    if selected_index >= 0:
        callback = partial(self._on_ask_profile_done, command)
        sublime.set_timeout(
            partial(self._ask_profile_and_run_command, group_selected, callback), 0
        )


def _ask_profile_and_run_command(self, group_selected, callback):
    profiles = settings.get_profiles(group_selected)

    if len(profiles) <= 0:
        sublime.error_message("This group has no profiles configured")
        return

    profile_list = [profile["name"] for profile in profiles]

    self.window.show_quick_panel(
        profile_list, partial(callback, group_selected, profile_list), 0, 0, None
    )


def _on_ask_profile_done(self, command, group_selected, profile_list, selected_index):
    if selected_index >= 0:
        selected_profile = profile_list[selected_index]
        command.run_profile(group_selected, selected_profile)


class InlineInputProvider(engine.InputProvider):
    def __init__(
        self,
        input_text: str,
        source: InputSource,
        scope: Optional[sublime.Syntax],
        ext: Optional[str],
    ):
        self._input_text = input_text
        self.source = source
        self.scope = scope
        self.ext = ext

    def get_input_text(self):
        return self._input_text


class ConsoleOutputProvider(engine.OutputProvider):
    def writeline(self, line: str):
        logging.info(line.rstrip())


class ViewOutputProvider(engine.OutputProvider):
    def __init__(self, target_view: sublime.View) -> None:
        super().__init__()
        self._target_view = target_view

    def writeline(self, line: str):
        line = line.replace("\r\n", "\n")

        _logger.info("Writing: %s", line)
        # self._target_view.run_command("move_to", {"to": "eof"})

        read_only = self._target_view.is_read_only()

        if read_only:
            self._target_view.set_read_only(False)

        self._target_view.run_command("append", {"characters": line})

        if read_only:
            self._target_view.set_read_only(True)


def find_view_by_id(view_id):
    for w in sublime.windows():
        for v in w.views():
            if str(v.id()) == view_id:
                return v

    return None


def create_output_provider(cmd: sublime_plugin.WindowCommand, output: Dict[str, str]):
    source_view = cmd.window.active_view()

    source_view_id = str(source_view.id())
    target_view_name = source_view.settings().get(TR_SETTING_TARGET_OUTPUT_NAME)

    target_view = (
        cmd.window.find_output_panel(target_view_name) if target_view_name else None
    )

    if not target_view:
        target_view_name = "ToolRunner Output (%s)" % source_view_id
        target_view = cmd.window.create_output_panel(target_view_name)
        target_view.settings().set(TR_SETTING_IS_OUTPUT, True)
        target_view.settings().set(TR_SETTING_OUTPUT_ID, target_view_name)
        target_view.settings().set(TR_SETTING_SOURCE_VIEW_ID, source_view_id)
        target_view.set_read_only(True)
        target_view_id = str(target_view.id())
        source_view.settings().set(TR_SETTING_TARGET_OUTPUT_NAME, target_view_name)

        _logger.info(
            "Created view with id %s as %s for view %s",
            target_view_id,
            target_view_name,
            source_view_id,
        )

    show_panel(cmd.window, target_view_name)
    target_view.set_name("ToolRunner Output for %s" % source_view.name())

    return ViewOutputProvider(target_view)


def focus_output(self: sublime_plugin.WindowCommand):
    source_view = self.window.active_view()

    target_view_name = source_view.settings().get(TR_SETTING_TARGET_OUTPUT_NAME, None)

    if target_view_name:
        show_panel(self.window, target_view_name)
    else:
        util.notify("This view don't have an output")


def focus_source(self: sublime_plugin.WindowCommand):
    target_window = self.window
    target_view = target_window.active_view()
    source_view_id = target_view.settings(TR_SETTING_SOURCE_VIEW_ID)

    if source_view_id is None:
        util.notify("This view is not an output")

    for view in target_window.views():
        if str(view.id()) == source_view_id:
            target_window.focus_view(view)
            return


def show_panel(window: sublime.Window, panel_name: str):
    window.run_command("show_panel", {"panel": "output." + panel_name})


def close_panel(window: sublime.Window, panel_name: str):
    window.destroy_output_panel(panel_name)


def on_pre_close_view(cmd: sublime_plugin.EventListener, view: sublime.View):
    target_output_name = view.settings().get(TR_SETTING_TARGET_OUTPUT_NAME, None)
    if target_output_name:
        close_panel(view.window(), target_output_name)


def run(
    self: sublime_plugin.WindowCommand,
    tool: Union[str, None],
    group: Union[str, None],
    profile: Union[str, None],
    default_profile: bool,
    input_source: InputSource,
    output_target: OutputTarget,
):
    if input_source is None:
        input_source = InputSource.BLOCK

    if output_target is None:
        output_target = {type: "panel"}

    _logger.info(
        "RUN %s/%s/%s/%s/%s", tool, group, profile, default_profile, input_source
    )

    input_provider = create_input_provider_from(self.window.active_view(), input_source)

    if tool is not None:
        tool = discover_tool(input_provider)

    if tool is not None:
        run_tool(self, tool, input_source, output_target)
    elif group is not None:
        if default_profile:
            profile = settings.get_setting("default_profiles", default=dict()).get(
                group
            )
        if profile is not None:
            run_profile(self, group, profile, input_source)
        else:
            ask_profile_and_run_command(self, group, input_source)
    else:
        ask_type_to_run(self, group)


def extract_extension(file_name: Optional[str]) -> Optional[str]:
    if not file_name:
        return None

    return os.path.splitext(file_name)[1]


def discover_tool(input_provider: InlineInputProvider):
    scope_mapping = settings.get_scope_mapping()
    tool_id = scope_mapping.get(input_provider.scope)

    if tool_id:
        return tool_id

    file_name_ext_mapping = settings.get_file_name_ext_mapping()

    tool_id = file_name_ext_mapping.get(input_provider.ext, None)
    return tool_id
