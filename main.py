#!/usr/bin/env python3

# main.py

from __future__ import annotations

from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Confirm
from typing import Any, Dict, Generator, List, Optional
import json
import os
import re
import requests
import sys
from tools import *

# Set up globals and environment variables
console = Console()
DEBUG = "--debug" in sys.argv

load_dotenv()
OPENWEBUI_URL: str = os.getenv("OPENWEBUI_BASE_URL")
API_KEY: Optional[str] = os.getenv("OPENWEBUI_API_KEY")
MODEL = os.getenv("OPENWEBUI_MODEL")

if not API_KEY:
    API_KEY = console.input("Enter your OPENWEBUI_API_KEY: ").strip()
    if not API_KEY:
        console.print("[red]No API key supplied, exiting.[/red]")
        sys.exit(1)

SYSTEM_PROMPT = ""
file_path = 'prompt.txt'
with open(file_path, 'r') as file:
    SYSTEM_PROMPT = file.read()

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Accept": "text/event-stream",
}

# Streaming
def stream_chat(messages: List[Dict[str, str]]) -> Generator[Dict[str, Any], None, None]:
    """Yield chat completion chunks from Open WebUI (SSE format)."""
    url = f"{OPENWEBUI_URL}/api/chat/completions"
    payload = {"model": MODEL, "stream": True, "max_tokens": 32768, "messages": messages}
    with requests.post(url, headers=HEADERS, json=payload, stream=True, timeout=300) as resp:
        if resp.status_code != 200:
            raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}")
        for line in resp.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            if line.strip() == "data: [DONE]":
                break
            yield json.loads(line[6:])


# Prompt user before shell execution
def execute_tool(call: Dict[str, Any]) -> str:
    name = call.get("tool")
    args = call.get("args", {})
    func = TOOLS.get(name)
    if func is None:
        return f"Unknown tool {name}."
    if name == "run_command":
        # Simple Y/N confirmation without Rich markup tags
        ok = Confirm.ask(f"Run command '{args.get('command')}'?", default=False)
        if not ok:
            return "Command aborted by user."
    try:
        return func(**args)  # type: ignore[arg-type]
    except TypeError as err:
        return f"Argument error: {err}"

# JSON extraction
THINK_RE = re.compile(r"<think[\s\S]*?</think>")
DECODER = json.JSONDecoder()

def extract_tool_json(text: str) -> Optional[Dict[str, Any]]:
    """Return first embedded JSON with a 'tool' key, if any."""
    cleaned = THINK_RE.sub("", text)
    for start in (m.start() for m in re.finditer(r"\{", cleaned)):
        try:
            obj, _ = DECODER.raw_decode(cleaned[start:])
            if isinstance(obj, dict) and "tool" in obj:
                return obj
        except json.JSONDecodeError:
            continue
    return None

# REPL
def pretty_print_call(call: Dict[str, Any]) -> None:
    # Show nicely-indented JSON args using built-in json + Rich styling
    args_str = json.dumps(call.get("args", {}), indent=2)
    console.print(f"[cyan]→ Calling [bold]{call['tool']}[/bold] with args:[/cyan]\n{args_str}")


def main() -> None:

    messages: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    last_think = ""

    console.print("[bold green]Cunningham ready. Type your request. Ctrl‑D to quit.[/bold green]")

    while True:
        try:
            user_input = console.input("You> ")
        except EOFError:
            console.print()
            break

        if user_input.strip() == "/think":
            console.print(last_think or "No thoughts from last response.")
            continue
        if not user_input.strip():
            continue

        messages.append({"role": "user", "content": user_input})

        def stream_assistant() -> str:
            full = ""
            in_think = False
            think_shown = False
            console.print("Assistant: ", end="")
            for chunk in stream_chat(messages):
                token = (
                    chunk["choices"][0].get("delta", {}).get("content")
                    or chunk["choices"][0].get("message", {}).get("content", "")
                )
                if not token:
                    continue
                full += token

                i = 0
                while i < len(token):
                    if not in_think and token.startswith("<think", i):
                        in_think = True
                        if not think_shown:
                            console.print("Thinking...", style="dim", end="")
                            think_shown = True
                        i = token.find(">", i) + 1
                        continue
                    if in_think:
                        end = token.find("</think>", i)
                        if end == -1:
                            break  # still inside think
                        in_think = False
                        i = end + len("</think>")
                        continue
                    next_tag = token.find("<", i)
                    visible = token[i: next_tag if next_tag != -1 else None]
                    if visible:
                        console.print(visible, end="", markup=False)
                    if next_tag == -1:
                        break
                    i = next_tag
            console.print()
            return full

        assistant_reply = stream_assistant()
        think_blocks = THINK_RE.findall(assistant_reply)
        if think_blocks:
            last_think = think_blocks[-1]

        call = extract_tool_json(assistant_reply)
        while call:
            pretty_print_call(call)
            result = execute_tool(call)

            # Stop the loop if the user declined the command
            if result == "Command aborted by user.":
                console.print("[yellow]Command cancelled by user; no further tools executed.[/yellow]")
                messages.append({
                    "role": "assistant",
                    "content": "Okay, I've cancelled that command. Let me know how you'd like to proceed."
                })
                break

            console.print("[magenta]Tool result:[/magenta]")
            print(result)

            messages.append({"role": "tool", "name": call["tool"], "content": result})

            follow = stream_assistant()
            messages.append({"role": "assistant", "content": follow})

            call = extract_tool_json(follow)  # loop continues until no more tools

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\nSession ended.")

