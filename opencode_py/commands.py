"""Shared slash-command handling for console and PyTermGUI frontends.

Single owner for /quit /help /agent /model so both UIs behave identically.
Returns a string to display, QUIT to exit, or None if text is not a command.
"""
from typing import Any, Optional

QUIT = "__QUIT__"


def handle_command(agent, text):
    # type: (Any, str) -> Optional[str]
    t = (text or "").strip()
    if t in ("/quit", "/exit", ":q"):
        return QUIT
    if t in ("/help", "/?"):
        return "/agent build|plan  /model <name>  /quit"
    if t.startswith("/agent"):
        parts = t.split()
        if len(parts) == 2 and parts[1] in ("build", "plan"):
            agent.set_agent(parts[1])
            return "agent=%s" % agent.agent
        return "usage: /agent build|plan"
    if t.startswith("/model"):
        parts = t.split(None, 1)
        if len(parts) == 2 and parts[1].strip():
            agent.model = parts[1].strip()
            return "model=%s" % agent.model
        return "usage: /model <name>"
    return None
