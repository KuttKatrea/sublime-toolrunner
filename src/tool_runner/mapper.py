import dataclasses
import logging
import os
import os.path
import re
import tempfile
from enum import Enum
from typing import Any, Dict, List, NamedTuple, Optional, Tuple, Union, cast

import sublime
import sublime_plugin

from . import engine, settings, util

CELL_X1 = 0
CELL_Y1 = 1
CELL_X2 = 2
CELL_Y2 = 3


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


class OutputTargetMode(str, Enum):
    NONE = "none"
    PANEL = "panel"
    BUFFER = "buffer"


class OutputTargetPosition(str, Enum):
    BOTTOM = "bottom"
    RIGHT = "right"


@dataclasses.dataclass
class OutputTarget:
    mode: OutputTargetMode = OutputTargetMode.PANEL
    position: OutputTargetPosition = OutputTargetPosition.BOTTOM
    syntax: str = "scope:tool-runner.output"


class CwdStrategy(str, Enum):
    UNSPECIFIED = "unspecified"
    PROJECT_FILE_DIR = "project-file-dir"
    PROJECT_FOLDER = "project-folder"
    PROJECT_SOURCE_FILE_FOLDER = "project-source-file-folder"
    SOURCE_FILE_DIR = "source-file-dir"
    DISCOVER = "discover"
    HOME = "home"
    TMP = "tmp"


@dataclasses.dataclass
class CwdSource:
    strategy: CwdStrategy
    discovery_patterns: List[str] = dataclasses.field(default_factory=list)
    folder_index: int = 0


_logger = logging.getLogger(f"{__package__}.{__name__}")

TR_SETTING_TARGET_OUTPUT_ID = "tr-target-output-id"
TR_SETTING_IS_OUTPUT = "tr-is-output"
TR_SETTING_OUTPUT_ID = "tr-output-id"
TR_SETTING_SOURCE_VIEW_ID = "tr-source-view-id"


class InlineInputProvider(engine.InputProvider):
    def __init__(self, input_text: str, source: InputSource):
        self._input_text = input_text
        self.source = source

    def get_input_text(self) -> str:
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


class NullOutputProvider(engine.OutputProvider):
    def writeline(self, line: str):
        pass

    def scroll_to_start(self):
        pass


class ViewOutputProvider(engine.OutputProvider):
    def __init__(self, target_view: sublime.View, start_point: "sublime.Point") -> None:
        super().__init__()
        self._target_view = target_view
        self._start_point = start_point

    def scroll_to_start(self):
        viewport_position = self._target_view.text_to_layout(self._start_point)
        self._target_view.set_viewport_position(viewport_position)

    def writeline(self, line: str):
        line = line.replace("\r\n", "\n")

        _logger.info("Writing: %s", line)

        _logger.info("Selection: %s", self._target_view.sel())

        read_only = self._target_view.is_read_only()

        if read_only:
            self._target_view.set_read_only(False)

        self._target_view.run_command("append", {"characters": line})

        if read_only:
            self._target_view.set_read_only(True)

        if self._target_view != self._target_view.window().active_view():
            self._target_view.run_command("move_to", {"to": "eof"})

        #    self._target_view.show(self._target_view.size())


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
        # region.a += 1
        # region.b -= 1
        update_selection = True

    if input_source in {InputSource.SCOPE, InputSource.AUTO_SCOPE}:
        source = InputSource.SCOPE
        if not selection_scope.scopes:
            raise Exception("No valid scope found (scopes should be source.xxx).")
        region = _expand_to_scope(
            source_view, current_selection.a, selection_scope.scopes[0]
        )
        update_selection = True

    if region is None:
        raise Exception(f"Invalid input-source: {input_source}")

    if update_selection:

        def selection_update():
            source_view.sel().clear()
            source_view.sel().add(region)

        sublime.set_timeout(selection_update, 0)

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


