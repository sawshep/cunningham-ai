# tools.py

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Generator, List, Optional
import subprocess

# Tools
"""List contents of the provided directory, or the current
working directory if no argument is provided.
Forward-slashes are appended to directories."""
def list_directory(path: str | None = None) -> str:
    p = Path(path or ".").expanduser().resolve()
    if not p.exists():
        return f"Path {p} does not exist."
    if p.is_file():
        return f"{p} is a file."
    entries = (
        f"{e.name}/" if e.is_dir() else e.name
        for e in p.iterdir()
    )
    return "\n".join(sorted(entries)) or "(empty)"

def read_file(path: str) -> str:
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        return f"File {p} not found."
    lines = p.read_text().splitlines()
    return "\n".join(f"{i+1:4d}: {line}" for i, line in enumerate(lines))

def insert_line(path: str, after_line: int, match: str) -> str:
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        return f"File {p} not found."
    lines = p.read_text().splitlines()
    if not (1 <= after_line <= len(lines)):
        return "Invalid line number."
    if lines[after_line - 1] != match:
        return "Match verification failed."
    lines.insert(after_line, "")
    p.write_text("\n".join(lines) + "\n")
    return f"Inserted blank line after {after_line}."

def replace_line(path: str, line_number: int, match: str, replacement: str) -> str:
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        return f"File {p} not found."
    lines = p.read_text().splitlines()
    if not (1 <= line_number <= len(lines)):
        return "Invalid line number."
    if lines[line_number - 1] != match:
        return "Match verification failed."
    lines[line_number - 1] = replacement
    p.write_text("\n".join(lines) + "\n")
    return f"Replaced line {line_number}."

def run_command(command: str) -> str:
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=120
        )
        return result.stdout
    except subprocess.CalledProcessError as exc:
        return f"Command failed: {exc.output}"
    except subprocess.TimeoutExpired:
        return "Command timed out."

TOOLS: Dict[str, Any] = {
    "list_directory": list_directory,
    "read_file": read_file,
    "insert_line": insert_line,
    "replace_line": replace_line,
    "run_command": run_command,
}
