from enum import IntEnum, IntFlag
from typing import Any, Callable, Dict, Iterator, List, Optional, Sequence, Tuple, Union

DIP = float
"""Represents a device-independent pixel position."""

Vector = Tuple[DIP, DIP]
"""Represents a X and Y coordinate."""

Point = int
"""Represents the offset from the beginning of the editor buffer."""

Value = Union[bool, str, int, float, List[Value], Dict[str, Value]]
"""A JSON-equivalent value."""

CommandArgs = Optional[Dict[str, Value]]
"""The arguments to a command may be None or a dict of str keys."""

Kind = Tuple[KindId, str, str]
"""Metadata about the kind of a symbol, CompletionItem, QuickPanelItem or ListInputItem. Controls the color and letter shown in the “icon” presented to the left of the item."""

Event = dict
"""
Contains information about a user’s interaction with a menu, command palette selection, quick panel selection or HTML document. The follow methods are used to signal that an event dict is desired:

- Commands may opt-in to receive an arg named event by implementing the method want_event(self) and returning True.
- A call to show_quick_panel() may opt-in to receive a second arg to the on_done callback by specifying the flag QuickPanelFlags.WANT_EVENT.
- ListInputHandler classes may opt-in to receive a second arg to the validate() and confirm() methods by by implementing the method want_event() and returning True.

The dict may contain zero or more of the following keys, based on the user interaction:

"x": float
  The X mouse position when a user clicks on a menu, or in a minihtml document.

"y": float
  The Y mouse position when a user clicks on a menu, or in a minihtml document.

"modifier_keys": dict
  Can have zero or more of the following keys:
  - "primary" - indicating Ctrl (Windows/Linux) or Cmd (Mac) was pressed
  - "ctrl" - indicating Ctrl was pressed
  - "alt" - indicating Alt was pressed
  - "altgr" - indicating AltGr was pressed (Linux only)
  - "shift" - indicating Shift was pressed
  - "super" - indicating Win (Windows/Linux) or Cmd (Mac) was pressed

Present when the user selects an item from a quick panel, selects an item from a ListInputHandler, or clicks a link in a minihtml document.
"""

CompletionValue = Union[str, Tuple[str, str], CompletionItem]
"""
Represents an available auto-completion item. completion values may be of several formats. The term trigger refers to the text matched against the user input, replacement is what is inserted into the view if the item is selected. An annotation is a unicode string hint displayed to the right-hand side of the trigger.
  - str:
    A string that is both the trigger and the replacement:

    [
        "method1()",
        "method2()",
    ]

  - 2-element tuple or list:
    A pair of strings - the trigger and the replacement:

    [
        ["me1", "method1()"],
        ["me2", "method2()"]
    ]

    If a t is present in the trigger, all subsequent text is treated as an annotation:

    [
        ["me1\tmethod", "method1()"],
        ["me2\tmethod", "method2()"]
    ]

    The replacement text may contain dollar-numeric fields such as a snippet does, e.g. $0, $1:

    [
        ["fn", "def ${1:name}($2) { $0 }"],
        ["for", "for ($1; $2; $3) { $0 }"]
    ]

  - CompletionItem object

    An object containing trigger, replacement, annotation, and kind metadata:

    [
        sublime.CompletionItem(
            "fn",
            annotation="def",
            completion="def ${1:name}($2) { $0 }",
            completion_format=sublime.COMPLETION_FORMAT_SNIPPET,
            kind=sublime.KIND_SNIPPET
        ),
        sublime.CompletionItem(
            "for",
            completion="for ($1; $2; $3) { $0 }",
            completion_format=sublime.COMPLETION_FORMAT_SNIPPET,
            kind=sublime.KIND_SNIPPET
        ),
    ]
"""

class Settings:
    """A dict like object that a settings hierarchy."""

    def __setitem__(self, key: str, value: Value):
        """Set the named key to the provided value."""
    def __getitem__(self, key: str) -> Value:
        """Get the named item to the provided value."""
    def __delitem__(self, key: str):
        """Deletes the provided key from the setting. Note that a parent setting may also provide this key, thus deleting may not entirely remove a key."""
    def __contains__(self, key: str) -> bool:
        """Returns whether the provided key is set."""
    def to_dict(self) -> dict:
        """Return the settings as a dict. This is not very fast."""
    def setdefault(self, key: str, value: Value):
        """Returns the value associated with the provided key. If it’s not present the provided value is assigned to the key and then returned."""
    def update(self, other=(), /, **kwargs):
        """
        Update the settings from the provided argument(s).

        Accepts:

            A dict or other implementation of collections.abc.Mapping.

            An object with a keys() method.

            An object that iterates over key/value pairs

            Keyword arguments, ie. update(**kwargs).
        """
    def has(self, key: str) -> bool:
        """Same as __contains__."""
    def set(self, key: str, value: Value):
        """Same as __setitem__."""
    def get(self, key: str, default: Value = None) -> Value:
        """Same as __getitem__."""
    def erase(self, key: str):
        """Same as __delitem__."""
    def add_on_change(self, tag: str, callback: Callable[[], None]):
        """
        Register a callback to be run whenever a setting is changed.

        Parameters

            tag

                A string associated with the callback. For use with clear_on_change.

            callback

                A callable object to be run when a setting is changed.
        """
    def clear_on_change(self, tag: str):
        """Remove all callbacks associated with the provided tag. See add_on_change."""

class Syntax:
    """Contains information about a syntax."""

    path: str
    """The packages path to the syntax file."""

    name: str
    """The name of the syntax."""

    hidden: bool
    """If the syntax is hidden from the user."""

    scope: str
    """The base scope name of the syntax."""

class QuickPanelItem:
    pass

