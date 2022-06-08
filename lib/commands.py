import logging
from functools import partial
from typing import Callable, Optional, Union

import sublime
import sublime_plugin

from . import engine, mapper, settings, util

_logger = logging.getLogger("ToolRunner:Commands")

RunToolCallback = Callable[[str], None]
RunGroupCallback = Callable[[str, str], None]

SELECTED_TYPE_TOOL = 0
SELECTED_TYPE_GROUP = 1


def run(
    self: sublime_plugin.WindowCommand,
    tool: Union[str, None],
    group: Union[str, None],
    profile: Union[str, None],
    default_profile: bool,
    input_source: mapper.InputSource,
    output_target: mapper.OutputTarget,
    params: Optional[dict],
):
    if input_source is None:
        input_source = mapper.InputSource.BLOCK

    if output_target is None:
        output_target = {type: "panel"}

    if params is None:
        params = {}

    _logger.info(
        "RUN %s/%s/%s/%s/%s", tool, group, profile, default_profile, input_source
    )

    input_provider = mapper.create_input_provider_from(
        self.window.active_view(), input_source
    )

    if not tool:
        _logger.info("No tool specified, discovering...")
        tool, group = mapper.discover_tool(input_provider)

    _logger.info(f"Selected tool and group: {tool}, {group}")

    if tool is not None:
        run_tool(self, tool, input_provider, output_target, params)
    elif group is not None:
        if default_profile:
            profile = settings.get_default_profile(group)
        if profile is not None:
            run_profile(self, group, profile, input_provider, output_target)
        else:
            ask_profile_to_run(
                self,
                group,
                create_run_profile_callback(self, input_provider, output_target),
            )
    else:
        ask_type_to_run(
            self,
            create_run_tool_callback(self, input_provider, output_target),
            create_run_profile_callback(self, input_provider, output_target),
        )


def create_run_tool_callback(
    self: sublime_plugin.WindowCommand,
    input_provider: mapper.InlineInputProvider,
    output_target: mapper.OutputTarget,
) -> RunToolCallback:
    def run_tool_callback(tool: str):
        try:
            run_tool(self, tool, input_provider, output_target)
        except Exception as ex:
            _logger.exception("Error running tool on callback", exc_info=ex)
            util.notify(str(ex))

    return run_tool_callback


def create_run_profile_callback(
    self: sublime_plugin.WindowCommand,
    input_provider: mapper.InlineInputProvider,
    output_target: mapper.OutputTarget,
) -> RunGroupCallback:
    def run_profile_callback(group: str, profile: str):
        try:
            run_profile(self, group, profile, input_provider, output_target)
        except Exception as ex:
            _logger.exception("Error running profile on callback", exc_info=ex)
            util.notify(str(ex))

    return run_profile_callback


def run_tool(
    cmd: sublime_plugin.WindowCommand,
    tool_id: str,
    input_provider: engine.InputProvider,
    output: mapper.OutputTarget,
    placeholder_values: dict,
    *args,
    **kwargs,
):
    _logger.debug("Ignoring parameters %s, %s", args, kwargs)

    _logger.info("Input: %s", input_provider)

    tool_settings = settings.get_tool(tool_id)

    if tool_settings is None:
        raise Exception(f"Tool {tool_id} doesn't exists")

    util.notify(f"Running {tool_settings['name']}")

    engine_tool = engine.Tool(
        name=tool_settings["name"],
        cmd=tool_settings["cmd"],
        input=engine.Input(**tool_settings.get("input", {})),
        output=engine.Output(**tool_settings.get("output", {})),
        placeholders={
            key: engine.Placeholder(**value)
            for key, value in tool_settings.get("params", {}).items()
        },
    )

    engine_cmd = engine.Command(
        tool=engine_tool,
        input_provider=input_provider,
        output_provider=mapper.create_output_provider(cmd, output),
        placeholders_values=placeholder_values,
        environment={"PYTHONUNBUFFERED": "1"},
        platform=sublime.platform(),
    )

    def callback(return_code: int):
        if return_code != 0:
            util.notify("Command finished with error.")
        else:
            util.notify("Command finished successfully.")

    engine.run_command(engine_cmd, callback)


