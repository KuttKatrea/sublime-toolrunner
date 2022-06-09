import logging
import os.path
import re
from enum import Enum
from typing import Dict, List, NamedTuple, Optional, Tuple

import sublime
import sublime_plugin

from . import engine, settings


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

basepackage = re.sub(r"\.lib$", "", __package__)
pluginname = "ToolRunner"

_logger = logging.getLogger("ToolRunner:Mapper")

TR_SETTING_TARGET_OUTPUT_NAME = "tr-target-output-name"
TR_SETTING_IS_OUTPUT = "tr-is-output"
TR_SETTING_OUTPUT_ID = "tr-output-id"
TR_SETTING_SOURCE_VIEW_ID = "tr-source-view-id"


class InlineInputProvider(engine.InputProvider):
    def __init__(self, input_text: str, source: InputSource):
        self._input_text = input_text
        self.source = source

    def get_input_text(self):
        return self._input_text

    def __repr__(self):
        return "{}(source={},input_text={})".format(
            self.__class__,
            self.source,
            self._input_text[slice(-10, None)],
        )


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

        self._target_view.show(self._target_view.size())


class SelectionScope(NamedTuple):
    scopes: List[str]
    ext: str


def get_scopes(source_view: sublime.View, current_selection: sublime.Region):
    scopes = [
        scope
        for scope in source_view.scope_name(current_selection.a).split(" ")
        if scope.startswith("source.")
    ]
    ext = extract_extension(source_view.buffer().file_name())

    return SelectionScope(scopes, ext)


def create_input_provider_from(
    source_view: sublime.View, input_source: InputSource
) -> InlineInputProvider:
    _logger.info("Input source: %s", input_source)

    current_selection = source_view.sel()[0]
    selection_scope = get_scopes(source_view, current_selection)

    if input_source is None:
        input_source = InputSource.AUTO_FILE

    region = None

    if input_source == InputSource.NONE:
        return InlineInputProvider("", input_source)

    if input_source in {
        InputSource.SELECTION,
        InputSource.AUTO_FILE,
        InputSource.AUTO_BLOCK,
        InputSource.AUTO_LINE,
        InputSource.AUTO_SCOPE,
    }:
        if len(current_selection) > 0:
            return InlineInputProvider(
                source_view.substr(current_selection), InputSource.SELECTION
            )

        if input_source == InputSource.SELECTION:
            raise Exception("Nothing selected")

    source = InputSource.NONE
    update_selection = False

    if input_source in {InputSource.FILE, InputSource.AUTO_FILE}:
        source = InputSource.FILE
        region = sublime.Region(0, source_view.size())

    if input_source in {InputSource.LINE, InputSource.AUTO_LINE}:
        source = InputSource.LINE
        region = source_view.line(current_selection)
        update_selection = True

    if input_source in {InputSource.BLOCK, InputSource.AUTO_BLOCK}:
        source = InputSource.BLOCK
        region = source_view.expand_by_class(
            current_selection, sublime.CLASS_EMPTY_LINE
        )
        region.a += 1
        region.b -= 1
        update_selection = True

    if input_source in {InputSource.SCOPE, InputSource.AUTO_SCOPE}:
        source = InputSource.SCOPE
        if not selection_scope.scopes:
            raise Exception("No valid scope found (scopes should be source.xxx).")
        region = _expand_to_scope(
            source_view, current_selection.a, selection_scope.scopes[0]
        )
        update_selection = True

    if update_selection:

        def selection_update():
            source_view.sel().clear()
            source_view.sel().add(region)

        sublime.set_timeout(selection_update, 0)

    if region is None:
        raise Exception(f"Invalid input-source: {input_source}")

    input_text = source_view.substr(region)

    if input_text != "" and input_text[-1] != "\n":
        input_text += "\n"

    return InlineInputProvider(input_text, source)


def find_view_by_id(view_id):
    for w in sublime.windows():
        for v in w.views():
            if str(v.id()) == view_id:
                return v

    return None


def create_output_provider(cmd: sublime_plugin.WindowCommand, output: Dict[str, str]):
    _logger.info(f"Output configuration: {output}")

    source_view = cmd.window.active_view()

    source_view_id = str(source_view.id())
    target_view_name = source_view.settings().get(TR_SETTING_TARGET_OUTPUT_NAME)

    target_view = (
        cmd.window.find_output_panel(target_view_name) if target_view_name else None
    )

    if not target_view:
        target_view_name = f"ToolRunner Output ({source_view_id})"
        target_view = cmd.window.create_output_panel(target_view_name)
        target_view.settings().set(TR_SETTING_IS_OUTPUT, True)
        target_view.settings().set(TR_SETTING_OUTPUT_ID, target_view_name)
        target_view.settings().set(TR_SETTING_SOURCE_VIEW_ID, source_view_id)
        target_view.settings().set("line_numbers", False)
        target_view.settings().set("translate_tabs_to_spaces", False)
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
    target_view.set_name(f"ToolRunner Output for {source_view.name()}")

    return ViewOutputProvider(target_view)


def extract_extension(file_name: Optional[str]) -> Optional[str]:
    if not file_name:
        return None

    pieces = os.path.splitext(file_name)
    # TODO: Empty extension
    return pieces[1][1:]


def discovered_as_tuple(data: Optional[dict]) -> Tuple[Optional[str], Optional[str]]:
    if not data:
        return (
            None,
            None,
        )

    if "tool" in data:
        return (
            data["tool"],
            None,
        )

    if "group" in data:
        return (
            None,
            data["group"],
        )


def discover_tool(source_view: sublime.View) -> Tuple[str, str]:
    current_selection = source_view.sel()[0]
    selection_scope = get_scopes(source_view, current_selection)
    _logger.info("Discovering tool from %s", selection_scope)

    scope_mapping = settings.get_scopes_mapping()
    _logger.info("Scope mappings: %s", scope_mapping)

    for scope in selection_scope.scopes:
        tool_data = scope_mapping.get(scope)  # type: dict

        if tool_data:
            return discovered_as_tuple(tool_data)

    file_name_ext_mapping = settings.get_extensions_mapping()
    _logger.info("File Ext mappings: %s", file_name_ext_mapping)

    tool_data = file_name_ext_mapping.get(selection_scope.ext, None)

    return discovered_as_tuple(tool_data)


def _expand_to_scope(source_view: sublime.View, point: "sublime.Point", scope: str):
    # source_view.expand_to_scope(current_selection[0].a, scopes[0])
    start = point
    end = point
    for check_point in range(point, 0 - 1, -1):
        if source_view.match_selector(check_point, scope):
            start = check_point
        else:
            break

    for check_point in range(point, source_view.size(), 1):
        if source_view.match_selector(check_point, scope):
            end = check_point
        else:
            break

    return sublime.Region(start, end)


def show_panel(window: sublime.Window, panel_name: str):
    window.run_command("show_panel", {"panel": "output." + panel_name})


def close_panel(window: sublime.Window, panel_name: str):
    window.destroy_output_panel(panel_name)