class Window:
    def id(
        self,
    ) -> int:
        """
        :returns: A number that uniquely identifies this window.
        """
        ...
    def is_valid(
        self,
    ) -> bool:
        """
        Check whether this window is still valid. Will return False for a closed window, for example.
        """
        ...
    def hwnd(
        self,
    ) -> int:
        """
        :returns: A platform specific window handle. Windows only.
        """
        ...
    def active_sheet(
        self,
    ) -> Optional[Sheet]:
        """
        :returns: The currently focused Sheet.
        """
        ...
    def active_view(
        self,
    ) -> Optional[View]:
        """
        :returns: The currently edited View.
        """
        ...
    def new_html_sheet(
        self, name: str, contents: str, flags=NewFileFlags.NONE, group=-1
    ) -> Sheet:
        """
        Construct a sheet with HTML contents rendered using minihtml Reference.
        :param name: The name of the sheet to show in the tab.
        :param contents: The HTML contents of the sheet.
        :param flags: Only NewFileFlags.TRANSIENT and NewFileFlags.ADD_TO_SELECTION are allowed.
        :param group: The group to add the sheet to. -1 for the active group.
        """
        ...
    def run_command(self, cmd: str, args: CommandArgs = None):
        """
        Run the named WindowCommand with the (optional) given args. This method is able to run any sort of command, dispatching the command via input focus.
        """
        ...
    def new_file(self, flags=NewFileFlags.NONE, syntax="") -> View:
        """
        Create a new empty file.
        :param flags: Either 0 or NewFileFlags.TRANSIENT.
        :param syntax: The name of the syntax to apply to the file.
        :return: The view for the file.
        """
        ...
    def open_file(self, fname: str, flags=NewFileFlags.NONE, group=-1) -> View:
        """
        Open the named file. If the file is already opened, it will be brought to the front. Note that as file loading is asynchronous, operations on the returned view won’t be possible until its is_loading() method returns False.
        :param fname: The path to the file to open.
        :param flags: NewFileFlags
        :param group: The group to add the sheet to. -1 for the active group.
        :return:
        """
        ...
    def find_open_file(self, fname: str) -> Optional[View]:
        """
        Find a opened file by file name.
        :return: The View to the file or None if the file isn’t open.
        """
        ...
    def file_history(
        self,
    ) -> [str]:
        """
        Get the list of previously opened files. This is the same list as File > Open Recent.
        """
        ...
    def num_groups(
        self,
    ) -> int:
        """
        :return: The number of view groups in the window.
        """
        ...
    def active_group(
        self,
    ) -> int:
        """
        :return: The index of the currently selected group.
        """
        ...
    def focus_group(self, idx: int):
        """
        Focus the specified group, making it active.
        """
        ...
    def focus_sheet(self, sheet: Sheet):
        """
        Switches to the given Sheet.
        """
        ...
    def focus_view(self, view: View):
        """
        Switches to the given View.
        """
        ...
    def select_sheets(self, sheets: [Sheet]):
        """
        Change the selected sheets for the entire window.
        """
        ...
    def bring_to_front(
        self,
    ):
        """
        Bring the window in front of any other windows.
        """
        ...
    def get_sheet_index(self, sheet: Sheet):
        """
        :returns: The a tuple of the group and index within the group of the given Sheet.
        """
        ...
    def get_view_index(self, view: View):
        """
        :returns: The a tuple of the group and index within the group of the given View.
        """
        ...
    def set_sheet_index(self, sheet: Sheet, group: int, index: int):
        """
        Move the given Sheet to the given group at the given index.
        """
        ...
    def set_view_index(self, view: View, group: int, index: int):
        """
        Move the given View to the given group at the given index.
        """
        ...
    def move_sheets_to_group(
        self, sheets: [Sheet], group: int, insertion_idx=-1, select=True
    ):
        """
         Moves all provided sheets to specified group at insertion index provided. If an index is not provided defaults to last index of the destination group.
        :param sheets: The sheets to move.
        :param group: The index of the group to move the sheets to.
        :param insertion_idx: The point inside the group at which to insert the sheets.
        :param select: Whether the sheets should be selected after moving them.
        """
        ...
    def sheets(
        self,
    ) -> [Sheet]:
        """
        :return: All open sheets in the window.
        """
        ...
    def views(self, *, include_transient=False) -> [View]:
        """
        :param include_transient:  Whether the transient sheet should be included.
        :return: All open sheets in the window.
        """
        ...
    def selected_sheets(
        self,
    ) -> [Sheet]:
        """
        :return: All selected sheets in the window.
        """
        ...
    def selected_sheets_in_group(self, group: int) -> [Sheet]:
        """
        :return: All selected sheets in the specified group.
        """
        ...
    def active_sheet_in_group(self, group: int) -> Optional[Sheet]:
        """
        :return: The currently focused Sheet in the given group.
        """
        ...
    def active_view_in_group(self, group: int) -> Optional[View]:
        """
        :return: The currently focused View in the given group.
        """
        ...
    def sheets_in_group(self, group: int) -> [Sheet]:
        """
        :return: A list of all sheets in the specified group.
        """
        ...
    def views_in_group(self, group: int) -> [View]:
        """
        :return: A list of all views in the specified group.
        """
        ...
    def transient_sheet_in_group(self, group: int) -> Sheet:
        """
        :return: The transient sheet in the specified group.
        """
        ...
    def transient_view_in_group(self, group: int) -> View:
        """
        :return: The transient view in the specified group.
        """
        ...
    def layout(
        self,
    ) -> Dict[str, sublime.Value]:
        """
        Get the group layout of the window.
        """
        ...
    def get_layout(
        self,
    ):
        """
        Deprecated

        Use layout() instead
        """
        ...
    def set_layout(self, layout: Dict[str, sublime.Value]):
        """
        Set the group layout of the window.
        """
        ...
    def create_output_panel(self, name: str, unlisted=False) -> View:
        """
        Find the view associated with the named output panel, creating it if required. The output panel can be shown by running the show_panel window command, with the panel argument set to the name with an "output." prefix.

        The optional unlisted parameter is a boolean to control if the output panel should be listed in the panel switcher.
        """
        ...
    def find_output_panel(self, name: str) -> View:
        """
        :return: The View associated with the named output panel, or None if the output panel does not exist.
        """
        ...
    def destroy_output_panel(self, name: str):
        """
        Destroy the named output panel, hiding it if currently open.
        """
        ...
    def active_panel(
        self,
    ) -> Optional[str]:
        """
        Returns the name of the currently open panel, or None if no panel is open. Will return built-in panel names (e.g. "console", "find", etc) in addition to output panels.
        """
        ...
    def panels(
        self,
    ) -> [str]:
        """
        Returns a list of the names of all panels that have not been marked as unlisted. Includes certain built-in panels in addition to output panels.
        """
        ...
    def get_output_panel(self, name: str):
        """
        Deprecated

        Use create_output_panel instead.
        """
        ...
    def show_input_panel(
        self,
        caption: str,
        initial_text: str,
        on_done: Optional[Callable[[str], None]],
        on_change: Optional[Callable[[str], None]],
        on_cancel: Optional[Callable[[], None]],
    ):
        """
        Shows the input panel, to collect a line of input from the user.
        :param caption: The label to put next to the input widget.
        :param initial_text: The initial text inside the input widget.
        :param on_done: Called with the final input when the user presses enter.
        :param on_change: Called with the input when it’s changed.
        :param on_cancel: Called when the user cancels input using esc
        :return: The View used for the input widget.
        """
        ...
    def show_quick_panel(
        self,
        items: Union[List[str], List[List[str]], List[QuickPanelItem]],
        on_select: Callable[[int], None],
        flags=QuickPanelFlags.NONE,
        selected_index=-1,
        on_highlight: Optional[Callable[[int], None]] = None,
        placeholder: Optional[str] = None,
    ):
        """
        Show a quick panel to select an item in a list. on_select will be called once, with the index of the selected item. If the quick panel was cancelled, on_select will be called with an argument of -1.
        :param items: May be either a list of strings, or a list of lists of strings where the first item is the trigger and all subsequent strings are details shown below. May be a QuickPanelItem.
        :param on_select: Called with the selected item’s index when the quick panel is completed. If the panel was cancelled this is called with -1.
                          A second Event argument may be passed when the QuickPanelFlags.WANT_EVENT flag is present.
        :param flags: QuickPanelFlags controlling behavior.
        :param selected_index: The initially selected item. -1 for no selection.
        :param on_highlight: Called every time the highlighted item in the quick panel is changed.
        :param placeholder: Text displayed in the filter input field before any query is typed.
        """
        ...
    def is_sidebar_visible(
        self,
    ) -> bool:
        """
        Whether the sidebar is visible.
        """
        ...
    def set_sidebar_visible(self, flag: bool):
        """
        Hides or shows the sidebar.
        """
        ...
    def is_minimap_visible(
        self,
    ) -> bool:
        """
        Whether the minimap is visible.
        """
        ...
    def set_minimap_visible(self, flag: bool):
        """
        Hides or shows the minimap.
        """
        ...
    def is_status_bar_visible(
        self,
    ) -> bool:
        """
        Whether the status bar is visible.
        """
        ...
    def set_status_bar_visible(self, flag: bool):
        """
        Hides or shows the status bar.
        """
        ...
    def get_tabs_visible(
        self,
    ) -> bool:
        """
        Whether the tabs are visible.
        """
        ...
    def set_tabs_visible(self, flag: bool):
        """
        Hides or shows the tabs.
        """
        ...
    def is_menu_visible(
        self,
    ) -> bool:
        """
        Whether the menu is visible.
        """
        ...
    def set_menu_visible(self, flag: bool):
        """
        Hides or shows the menu.
        """
        ...
    def folders(
        self,
    ) -> List[str]:
        """
        A list of the currently open folders in this Window.
        """
        ...
    def project_file_name(
        self,
    ) -> Optional[str]:
        """
        The name of the currently opened project file, if any.
        """
        ...
    def workspace_file_name(
        self,
    ) -> Optional[str]:
        """
        The name of the currently opened workspace file, if any.
        """
        ...
    def project_data(
        self,
    ) -> Value:
        """
        The project data associated with the current window. The data is in the same format as the contents of a .sublime-project file.
        """
        ...
    def set_project_data(self, data: Value):
        """
        Updates the project data associated with the current window. If the window is associated with a .sublime-project file, the project file will be updated on disk, otherwise the window will store the data internally.
        """
        ...
    def settings(
        self,
    ) -> Settings:
        """
        The Settings object for this Window. Any changes to this settings object will be specific to this window.
        """
        ...
    def template_settings(
        self,
    ) -> Settings:
        """
        Per-window settings that are persisted in the session, and duplicated into new windows.
        """
        ...
    def symbol_locations(
        self,
        sym: str,
        source=SymbolSource.ANY,
        type=SymbolType.ANY,
        kind_id=KindId.AMBIGUOUS,
        kind_letter="",
    ) -> List[SymbolLocation]:
        """
        Find all locations where the symbol sym is located.
        :param sym: The name of the symbol.
        :param source: Sources which should be searched for the symbol.
        :param type: The type of symbol to find
        :param kind_id: The KindId of the symbol.
        :param kind_letter: The letter representing the kind of the symbol. See Kind.
        :return: the found symbol locations.
        """
        ...
    def lookup_symbol_in_index(self, symbol: str) -> [SymbolLocation]:
        """
        All locations where the symbol is defined across files in the current project.
        Deprecated

        Use symbol_locations() instead.
        """
        ...
    def lookup_symbol_in_open_files(self, symbol: str) -> [SymbolLocation]:
        """
        All locations where the symbol is defined across open files.
        Deprecated

        Use symbol_locations() instead.
        """
        ...
    def lookup_references_in_index(self, symbol: str) -> [SymbolLocation]:
        """
        All locations where the symbol is referenced across files in the current project.
        Deprecated

        Use symbol_locations() instead.
        """
        ...
    def lookup_references_in_open_files(self, symbol: str) -> [SymbolLocation]:
        """
        All locations where the symbol is referenced across open files.
        Deprecated

        Use symbol_locations() instead.
        """
        ...
    def extract_variables(
        self,
    ) -> Dict[str, str]:
        """
        Get the dict of contextual keys of the window.

        May contain: * "packages" * "platform" * "file" * "file_path" * "file_name" * "file_base_name" * "file_extension" * "folder" * "project" * "project_path" * "project_name" * "project_base_name" * "project_extension"

        This dict is suitable for use with expand_variables().
        """
        ...
    def status_message(self, msg: str):
        """
        Show a message in the status bar.
        """
        ...

