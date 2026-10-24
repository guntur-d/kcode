"""Local tools: read/write/edit/bash/glob/grep/list_dir.

All stdlib, Python 3.8 compatible, Windows-safe (no pty, no fcntl).
"""
import fnmatch
import glob as _glob
import os
import re
import subprocess
from typing import Any, Callable, Dict, List


def _resolve(path, cwd):
    # type: (str, str) -> str
    if os.path.isabs(path):
        return path
    return os.path.join(cwd or os.getcwd(), path)


def _int(value, default):
    # type: (Any, int) -> int
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default


def tool_read(path, offset=1, limit=2000, cwd=None):
    # type: (str, int, int, str) -> str
    p = _resolve(path, cwd)
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    total = len(lines)
    start = max(1, offset or 1) - 1
    end = start + (limit or 2000)
    chunk = lines[start:end]
    out = ["%d: %s" % (start + i + 1, l.rstrip("\n")) for i, l in enumerate(chunk)]
    return "\n".join(out) + ("\n... (%d total lines)" % total if end < total else "")


def tool_write(path, content, cwd=None):
    # type: (str, str, str) -> str
    p = _resolve(path, cwd)
    parent = os.path.dirname(os.path.abspath(p))
    if parent and not os.path.exists(parent):
        os.makedirs(parent)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    return "wrote %d bytes to %s" % (len(content), p)


def tool_edit(path, old_string, new_string, cwd=None):
    # type: (str, str, str, str) -> str
    p = _resolve(path, cwd)
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        src = f.read()
    if old_string not in src:
        raise ValueError("old_string not found in %s" % p)
    if src.count(old_string) > 1:
        raise ValueError("old_string matches %d times; be more specific" % src.count(old_string))
    with open(p, "w", encoding="utf-8") as f:
        f.write(src.replace(old_string, new_string, 1))
    return "edited %s" % p


def tool_bash(command, cwd=None, timeout=60):
    # type: (str, str, int) -> str
    # Windows Server 2016: use shell=True, no pty. Capture combined output.
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=cwd or os.getcwd(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout or 60,
            universal_newlines=True,
        )
        out = proc.stdout or ""
        if len(out) > 20000:
            out = out[:20000] + "\n... [truncated]"
        return "[exit %d]\n%s" % (proc.returncode, out)
    except subprocess.TimeoutExpired:
        return "[timeout after %ss]" % (timeout or 60)


def tool_glob(pattern, cwd=None):
    # type: (str, str) -> str
    base = cwd or os.getcwd()
    # support ** via glob module
    hits = _glob.glob(os.path.join(base, pattern), recursive=True)
    rel = [os.path.relpath(h, base) for h in hits[:200]]
    return "\n".join(rel) if rel else "(no matches)"


def tool_grep(pattern, include="*", cwd=None):
    # type: (str, str, str) -> str
    base = cwd or os.getcwd()
    rx = re.compile(pattern)
    out = []  # type: List[str]
    for root, _dirs, files in os.walk(base):
        # skip noisy dirs
        if ".git" in root.split(os.sep) or "__pycache__" in root.split(os.sep):
            continue
        for fn in files:
            if include and include != "*":
                if not fnmatch.fnmatch(fn, include):
                    continue
            fp = os.path.join(root, fn)
            try:
                with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f, 1):
                        if rx.search(line):
                            rel = os.path.relpath(fp, base)
                            out.append("%s:%d: %s" % (rel, i, line.strip()[:300]))
                            if len(out) >= 200:
                                return "\n".join(out)
            except Exception:
                continue
    return "\n".join(out) if out else "(no matches)"


def tool_list_dir(path=".", cwd=None):
    # type: (str, str) -> str
    p = _resolve(path or ".", cwd)
    names = sorted(os.listdir(p))
    rows = []
    for n in names[:300]:
        fp = os.path.join(p, n)
        rows.append(n + "/" if os.path.isdir(fp) else n)
    return "\n".join(rows)


def _ad_read(args, cwd):
    # type: (Dict[str, Any], str) -> str
    return tool_read(args.get("path", ""), _int(args.get("offset"), 1), _int(args.get("limit"), 2000), cwd)


def _ad_write(args, cwd):
    # type: (Dict[str, Any], str) -> str
    return tool_write(args.get("path", ""), args.get("content", ""), cwd)


def _ad_edit(args, cwd):
    # type: (Dict[str, Any], str) -> str
    return tool_edit(args.get("path", ""), args.get("old_string", ""), args.get("new_string", ""), cwd)


def _ad_bash(args, cwd):
    # type: (Dict[str, Any], str) -> str
    return tool_bash(args.get("command", ""), cwd, _int(args.get("timeout"), 60))


def _ad_glob(args, cwd):
    # type: (Dict[str, Any], str) -> str
    return tool_glob(args.get("pattern", ""), cwd)


def _ad_grep(args, cwd):
    # type: (Dict[str, Any], str) -> str
    return tool_grep(args.get("pattern", ""), args.get("include", "*") or "*", cwd)


def _ad_list_dir(args, cwd):
    # type: (Dict[str, Any], str) -> str
    return tool_list_dir(args.get("path", ".") or ".", cwd)


ADAPTERS = {
    "read": _ad_read,
    "write": _ad_write,
    "edit": _ad_edit,
    "bash": _ad_bash,
    "glob": _ad_glob,
    "grep": _ad_grep,
    "list_dir": _ad_list_dir,
}  # type: Dict[str, Callable[[Dict[str, Any], str], str]]


def run_tool(name, args, cwd=None):
    # type: (str, Dict[str, Any], str) -> str
    fn = ADAPTERS.get(name)
    if fn is None:
        return "unknown tool: %s" % name
    try:
        return fn(args or {}, cwd)
    except Exception as e:
        return "tool error (%s): %s" % (name, e)


def tool_schemas():
    # type: () -> List[Dict[str, Any]]
    # Canonical owner: schemas describe these tools, so they live here
    # (llm.py only transports them). Single source of truth.
    return [
        {
            "type": "function",
            "function": {
                "name": "read",
                "description": "Read a file (optionally offset/limit lines).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "offset": {"type": "integer"},
                        "limit": {"type": "integer"},
                    },
                    "required": ["path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "write",
                "description": "Create/overwrite a file with content.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["path", "content"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "edit",
                "description": "Exact string replacement in a file.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "old_string": {"type": "string"},
                        "new_string": {"type": "string"},
                    },
                    "required": ["path", "old_string", "new_string"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "bash",
                "description": "Run a shell command in cwd, return output.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string"},
                        "timeout": {"type": "integer"},
                    },
                    "required": ["command"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "glob",
                "description": "Find files by glob pattern.",
                "parameters": {
                    "type": "object",
                    "properties": {"pattern": {"type": "string"}},
                    "required": ["pattern"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "grep",
                "description": "Search file contents with regex.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string"},
                        "include": {"type": "string"},
                    },
                    "required": ["pattern"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_dir",
                "description": "List directory entries.",
                "parameters": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": [],
                },
            },
        },
    ]
