ToolRunner for Sublime Text
---
Primarily designed to quickly execute SQL Statements through the **SQLCMD**
command-line tool, it was extended to allow execution of any command line tool.

ToolRunner takes the chosen source input (none, selection, line, block or
file) and pipes it into the chosen tool appending the output to a buffer or
panel.

Tools
---
A tool is an external application that is going to be run by Tool Runner.
The tools must be defined in the settings file.

ToolRuner comes with some preconfigured tools:

**Shells**

 - cmd
 - bash

**Database Clients**

 - sqlcmd (SQL Server command-line client)
 - mysql
 - mongo

**Interpreters**

 - python
 - ruby
 - nodejs
 - JScript (Cscript host)
 - VBScript (Cscript host)

But you can add your own.

Base Configuration
---
This is the general view of configuration options

```javascript
{
  // Preconfigured tools
  "default_tools": [],

  //User-defined tools.
  //Tools added in Host, Platform and User settings will be merged.
  "user_tools": [],

  // Executable overrides for specific tool.
  "user_tool_overrides": {
    "toolname": "cmdpath"
  },

  // User groups and profiles configuration.
  // Groups added in Host, Platform and User settings will be merged.
  // Check "Groups Configuration"
  "user_groups": [],

  // Default profile for the given groups.
  "default_profiles": {
    "group": "profile"
  },

  // Whether to dump debug messages to console
  "debug": false
}
```

Tool Configuration
---
This is the model for tool configuration options (default_tools, user_tools)

```javascript
[
  {
    // Friendly name to reference this tool
    // Optional. Defaults to cmd configuration value
    "name": "CMD",
    // Executable to call when this tool is run. Must be on PATH or must
    // be an absolute path
    // Required.
    "cmd": "sqlcmd",
    // Arguments that the command receives.
    // "${flags}", "${named_args}", "${positional_args}" are replaced as individual elements by its corresponding params.
    // Any other values are passed as-is.
    "arguments": [ "${flags}", "${named_args}", "${positional_args}" ],
    "options": {
      // Configuration of the input string passed to the tool
      "input": {
        //"pipe" pipes the input to the tool.
        //"manual" requires an argument "${input}" to be filled with the full input
        //"none" prevents to pass any input to the tool.
        "mode": "pipe",
        // Launch command even if input is empty. Forced to true when mode=none
        "allow_empty": false,
        // Python codec to encode the input for the tool.
        "codec": "utf_8"
      },
      // Configuration for the execution results view
      "output": {
        // "buffer" creates a normal view next to the current view
        // "panel" creates an output panel (like a build command)
        "type": "buffer",
        // Syntax file to apply to output
        "syntax_file": "Packages/${package}/lang/ToolRunner Output.tmLanguage",
        // Python codec to decode the output of the tool.
        "codec": "utf_8"
      },
      // Parameters this tool receives.
      // Key is the friendly name that will be used to pass this parameter
      "params": {
        "server": {
          // Indicates the type of parameter.
          // Defaults to "named"
          "type": "named",
          // Argument that will be prepended to this param value
          "argument": "-S"
        },
        "quiet": { "type": "flag", "argument": "-Q" },
        "address": { "type": "positional", "order": "1", "required": false }
      }
    }
  }
}
```

Tool Profile Groups Configuration
---

``` json
[
  {
    "name": "MSSQL",

    "tool": "mssql",

    "input": "",
    "output": "",
    "params": "",

    "profiles": [
      {
        "name": "Production",
        "desc": "Production",
        "tool": "", // overrides default-tool
        "input": {},
        "output": {}, // override options
        "params": {
          "server": "production.server.com"
        }
      }
    ]
  }
]
```


Commands (for use in Palette or Keybindings)
---
```json
[
  {
    "command": "tool_runner",
    "args": {
      // If none tool or group are passed, there will be a selector for Group/Profile
      "tool": "sqlcmd", // tool name
      "group": "group", // group name
      "default_profile": false, //
      "profile": "profile_name", // profile name
      "input": "auto-file", // [Required] none, selection, line, **auto-line**, block, auto-block, file, auto-file
      // If you use none be sure the command has allow_empty = true
      "output": {}, // overrides output config
      // tool params as defined in tool's params config.
      // Overrides profile params
      "params": {}
    }
  },
  {
    //Cancels the currently running tool for that view.
    "command": "tool_runner_cancel_running"
  },
  {
    //Changes focus to current output panel/view for that source view.
    "command": "tool_runner_focus_output"
  },
  {
    // Changes the default profile for a group.
    "command": "tool_runner_switch_default_profile",
    "args": {
      // If not indicated, will display the palette to select the group
      // to change the default for
      // The selected group will be saved in host-specific settings
      "profile_group": "MSSQL"
    }
  },

  {
    // Open settings file for indicated scope
    "command": "tool_runner_open_settings",
    "args": {
      // Scope to open settings for.
      // If no scope is passed, a panel will ask for it
      "scope": "default" // default, user, platform, host
    }
  }
]
```

Palette Commands and KeyBindings
---
I don't include default keybindings because they are so intrusive, and as this plugin is very generic it would be better for the user to define their own set of bindings depending on the file types and tools used.

View Example.sublime-keymap to view how to configure keybindings to launch the execution of statements (selected text or full file)

But you can create your own keybindings and commands, for example:

```javascript
{
  "keys": ["f5"],
  "command": "tool_runner"
},
{
  "keys": ["ctrl+f5"],
  "command": "tool_runner_cancel_current"
}
```

will allow you to execute ToolRunner with F5 (asking you which Tool/Profile to use), and CTRL+F5 to cancel the current running command for that view

Future
---
  - Better support for CMD
    The current way of piping the commands generates strange unwanted output (mainly the display of the command prompt).
    Better support may be given creating a temporary BAT file and executing it instead of piping, but you will have to use bat semantics too (eg. %%A instead of %A in for loops)

  - Support for Windows CScript (JScript, VBScript).
    CScript requires always a file, so we must generate a temporary file to execute, just like in the previous point.

  - Testing on MacOS