def create_output_provider(
    cmd: sublime_plugin.WindowCommand, output_target: OutputTarget
):
    _logger.info(f"Output configuration: {output_target}")

    if output_target.mode == OutputTargetMode.NONE:
        return NullOutputProvider()

    if output_target.mode == OutputTargetMode.PANEL:
        return get_panel_output_provider(cmd, output_target)

    if output_target.mode == OutputTargetMode.BUFFER:
        return get_buffer_output_provider(cmd, output_target)

    raise Exception(f"Unknown output target {output_target}")


def extract_extension(file_name: Optional[str]) -> str:
    if not file_name:
        return ""

    pieces = os.path.splitext(file_name)
    # TODO: Empty extension
    return pieces[1][1:]


def discovered_as_tuple(
    data: Optional[Dict[str, Any]]
) -> Tuple[Optional[str], Optional[str]]:
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

    raise Exception("No tool or group key in dict")


def discover_tool(source_view: sublime.View) -> Tuple[Optional[str], Optional[str]]:
    current_selection = source_view.sel()[0]
    selection_scope = get_scopes(source_view, current_selection)
    _logger.info("Discovering tool from %s", selection_scope)

    scope_mapping = settings.get_scopes_mapping()
    _logger.info("Scope mappings: %s", scope_mapping)

    for scope in selection_scope.scopes:
        tool_data = scope_mapping.get(scope)

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


def run_tool(
    cmd: sublime_plugin.WindowCommand,
    tool_id: str,
    desc: Optional[str] = None,
    input_source: Optional[str] = None,
    output_target: Optional[Dict[str, Any]] = None,
    placeholder_values: Optional[Dict[str, Union[str, bool]]] = None,
    cwd_sources: Optional[List[Dict[str, str]]] = None,
    environment: Optional[Dict[str, str]] = None,
):
    if input_source is None:
        input_source = InputSource.AUTO_FILE

    output_target = util.merge_maps_as_new(
        settings.get_default_output_target(), output_target
    )

    if cwd_sources is None:
        cwd_sources = settings.get_default_cwd_sources() or []

    if environment is None:
        environment = {}

    _logger.info(
        "Running tool: tool_id=%s desc=%s input_source=%s output_target=%s placeholder_values=%s cwd_sources=%s environment=%s",
        tool_id,
        desc,
        input_source,
        output_target,
        placeholder_values,
        cwd_sources,
        environment,
    )

    source_view = cmd.window.active_view()

    assert source_view

    input_provider = create_input_provider_from(source_view, InputSource(input_source))

    output_provider = create_output_provider(cmd, OutputTarget(**output_target))

    cwd = get_usable_cwd_from(
        cmd, [CwdSource(**cwd_source) for cwd_source in cwd_sources]
    )

    tool_settings = settings.get_tool(tool_id)

    if tool_settings is None:
        raise Exception(f"Tool {tool_id} doesn't exists")

    if not desc:
        desc = cast(str, tool_settings["name"])

    util.notify(f"Running {desc}")

    engine_tool = engine.Tool(
        name=tool_settings.get("name"),
        cmd=tool_settings.get("cmd", [tool_id]),
        arguments=tool_settings.get("arguments", []),
        input=engine.Input(**tool_settings.get("input", {})),
        output=engine.Output(**tool_settings.get("output", {})),
        placeholders={
            key: engine.Placeholder(**value)
            for key, value in tool_settings.get("params", {}).items()
        },
        environment=tool_settings.get("environment", {}),
    )

    engine_cmd = engine.Command(
        tool=engine_tool,
        input_provider=input_provider,
        output_provider=output_provider,
        placeholders_values=placeholder_values,
        environment=environment,
        platform=sublime.platform(),
        cwd=cwd,
    )

    def callback(return_code: int):
        if return_code != 0:
            util.notify("Command finished with error.")
        else:
            util.notify("Command finished successfully.")

        output_provider.scroll_to_start()

    engine.run_command(engine_cmd, callback)


