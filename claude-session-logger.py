#!/usr/bin/env python3
"""Claude Code Session Logger - Logs all session activity as daily Markdown files.
Also generates Basic Memory MCP notes per session."""

import json
import sys
import os
import argparse
import re
from datetime import datetime
from pathlib import Path


LOG_DIR = Path.home() / ".claude" / "session-logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

BASIC_MEMORY_DIR = Path(r"C:\Users\Lucas\basic-memory\workspace\sessoes")

STATE_FILE = LOG_DIR / ".current-session.json"


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


# --- State management for Basic Memory accumulation ---


def load_state():
    """Load accumulated session state from disk."""
    try:
        if STATE_FILE.exists():
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError):
        pass
    return None


def save_state(state):
    """Save session state to disk."""
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except IOError:
        pass


def delete_state():
    """Remove the state file."""
    try:
        if STATE_FILE.exists():
            STATE_FILE.unlink()
    except IOError:
        pass


def init_state(session_id, cwd):
    """Initialize a new session state."""
    state = {
        "session_id": session_id,
        "cwd": cwd,
        "start_time": datetime.now().isoformat(),
        "prompts": [],
        "tools": [],
        "files_edited": [],
        "bash_commands": [],
    }
    save_state(state)
    return state


def accumulate_prompt(prompt):
    """Add a user prompt to the state."""
    state = load_state()
    if state is None:
        return
    truncated = prompt[:500] if len(prompt) > 500 else prompt
    state["prompts"].append(truncated)
    save_state(state)


def accumulate_tool(tool_name, tool_input):
    """Add a tool usage to the state."""
    state = load_state()
    if state is None:
        return

    tool_entry = {"name": tool_name}

    if tool_name in ("Read", "Write", "Edit"):
        file_path = tool_input.get("file_path", "unknown")
        tool_entry["detail"] = file_path
        if tool_name in ("Write", "Edit") and file_path not in state["files_edited"]:
            state["files_edited"].append(file_path)
    elif tool_name == "Bash":
        command = tool_input.get("command", "")
        desc = tool_input.get("description", "")
        tool_entry["detail"] = desc if desc else command[:200]
        state["bash_commands"].append(command[:200])
    elif tool_name == "Glob":
        tool_entry["detail"] = tool_input.get("pattern", "")
    elif tool_name == "Grep":
        pattern = tool_input.get("pattern", "")
        path = tool_input.get("path", ".")
        tool_entry["detail"] = f"{pattern} in {path}"
    elif tool_name in ("Agent", "Task"):
        desc = tool_input.get("description", "")
        agent_type = tool_input.get("subagent_type", "unknown")
        tool_entry["detail"] = f"{agent_type}: {desc}"
    elif tool_name == "WebFetch":
        tool_entry["detail"] = tool_input.get("url", "")
    elif tool_name == "WebSearch":
        tool_entry["detail"] = tool_input.get("query", "")
    else:
        keys = list(tool_input.keys())[:5]
        tool_entry["detail"] = ", ".join(keys) if keys else ""

    state["tools"].append(tool_entry)
    save_state(state)


def extract_project_name(cwd):
    """Extract project name from working directory (last folder in path)."""
    if not cwd or cwd == "unknown":
        return "unknown"
    path = Path(cwd)
    return path.name or "unknown"