class View:
    """
    Represents a view into a text Buffer.

    Note that multiple views may refer to the same Buffer, but they have their own unique selection and geometry. A list of these may be gotten using View.clones() or Buffer.views().
    """

    def id(self) -> int:
        """A number that uniquely identifies this view."""
        ...
    def buffer_id(self) -> int:
        """A number that uniquely identifies this view’s Buffer."""
        ...
    def buffer(self) -> Buffer:
        """The Buffer for which this is a view."""
        ...
    def sheet_id(self) -> int:
        """The ID of the Sheet for this View, or 0 if not part of any sheet."""
        ...
    def sheet(self) -> Optional[Sheet]:
        """The Sheet for this view, if displayed in a sheet."""
        ...
    def element(self) -> Optional[str]:
        """
        None for normal views that are part of a Sheet. For views that comprise part of the UI a string is returned from the following list:

            "console:input" - The console input.

            "goto_anything:input" - The input for the Goto Anything.

            "command_palette:input" - The input for the Command Palette.

            "find:input" - The input for the Find panel.

            "incremental_find:input" - The input for the Incremental Find panel.

            "replace:input:find" - The Find input for the Replace panel.

            "replace:input:replace" - The Replace input for the Replace panel.

            "find_in_files:input:find" - The Find input for the Find in Files panel.

            "find_in_files:input:location" - The Where input for the Find in Files panel.

            "find_in_files:input:replace" - The Replace input for the Find in Files panel.

            "find_in_files:output" - The output panel for Find in Files (buffer or output panel).

            "input:input" - The input for the Input panel.

            "exec:output" - The output for the exec command.

            "output:output" - A general output panel.

        The console output, indexer status output and license input controls are not accessible via the API.
        """
        ...
    def is_valid(self) -> bool:
        """Check whether this view is still valid. Will return False for a closed view, for example."""
        ...
    def is_primary(self) -> bool:
        """Whether view is the primary view into a Buffer. Will only be False if the user has opened multiple views into a file."""
        ...
    def window(self) -> None:
        """A reference to the window containing the view, if any."""
        ...
    def clones(self) -> [View]:
        """All the other views into the same Buffer. See View."""
        ...
    def file_name(self) -> Optional[str]:
        """The full name of the file associated with the sheet, or None if it doesn’t exist on disk."""
        ...
    def close(self, on_close=Callable[View]) -> bool:
        """Closes the view."""
        ...
    def retarget(self, new_fname: str):
        """Change the file path the buffer will save to."""
        ...
    def name(self) -> str:
        """The name assigned to the buffer, if any."""
        ...
    def set_name(self, name: str):
        """Assign a name to the buffer. Displayed as in the tab for unsaved files."""
        ...
    def reset_reference_document(self):
        """Clears the state of the incremental diff for the view."""
        ...
    def set_reference_document(self, reference: str):
        """Uses the string reference to calculate the initial diff for the incremental diff."""
        ...
    def is_loading(self) -> bool:
        """Whether the buffer is still loading from disk, and not ready for use."""
        ...
    def is_dirty(self) -> bool:
        """Whether there are any unsaved modifications to the buffer."""
        ...
    def is_read_only(self) -> bool:
        """Whether the buffer may not be modified."""
        ...
    def set_read_only(self, read_only: bool):
        """Set the read only property on the buffer."""
        ...
    def is_scratch(self) -> bool:
        """Whether the buffer is a scratch buffer. See set_scratch()."""
        ...
    def set_scratch(self, scratch: bool):
        """Sets the scratch property on the buffer. When a modified scratch buffer is closed, it will be closed without prompting to save. Scratch buffers never report as being dirty."""
        ...
    def encoding(self) -> str:
        """The encoding currently associated with the buffer."""
        ...
    def set_encoding(self, encoding_name: str):
        """Applies a new encoding to the file. This will be used when the file is saved."""
        ...
    def line_endings(self) -> str:
        """The encoding currently associated with the file."""
        ...
    def set_line_endings(self, line_ending_name: str):
        """Sets the line endings that will be applied when next saving."""
        ...
    def size(self) -> int:
        """The number of character in the file."""
        ...
    def insert(self, edit: Edit, pt: Point, text: str) -> int:
        """
        Insert the given string into the buffer.

        :param edit: An Edit object provided by a TextCommand.
        :param pt: The text point in the view where to insert.
        :param text: The text to insert.
        :return: The actual number of characters inserted. This may differ from the provided text due to tab translation.
        Raises ValueError
        If the Edit object is in an invalid state, ie. outside of a TextCommand.
        """
        ...
    def erase(self, edit: Edit, region: Region):
        """Erases the contents of the provided Region from the buffer."""
        ...
    def replace(self, edit: Edit, region: Region, text: str):
        """Replaces the contents of the Region in the buffer with the provided string."""
        ...
    def change_count(self) -> int:
        """
        Each time the buffer is modified, the change count is incremented. The change count can be used to determine if the buffer has changed since the last it was inspected.
        :return: The current change count.
        """
        ...
    def change_id(self):
        """Get a 3-element tuple that can be passed to transform_region_from() to obtain a region equivalent to a region of the view in the past. This is primarily useful for plugins providing text modification that must operate in an asynchronous fashion and must be able to handle the view contents changing between the request and response."""
        ...
    def transform_region_from(
        self, region: Region, change_id: int, _from_: int, _to_: int
    ) -> Region:
        """
        Transforms a region from a previous point in time to an equivalent region in the current state of the View. The change_id must have been obtained from change_id() at the point in time the region is from.
        """
        ...
    def run_command(self, cmd: str, args: CommandArgs = None):
        """Run the named TextCommand with the (optional) given args."""
        ...
    def sel(self) -> Selection:
        """The views Selection."""
        ...
    def substr(self, x: Union[Region, Point]) -> str:
        """The string at the Point or within the Region provided."""
        ...
    def find(self, pattern: str, start_pt: Point, flags=FindFlags.NONE) -> Region:
        """

        :param pattern: The regex or literal pattern to search by.
        :param start_pt: The Point to start searching from.
        :param flags: Controls various behaviors of find. See FindFlags.
        :return: The first Region matching the provided pattern.
        """
        ...
    def find_all(
        self,
        pattern: str,
        flags=FindFlags.NONE,
        fmt: Optional[str] = None,
        extractions: Optional[List[str]] = None,
    ) -> [Region]:
        """
        :param pattern: The regex or literal pattern to search by.
        :param flags: Controls various behaviors of find. See FindFlags.
        :param fmt: When not None all matches in the extractions list will be formatted with the provided format string.
        :param extractions: An optionally provided list to place the contents of the find results into.
        :return: All (non-overlapping) regions matching the pattern.
        """
        ...
    def settings(self) -> Settings:
        """The view’s Settings object. Any changes to it will be private to this view."""
        ...
    def meta_info(self, key: str, pt: Point) -> Value:
        """
        Look up the preference key for the scope at the provided Point from all matching .tmPreferences files.

        Examples of keys are TM_COMMENT_START and showInSymbolList.
        """
        ...
    def extract_tokens_with_scopes(self, region: Region) -> List[Region, str]:
        """
        :param region: The region from which to extract tokens and scopes.
        :return: A list of pairs containing the Region and the scope of each token.
        """
        ...
    def extract_scope(self, pt: Point) -> Region:
        """
        :return: The extent of the syntax scope name assigned to the character at the given Point.
        """
        ...
    def expand_to_scope(self, pt: Point, selector: str) -> Optional[Region]:
        """
        Expand by the provided scope selector from the Point.
        :param pt: The point from which to expand.
        :param selector: The scope selector to match.
        :return: The matched Region, if any.
        """
        ...
    def scope_name(self, pt: Point) -> str:
        """
        The syntax scope name assigned to the character at the given point.
        """
        ...
    def context_backtrace(self, pt: Point) -> List[ContextStackFrame]:
        """
        Get a backtrace of ContextStackFrames at the provided Point.

        Note this function is particularly slow.
        """
        ...
    def match_selector(self, pt: Point, selector: str) -> bool:
        """Whether the provided scope selector matches the Point."""
        ...
    def score_selector(self, pt: Point, selector: str) -> int:
        """
        Equivalent to:

        sublime.score_selector(view.scope_name(pt), selector)

        See sublime.score_selector.
        """
        ...
    def find_by_selector(self, selector: str) -> List[Region]:
        """
        Find all regions in the file matching the given selector.
        :return: The list of matched regions.
        """
    def style(self) -> Dict[str, str]:
        """
        See style_for_scope.
        :return: The global style settings for the view. All colors are normalized to the six character hex form with a leading hash, e.g. #ff0000.
        """
        ...
    def style_for_scope(self, scope: str) -> Dict[str, str]:
        """
        Accepts a string scope name and returns a dict of style information including the keys:

        "foreground"

        "background" (only if set)

        "bold"

        "italic"

        "glow"
        4063

        "underline"

        "stippled_underline"

        "squiggly_underline"

        "source_line"

        "source_column"

        "source_file"

        The foreground and background colors are normalized to the six character hex form with a leading hash, e.g. #ff0000.

            def lines(self,region: Region) -> List[Region]:
                ...

        :return: A list of lines (in sorted order) intersecting the provided Region.
        """
        ...
    def split_by_newlines(self, region: Region) -> [Region]:
        """
        Splits the region up such that each Region returned exists on exactly one line.
        """
        ...
    def line(self, x: Union[Region, Point]) -> Region:
        """
        :return: The line that contains the Point or an expanded Region to the beginning/end of lines, excluding the newline character.
        """
        ...
    def full_line(self, x: Union[Region, Point]) -> Region:
        """The line that contains the Point or an expanded Region to the beginning/end of lines, including the newline character."""
        ...
    def word(self, x: Union[Region, Point]) -> Region:
        """The word that contains the provided Point. If a Region is provided it’s beginning/end are expanded to word boundaries."""
        ...
    def classify(self, pt: Point) -> PointClassification:
        """Classify the provided Point. See PointClassification."""
        ...
    def find_by_class(
        self,
        pt: Point,
        forward: bool,
        classes: PointClassification,
        separators="",
        sub_word_separators="",
    ) -> Point:
        """
        Find the next location that matches the provided PointClassification.

        :param pt: The point to start searching from.
        :param forward: Whether to search forward or backwards.
        :param classes: The classification to search for.
        :param separators: The word separators to use when classifying.
        :param sub_word_separators: The sub-word separators to use when classifying.
        :return: The found point.
        """
        ...
    def expand_by_class(
        self,
        x: Union[Region, Point],
        classes: PointClassification,
        separators="",
        sub_word_separators="",
    ) -> Region:
        """
        Expand the provided Point or Region to the left and right until each side lands on a location that matches the provided PointClassification. See find_by_class.

        :param classes: The classification to search by.
        :param separators: The word separators to use when classifying.
        :param sub_word_separators: The sub-word separators to use when classifying.
        """
        ...
    def rowcol(self, tp: Point):
        """Calculates the 0-based line and column numbers of the point. Column numbers are returned as number of Unicode characters."""
        ...
    def rowcol_utf8(self, tp: Point):
        """Calculates the 0-based line and column numbers of the point. Column numbers are returned as UTF-8 code units."""
        ...
    def rowcol_utf16(self, tp: Point):
        """Calculates the 0-based line and column numbers of the point. Column numbers are returned as UTF-16 code units."""
        ...
    def text_point(self, row: int, col: int, *, clamp_column=False) -> Point:
        """
        Calculates the character offset of the given, 0-based, row and col. col is interpreted as the number of Unicode characters to advance past the beginning of the row.
        :param clamp_column: Whether col should be restricted to valid values for the given row.
        """
        ...
    def text_point_utf8(self, row: int, col: int, *, clamp_column=False) -> Point:
        """
        Calculates the character offset of the given, 0-based, row and col. col is interpreted as the number of UTF-8 code units to advance past the beginning of the row.
        :param clamp_column: whether col should be restricted to valid values for the given row.
        :return:
        """
        ...
    def text_point_utf16(self, row: int, col: int, *, clamp_column=False) -> Point:
        """
        Calculates the character offset of the given, 0-based, row and col. col is interpreted as the number of UTF-16 code units to advance past the beginning of the row.

        :param clamp_column: whether col should be restricted to valid values for the given row.
        """
        ...
    def visible_region(self) -> Region:
        """
        :return: The currently visible area of the view.
        """
        ...
    def show(
        self,
        location: Union[Region, Selection, Point],
        show_surrounds=True,
        keep_to_left=False,
        animate=True,
    ):
        """
        Scroll the view to show the given location.
        :param location: The location to scroll the view to. For a Selection only the first Region is shown.
        :param show_surrounds: Whether to show the surrounding context around the location.
        :param keep_to_left: Whether the view should be kept to the left, if horizontal scrolling is possible.
        :param animate: Whether the scrolling should be animated.
        """
        ...
    def show_at_center(self, location: Union[Region, Point], animate=True):
        """
        Scroll the view to center on the location.
        :param location:  Which Point or Region to scroll to.
        :param animate:Whether the scrolling should be animated.
        :return:
        """
        ...
    def viewport_position(self) -> Vector:
        """
        :return: The offset of the viewport in layout coordinates.
        """
        ...
    def set_viewport_position(self, xy: Vector, animate=True):
        """Scrolls the viewport to the given layout position."""
        ...
    def viewport_extent(self) -> Vector:
        """
        :return: The width and height of the viewport.
        """
    def layout_extent(self) -> Vector:
        """
        :return: The width and height of the layout.
        """
    def text_to_layout(self, tp: Point) -> Vector:
        """Convert a text point to a layout position."""
        ...
    def text_to_window(self, tp: Point) -> Vector:
        """Convert a text point to a window position."""
        ...
    def layout_to_text(self, xy: Vector) -> Point:
        """Convert a layout position to a text point."""
        ...
    def layout_to_window(self, xy: Vector) -> Vector:
        """Convert a layout position to a window position."""
        ...
    def window_to_layout(self, xy: Vector) -> Vector:
        """Convert a window position to a layout position."""
        ...
    def window_to_text(self, xy: Vector) -> Point:
        """Convert a window position to a text point."""
        ...
    def line_height(self) -> DIP:
        """The light height used in the layout."""
        ...
    def em_width(self) -> DIP:
        """The typical character width used in the layout."""
        ...
    def is_folded(self, region: Region) -> bool:
        """Whether the provided Region is folded."""
        ...
    def folded_regions(self) -> List[Region]:
        """The list of folded regions."""
        ...
    def fold(self, x: Union[Region, List[Region]]) -> bool:
        """
        Fold the provided Region (s).

        :return: False if the regions were already folded.
        """
        ...
    def unfold(self, x: Union[Region, List[Region]]) -> List[Region]:
        """
        Unfold all text in the provided Region (s).

        :return: The unfolded regions.
        """
        ...
    def add_regions(
        self,
        key: str,
        regions: [Region],
        scope="",
        icon="",
        flags=RegionFlags.NONE,
        annotations: [str] = [],
        annotation_color="",
        on_navigate: Optional[Callable[[str], None]] = None,
        on_close: Optional[Callable[[], None]] = None,
    ):
        """
        Adds visual indicators to regions of text in the view. Indicators include icons in the gutter, underlines under the text, borders around the text and annotations. Annotations are drawn aligned to the right-hand edge of the view and may contain HTML markup.
        :param key: An identifier for the collection of regions. If a set of regions already exists for this key they will be overridden. See get_regions.
        :param regions: The list of regions to add. These should not overlap.
        :param scope: An optional string used to source a color to draw the regions in. The scope is matched against the color scheme. Examples include: "invalid" and "string". See Scope Naming for a list of common scopes. If the scope is empty, the regions won’t be drawn.

        Also supports the following pseudo-scopes, to allow picking the closest color from the user‘s color scheme:
        "region.redish"
        "region.orangish"
        "region.yellowish"
        "region.greenish"
        "region.cyanish"
        "region.bluish"
        "region.purplish"
        "region.pinkish"

        :param icon:

        An optional string specifying an icon to draw in the gutter next to each region. The icon will be tinted using the color associated with the scope. Standard icon names are "dot", "circle"` and ``"bookmark". The icon may also be a full package-relative path, such as "Packages/Theme - Default/dot.png".

        :param flags:

        Flags specifying how the region should be drawn, among other behavior. See RegionFlags.

        :param annotations:
        An optional collection of strings containing HTML documents to display along the right-hand edge of the view. There should be the same number of annotations as regions. See minihtml Reference for supported HTML.

        :param annotation_color:
        4050

        An optional string of the CSS color to use when drawing the left border of the annotation. See minihtml Reference: Colors for supported color formats.

        :param on_navitate:
        4050

        Called when a link in an annotation is clicked. Will be passed the href of the link.

        :param on_close:
        4050

        Called when the annotations are closed.
        """
        ...
    def get_regions(self, key: str) -> [Region]:
        """
        :return: The regions associated with the given key, if any.
        """
        ...
    def erase_regions(self, key: str):
        """
        Remove the regions associated with the given key.
        """
        ...
    def assign_syntax(self, syntax: Union[str, Syntax]):
        """
        Changes the syntax used by the view. syntax may be a packages path to a syntax file, or a scope: specifier string.

        syntax may be a Syntax object.
        4080
        """
        ...
    def set_syntax_file(self, syntax_file: str):
        """
        Deprecated

        Use assign_syntax() instead.
        """
        ...
    def syntax(self) -> Optional[Syntax]:
        """
        :return: The syntax assigned to the buffer.
        """
        ...
    def symbols(self) -> List[Region, str]:
        """
        Extract all the symbols defined in the buffer.

        Deprecated

        Use symbol_regions() instead.
        """
        ...
    def get_symbols(self) -> List[Region, str]:
        """
        Deprecated

        Use symbol_regions() instead.
        """
        ...
    def indexed_symbols(self) -> List[Region, str]:
        """
        A list of the Region and name of symbols.
        Deprecated

        Use indexed_symbol_regions() instead.
        """
        ...
    def indexed_references(self) -> List[Region, str]:
        """
        A list of the Region and name of symbols.
        Deprecated

        Use indexed_symbol_regions() instead.
        """
        ...
    def symbol_regions(self) -> List[SymbolRegion]:
        """
        Info about symbols that are part of the view’s symbol list.
        """
        ...
    def indexed_symbol_regions(self, type=SymbolType.ANY) -> List[SymbolRegion]:
        """
        :param type: The type of symbol to return.
        :return : Info about symbols that are indexed.
        """
        ...
    def set_status(self, key: str, value: str):
        """
        Add the status key to the view. The value will be displayed in the status bar, in a comma separated list of all status values, ordered by key. Setting the value to "" will clear the status.
        """
        ...
    def get_status(self, key: str) -> str:
        """
        :return: The previous assigned value associated with the given key, if any.
        See set_status().
        """
        ...
    def erase_status(self, key: str):
        """
        Clear the status associated with the provided key.
        """
    def extract_completions(self, prefix: str, tp: Point = -1) -> List[str]:
        """
        Get a list of word-completions based on the contents of the view.
        :param prefix: The prefix to filter words by.
        :param tp: The Point by which to weigh words. Closer words are preferred.
        :return:
        """
        ...
    def command_history(self, index: int, modifying_only=False):
        """
        Get info on previous run commands stored in the undo/redo stack.
        :param index: The offset into the undo/redo stack. Positive values for index indicate to look in the redo stack for commands.
        :param modifying_only: Whether only commands that modify the text buffer are considered.
        :return: The command name, command arguments and repeat count for the history entry. If the undo/redo history doesn’t extend far enough, then (None, None, 0) will be returned.
        """
        ...
    def overwrite_status(self) -> bool:
        """
        :return: The overwrite status, which the user normally toggles via the insert key.
        """
        ...
    def set_overwrite_status(self, value: bool):
        """
        Set the overwrite status. See overwrite_status().
        """
        ...
    def show_popup_menu(self, items: [str], on_done: Callable[[int], None], flags=0):
        """
        Show a popup menu at the caret, for selecting an item in a list.
        :param items: The list of entries to show in the list.
        :param on_done: Called once with the index of the selected item. If the popup was cancelled -1 is passed instead.
        :param flags: must be 0, currently unused.
        """
        ...
    def show_popup(
        self,
        content: str,
        flags=PopupFlags.NONE,
        location: Point = -1,
        max_width: DIP = 320,
        max_height: DIP = 240,
        on_navigate: Optional[Callable[[str], None]] = None,
        on_hide: Optional[Callable[[], None]] = None,
    ):
        """
        Show a popup displaying HTML content.
        :param content: The HTML content to display.
        :param flags: Flags controlling popup behavior. See PopupFlags.
        :param location: The Point at which to display the popup. If -1 the popup is shown at the mouse cursor.
        :param max_width: The maximum width of the popup.
        :param max_height: The maximum height of the popup.
        :param on_navigate: Called when a link is clicked in the popup. Passed the value of the href attribute of the clicked link.
        :param on_hide: Called when the popup is hidden.
        """
        ...
    def update_popup(self, content: str):
        """
        Update the content of the currently visible popup.
        """
        ...
    def is_popup_visible(self) -> bool:
        """
        :return: Whether a popup is currently shown.
        """
        ...
    def hide_popup(self):
        """Hide the current popup."""
    def is_auto_complete_visible(self) -> bool:
        """
        :return: Whether the auto-complete menu is currently visible.
        """
        ...
    def preserve_auto_complete_on_focus_lost(self):
        """Sets the auto complete popup state to be preserved the next time the View loses focus. When the View regains focus, the auto complete window will be re-shown, with the previously selected entry pre-selected."""
        ...
    def export_to_html(
        self,
        regions: Optional[Union[Region, List[Region]]] = None,
        minihtml=False,
        enclosing_tags=False,
        font_size=True,
        font_family=True,
    ):
        """
        Generates an HTML string of the current view contents, including styling for syntax highlighting.

        Parameters

        regions

        The region(s) to export. By default the whole view is exported.

        minihtml

        Whether the exported HTML should be compatible with minihtml Reference.

        enclosing_tags

        Whether a <div> with base-styling is added. Note that without this no background color is set.

        font_size

        Whether to include the font size in the top level styling. Only applies when enclosing_tags is True.

        font_family

        Whether to include the font family in the top level styling. Only applies when enclosing_tags is True.
        """
        ...
    def clear_undo_stack(self):
        """Clear the undo/redo stack."""
        ...

