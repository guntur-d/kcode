"""CLI entrypoint. Python 3.8 compatible (argparse only)."""
import argparse
import os
import sys

from . import __version__
from .agent import Agent
from .config import AGENTS, KNOWN_KEYS, config_path, load_config, mask_key, save_config, validate
from .providers import count as provider_count
from .providers import get_provider, provider_ids


def build_parser():
    # type: () -> argparse.ArgumentParser
    p = argparse.ArgumentParser(prog="opencode-py", description="Minimal opencode port for Python 3.8")
    p.add_argument("--version", action="store_true", help="print version")
    p.add_argument("--print", dest="do_print", action="store_true", help="non-interactive: print answer and exit")
    p.add_argument("--no-tui", action="store_true", help="force plain console even if PyTermGUI installed")
    p.add_argument("--model", default=None, help="override model")
    p.add_argument("--provider", default=None, metavar="ID",
                   help="use a catalog provider (fills base_url/api key; see --list-providers)")
    p.add_argument("--list-providers", action="store_true",
                   help="list the %d known providers and exit" % provider_count())
    p.add_argument("--base-url", default=None, help="override OpenAI-compatible base URL")
    p.add_argument("--api-key", default=None, help="override API key (else from config file / OPENAI_API_KEY)")
    p.add_argument("--agent", default=None, choices=["build", "plan"], help="agent mode")
    p.add_argument("--cwd", default=None, help="working directory")
    p.add_argument("--session", default="default", help="session id")
    p.add_argument("--init", action="store_true", help="interactive setup: write base_url + api_key + model to config file and exit")
    p.add_argument("--save-config", action="store_true", help="persist effective --model/--base-url/--api-key/--agent to config file and exit")
    p.add_argument("--show-config", action="store_true", help="print config file path + masked values and exit")
    p.add_argument("--validate", action="store_true", help="validate effective config and exit (non-zero on error)")
    p.add_argument("--set", dest="set_kv", action="append", default=[], metavar="key=value",
                   help="set config key (repeatable); saved immediately")
    p.add_argument("--unset", dest="unset_keys", action="append", default=[], metavar="key",
                   help="clear config key to empty (repeatable); saved immediately")
    p.add_argument("prompt", nargs="*", help="prompt text (with --print)")
    return p


def run_init(cfg):
    # type: (dict) -> int
    # Interactive setup: prompts default to current effective values,
    # writes base_url + api_key + model + agent to config.json.
    try:
        from getpass import getpass
    except Exception:
        getpass = input  # type: ignore
    print("opencode-py setup (writes %s)" % config_path())
    cur_base = str(cfg.get("base_url", "") or "")
    cur_model = str(cfg.get("model", "") or "")
    cur_agent = str(cfg.get("agent", "") or "build")
    cur_provider = str(cfg.get("provider", "") or "openai")
    try:
        provider = input("provider [%s] (see --list-providers): " % cur_provider).strip() or cur_provider
        base = input("base_url [%s]: " % cur_base).strip() or cur_base
        model = input("model [%s]: " % cur_model).strip() or cur_model
        agent = input("agent [build|plan] [%s]: " % cur_agent).strip() or cur_agent
        try:
            key = getpass("api_key (hidden, Enter to keep %s): " % mask_key(str(cfg.get("api_key", "") or "")))
        except Exception:
            key = ""
        key = (key or "").strip()
    except (KeyboardInterrupt, EOFError):
        print("\ncancelled")
        return 1
    if agent not in AGENTS:
        print("agent must be build|plan, keeping %s" % cur_agent)
        agent = cur_agent
    if get_provider(provider) is None:
        print("unknown provider %r, keeping %s (see --list-providers)" % (provider, cur_provider))
        provider = cur_provider
    cfg["provider"] = provider
    cfg["base_url"] = base
    cfg["model"] = model
    cfg["agent"] = agent
    if key:
        cfg["api_key"] = key
    errors = validate(cfg)
    if errors and not str(cfg.get("api_key", "")):
        print("warning: %s" % "; ".join(errors))
    path = save_config(cfg)
    print("saved to %s" % path)
    print("provider: %s" % cfg.get("provider", ""))
    print("base_url: %s" % cfg.get("base_url", ""))
    print("api_key: %s" % mask_key(str(cfg.get("api_key", "") or "")))
    return 0


