# Claude Code Session Logger

Automatically log everything Claude Code does during your sessions — every prompt, file read, edit, bash command, subagent spawn, and session lifecycle event.

Logs are saved as **daily Markdown files** in \~/.claude/session-logs/\ and automatically indexed into **Basic Memory** for long-term context retention.

## Features

- **Daily Markdown Logs:** Organized by date in \~/.claude/session-logs/\.
- **Basic Memory Integration:** Automatically generates session summaries and stores them in your Basic Memory workspace for future retrieval.
- **Rich Context:** Captures session IDs, working directories, tool calls, bash commands, and user prompts.
- **Hook-based:** Zero-overhead integration using Claude Code's native lifecycle hooks.

## What gets logged

| Event | What it captures |
|---|---|
| **SessionStart** | Session ID, working directory |
| **UserPromptSubmit** | Every prompt you send to Claude |
| **PreToolUse** | Every tool call with details (file paths, commands, search patterns, subagent info) |  
| **PostToolUse** | Tool result size |
| **Stop** | End of each turn with stop reason |
| **SessionEnd** | Session close & Basic Memory sync |

## Setup

### Requirements

- Python 3.6+
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code)
- (Optional) [Basic Memory](https://github.com/lucasaugustodev/basic-memory) for long-term memory support.

### 1. Copy the script

\\\ash
mkdir -p ~/.claude/scripts
cp claude-session-logger.py ~/.claude/scripts/claude-session-logger.py
chmod +x ~/.claude/scripts/claude-session-logger.py
\\\

### 2. Configure hooks

Add the hooks to your Claude Code settings. You can use either:

- **Global config:** \~/.claude/settings.json\
- **Per-project config:** \.claude/settings.json\

If the file already exists, **merge** the \hooks\ block with your existing config.

Copy the hooks block from [\hooks-config.json\](hooks-config.json) into your settings file.

<details>
<summary>Full hooks config to add</summary>

\\\json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/scripts/claude-session-logger.py --event SessionStart"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/scripts/claude-session-logger.py --event UserPromptSubmit"      
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/scripts/claude-session-logger.py --event PreToolUse"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/scripts/claude-session-logger.py --event PostToolUse"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/scripts/claude-session-logger.py --event Stop"
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/scripts/claude-session-logger.py --event SessionEnd"
          }
        ]
      }
    ]
  }
}
\\\

</details>

> **Windows note:** If \python3\ is not recognized, replace it with \python\ in all hook commands.        

### 3. Basic Memory Configuration (Optional)

To enable **Basic Memory** integration, ensure the \BASIC_MEMORY_DIR\ variable in \claude-session-logger.py\ points to your workspace sessions folder:

\\\python
BASIC_MEMORY_DIR = Path(r"C:\Users\Lucas\basic-memory\workspace\sessoes")
\\\

The script will automatically create a session note (e.g., \sessao-2026-03-02-1430.md\) in this directory when a session ends.

## How it works

The script uses [Claude Code hooks](https://docs.anthropic.com/en/docs/claude-code/hooks) — shell commands that Claude Code executes automatically at specific lifecycle events. Each hook passes event data as JSON via stdin, and the script parses it to write structured Markdown logs.

At the end of each session, the script summarizes the activity (prompts, tools used, files edited) and generates a structured note for **Basic Memory**, allowing you to search through your past interactions efficiently.

## Log location

Markdown logs are stored in:
\~/.claude/session-logs/\

## Customization

- **Change log directory:** Edit \LOG_DIR\ at the top of the script.
- **Change Basic Memory workspace:** Edit \BASIC_MEMORY_DIR\.
- **Prompt truncation:** Long prompts are truncated at 2000 characters by default.

## License

MIT
