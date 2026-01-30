#!/usr/bin/env python3
"""nanocode - minimal claude code alternative"""

import glob as globlib, json, os, re, subprocess, urllib.request

# Ollama configuration
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
API_URL = f"{OLLAMA_HOST}/api/generate"
MODEL = os.environ.get("MODEL", "HammerAI/hermes-3-llama-3.1:latest")

# ANSI colors
RESET, BOLD, DIM = "\033[0m", "\033[1m", "\033[2m"
BLUE, CYAN, GREEN, YELLOW, RED = (
    "\033[34m",
    "\033[36m",
    "\033[32m",
    "\033[33m",
    "\033[31m",
)


# --- Tool implementations ---


def read(args):
    lines = open(args["path"]).readlines()
    offset = args.get("offset", 0)
    limit = args.get("limit", len(lines))
    selected = lines[offset : offset + limit]
    return "".join(f"{offset + idx + 1:4}| {line}" for idx, line in enumerate(selected))


def write(args):
    with open(args["path"], "w") as f:
        f.write(args["content"])
    return "ok"


def edit(args):
    text = open(args["path"]).read()
    old, new = args["old"], args["new"]
    if old not in text:
        return "error: old_string not found"
    count = text.count(old)
    if not args.get("all") and count > 1:
        return f"error: old_string appears {count} times, must be unique (use all=true)"
    replacement = (
        text.replace(old, new) if args.get("all") else text.replace(old, new, 1)
    )
    with open(args["path"], "w") as f:
        f.write(replacement)
    return "ok"


def glob(args):
    pattern = (args.get("path", ".") + "/" + args["pat"]).replace("//", "/")
    files = globlib.glob(pattern, recursive=True)
    files = sorted(
        files,
        key=lambda f: os.path.getmtime(f) if os.path.isfile(f) else 0,
        reverse=True,
    )
    return "\n".join(files) or "none"


def grep(args):
    pattern = re.compile(args["pat"])
    hits = []
    for filepath in globlib.glob(args.get("path", ".") + "/**", recursive=True):
        try:
            for line_num, line in enumerate(open(filepath), 1):
                if pattern.search(line):
                    hits.append(f"{filepath}:{line_num}:{line.rstrip()}")
        except Exception:
            pass
    return "\n".join(hits[:50]) or "none"


def bash(args):
    proc = subprocess.Popen(
        args["cmd"], shell=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True
    )
    output_lines = []
    try:
        while True:
            line = proc.stdout.readline()
            if not line and proc.poll() is not None:
                break
            if line:
                print(f"  {DIM}│ {line.rstrip()}{RESET}", flush=True)
                output_lines.append(line)
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
        output_lines.append("\n(timed out after 30s)")
    return "".join(output_lines).strip() or "(empty)"


# --- Tool definitions: (description, schema, function) ---

TOOLS = {
    "read": (
        "Read file with line numbers (file path, not directory)",
        {"path": "string", "offset": "number?", "limit": "number?"},
        read,
    ),
    "write": (
        "Write content to file",
        {"path": "string", "content": "string"},
        write,
    ),
    "edit": (
        "Replace old with new in file (old must be unique unless all=true)",
        {"path": "string", "old": "string", "new": "string", "all": "boolean?"},
        edit,
    ),
    "glob": (
        "Find files by pattern, sorted by mtime",
        {"pat": "string", "path": "string?"},
        glob,
    ),
    "grep": (
        "Search files for regex pattern",
        {"pat": "string", "path": "string?"},
        grep,
    ),
    "bash": (
        "Run shell command",
        {"cmd": "string"},
        bash,
    ),
}


def run_tool(name, args):
    try:
        return TOOLS[name][2](args)
    except Exception as err:
        return f"error: {err}"


def make_tools_prompt():
    """Generate tool descriptions for the system prompt"""
    tools_desc = [
        "You are a coding assistant with access to tools for file operations.",
        "",
        "AVAILABLE TOOLS:",
    ]

    for name, (description, params, _fn) in TOOLS.items():
        param_list = ", ".join(f"{k}: {v}" for k, v in params.items())
        tools_desc.append(f"  {name}({param_list}) - {description}")

    tools_desc.extend([
        "",
        "TOOL USAGE INSTRUCTIONS:",
        "When you need to use a tool, you MUST respond with valid JSON in exactly this format:",
        '{"tool": "tool_name", "args": {"param1": "value1", "param2": "value2"}}',
        "",
        "Examples:",
        '- To list Python files: {"tool": "glob", "args": {"pat": "*.py"}}',
        '- To read a file: {"tool": "read", "args": {"path": "script.py"}}',
        '- To search for text: {"tool": "grep", "args": {"pat": "function"}}',
        "",
        "You may include a brief explanation BEFORE the JSON, but the JSON must be on its own line.",
        "After receiving tool results, continue helping the user with their request.",
    ])
    return "\n".join(tools_desc)


