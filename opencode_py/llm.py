"""OpenAI-compatible chat client over stdlib urllib (no requests needed).

Works on Python 3.8 + Windows Server 2016 with zero extra deps.
Supports `tools` (function calling) when the endpoint supports it.
Tool schemas live in tools.py (canonical owner); this module only transports.
"""
import json
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional


def _headers(api_key):
    # type: (str) -> Dict[str, str]
    h = {"Content-Type": "application/json"}  # type: Dict[str, str]
    if api_key:
        h["Authorization"] = "Bearer " + api_key
    return h


def chat_completion(base_url, api_key, model, messages, tools=None, timeout=120):
    # type: (str, str, str, List[Dict[str, Any]], Optional[List[Dict[str, Any]]], int) -> Dict[str, Any]
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
    }  # type: Dict[str, Any]
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=_headers(api_key), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw)  # type: ignore[no-any-return]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError("LLM HTTP %s: %s" % (e.code, body[:2000]))
    except Exception as e:
        raise RuntimeError("LLM request failed: %s" % e)


def extract_assistant(response):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    choices = response.get("choices", [])
    if not choices:
        raise RuntimeError("Empty LLM response: %s" % json.dumps(response)[:1000])
    return choices[0].get("message", {})