class Buffer:
    """Represents a text buffer. Multiple View objects may share the same buffer."""

    def id() -> int:
        """Returns a number that uniquely identifies this buffer."""
        ...
    def file_name() -> Optional[str]:
        """The full name file the file associated with the buffer, or None if it doesn’t exist on disk."""
        ...
    def views() -> [View]:
        """Returns a list of all views that are associated with this buffer."""
        ...
    def primary_view() -> View:
        """The primary view associated with this buffer."""
        ...

class Region:
    """
    A singular selection region. This region has a order - b may be before or at a.

    Also commonly used to represent an area of the text buffer, where ordering and xpos are generally ignored.
    """

    a: Point
    b: Point
    xpos: DIP

    def __init__(self, a: Point, b: Point, xpos: DIP = -1):
        """
        :param a:     The first end of the region.
        :param b:     The second end of the region. In a selection this is the location of the caret. May be less than a.
        :param xpos:  In a selection this is the target horizontal position of the region. This affects behavior when pressing the up or down keys. Use -1 if undefined.
        """
        ...
    def __len__() -> int:
        """
        :return: The size of the region.
        """
        ...
    def __contains__(v: Union[Region, Point]) -> bool:
        """
        :return: Whether the provided Region or Point is entirely contained within this region.
        """
    def to_tuple():
        """
        :return: This region as a tuple (a, b).
        """
        ...
    def empty() -> bool:
        """
        :return: Whether the region is empty, ie. a == b.
        """
        ...
    def begin() -> Point:
        """
        :return: The smaller of a and b.
        """
        ...
    def end() -> Point:
        """
        :return: The larger of a and b.
        """
        ...
    def size() -> int:
        """
        Equivalent to __len__.
        """
        ...
    def contains(x: Point) -> bool:
        """
        Equivalent to __contains__.
        """
        ...
    def cover(region: Region) -> Region:
        """
        :return: A Region spanning both regions.
        """
        ...
    def intersection(region: Region) -> Region:
        """
        :return: A Region covered by both regions.
        """
        ...
    def intersects(region: Region) -> bool:
        """
        :return: Whether the provided region intersects this region.
        """
        ...

