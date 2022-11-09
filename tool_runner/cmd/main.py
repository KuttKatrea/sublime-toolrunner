import logging
from functools import partial
from typing import Callable, List, Optional, Union

import sublime
import sublime_plugin

from .. import debug, mapper, settings

RunToolCallback = Callable[[str], None]
RunGroupCallback = Callable[[str, str], None]

SELECTED_TYPE_TOOL = 0
SELECTED_TYPE_GROUP = 1

_logger = logging.getLogger(f"{__package__}.{__name__}")


class ToolRunner(sublime_plugin.WindowCommand):
    @debug.notify_on_error("Error running")
    def run(
        self,
        tool: Union[str, None] = None,
        group: Union[str, None] = None,
        profile: Union[str, None] = None,
        default_profile: bool = False,
        input_source: Optional[str] = None,
        output_target: Optional[dict] = None,
        params: Optional[dict] = None,
        environment: Optional[dict] = None,
        cwd_sources: Optional[List[dict]] = None,
        *args,
        **kwargs,
    ):
        debug.log_unused_args(*args, **kwargs)

        _logger.info(
            "RUN %s/%s/%s/%s/%s", tool, group, profile, default_profile, input_source
        )

        if not tool and not group:
            _logger.info("No tool specified, discovering...")
            active_view = self.window.active_view()
            assert active_view
            tool, group = mapper.discover_tool(active_view)

        _logger.info("Selected tool and group: %s, %s", tool, group)

        if tool is not None:
            mapper.run_tool(
                cmd=self,
                tool_id=tool,
                input_source=input_source,
                output_target=output_target,
                placeholder_values=params,
                environment=environment,
                cwd_sources=cwd_sources,
            )
        elif group is not None:
            if default_profile:
                profile = settings.get_default_profile(group)

            if profile is not None:
                mapper.run_group(
                    self,
                    group_id=group,
                    profile=profile,
                    input_source=input_source,
                    output_target=output_target,
                    environment=environment,
                    cwd_sources=cwd_sources,
                )
            else:
                ask_profile_to_run(
                    self,
                    group,
                    create_run_group_callback(
                        self, input_source, output_target, environment, cwd_sources
                    ),
                )
        else:
            ask_type_to_run(
                self,
                create_run_tool_callback(
                    self, input_source, output_target, environment, cwd_sources
                ),
                create_run_group_callback(
                    self, input_source, output_target, environment, cwd_sources
                ),
            )


def create_run_tool_callback(
    self: sublime_plugin.WindowCommand,
    input_source: Optional[str],
    output_target: Optional[dict],
    environment: Optional[dict],
    cwd_sources: Optional[List[dict]],
) -> RunToolCallback:
    @debug.notify_on_error("Error running tool on callback")
    def run_tool_callback(tool: str):
        mapper.run_tool(
            self,
            tool_id=tool,
            input_source=input_source,
            output_target=output_target,
            environment=environment,
            cwd_sources=cwd_sources,
        )

    return run_tool_callback


def create_run_group_callback(
    self: sublime_plugin.WindowCommand,
    input_source: Optional[str],
    output_target: Optional[dict],
    environment: Optional[dict],
    cwd_sources: Optional[List[dict]],
) -> RunGroupCallback:
    @debug.notify_on_error("Error running profile on callback")
    def run_group_callback(group: str, profile: str):
        mapper.run_group(
            self,
            group_id=group,
            profile=profile,
            input_source=input_source,
            output_target=output_target,
            environment=environment,
            cwd_sources=cwd_sources,
        )

    return run_group_callback


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
            tool_selection_list.append(f"{desc} ({tool_name})")
        else:
            tool_selection_list.append(tool_name)

    def on_ask_tool_done(selected_index):
        tool_selected = tool_list[selected_index]

        if selected_index > -1:
            on_tool_selected_callback(tool_selected)

    self.window.show_quick_panel(tool_selection_list, on_ask_tool_done, 0, 0, None)


def ask_group_and_profile_to_run(
    self: sublime_plugin.WindowCommand, run_group_callback: RunGroupCallback
):
    group_list = [single_group["name"] for single_group in settings.get_groups()]

    def ask_profile_and_run_command_callback(group_selected_index: int):
        def ask_profile_and_run_command():
            group_selected = group_list[group_selected_index]

            ask_profile_to_run(self, group_selected, run_group_callback)

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
    run_group_callback: RunGroupCallback,
):
    profiles = settings.get_profiles(group)
    profile_list = [profile["name"] for profile in profiles]

    def on_profile_selected_callback(selected_index: int):
        def on_profile_selected():
            if selected_index >= 0:
                selected_profile_name = profile_list[selected_index]
                run_group_callback(group, selected_profile_name)

        if len(profiles) <= 0:
            sublime.error_message("This group has no profiles configured")
            return

        sublime.set_timeout(on_profile_selected, 0)

    self.window.show_quick_panel(profile_list, on_profile_selected_callback, 0, 0, None)