def run_group(
    cmd: sublime_plugin.WindowCommand,
    group_id: str,
    profile: str,
    input_source: Optional[str],
    output_target: Optional[Dict[str, Any]],
    environment: Optional[Dict[str, str]],
    cwd_sources: Optional[List[Dict[str, str]]],
):
    group_descriptor = None
    profile_descriptor = None

    group_list = settings.get_groups()

    for single_group in group_list:
        if single_group["name"] == group_id:
            group_descriptor = single_group
            break

    if group_descriptor is None:
        raise Exception(f"No group named {group_id}")

    _logger.info("Running command for group: %s", group_descriptor)

    for single_profile in group_descriptor["profiles"]:
        if single_profile["name"] == profile:
            profile_descriptor = single_profile

    if profile_descriptor is None:
        raise Exception(f"No profile named {profile} for the group {group_id}")

    _logger.info("Running command for profile: %s", profile_descriptor)

    tool_id = profile_descriptor.get("tool", group_descriptor.get("tool"))

    input_source = (
        input_source
        or profile_descriptor.get("input_source")
        or group_descriptor.get("input_source")
    )

    output_target = util.merge_maps_as_new(
        group_descriptor.get("output_target"),
        profile_descriptor.get("output_target"),
        output_target,
    )

    cwd_sources = (
        cwd_sources
        or profile_descriptor.get("cwd_sources")
        or group_descriptor.get("cwd_sources")
    )

    environment = util.merge_maps_as_new(
        group_descriptor.get("environment"),
        profile_descriptor.get("environment"),
        environment,
    )

    run_tool(
        cmd=cmd,
        desc=f"{group_id}/{profile}",
        tool_id=tool_id,
        input_source=input_source,
        output_target=output_target,
        placeholder_values=profile_descriptor.get("params", {}),
        cwd_sources=cwd_sources,
        environment=environment,
    )


def get_usable_cwd_from(
    cmd: sublime_plugin.WindowCommand, cwd_sources: List[CwdSource]
) -> str:

    _logger.info("Testing: %s", cwd_sources)

    for k in cwd_sources:
        cwd = get_cwd_from(cmd, k)
        _logger.info("Testing: %s", k)
        if cwd is not None:
            _logger.info("Returning: %s", cwd)
            return cwd

    _logger.info("Returning CWD")
    return os.getcwd()


def get_cwd_from(
    cmd: sublime_plugin.WindowCommand, cwd_source: CwdSource
) -> Optional[str]:
    if cwd_source.strategy == CwdStrategy.PROJECT_FILE_DIR:
        project_filename = cmd.window.project_file_name()

        if not project_filename:
            _logger.info("No project opened")
            return None

        return os.path.dirname(project_filename)

    if cwd_source.strategy == CwdStrategy.PROJECT_FOLDER:
        folders = cmd.window.folders()
        if not folders:
            _logger.info("No folders opened")
            return None

        if len(folders) < cwd_source.folder_index:
            _logger.info(f"No folder with index {cwd_source.folder_index}")
            return None

        return folders[cwd_source.folder_index]

    if cwd_source.strategy == CwdStrategy.PROJECT_SOURCE_FILE_FOLDER:
        filename = get_active_filename(cmd)
        if not filename:
            return None

        for folder in cmd.window.folders():
            if folder in filename:
                return folder

        return None

    if cwd_source.strategy == CwdStrategy.SOURCE_FILE_DIR:
        filename = get_active_filename(cmd)
        if not filename:
            return None

        return os.path.dirname(filename)

    if cwd_source.strategy == CwdStrategy.DISCOVER:
        filename = get_active_filename(cmd)
        if not filename:
            return None

        return discover_path(os.path.dirname(filename), cwd_source.discovery_patterns)

    if cwd_source.strategy == CwdStrategy.HOME:
        return os.path.expanduser("~")

    if cwd_source.strategy == CwdStrategy.TMP:
        tempdir = os.path.join(tempfile.gettempdir(), "toolrunner")
        if not os.path.exists(tempdir):
            os.mkdir(tempdir)
        return tempdir

    return None


