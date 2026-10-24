# kcode — an effort to make a Python-based TUI work on old machines

> **Disclaimer: this is just an effort — a small experiment to get a
> Python-based TUI coding agent running on old machines** (think Windows
> Server 2016 with Python 3.8, legacy `conhost.exe`, no admin rights, sometimes
> no internet). It is **not** a full rewrite of
> [opencode](https://github.com/anomalyco/opencode) and not affiliated with it.
> Expect rough edges; the goal is "it runs at all", not "it does everything".

Why this exists: modern TUI frameworks moved on — e.g.
[Textual](https://github.com/Textualize/textual) now needs Python ≥ 3.9 plus
`rich`, `pygments`, `markdown-it`, `platformdirs` (and tree-sitter extras on
3.10+). [PyTermGUI](https://github.com/bczsalba/pytermgui), though archived,
still declares `requires-python >= 3.8` with only `wcwidth +
typing_extensions` as dependencies. So this experiment builds a minimal
opencode-style agent loop on **stdlib-only core + optional PyTermGUI**,
falling back to a plain `input()/print()` console when the terminal can't cope.

## What it is (and isn't)

- **Is:** a minimal AI coding agent you can run with `py -3.8` on a 2016 box:
  agent loop (`build` full-access / `plan` read-only), 7 local tools
  (`read/write/edit/bash/glob/grep/list_dir`), any OpenAI-compatible
  `/chat/completions` endpoint via stdlib `urllib`, JSON config file, session
  logs, `--print` mode for scripts.
- **Isn't:** the real opencode. Not ported: 75+ providers, LSP, MCP,
  multi-session server, permission daemon, desktop app, rich TUI widgets.

## Install on a real Win2016 server (Python 3.8)

1. Install **Python 3.8 64-bit** from python.org
   (check `Add python.exe to PATH`, `pip`, `py launcher`).
   Verify: `py -3.8 --version` + `py -3.8 -m pip --version`.
   Win2016 needs TLS 1.2 for PyPI / OpenAI HTTPS — stock 2016 is fine
   once Windows Update is current; otherwise use the offline `vendor\` path below.
2. Copy this folder to the server (or `dist\opencode_py-0.1.0-py3-none-any.whl`
   + `vendor\` + `requirements-py38.txt` + `install.bat` + `config.example.json`).
3. Run `install.bat` (double-click or `install.bat` in `cmd`). It:
   - upgrades `pip`, installs `requirements-py38.txt`
     (from `vendor\` offline if present, else PyPI),
   - `pip install .` (registers the `opencode-py` command from `dist\` if present),
   - prints `--show-config`.
   Pure-stdlib fallback (no TUI): skip requirements, just `py -3.8 -m pip install .`
   or even run uninstalled via `py -3.8 -m opencode_py --no-tui` from this folder.
4. Configure (pick one):
   - `opencode-py --init` (prompts, key hidden) — recommended,
   - `copy config.example.json %USERPROFILE%\.opencode-py\config.json` then edit,
   - or one-shot: `opencode-py --api-key sk-... --base-url https://api.openai.com/v1 --model gpt-4o-mini --save-config`.
   Verify: `opencode-py --show-config` (key is masked).
5. Run: `opencode-py` (TUI if ANSI works) or `opencode-py --no-tui` (safe on
   legacy `conhost.exe`). Non-interactive: `opencode-py --print "do X"`.
   If the TUI is garbled on 2016 `conhost`, run `chcp 65001` first or stick to
   `--no-tui` / `set NO_COLOR=1`. Behind a proxy: `set HTTPS_PROXY=http://...`.

Build artifacts (already in repo): `dist\*.whl + *.tar.gz` via `python -m build`,
offline wheels in `vendor\` (`PyTermGUI 7.8.1 + wcwidth 0.5.0 + typing_extensions 4.12.2`,
all `py3-none-any`, Python 3.8 compatible).

Quick (machine with internet + Python 3.8):

```bat
py -3.8 -m pip install -r requirements.txt
rem interactive setup -> writes %USERPROFILE%\.opencode-py\config.json
py -3.8 -m opencode_py --init
py -3.8 -m opencode_py --no-tui
```

Linux:

```bash
python3.8 -m pip install -r requirements.txt
python3.8 -m opencode_py --init
OPENAI_API_KEY=sk-... python3.8 -m opencode_py
```

## Config file (api_key + base_url)

`~/.opencode-py/config.json` (`OPENCODE_PY_HOME` overrides dir for tests/portable use):

```json
{
  "base_url": "https://api.openai.com/v1",
  "api_key": "sk-...",
  "model": "gpt-4o-mini",
  "agent": "build"
}
```

Precedence: defaults < config file < env (`OPENAI_API_KEY/BASE_URL/MODEL`) < CLI flags.
File holds the secrets; env/CLI still override per-run (CI, shared Win2016 servers).

```bash
python -m opencode_py --init                      # prompt + save (api_key hidden)
python -m opencode_py --show-config               # path + masked key
python -m opencode_py --validate                  # fail non-zero on bad config
python -m opencode_py --set model=llama3 --set agent=plan       # save now
python -m opencode_py --unset api_key             # clear a key, save now
python -m opencode_py --api-key sk-... --base-url http://localhost:11434/v1 \
  --model llama3 --save-config                    # non-interactive save
chmod 600 ~/.opencode-py/config.json  # auto-done on save where supported
```

Corrupt `config.json` never crashes startup: it is moved aside to
`config.json.corrupt.<timestamp>` with a stderr note, and defaults load.

## Usage

```bash
# interactive TUI (PyTermGUI if available, else plain console)
python -m opencode_py
python -m opencode_py --no-tui
python -m opencode_py --agent plan

# non-interactive (scripts / CI)
python -m opencode_py --print "list files and explain this repo"
echo "fix typo" | python -m opencode_py --print

# overrides (any OpenAI-compatible base_url: Ollama, LM Studio, vLLM, OpenRouter, Azure)
python -m opencode_py --model gpt-4o-mini --base-url http://localhost:11434/v1 --print "hi"
```

TUI keys/commands: type text + `Enter`, `/agent build|plan`, `/model <name>`, `/quit`.

## Old-machine notes (Windows Server 2016)

- Legacy `conhost.exe` has reduced ANSI/mouse — the app auto-falls back to
  plain console (`--no-tui`, `NO_COLOR=1`, `TERM=dumb`).
- No `pty`/`fcntl` used; `bash` tool uses `shell=True` + captured pipes.
- Python 3.8 syntax only: no `X|Y`, no `match`, no `tomllib`, `typing.List/Dict/Optional`.