def slugify(text):
    """Convert text to a slug-friendly format."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def generate_basic_memory_note(state):
    """Generate a Basic Memory .md note from accumulated session state."""
    BASIC_MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    start_dt = datetime.fromisoformat(state["start_time"])
    end_dt = datetime.now()

    date_str = start_dt.strftime("%Y-%m-%d")
    time_str = start_dt.strftime("%H%M")
    start_time_display = start_dt.strftime("%H:%M")
    end_time_display = end_dt.strftime("%H:%M")

    session_id = state.get("session_id", "unknown")
    cwd = state.get("cwd", "unknown")
    project_name = extract_project_name(cwd)
    project_slug = slugify(project_name)

    permalink = f"sessao-{date_str}-{time_str}"
    filename = f"{permalink}.md"

    # Build content
    lines = []
    lines.append("---")
    lines.append(f"title: Sess\u00e3o Claude Code - {date_str} {start_time_display}")
    lines.append(f"tags: [sessao, claude-code, {project_slug}]")
    lines.append("type: session-log")
    lines.append(f"permalink: {permalink}")
    lines.append("---")
    lines.append("")
    lines.append(f"# Sess\u00e3o Claude Code - {date_str} {start_time_display}")
    lines.append("")
    lines.append("## Observations")
    lines.append(f"- [session] ID: {session_id}")
    lines.append(f"- [directory] {cwd}")
    lines.append(f"- [duration] In\u00edcio {start_time_display} - Fim {end_time_display}")

    # Prompts
    for prompt in state.get("prompts", []):
        clean = prompt.replace("\n", " ").strip()
        if len(clean) > 500:
            clean = clean[:500] + "..."
        lines.append(f'- [prompt] "{clean}"')

    # Tools (deduplicated)
    seen_tools = set()
    for tool in state.get("tools", []):
        name = tool.get("name", "unknown")
        detail = tool.get("detail", "")
        key = f"{name}:{detail}"
        if key in seen_tools:
            continue
        seen_tools.add(key)
        if detail:
            lines.append(f"- [tool] {name}: {detail}")
        else:
            lines.append(f"- [tool] {name}")

    # Decisions inferred from file edits
    for f_path in state.get("files_edited", []):
        lines.append(f"- [decision] Editou arquivo: {f_path}")

    lines.append("")
    lines.append("## Relations")
    lines.append(f"- relates_to [[{project_name}]]")
    lines.append("")

    output_path = BASIC_MEMORY_DIR / filename
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# --- Event handlers ---


def handle_session_start(data):
    session_id = data.get("session_id", "unknown")
    cwd = data.get("cwd", "unknown")
    append_log(
        f"---\n\n"
        f"## Session Started - {timestamp()}\n"
        f"- **Session ID:** `{session_id}`\n"
        f"- **Working Directory:** `{cwd}`\n\n"
    )
    # Flush orphaned state from a previous crashed session
    old_state = load_state()
    if old_state is not None:
        try:
            generate_basic_memory_note(old_state)
        except Exception:
            pass
    # Initialize fresh state
    init_state(session_id, cwd)


def handle_user_prompt(data):
    prompt = data.get("prompt", "(empty)")
    # Truncate very long prompts
    if len(prompt) > 2000:
        prompt = prompt[:2000] + "\n...(truncated)"
    append_log(
        f"### [{timestamp()}] User Prompt\n"
        f"```\n{prompt}\n```\n\n"
    )
    # Accumulate for Basic Memory
    accumulate_prompt(data.get("prompt", "(empty)"))


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
        # Generic: log input keys
        keys = list(tool_input.keys())[:5]
        if keys:
            entry += f"- **Params:** {', '.join(keys)}\n"

    entry += "\n"
    append_log(entry)
    # Accumulate for Basic Memory
    accumulate_tool(tool_name, tool_input)


def handle_post_tool_use(data):
    tool_name = data.get("tool_name", "unknown")
    tool_output = data.get("tool_output", "")

    # Only log brief output summaries to avoid huge logs
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
    # Overwrite BM note with latest data (fallback if SessionEnd never fires)
    state = load_state()
    if state is not None:
        try:
            generate_basic_memory_note(state)
        except Exception:
            pass


def handle_session_end(data):
    session_id = data.get("session_id", "unknown")
    append_log(
        f"## Session Ended - {timestamp()}\n"
        f"- **Session ID:** `{session_id}`\n\n"
        f"---\n\n"
    )
    # Final Basic Memory note + cleanup
    state = load_state()
    if state is not None:
        try:
            generate_basic_memory_note(state)
        except Exception:
            pass
        delete_state()


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