def get_active_filename(cmd: sublime_plugin.WindowCommand):
    active_view = cmd.window.active_view()
    assert active_view
    file_name = active_view.file_name()
    if not file_name:
        return None
    return file_name


def discover_path(current_dir: str, discovery_patterns: List[str]) -> Optional[str]:
    while current_dir:
        _logger.info("Testing %s for %s", current_dir, discovery_patterns)

        for item in os.listdir(current_dir):
            for pattern in discovery_patterns:
                _logger.info("Matching %s with %s", item, pattern)
                if re.fullmatch(pattern, item):
                    return current_dir

        new_current_dir = os.path.dirname(current_dir)
        if current_dir == new_current_dir:  # we are in root
            return None
        current_dir = new_current_dir

    return None


def get_panel_output_provider(
    cmd: sublime_plugin.WindowCommand, output_target: OutputTarget
):
    source_view = cmd.window.active_view()

    assert source_view

    source_view_id = str(source_view.id())
    target_view_id: str = cast(
        str, source_view.settings().get(TR_SETTING_TARGET_OUTPUT_ID)
    )

    target_view = (
        cmd.window.find_output_panel(target_view_id) if target_view_id else None
    )

    if not target_view:
        target_view_id = f"ToolRunner Output ({source_view_id})"  # Output panels are identified by a name

        target_view = cmd.window.create_output_panel(target_view_id)
        target_view.settings().set(TR_SETTING_IS_OUTPUT, True)
        target_view.settings().set(TR_SETTING_OUTPUT_ID, target_view_id)
        target_view.settings().set(TR_SETTING_SOURCE_VIEW_ID, source_view_id)
        target_view.settings().set("line_numbers", False)
        target_view.settings().set("translate_tabs_to_spaces", False)
        target_view.set_read_only(True)
        if output_target.syntax:
            target_view.assign_syntax(output_target.syntax)

        source_view.settings().set(TR_SETTING_TARGET_OUTPUT_ID, target_view_id)

        _logger.info(
            "Created view with id %s for view %s",
            target_view_id,
            source_view_id,
        )

        start_point = 0
    else:
        start_point = target_view.size()

    show_panel(cmd.window, target_view_id)
    target_view.set_name(f"ToolRunner Output for {source_view_id}")

    return ViewOutputProvider(target_view, start_point)


def get_buffer_output_provider(
    cmd: sublime_plugin.WindowCommand, output_target: OutputTarget
):
    source_view = cmd.window.active_view()

    assert source_view

    source_view_id = source_view.id()
    target_view_id = source_view.settings().get(TR_SETTING_TARGET_OUTPUT_ID)

    target_view = None

    if target_view_id is not None:
        _logger.info("Looking for target_view_id: %s", target_view_id)
        for view in cmd.window.views():
            if view.id() == target_view_id:
                _logger.info("Found: %s", view.name())
                target_view = view

    if not target_view:
        target_view_name = f"ToolRunner Output ({source_view_id})"

        target_view = create_output_buffer(cmd.window, source_view, output_target)
        target_view_id = target_view.id()

        target_view.settings().set(TR_SETTING_IS_OUTPUT, True)
        target_view.settings().set(TR_SETTING_OUTPUT_ID, target_view_id)
        target_view.settings().set(TR_SETTING_SOURCE_VIEW_ID, source_view_id)
        target_view.settings().set("line_numbers", False)
        target_view.settings().set("translate_tabs_to_spaces", False)
        target_view.set_read_only(True)
        target_view.set_scratch(True)

        if output_target.syntax:
            target_view.assign_syntax(output_target.syntax)

        source_view.settings().set(TR_SETTING_TARGET_OUTPUT_ID, target_view_id)

        _logger.info(
            "Created view with id %s as %s for view %s",
            target_view_id,
            target_view_name,
            source_view_id,
        )

        start_point = 0
    else:
        start_point = target_view.size()

    # cmd.window.focus_group()
    # cmd.window.focus_view(target_view)

    target_view.set_name(f"ToolRunner Output for {source_view_id}")

    return ViewOutputProvider(target_view, start_point)