class Selection(Sequence[Region]):
    def __len__(self) -> int:
        "The number of regions in the selection."
        ...
    def __delitem__(self, index: int):
        "Delete the region at the given index."
        ...
    def is_valid(self) -> bool:
        "Whether this selection is for a valid view."
        ...
    def clear(self):
        "Remove all regions from the selection."
        ...
    def add(self, x: Union[Region, Point]):
        "Add a Region or Point to the selection. It will be merged with the existing regions if intersecting."
        ...
    def add_all(self, regions: Iterator[Region]):
        "Add all the regions from the given iterable."
        ...
    def subtract(self, region: Region):
        "Subtract a region from the selection, such that the whole region is no longer contained within the selection."
        ...
    def contains(self, region: Region) -> bool:
        "Whether the provided region is contained within the selection."
        ...

class PointClassification(IntFlag):
    """
    Flags that identify characteristics about a Point in a text sheet. See View.classify.

    For backwards compatibility these values are also available outside this enumeration with a CLASS_ prefix.
    """

    NONE = 0
    WORD_START = 1
    """The point is the start of a word."""

    WORD_END = 2
    """The point is the end of a word."""

    PUNCTUATION_START = 4
    """The point is the start of a sequence of punctuation characters."""

    PUNCTUATION_END = 8
    """The point is the end of a sequence of punctuation characters."""

    SUB_WORD_START = 16
    """The point is the start of a sub-word."""

    SUB_WORD_END = 32
    """The point is the end of a sub-word."""

    LINE_START = 64
    """The point is the start of a line."""

    LINE_END = 128
    """The point is the end of a line."""

    EMPTY_LINE = 256
    """The point is an empty line."""