def handle_config_commands(args, cfg):
    # type: (argparse.Namespace, dict) -> int
    # Returns exit code, or -1 when no config command matched.
    if args.list_providers:
        print("%-24s %-10s %-42s %s" % ("ID", "PROTO", "BASE_URL", "NAME"))
        for pid in provider_ids():
            p = get_provider(pid)
            base = p["base"] or "(needs --base-url)"
            print("%-24s %-10s %-42s %s" % (pid, p["proto"], base[:42], p["name"]))
        return 0
    if args.set_kv or args.unset_keys:
        for item in args.set_kv:
            if "=" not in item:
                print("bad --set %r, want key=value" % item, file=sys.stderr)
                return 2
            k, v = item.split("=", 1)
            k, v = k.strip(), v.strip()
            if k not in KNOWN_KEYS:
                print("unknown key %r (want one of %s)" % (k, "/".join(KNOWN_KEYS)), file=sys.stderr)
                return 2
            if k == "agent" and v not in AGENTS:
                print("agent must be build|plan", file=sys.stderr)
                return 2
            cfg[k] = v
        for k in args.unset_keys:
            if k not in KNOWN_KEYS:
                print("unknown key %r (want one of %s)" % (k, "/".join(KNOWN_KEYS)), file=sys.stderr)
                return 2
            cfg[k] = ""
        path = save_config(cfg)
        print("saved to %s" % path)
        return 0
    if args.show_config:
        print("config: %s" % config_path())
        print("provider: %s" % cfg.get("provider", ""))
        print("base_url: %s" % cfg.get("base_url", ""))
        print("api_key: %s" % mask_key(str(cfg.get("api_key", "") or "")))
        print("model: %s" % cfg.get("model", ""))
        print("agent: %s" % cfg.get("agent", ""))
        return 0
    if args.validate:
        errors = validate(cfg)
        if errors:
            for e in errors:
                print("config error: %s" % e, file=sys.stderr)
            return 1
        print("config OK: %s" % config_path())
        return 0
    if args.save_config:
        path = save_config(cfg)
        print("saved to %s (api_key: %s)" % (path, mask_key(str(cfg.get("api_key", "") or ""))))
        return 0
    if args.init:
        return run_init(cfg)
    return -1


def run_print_mode(agent, prompt_parts):
    # type: (Agent, list) -> int
    prompt = " ".join(prompt_parts or [])
    if not prompt and not sys.stdin.isatty():
        prompt = sys.stdin.read()
    if not prompt.strip():
        print("usage: opencode-py --print \"do X\"  (or pipe stdin)", file=sys.stderr)
        return 2
    print(agent.ask(prompt))
    return 0


def run_interactive(agent, args, initial):
    # type: (Agent, argparse.Namespace, str) -> int
    use_tui = not args.no_tui
    term = (os.environ.get("TERM") or "").lower()
    if os.environ.get("NO_COLOR") or term in ("dumb", ""):
        if sys.platform.startswith("win") and "WT_SESSION" not in os.environ:
            use_tui = False
    if use_tui:
        from .tui_ptg import run_ptg

        if initial:
            print(agent.ask(initial))
        return run_ptg(agent)
    from .console import run_console

    if initial:
        print(agent.ask(initial))
    return run_console(agent)


def main(argv=None):
    # type: (object) -> int
    args = build_parser().parse_args(argv)
    if args.version:
        print(__version__)
        return 0
    cfg = load_config({
        "model": args.model,
        "provider": args.provider,
        "base_url": args.base_url,
        "api_key": args.api_key,
        "agent": args.agent,
    })
    rc = handle_config_commands(args, cfg)
    if rc >= 0:
        return rc
    agent = Agent(cfg, cwd=args.cwd or os.getcwd(), session_id=args.session or "default")
    if args.do_print:
        return run_print_mode(agent, args.prompt)
    initial = " ".join(args.prompt or []).strip()
    return run_interactive(agent, args, initial)
