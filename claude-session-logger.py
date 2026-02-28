#!/usr/bin/env python3
"""Claude Code Session Logger - Logs all session activity as daily Markdown files."""

import json
import sys
import argparse
from datetime import datetime
from pathlib import Path


LOG_DIR = Path.home() / ".claude" / "session-logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def get_log_file():
    today = datetime.now().strftime("%Y-%m-%d")
    return LOG_DIR / f"{today}.md"


def timestamp():
    return datetime.now().strftime("%H:%M:%S")


def append_log(content: str):
    log_file = get_log_file()
    is_new = not log_file.exists()
    with open(log_file, "a", encoding="utf-8") as f:
        if is_new:
            today = datetime.now().strftime("%Y-%m-%d")
            f.write(f"# Claude Code Session Log - {today}\n\n")
        f.write(content)


def read_stdin():
    try:
        if not sys.stdin.isatty():
            return json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        pass
    return {}


def handle_session_start(data):
    session_id = data.get("session_id", "unknown")
    cwd = data.get("cwd", "unknown")
    append_log(
        f"---\n\n"
        f"## Session Started - {timestamp()}\n"
        f"- **Session ID:** `{session_id}`\n"
        f"- **Working Directory:** `{cwd}`\n\n"
    )


def handle_user_prompt(data):
    prompt = data.get("prompt", "(empty)")
    if len(prompt) > 2000:
        prompt = prompt[:2000] + "\n...(truncated)"
    append_log(
        f"### [{timestamp()}] User Prompt\n"
        f"```\n{prompt}\n```\n\n"
    )


def handle_pre_tool_use(data):
    tool_name = data.get("tool_name", "unknown")
    tool_input = data.get("tool_input", {})

    entry = f"### [{timestamp()}] Tool Call: `{tool_name}`\n"

    if tool_name == "Read":
        file_path = tool_input.get("file_path", "unknown")
        entry += f"- **Read file:** `{file_path}`\n"
    elif tool_name == "Write":
        file_path = tool_input.get("file_path", "unknown")
        entry += f"- **Write file:** `{file_path}`\n"
    elif tool_name == "Edit":
        file_path = tool_input.get("file_path", "unknown")
        entry += f"- **Edit file:** `{file_path}`\n"
    elif tool_name == "Bash":
        command = tool_input.get("command", "")
        desc = tool_input.get("description", "")
        if desc:
            entry += f"- **Description:** {desc}\n"
        entry += f"- **Command:** `{command}`\n"
    elif tool_name == "Glob":
        pattern = tool_input.get("pattern", "")
        entry += f"- **Pattern:** `{pattern}`\n"
    elif tool_name == "Grep":
        pattern = tool_input.get("pattern", "")
        path = tool_input.get("path", ".")
        entry += f"- **Search:** `{pattern}` in `{path}`\n"
    elif tool_name == "Task":
        desc = tool_input.get("description", "")
        agent_type = tool_input.get("subagent_type", "unknown")
        entry += f"- **Subagent:** `{agent_type}` - {desc}\n"
    elif tool_name == "WebFetch":
        url = tool_input.get("url", "")
        entry += f"- **URL:** `{url}`\n"
    elif tool_name == "WebSearch":
        query = tool_input.get("query", "")
        entry += f"- **Query:** `{query}`\n"
    else:
        keys = list(tool_input.keys())[:5]
        if keys:
            entry += f"- **Params:** {', '.join(keys)}\n"

    entry += "\n"
    append_log(entry)


def handle_post_tool_use(data):
    tool_name = data.get("tool_name", "unknown")
    tool_output = data.get("tool_output", "")

    if isinstance(tool_output, str):
        output_preview = tool_output[:300]
        if len(tool_output) > 300:
            output_preview += "..."
    elif isinstance(tool_output, dict):
        output_preview = json.dumps(tool_output, ensure_ascii=False)[:300]
    else:
        output_preview = str(tool_output)[:300]

    append_log(
        f"- **Result `{tool_name}`:** {len(str(tool_output))} chars\n\n"
    )


def handle_stop(data):
    reason = data.get("stop_reason", "unknown")
    append_log(
        f"### [{timestamp()}] Turn Ended\n"
        f"- **Reason:** {reason}\n\n"
    )


def handle_session_end(data):
    session_id = data.get("session_id", "unknown")
    append_log(
        f"## Session Ended - {timestamp()}\n"
        f"- **Session ID:** `{session_id}`\n\n"
        f"---\n\n"
    )


EVENT_HANDLERS = {
    "SessionStart": handle_session_start,
    "UserPrompt": handle_user_prompt,
    "UserPromptSubmit": handle_user_prompt,
    "PreToolUse": handle_pre_tool_use,
    "PostToolUse": handle_post_tool_use,
    "Stop": handle_stop,
    "SessionEnd": handle_session_end,
}


def main():
    parser = argparse.ArgumentParser(description="Claude Code Session Logger")
    parser.add_argument("--event", required=True, help="Event type")
    args = parser.parse_args()

    data = read_stdin()
    handler = EVENT_HANDLERS.get(args.event)
    if handler:
        handler(data)


if __name__ == "__main__":
    main()
