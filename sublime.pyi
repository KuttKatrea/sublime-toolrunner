from enum import IntFlag, IntEnum
from typing import List, Union, Any, Iterator, Optional, Sequence, Callable, Tuple, Dict

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
    def active_view(self) -> View:
        pass

    def show_quick_panel(self, items: Union[List[str], List[List[str]], List[QuickPanelItem]], on_select: Callable[[int], None], flags=QuickPanelFlags.NONE, selected_index=- 1, on_highlight: Optional[Callable[[int], None]] = None, placeholder: Optional[str] = None):
        "Show a quick panel to select an item in a list. on_select will be called once, with the index of the selected item. If the quick panel was cancelled, on_select will be called with an argument of -1."

class View:
    """
    Represents a view into a text Buffer.

    Note that multiple views may refer to the same Buffer, but they have their own unique selection and geometry. A list of these may be gotten using View.clones() or Buffer.views().
    """

    def sel(self) -> Selection:
        pass

    def substr(self, x: Union[Region, Point]) -> str:
        "The string at the Point or within the Region provided."

    def line(self, x: Union[Region, Point]) -> Region:
        "The line that contains the Point or an expanded Region to the beginning/end of lines, excluding the newline character."

    def expand_by_class(self, x: Union[Region, Point], classes: PointClassification, separators='', sub_word_separators='')-> Region:
        "Expand the provided Point or Region to the left and right until each side lands on a location that matches the provided PointClassification. See find_by_class."

    def size(self) -> int:
        """Equivalent to __len__."""
        pass

    def id(self) -> int:
        pass
    def syntax(self) -> Syntax:
        pass

    def buffer(self) -> Buffer:
        pass

    def settings(self) -> Settings:
        pass

class Buffer():
    pass

class Region:
    def __init__(
        self,
        a: Point,
        b: Point,
        xpos: DIP = -1
        ):
        """
        A singular selection region. This region has a order - b may be before or at a.

        Also commonly used to represent an area of the text buffer, where ordering and xpos are generally ignored.

        :param a:     The first end of the region.
        :param b:     The second end of the region. In a selection this is the location of the caret. May be less than a.
        :param xpos:  In a selection this is the target horizontal position of the region. This affects behavior when pressing the up or down keys. Use -1 if undefined.
        """


class Selection(Sequence[Region]):
    def __len__(self) -> int:
        "The number of regions in the selection."

    def __delitem__(self, index: int):
        "Delete the region at the given index."

    def is_valid(self) -> bool:
        "Whether this selection is for a valid view."

    def clear(self):
        "Remove all regions from the selection."

    def add(self, x: Union[Region, Point]):
        "Add a Region or Point to the selection. It will be merged with the existing regions if intersecting."

    def add_all(self, regions: Iterator[Region]):
        "Add all the regions from the given iterable."

    def subtract(self, region: Region):
        "Subtract a region from the selection, such that the whole region is no longer contained within the selection."

    def contains(self, region: Region) -> bool:
        "Whether the provided region is contained within the selection."


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
