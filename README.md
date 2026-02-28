# Claude Code Session Logger

Automatically log everything Claude Code does during your sessions — every prompt, file read, edit, bash command, subagent spawn, and session lifecycle event.

Logs are saved as **daily Markdown files** in `~/.claude/session-logs/`.

## What gets logged

| Event | What it captures |
|---|---|
| **SessionStart** | Session ID, working directory |
| **UserPromptSubmit** | Every prompt you send to Claude |
| **PreToolUse** | Every tool call with details (file paths, commands, search patterns, subagent info) |
| **PostToolUse** | Tool result size |
| **Stop** | End of each turn with stop reason |
| **SessionEnd** | Session close |

## Example output

```markdown
# Claude Code Session Log - 2026-02-28

---

## Session Started - 14:30:00
- **Session ID:** `abc-123`
- **Working Directory:** `/home/user/my-project`

### [14:30:05] User Prompt
` ` `
fix the login bug in auth.ts
` ` `

### [14:30:07] Tool Call: `Read`
- **Read file:** `/home/user/my-project/src/auth.ts`

- **Result `Read`:** 2340 chars

### [14:30:10] Tool Call: `Edit`
- **Edit file:** `/home/user/my-project/src/auth.ts`

- **Result `Edit`:** 150 chars

### [14:30:12] Tool Call: `Bash`
- **Description:** Run tests
- **Command:** `npm test`

- **Result `Bash`:** 890 chars

### [14:30:15] Turn Ended
- **Reason:** end_turn

## Session Ended - 14:35:00
- **Session ID:** `abc-123`

---
```

## Setup

### Requirements

- Python 3.6+
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code)

### 1. Copy the script

```bash
mkdir -p ~/.claude/scripts
cp claude-session-logger.py ~/.claude/scripts/claude-session-logger.py
chmod +x ~/.claude/scripts/claude-session-logger.py
```

### 2. Configure hooks

Add the hooks to your Claude Code settings. You can use either:

- **Global config:** `~/.claude/settings.json`
- **Per-project config:** `.claude/settings.json`

If the file already exists, **merge** the `hooks` block with your existing config.

Copy the hooks block from [`hooks-config.json`](hooks-config.json) into your settings file.

<details>
<summary>Full hooks config to add</summary>

```json
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
```

</details>

> **Windows note:** If `python3` is not recognized, replace it with `python` in all hook commands.

### 3. Done

Start a new Claude Code session. Logs will appear in `~/.claude/session-logs/` as daily Markdown files (e.g. `2026-02-28.md`).

## Log location

```
~/.claude/session-logs/
  2026-02-25.md
  2026-02-26.md
  2026-02-27.md
  2026-02-28.md
```

## How it works

The script uses [Claude Code hooks](https://docs.anthropic.com/en/docs/claude-code/hooks) — shell commands that Claude Code executes automatically at specific lifecycle events. Each hook passes event data as JSON via stdin, and the script parses it to write structured Markdown logs.

The script:
1. Receives the event type via `--event` argument
2. Reads event data (JSON) from stdin
3. Appends a formatted entry to the daily log file
4. Creates a new log file automatically when the day changes

## Customization

**Change log directory:** Edit the `LOG_DIR` variable at the top of the script.

**Change timestamp format:** Edit the `timestamp()` function.

**Add more tool details:** Extend the `handle_pre_tool_use()` function with additional `elif` blocks for specific tool names.

**Prompt truncation:** Long prompts are truncated at 2000 characters. Change the limit in `handle_user_prompt()`.

## License

MIT