def run_profile(
    cmd: sublime_plugin.WindowCommand,
    group: str,
    profile: str,
    input_provider: engine.InputProvider,
    output: mapper.OutputTarget,
):
    group_descriptor = None
    profile_descriptor = None

    group_list = settings.get_groups()

    for single_group in group_list:
        if single_group["name"] == group:
            group_descriptor = single_group
            break

    for single_profile in group_descriptor["profiles"]:
        if single_profile["name"] == profile:
            profile_descriptor = single_profile

    _logger.info("Running command for profile: %s", profile_descriptor)

    tool_id = profile_descriptor.get("tool", group_descriptor.get("tool"))

    # self._desc = "%s/%s" % (selected_group, selected_profile)

    run_tool(
        cmd=cmd,
        tool_id=tool_id,
        input_provider=input_provider,
        output=output,
        placeholder_values=profile_descriptor.get("params", {}),
    )


def ask_type_to_run(
    cmd: sublime_plugin.WindowCommand,
    run_tool_callback: RunToolCallback,
    run_group_callback: RunGroupCallback,
):
    def on_ask_type_done(selected_index):
        if selected_index == SELECTED_TYPE_TOOL:
            sublime.set_timeout(
                partial(ask_tool_to_run, cmd, run_tool_callback),
                0,
            )

        elif selected_index == SELECTED_TYPE_GROUP:
            sublime.set_timeout(
                partial(ask_group_and_profile_to_run, cmd, run_group_callback),
                0,
            )

    cmd.window.show_quick_panel(["Tool", "Group"], on_ask_type_done, 0, 0, None)


def ask_tool_to_run(
    self: sublime_plugin.WindowCommand, on_tool_selected_callback: RunToolCallback
):
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

    def on_ask_tool_done(selected_index):
        tool_selected = tool_list[selected_index]

        if selected_index > -1:
            on_tool_selected_callback(tool_selected)

    self.window.show_quick_panel(tool_selection_list, on_ask_tool_done, 0, 0, None)


def ask_group_and_profile_to_run(
    self: sublime_plugin.WindowCommand, run_profile_callback: RunGroupCallback
):
    group_list = [single_group["name"] for single_group in settings.get_groups()]

    def ask_profile_and_run_command_callback(group_selected_index: int):
        def ask_profile_and_run_command():
            group_selected = group_list[group_selected_index]

            ask_profile_to_run(self, group_selected, run_profile_callback)

        sublime.set_timeout(ask_profile_and_run_command, 0)

    if len(group_list) <= 0:
        sublime.error_message("There are no groups configured")
    else:
        self.window.show_quick_panel(
            group_list, ask_profile_and_run_command_callback, 0, 0, None
        )


def ask_profile_to_run(
    self: sublime_plugin.WindowCommand,
    group: str,
    run_profile_callback: RunGroupCallback,
):
    profiles = settings.get_profiles(group)
    profile_list = [profile["name"] for profile in profiles]

    def on_profile_selected_callback(selected_index: int):
        def on_profile_selected():
            if selected_index >= 0:
                selected_profile_name = profile_list[selected_index]
                run_profile_callback(group, selected_profile_name)

        if len(profiles) <= 0:
            sublime.error_message("This group has no profiles configured")
            return

        sublime.set_timeout(on_profile_selected, 0)

    self.window.show_quick_panel(profile_list, on_profile_selected_callback, 0, 0, None)


def focus_output(self: sublime_plugin.WindowCommand):
    source_view = self.window.active_view()

    target_view_name = source_view.settings().get(
        mapper.TR_SETTING_TARGET_OUTPUT_NAME, None
    )

    if target_view_name:
        mapper.show_panel(self.window, target_view_name)
    else:
        util.notify("This view don't have an output")


def focus_source(self: sublime_plugin.WindowCommand):
    target_window = self.window
    target_view = target_window.active_view()
    source_view_id = target_view.settings().get(mapper.TR_SETTING_SOURCE_VIEW_ID, None)

    if source_view_id is None:
        util.notify("This view is not an output")

    for view in target_window.views():
        if str(view.id()) == source_view_id:
            target_window.focus_view(view)
            return


def on_pre_close_view(cmd: sublime_plugin.EventListener, view: sublime.View):
    target_output_name = view.settings().get(mapper.TR_SETTING_TARGET_OUTPUT_NAME, None)
    if target_output_name:
        mapper.close_panel(view.window(), target_output_name)