def create_output_buffer(
    win: sublime.Window, view: sublime.View, output_target: OutputTarget
) -> sublime.View:
    group, idx = win.get_view_index(view)

    if output_target.position not in set(
        [
            OutputTargetPosition.RIGHT,
            OutputTargetPosition.BOTTOM,
        ]
    ):
        target = group
    else:
        layout = win.layout()

        target = get_existing_target(
            layout=layout, source_group=group, position=output_target.position
        )

        _logger.info("Found target: %s", target)

        if target is None:
            layout, target = create_layout_cell(
                layout=layout, source_group=group, position=output_target.position
            )

            _logger.info("Created layout and target: %s, %s", layout, target)

            win.set_layout(layout)

    win.focus_group(target)
    target_view = win.new_file()
    # group, idx = win.get_view_index(view)
    win.focus_group(group)

    return target_view


def get_existing_target(layout, source_group: int, position: OutputTargetPosition):
    source_cell = layout["cells"][source_group]

    if position == OutputTargetPosition.RIGHT:
        match_coords_cross = (CELL_X2, CELL_X1)
        match_coords_equal = (CELL_Y1, CELL_Y2)

    else:
        match_coords_cross = (CELL_Y2, CELL_Y1)
        match_coords_equal = (CELL_X1, CELL_X2)

    for idx, cell in enumerate(layout["cells"]):
        if idx == source_group:
            continue

        if cell[match_coords_cross[1]] == source_cell[match_coords_cross[0]]:
            if cell[match_coords_equal[0]] == source_cell[match_coords_equal[0]]:
                if cell[match_coords_equal[1]] == source_cell[match_coords_equal[1]]:
                    return idx

    return None


def create_layout_cell(layout, source_group, position):
    rows = layout["rows"]
    cols = layout["cols"]
    cells = layout["cells"]

    source_cell = cells[source_group]

    if position == OutputTargetPosition.RIGHT:
        KEEP_AXIS_1 = CELL_Y1
        KEEP_AXIS_2 = CELL_Y2
        SPLIT_AXIS_1 = CELL_X1
        SPLIT_AXIS_2 = CELL_X2

        list_to_split = cols
    else:
        KEEP_AXIS_1 = CELL_X1
        KEEP_AXIS_2 = CELL_X2
        SPLIT_AXIS_1 = CELL_Y1
        SPLIT_AXIS_2 = CELL_Y2

        list_to_split = rows

    abs_1 = list_to_split[source_cell[SPLIT_AXIS_1]]
    abs_2 = list_to_split[source_cell[SPLIT_AXIS_2]]

    split = abs_1 + (abs_2 - abs_1) * 2 / 3

    split_insert_position = [i for i, v in enumerate(list_to_split) if v > split][0]
    list_to_split.insert(split_insert_position, split)

    for cell in cells:
        if cell[SPLIT_AXIS_1] >= split_insert_position:
            cell[SPLIT_AXIS_1] += 1

        if cell[SPLIT_AXIS_2] >= split_insert_position:
            cell[SPLIT_AXIS_2] += 1

    source_position = source_cell[SPLIT_AXIS_2]

    source_cell[SPLIT_AXIS_2] = split_insert_position

    target = len(cells)

    new_cell = [0 for i in range(4)]

    new_cell[KEEP_AXIS_1] = source_cell[KEEP_AXIS_1]
    new_cell[KEEP_AXIS_2] = source_cell[KEEP_AXIS_2]
    new_cell[SPLIT_AXIS_1] = split_insert_position
    new_cell[SPLIT_AXIS_2] = source_position

    cells.append(new_cell)

    return {"rows": rows, "cols": cols, "cells": cells}, target
