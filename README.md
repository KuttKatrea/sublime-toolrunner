Sublime - Quick Runner
---

Primarily designed to quickly execute SQL Statements through the SQLCMD
tool, it was extended to let use any command-line tool that can receive
input through pipes.

Quick Runner takes the chosen source input (none, selection, line, block or
file) and pipes them into the chosen tool appending the output to a buffer or
panel.

Commands
---

sql_quick_run
args: 
  source, // none, selection, line, **auto-line**, block, auto-block, file, auto-file
  tool, // group.tool, default.group, choose.group

Tools Configuration
---

```json
tools: {
  "mssql": {

  },
  "grunt": {
    "cmd": "node",
    "default_arguments": [ "grunt" ],
    "arguments": [ "option", "task" ],
    "options": {},
    "flags": {
      "verbose": "-v"
    }
  }
}
```

``` json
groups:
  [
    {
      "name": "MSSQL",
      "type": "mssql",
      "target": {
        "type": "panel", //buffer
        "group": "perview" //new, single
      },
      "configurations": [
        {
          "name": "Production",
          "desc": "Production",
          "params": {
            "server": "production.server.com"
          }
        }
      ]
    }
  ]
```


KeyBindings
---
I don't include default keybindings because they are so intrusive, and as this
plugin is very generic it would be better for the user to define their own set
of bindings depending on the file types and tools used.

View Example.sublime-keymap to view how to configure keybindings to launch
the execution of statements (selected text or full file)