def messages_to_prompt(messages):
    """Convert messages array to a single prompt string"""
    prompt_parts = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if role == "system":
            prompt_parts.append(f"System: {content}\n")
        elif role == "user":
            prompt_parts.append(f"User: {content}\n")
        elif role == "assistant":
            prompt_parts.append(f"Assistant: {content}\n")
    prompt_parts.append("Assistant:")
    return "\n".join(prompt_parts)


def call_api(messages, system_prompt):
    """Call Ollama /api/generate endpoint"""
    prompt = messages_to_prompt(messages)

    request = urllib.request.Request(
        API_URL,
        data=json.dumps(
            {
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                },
            }
        ).encode(),
        headers={
            "Content-Type": "application/json",
        },
    )
    response = urllib.request.urlopen(request)
    data = json.loads(response.read())
    return data["response"]


def parse_tool_call(text):
    """Extract tool call JSON from response text"""
    # Try to find JSON in the response - be more flexible with the pattern
    # Match any JSON object that contains "tool" and "args" fields
    json_pattern = r'\{[^{}]*"tool"\s*:\s*"[^"]+"\s*,\s*"args"\s*:\s*\{[^}]*\}[^{}]*\}'
    json_match = re.search(json_pattern, text)

    if json_match:
        try:
            json_str = json_match.group(0)
            tool_data = json.loads(json_str)
            if "tool" in tool_data and "args" in tool_data:
                # Remove the JSON from the text
                text_before = text[:json_match.start()].strip()
                text_after = text[json_match.end():].strip()
                explanation = (text_before + " " + text_after).strip()
                return tool_data["tool"], tool_data["args"], explanation
        except json.JSONDecodeError as e:
            # JSON parsing failed, return as regular text
            pass

    return None, None, text


def separator():
    return f"{DIM}{'─' * min(os.get_terminal_size().columns, 80)}{RESET}"


def render_markdown(text):
    return re.sub(r"\*\*(.+?)\*\*", f"{BOLD}\\1{RESET}", text)


def main():
    print(f"{BOLD}nanocode{RESET} | {DIM}{MODEL} (Ollama) | {os.getcwd()}{RESET}\n")
    messages = []
    system_prompt = f"You are a concise coding assistant. Current working directory: {os.getcwd()}.\n\n{make_tools_prompt()}"

    # Add system message
    messages.append({"role": "system", "content": system_prompt})

    while True:
        try:
            print(separator())
            user_input = input(f"{BOLD}{BLUE}❯{RESET} ").strip()
            print(separator())
            if not user_input:
                continue
            if user_input in ("/q", "exit"):
                break
            if user_input == "/c":
                messages = [{"role": "system", "content": system_prompt}]
                print(f"{GREEN}⏺ Cleared conversation{RESET}")
                continue

            messages.append({"role": "user", "content": user_input})

            # agentic loop: keep calling API until no more tool calls
            while True:
                response_text = call_api(messages, system_prompt)
                tool_name, tool_args, explanation = parse_tool_call(response_text)

                # Show explanation if present
                if explanation:
                    print(f"\n{CYAN}⏺{RESET} {render_markdown(explanation)}")

                if tool_name:
                    # Tool call detected
                    arg_preview = str(list(tool_args.values())[0])[:50] if tool_args else ""
                    print(
                        f"\n{GREEN}⏺ {tool_name.capitalize()}{RESET}({DIM}{arg_preview}{RESET})"
                    )

                    result = run_tool(tool_name, tool_args)
                    result_lines = result.split("\n")
                    preview = result_lines[0][:60]
                    if len(result_lines) > 1:
                        preview += f" ... +{len(result_lines) - 1} lines"
                    elif len(result_lines[0]) > 60:
                        preview += "..."
                    print(f"  {DIM}⎿  {preview}{RESET}")

                    # Add assistant response and tool result to history
                    messages.append({"role": "assistant", "content": response_text})
                    messages.append({"role": "user", "content": f"Tool result:\n{result}"})
                else:
                    # No tool call, just regular response
                    messages.append({"role": "assistant", "content": response_text})
                    break

            print()

        except (KeyboardInterrupt, EOFError):
            break
        except Exception as err:
            print(f"{RED}⏺ Error: {err}{RESET}")


if __name__ == "__main__":
    main()
