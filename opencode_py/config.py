"""Config handling. Python 3.8 compatible.

Contract: load_config() returns a plain dict with exactly the KNOWN_KEYS.
Precedence: defaults < config file < env vars < CLI overrides.
"""
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_AGENT = "build"
DEFAULT_PROVIDER = "openai"

KNOWN_KEYS = ("provider", "base_url", "api_key", "model", "agent")
AGENTS = ("build", "plan")


def config_dir():
    # type: () -> str
    base = os.environ.get("OPENCODE_PY_HOME")
    if base:
        return base
    return os.path.join(os.path.expanduser("~"), ".opencode-py")


def config_path():
    # type: () -> str
    return os.path.join(config_dir(), "config.json")


def session_path(session_id):
    # type: (str) -> str
    d = os.path.join(config_dir(), "sessions")
    if not os.path.exists(d):
        try:
            os.makedirs(d)
        except Exception:
            pass
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in session_id)[:64]
    return os.path.join(d, "%s.jsonl" % (safe or "default"))


def _defaults():
    # type: () -> Dict[str, Any]
    return {
        "provider": DEFAULT_PROVIDER,
        "base_url": DEFAULT_BASE_URL,
        "api_key": "",
        "model": DEFAULT_MODEL,
        "agent": DEFAULT_AGENT,
    }


def _from_file(path):
    # type: (str) -> Dict[str, Any]
    found = {}  # type: Dict[str, Any]
    if not os.path.exists(path):
        return found
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        _backup_corrupt(path, e)
        return found
    if not isinstance(data, dict):
        _backup_corrupt(path, ValueError("top-level JSON must be an object"))
        return found
    for k in KNOWN_KEYS:
        if data.get(k):
            found[k] = data[k]
    return found


def _backup_corrupt(path, err):
    # type: (str, Exception) -> None
    try:
        backup = "%s.corrupt.%d" % (path, int(time.time()))
        os.replace(path, backup)
        sys.stderr.write("opencode-py: corrupt config %s (%s); moved to %s\n" % (path, err, backup))
    except Exception:
        sys.stderr.write("opencode-py: corrupt config %s (%s); ignoring\n" % (path, err))


def _from_env(provider_id=""):
    # type: (str) -> Dict[str, Any]
    found = {}  # type: Dict[str, Any]
    if os.environ.get("OPENAI_BASE_URL"):
        found["base_url"] = os.environ.get("OPENAI_BASE_URL", "")
    if os.environ.get("OPENAI_API_KEY"):
        found["api_key"] = os.environ.get("OPENAI_API_KEY", "")
    if os.environ.get("OPENAI_MODEL"):
        found["model"] = os.environ.get("OPENAI_MODEL", "")
    if os.environ.get("OPENCODE_API_KEY") and not found.get("api_key"):
        # OpenCode Zen / Go share one key variable.
        found["api_key"] = os.environ.get("OPENCODE_API_KEY", "")
    if provider_id:
        from .providers import get_provider

        p = get_provider(provider_id)
        if p and p["key"] and not found.get("api_key"):
            hit = os.environ.get(p["key"], "")
            if hit:
                found["api_key"] = hit
    return found


def normalize(cfg):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    if isinstance(cfg.get("base_url"), str):
        cfg["base_url"] = cfg["base_url"].rstrip("/")
    if cfg.get("agent") not in AGENTS:
        cfg["agent"] = DEFAULT_AGENT
    if not str(cfg.get("provider", "") or "").strip():
        cfg["provider"] = DEFAULT_PROVIDER
    else:
        cfg["provider"] = str(cfg.get("provider")).strip().lower()
    for k in ("base_url", "api_key", "model"):
        if cfg.get(k) is None:
            cfg[k] = ""
        elif not isinstance(cfg.get(k), str):
            cfg[k] = str(cfg.get(k))
    return cfg


def validate(cfg):
    # type: (Dict[str, Any]) -> List[str]
    from .providers import CUSTOM, get_provider

    errors = []  # type: List[str]
    pid = str(cfg.get("provider", "") or "openai")
    p = get_provider(pid)
    if p is None:
        errors.append("unknown provider %r (see --list-providers)" % pid)
    elif p["proto"] == CUSTOM:
        errors.append("provider %s needs manual setup: %s" % (pid, p["note"]))
    base = str(cfg.get("base_url", "") or "")
    if not base:
        hint = ""
        if p is not None and p["note"]:
            hint = " (%s: %s)" % (pid, p["note"])
        errors.append("base_url is empty%s" % hint)
    elif not (base.startswith("http://") or base.startswith("https://")):
        errors.append("base_url must start with http:// or https://")
    if not str(cfg.get("model", "") or "").strip():
        errors.append("model is empty")
    if cfg.get("agent") not in AGENTS:
        errors.append("agent must be one of %s" % ("/".join(AGENTS)))
    return errors


def load_config(overrides=None):
    # type: (Optional[Dict[str, Any]]) -> Dict[str, Any]
    # Precedence: defaults < config file < provider fill < env < CLI.
    # Switching --provider without --base-url follows the new endpoint.
    from .providers import resolve

    cfg = _defaults()
    cfg.update(_from_file(config_path()))
    cli = overrides or {}
    new_pid = str(cli.get("provider") or "").strip().lower()
    if new_pid and new_pid != str(cfg.get("provider", "")):
        cfg["provider"] = new_pid
        if not cli.get("base_url"):
            cfg["base_url"] = ""
    resolve(cfg, DEFAULT_BASE_URL)
    cfg.update(_from_env(str(cfg.get("provider", "") or "")))
    for k, v in cli.items():
        if k in KNOWN_KEYS and v is not None:
            cfg[k] = v
    resolve(cfg, DEFAULT_BASE_URL)
    return normalize(cfg)


def save_config(cfg):
    # type: (Dict[str, Any]) -> str
    cfg = normalize(dict(cfg))
    d = config_dir()
    if not os.path.exists(d):
        os.makedirs(d)
    path = config_path()
    safe = {k: cfg.get(k, "") for k in KNOWN_KEYS}  # type: Dict[str, Any]
    tmp = "%s.tmp.%d" % (path, os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(safe, f, indent=2)
        f.write("\n")
    try:
        os.chmod(tmp, 0o600)
    except Exception:
        pass
    os.replace(tmp, path)
    return path


def mask_key(key):
    # type: (str) -> str
    if not key:
        return "(not set)"
    if len(key) <= 8:
        return "****"
    return key[:4] + "..." + key[-4:]
