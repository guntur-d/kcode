"""Agent loop: build (full tools) vs plan (read-only). Python 3.8 compatible."""
import json
import os
from typing import Any, Callable, Dict, List, Optional

from . import llm, tools
from .config import session_path

SYSTEM_BUILD = (
    "You are opencode-py, a terminal coding agent (Python 3.8 port of opencode).\n"
    "You have tools: read, write, edit, bash, glob, grep, list_dir.\n"
    "Use OpenAI tool-calling when available. Otherwise you may emit:\n"
    "<invoke name=\"read\">{\"path\": \"...\"}</invoke>\n"
    "Keep answers concise. Prefer small verifiable steps. "
    "After tool results, summarize what you did.\n"
)

SYSTEM_PLAN = (
    "You are opencode-py in PLAN mode (read-only analysis).\n"
    "You may use read, glob, grep, list_dir ONLY. "
    "Do NOT write/edit files or run bash. Explain findings and propose a plan.\n"
)

READ_ONLY = frozenset(["read", "glob", "grep", "list_dir"])

try:
    import re as _re
    XML_RE = _re.compile(r'<invoke\s+name="([^"]+)">\s*(\{.*?\})\s*</invoke>', _re.DOTALL)
except Exception:  # pragma: no cover - re is stdlib, always present
    XML_RE = None  # type: ignore


class Agent(object):
    def __init__(self, cfg, cwd=None, session_id="default"):
        # type: (Dict[str, Any], Optional[str], str) -> None
        self.cfg = cfg
        self.cwd = cwd or os.getcwd()
        self.session_id = session_id
        self.agent = str(cfg.get("agent", "build"))
        self.model = str(cfg.get("model", "gpt-4o-mini"))
        self.messages = []  # type: List[Dict[str, Any]]
        system = SYSTEM_PLAN if self.agent == "plan" else SYSTEM_BUILD
        self.messages.append({"role": "system", "content": system + "\nWorking dir: " + self.cwd})
        self._load_session()

    def _load_session(self):
        # type: () -> None
        try:
            p = session_path(self.session_id)
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            self.messages.append(json.loads(line))
        except Exception:
            pass

    def _save(self, msg):
        # type: (Dict[str, Any]) -> None
        try:
            p = session_path(self.session_id)
            with open(p, "a", encoding="utf-8") as f:
                f.write(json.dumps(msg) + "\n")
        except Exception:
            pass

    def set_agent(self, name):
        # type: (str) -> None
        self.agent = "plan" if name == "plan" else "build"
        self.cfg["agent"] = self.agent

    def _execute_tool(self, name, args, on_tool=None):
        # type: (str, Dict[str, Any], Optional[Callable[[str, Dict[str, Any], str], None]]) -> str
        # Single choke point for permission + dispatch + callback.
        if self.agent == "plan" and name not in READ_ONLY:
            result = "denied in plan mode (read-only): %s" % name
        else:
            result = tools.run_tool(name, args, cwd=self.cwd)
        if on_tool is not None:
            try:
                on_tool(name, args, result)
            except Exception:
                pass
        return result

    def ask(self, user_text, on_tool=None, max_rounds=8):
        # type: (str, Optional[Callable[[str, Dict[str, Any], str], None]], int) -> str
        umsg = {"role": "user", "content": user_text}  # type: Dict[str, Any]
        self.messages.append(umsg)
        self._save(umsg)
        final = ""
        for _i in range(max_rounds):
            resp = llm.chat_completion(
                self.cfg.get("base_url", ""),
                self.cfg.get("api_key", ""),
                self.model,
                self.messages,
                tools=tools.tool_schemas(),
            )
            msg = llm.extract_assistant(resp)
            self.messages.append(msg)
            self._save(msg)
            tool_calls = msg.get("tool_calls") or []
            if tool_calls:
                for tc in tool_calls:
                    fn = (tc.get("function") or {}).get("name", "")
                    raw = (tc.get("function") or {}).get("arguments", "{}") or "{}"
                    try:
                        args = json.loads(raw)
                    except Exception:
                        args = {}
                    result = self._execute_tool(fn, args, on_tool)
                    tmsg = {
                        "role": "tool",
                        "tool_call_id": tc.get("id", ""),
                        "name": fn,
                        "content": result,
                    }  # type: Dict[str, Any]
                    self.messages.append(tmsg)
                    self._save(tmsg)
                continue
            # fallback: XML <invoke> parsing for endpoints without tool-calling
            content = msg.get("content") or ""
            fn, args = _parse_invoke(content)
            if fn is not None and args is not None:
                result = self._execute_tool(fn, args, on_tool)
                tmsg2 = {"role": "user", "content": "tool %s result:\n%s" % (fn, result)}
                self.messages.append(tmsg2)
                self._save(tmsg2)
                continue
            final = content or ""
            break
        return final or "(no response)"


def _parse_invoke(content):
    # type: (str) -> Any
    if not content or XML_RE is None:
        return None, None
    m = XML_RE.search(content)
    if not m:
        return None, None
    try:
        return m.group(1), json.loads(m.group(2))
    except Exception:
        return m.group(1), {}