CLASS_NONE = PointClassification.NONE
CLASS_EMPTY_LINE = PointClassification.EMPTY_LINE

class QueryOperator(IntEnum):
    """
    Enumeration of operators able to be used when querying contexts.

    See EventListener.on_query_context and ViewEventListener.on_query_context.

    For backwards compatibility these values are also available outside this enumeration with a OP_ prefix.

    EQUAL = 0

    NOT_EQUAL = 1

    REGEX_MATCH = 2

    NOT_REGEX_MATCH = 3

    REGEX_CONTAINS = 4

    NOT_REGEX_CONTAINS = 5
    """

    EQUAL = 0
    NOT_EQUAL = 1
    REGEX_MATCH = 2
    NOT_REGEX_MATCH = 3
    REGEX_CONTAINS = 4
    NOT_REGEX_CONTAINS = 5

OP_EQUAL = QueryOperator.EQUAL
OP_NOT_EQUAL = QueryOperator.NOT_EQUAL
OP_REGEX_MATCH = QueryOperator.REGEX_MATCH
OP_NOT_REGEX_MATCH = QueryOperator.NOT_REGEX_MATCH
OP_REGEX_CONTAINS = QueryOperator.REGEX_CONTAINS
OP_NOT_REGEX_CONTAINS = QueryOperator.NOT_REGEX_CONTAINS

