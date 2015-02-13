Sublime - ToolRunner
---

Primarily designed to quickly execute SQL Statements through the SQLCMD
tool, it was extended to let use any command-line tool.

ToolRunner takes the chosen source input (none, selection, line, block or
file) and pipes it into the chosen tool appending the output to a buffer or
panel.

Base Configuration
---
```json
{
  "default_tools": {}, // Check Tools Configuration

  "user_tools": {}, //Check Tools configuration

  "tools_override": {
    "toolname": "cmdpath"
  },

  "user_groups": [], // Check groups configuration

  "user_groups_default_profiles": {
    "Group": "profile"
  },

  "debug": false
}
```

Tool Configuration
---

```json
{
  "mssql": {
    "cmd": "sqlcmd", // Required.
    "arguments": [ "${flags}", "${named_args}", "${positional_args}" ], // Arguments that must be passed always. Defaults to []
    "options": {
      // If manual and not in arguments, there will not be input sent to tool
      "input": {
        "mode": "pipe", //pipe, manual. If manual it must be added in arguments as "${input}"
        "allow_empty": false, // Launch command even if input is empty string.
        "codec": "utf-8"
      },
      "output": {
        "type": "panel", //buffer
        "reuse": "view", //always view never
        "split": "bottom", //top, right, left, none. Only for type: buffer
        "focus": {
          // Focus the output view when focusing the source view from which it spawned
          // If its a panel, make it visible. If it's a view, make it visible in its group (except if its the same group of the input file)
          "onsourcefocus": false,
          "onexecution": true
        },
        "syntax_file": null, // Defaults to "ToolRunner Output.tmLanguage"
        "codec": "utf-8",
        "keep_reusing_after_save": false
      },
      "params": {
        "server": { "type": "named", "argument": "-S" },
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
      "group": "[select]", // [select], group name
      "profile": "[select]", // [default], [select], profile name
      "input": "auto-line", // [Required] none, selection, line, **auto-line**, block, auto-block, file, auto-file
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
  },w

  {
    // Open settings file for indicated scope
    "command": "tool_runner_open_settings",
    "args": {
      // Scope to open settings for.
      // If no scope is passed, a panel will ask for it
      "scope": "default" // default, user, os, host
    }
  }
]
```

Palette Commands and KeyBindings
---
I don't include default keybindings because they are so intrusive, and as this
plugin is very generic it would be better for the user to define their own set
of bindings depending on the file types and tools used.

View Example.sublime-keymap to view how to configure keybindings to launch
the execution of statements (selected text or full file)
