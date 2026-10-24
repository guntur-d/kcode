"""Chat client over stdlib urllib (no requests needed).

Works on Python 3.8 + Windows Server 2016 with zero extra deps.
Protocols (see providers.py): "openai" (/chat/completions, Bearer),
"anthropic" (/messages, x-api-key), "azure" (deployment URL, api-key).
"custom" providers are rejected here with their setup hint; config.validate
catches this earlier.
Tool schemas live in tools.py (canonical owner); this module only transports.
"""
import json
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

AZURE_API_VERSION = "2024-10-01-preview"
ANTHROPIC_VERSION = "2023-06-01"


def _headers(api_key):
    # type: (str) -> Dict[str, str]
    h = {"Content-Type": "application/json"}  # type: Dict[str, str]
    if api_key:
        h["Authorization"] = "Bearer " + api_key
    return h


def _post(url, headers, payload, timeout):
    # type: (str, Dict[str, str], Dict[str, Any], int) -> Dict[str, Any]
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError("LLM HTTP %s: %s" % (e.code, body[:2000]))
    except Exception as e:
        raise RuntimeError("LLM request failed: %s" % e)


def chat_completion(base_url, api_key, model, messages, tools=None, timeout=120, protocol="openai"):
    # type: (str, str, str, List[Dict[str, Any]], Optional[List[Dict[str, Any]]], int, str) -> Dict[str, Any]
    base = (base_url or "").rstrip("/")
    if not base:
        raise RuntimeError("base_url is empty (pick a provider or set --base-url)")
    if protocol == "anthropic":
        return _post(base + "/messages", _anthropic_headers(api_key),
                     _anthropic_payload(model, messages), timeout)
    if protocol == "azure":
        url = "%s/openai/deployments/%s/chat/completions?api-version=%s" % (
            base, model, AZURE_API_VERSION)
        h = {"Content-Type": "application/json", "api-key": api_key or ""}
        payload = {"messages": messages}  # type: Dict[str, Any]
        if tools:
            payload["tools"] = tools
        return _post(url, h, payload, timeout)
    if protocol == "custom":
        raise RuntimeError("this provider needs manual setup outside HTTP chat")
    payload = {"model": model, "messages": messages}  # type: Dict[str, Any]
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    return _post(base + "/chat/completions", _headers(api_key), payload, timeout)


def _anthropic_headers(api_key):
    # type: (str) -> Dict[str, str]
    return {
        "Content-Type": "application/json",
        "x-api-key": api_key or "",
        "anthropic-version": ANTHROPIC_VERSION,
    }


def _anthropic_payload(model, messages):
    # type: (str, List[Dict[str, Any]]) -> Dict[str, Any]
    # Anthropic takes system separately and has no "tool" role: fold tool
    # outputs back into user turns so the loop keeps working as text.
    system_parts = []
    conv = []  # type: List[Dict[str, Any]]
    for m in messages or []:
        role = m.get("role", "user")
        content = m.get("content", "")
        if role == "system":
            system_parts.append(str(content))
        elif role == "tool":
            conv.append({"role": "user",
                         "content": "tool %s result:\n%s" % (m.get("name", ""), content)})
        elif role in ("user", "assistant"):
            conv.append({"role": role, "content": str(content)})
    payload = {"model": model, "max_tokens": 4096, "messages": conv}  # type: Dict[str, Any]
    if system_parts:
        payload["system"] = "\n".join(system_parts)
    return payload


def extract_assistant(response):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    if isinstance(response.get("content"), list):
        # Anthropic Messages shape: join text blocks; agent XML fallback
        # still applies for tool use on this protocol.
        text = "".join(
            b.get("text", "") for b in response["content"]
            if isinstance(b, dict) and b.get("type") == "text")
        return {"role": "assistant", "content": text}
    choices = response.get("choices", [])
    if not choices:
        raise RuntimeError("Empty LLM response: %s" % json.dumps(response)[:1000])
    return choices[0].get("message", {})