def set_timeout(callback, delay) -> None:
    """Runs the callback in the main thread after the given delay (in milliseconds). Callbacks with an equal delay will be run in the order they were added."""

def set_timeout_async(callback, delay) -> None:
    """Runs the callback on an alternate thread after the given delay (in milliseconds)."""

def error_message(string) -> None:
    """Displays an error dialog to the user."""

def message_dialog(string) -> None:
    """Displays a message dialog to the user."""

def ok_cancel_dialog(string, ok_title=None) -> bool:
    """Displays an ok / cancel question dialog to the user. If ok_title is provided, this may be used as the text on the ok button. Returns True if the user presses the ok button."""

def yes_no_cancel_dialog(string, yes_title=None, no_title=None) -> int:
    """Displays a yes / no / cancel question dialog to the user. If yes_title and/or no_title are provided, they will be used as the text on the corresponding buttons on some platforms. Returns sublime.DIALOG_YES, sublime.DIALOG_NO or sublime.DIALOG_CANCEL."""

def open_dialog(
    callback, file_types=None, directory=None, multi_select=None, allow_folders=None
) -> None:
    """
    Presents the user with a file dialog for the purpose of opening a file, and passes the resulting file path to callback.

    callback

         A callback to accept the result of the user's choice. If the user cancels the dialog, None will be passed. If a file is selected, a str containing the path will be passed. If the parameter multi_select is True, a list of str file paths will be passed.
     file_types

         A specification of allowable file types. This parameter should be a list containing 2-element tuples:

             A str containing a description
             A list of str with valid file extensions

         Example:

         [
             ('Python source files', ['py', 'py3', 'pyw']),
             ('C source files', ['c', 'h'])
         ]

     directory

         A str of the directory to open the file dialog to. If not specified, will use the directory of the current view.
     multi_select

         A bool to indicate that the user should be allowed to select multiple files
     allow_folders

         A bool to indicate that the user should be allowed to select folders
    """

def save_dialog(
    callback, file_types=None, directory=None, name=None, extension=None
) -> None:

    # Presents the user with file dialog for the purpose of saving a file, and passes the result to callback.
    #
    # callback
    #
    #     A callback to accept the result of the user's choice. If the user cancels the dialog, None will be passed. If a file is selected, a str containing the path will be passed.
    # file_types
    #
    #     A specification of allowable file types. This parameter should be a list containing 2-element tuples:
    #
    #         A str containing a description
    #         A list of str with valid file extensions
    #
    #     Example:
    #
    #     [
    #         ('Python source files', ['py', 'py3', 'pyw']),
    #         ('C source files', ['c', 'h'])
    #     ]
    #
    # directory
    #
    #     A str of the directory to open the file dialog to. If not specified, will use the directory of the current view.
    # name
    #
    #     A str with the default file name
    # extension
    #
    #     A str containing the default file extension
    pass

def select_folder_dialog(callback, directory=None, multi_select=None) -> None:
    # Presents the user with a file dialog for the purpose of selecting a folder, and passes the result to callback.
    #
    # callback
    #
    #     A callback to accept the result of the user's choice. If the user cancels the dialog, None will be passed. If a folder is selected, a str containing the path will be passed. If the parameter multi_select is True, a list of str folder paths will be passed.
    # directory
    #
    #     A str of the directory to open the file dialog to. If not specified, will use the directory of the current view.
    # multi_select
    #
    #     A bool to indicate that the user should be allowed to select multiple folders
    pass

def load_resource(name) -> str:
    # Loads the given resource. The name should be in the format "Packages/Default/Main.sublime-menu".
    pass

def load_binary_resource(name) -> bytes:
    # Loads the given resource. The name should be in the format "Packages/Default/Main.sublime-menu".
    pass

def find_resources(pattern) -> List[str]:
    # Finds resources whose file name matches the given pattern.
    pass

def ui_info() -> dict:
    # Returns information about the user interface, including top-level keys system, theme and color_scheme   4096
    pass

def list_syntaxes() -> List[Syntax]:
    # Returns a list of all available syntaxes    4081
    pass

def syntax_from_path(path) -> Union[Syntax, None]:
    # Returns the the Syntax, if any, at the unicode string path specified    4081
    pass

def find_syntax_by_name(name) -> List[Syntax]:
    # Returns the the Syntax, if any, with the unicode string name specified  4081
    pass

def find_syntax_by_scope(scope) -> List[Syntax]:
    # Returns the the Syntax, if any, with the unicode string base scope specified    4081
    pass

def find_syntax_for_file(fname, first_line=None) -> Union[Syntax, None]:
    # Returns the the Syntax that will be used when opening a file with the name fname. The first_line of file contents may also be provided if available.    4081
    pass

def encode_value(value, pretty=None) -> str:
    #    Encode a JSON compatible value into a string representation. If pretty is set to True, the string will include newlines and indentation.
    pass

def decode_value(string) -> Any:
    #  Decodes a JSON string into an object. If the string is invalid, a ValueError will be thrown.
    pass

def expand_variables(value, variables) -> Any:
    #  Expands any variables in the string value using the variables defined in the dictionary variables. value may also be a list or dict, in which case the structure will be recursively expanded. Strings should use snippet syntax, for example: expand_variables("Hello, ${name}", {"name": "Foo"})
    pass

def format_command(cmd, *args) -> str:
    #    Create a "command string" from a str cmd name, and an optional dict of args. This is used when constructing a command-based CompletionItem.     4075
    pass

def command_url(cmd, *args) -> str:
    #    Creates a subl:-protocol URL for executing a command in a minihtml link.    4075
    pass

def load_settings(base_name) -> Settings:
    #   Loads the named settings. The name should include a file name and extension, but not a path. The packages will be searched for files matching the base_name, and the results will be collated into the settings object. Subsequent calls to load_settings() with the base_name will return the same object, and not load the settings from disk again.
    pass

def save_settings(base_name) -> None:
    #   Flushes any in-memory changes to the named settings object to disk.
    pass

def windows() -> List[Window]:
    #    Returns a list of all the open windows.
    pass

def active_window() -> Window:
    # Returns the most recently used window.
    pass

def packages_path() -> str:
    #    Returns the path where all the user's loose packages are located.
    pass

def installed_packages_path() -> str:
    #    Returns the path where all the user's .sublime-package files are located.
    pass

def cache_path() -> str:
    #    Returns the path where Sublime Text stores cache files.
    pass

def get_clipboard(size_limit=None) -> str:
    #    DEPRECATED - use get_clipboard_async() when possible. Returns the contents of the clipboard. size_limit protects against unnecessarily large data, and defaults to 16,777,216 bytes. If the clipboard is larger than size_limit, an empty string will be returned.
    pass

def get_clipboard_async(callback, size_limit=None) -> None:
    #   Calls callback with the contents of the clipboard. size_limit protects against unnecessarily large data, and defaults to 16,777,216 bytes. If the clipboard is larger than size_limit, an empty string will be passed.  4075
    pass

def set_clipboard(string) -> None:
    #   Sets the contents of the clipboard.
    pass

def score_selector(scope, selector) -> int:
    #    Matches the selector against the given scope, returning a score. A score of 0 means no match, above 0 means a match. Different selectors may be compared against the same scope: a higher score means the selector is a better match for the scope.
    pass

def run_command(string, *args) -> None:
    """
    Runs the named ApplicationCommand with the (optional) given args.
    """

def get_macro() -> List[dict]:
    """
    Returns a list of the commands and args that compromise the currently recorded macro. Each dict will contain the keys "command" and "args".
    """

def log_commands(flag) -> None:
    """
    Controls command logging. If enabled, all commands run from key bindings and the menu will be logged to the console.
    """

def log_input(flag) -> None:
    """
    Controls input logging. If enabled, all key presses will be logged to the console.
    """

def log_result_regex(flag) -> None:
    """
    Controls result regex logging. This is useful for debugging regular expressions used in build systems.
    """

def log_control_tree(flag) -> None:
    """
    When enabled, clicking with Ctrl+Alt will log the control tree under the mouse to the console.
    """

def log_fps(flag) -> None:
    """
    When enabled, logs the number of frames per second being rendered for the user interface
    """

def version() -> str:
    """
    Returns the version number
    """

def platform() -> str:
    """
    Returns the platform, which may be "osx", "linux" or "windows"
    """

def arch() -> str:
    """
    Returns the CPU architecture, which may be "x32", "x64" or "arm64"
    """

def channel() -> str:
    """
    Returns the release channel this build of Sublime Text is from: "dev" or "stable"
    """
