# kcode — an effort to make a Python-based TUI work on old machines

> **Disclaimer: this is just an effort — a small experiment to get a
> Python-based TUI coding agent running on old machines** (think Windows
> Server 2016 with Python 3.8, legacy `conhost.exe`, no admin rights, sometimes
> no internet). It is **not** a full rewrite of
> [opencode](https://github.com/anomalyco/opencode) and not affiliated with it.
> Expect rough edges; the goal is "it runs at all", not "it does everything".

Original project this is ported from (MVP subset only):
**https://github.com/anomalyco/opencode** — provider directory, Zen/Gateway
docs and the agent-loop idea. Nothing here is affiliated with the OpenCode team.

Why this exists: modern TUI frameworks moved on — e.g.
[Textual](https://github.com/Textualize/textual) now needs Python ≥ 3.9 plus
`rich`, `pygments`, `markdown-it`, `platformdirs` (and tree-sitter extras on
3.10+). [PyTermGUI](https://github.com/bczsalba/pytermgui), though archived,
still declares `requires-python >= 3.8` with only `wcwidth +
typing_extensions` as dependencies. So this experiment builds a minimal
opencode-style agent loop on **stdlib-only core + optional PyTermGUI**,
falling back to a plain `input()/print()` console when the terminal can't cope.

## Get running in 6 steps (Windows Server 2016)

Copy-paste in order. Expected output is shown under each command.

**1. Install Python 3.8 64-bit.** Do **not** use the 3.8.20 page —
python.org ships 3.8.20 as source-only tarballs (no Windows installer;
3.8.10 was the last 3.8 with binary installers). Get
**`python-3.8.10-amd64.exe`** ("Windows installer (64-bit)") from
https://www.python.org/downloads/release/python-3810/
(tick `Add python.exe to PATH`, `pip`, `py launcher`). Then:

```bat
py -3.8 --version
rem expect: Python 3.8.x
py -3.8 -m pip --version
rem expect: pip 2x.x ...
```

Need a newer box just to try it? Any Python 3.8+ works — the steps are identical.

**2. Get the code onto the machine** — clone, or copy this folder
(or at minimum `dist\opencode_py-0.1.0-py3-none-any.whl` + `vendor\` +
`requirements-py38.txt` + `install.bat` + `config.example.json`):

```bat
git clone https://github.com/guntur-d/kcode.git
cd kcode
```

**3. Install** (no admin needed; works offline via `vendor\` if present):

```bat
install.bat
rem expect: ... Successfully installed opencode-py ...
rem         config: C:\Users\YOU\.opencode-py\config.json
```

No internet and no `vendor\`? Skip the TUI deps — the core is stdlib-only:

```bat
py -3.8 -m pip install .
```

**4. Add your API key** (pick one):

```bat
opencode-py --init
rem prompts for provider/base_url/model, key is hidden; saves to
rem %USERPROFILE%\.opencode-py\config.json
```

No TUI / scripting it instead:

```bat
opencode-py --provider opencode --api-key sk-... --model opencode/gpt-5-nano --save-config
rem local model instead: opencode-py --provider ollama --model qwen3-coder --save-config
```

**5. Verify setup** — you should see your provider with the key masked:

```bat
opencode-py --show-config
rem expect: provider: opencode / base_url: https://opencode.ai/zen/v1 / api_key: sk-...XXXX
opencode-py --validate
rem expect: config OK: C:\Users\YOU\.opencode-py\config.json
```

If `--validate` complains, it tells you exactly what to fix
(unknown provider id, missing base_url, empty model).

**6. Run it:**

```bat
opencode-py --print "say hi in one line"
rem expect: one line of model output, e.g. hi!

opencode-py --no-tui
rem interactive plain console; type a question, /quit to exit

opencode-py
rem full TUI if your terminal supports ANSI; garbled output?
rem run chcp 65001 first, or stick with --no-tui
```

Done — you're running. Details for each step live in the sections below
(install options, config file reference, all 80+ providers).

## What it is (and isn't)

- **Is:** a minimal AI coding agent you can run with `py -3.8` on a 2016 box:
  agent loop (`build` full-access / `plan` read-only), 7 local tools
  (`read/write/edit/bash/glob/grep/list_dir`), **80+ providers** (incl. OpenCode
  Zen at `https://opencode.ai/zen/v1`) via stdlib `urllib` with openai /
  anthropic / azure protocols, JSON config file, session
  logs, `--print` mode for scripts.
- **Isn't:** the real opencode. Not ported: LSP, MCP,
  multi-session server, permission daemon, desktop app, rich TUI widgets.

## Install details (reference)

All of this is automated by `install.bat` (step 3 above); read on only if
something deviates.

- **Python:** 3.8 64-bit — specifically **3.8.10** (`python-3.8.10-amd64.exe`
  from https://www.python.org/downloads/release/python-3810/).
  Later 3.8.x pages (3.8.11–3.8.20) are source-only, no Windows installer.
  Verify with `py -3.8 --version`.
  Win2016 needs TLS 1.2 for PyPI / OpenAI HTTPS — stock 2016 is fine
  once Windows Update is current; otherwise use the offline `vendor\` path.
- **What `install.bat` does:** upgrades `pip` → installs `requirements-py38.txt`
  (from `vendor\` offline if present, else PyPI) → `pip install .` (registers the
  `opencode-py` command from `dist\` if present) → prints `--show-config`.
- **Pure-stdlib fallback (no TUI):** skip requirements, just `py -3.8 -m pip install .`
  or run uninstalled via `py -3.8 -m opencode_py --no-tui` from this folder.
- **Proxy:** `set HTTPS_PROXY=http://...` before running.
- **Linux:** same steps with `python3.8`:

```bash
python3.8 -m pip install -r requirements-py38.txt
python3.8 -m pip install .
python3.8 -m opencode_py --init
python3.8 -m opencode_py --no-tui
```

Build artifacts (already in repo): `dist\*.whl + *.tar.gz` via `python -m build`,
offline wheels in `vendor\` (`PyTermGUI 7.8.1 + wcwidth 0.5.0 + typing_extensions 4.12.2`,
all `py3-none-any`, Python 3.8 compatible).

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
  "provider": "openai",
  "base_url": "https://api.openai.com/v1",
  "api_key": "sk-...",
  "model": "gpt-4o-mini",
  "agent": "build"
}
```

Precedence: defaults < config file < provider catalog < env
(`OPENAI_*`, `OPENCODE_API_KEY`, `<PROVIDER>_API_KEY`) < CLI flags.
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

## Providers (80+, incl. opencode.ai)

Ported from the [opencode provider directory](https://opencode.ai/docs/providers/)
(AI SDK + Models.dev catalog). Three protocols are spoken over stdlib `urllib`:

* `openai` — `POST {base}/chat/completions`, Bearer auth (the default; ~65 providers).
* `anthropic` — `POST {base}/messages`, `x-api-key` auth (Anthropic direct).
  Tool-calling degrades to text + `<invoke>` fallback on this protocol.
* `azure` — `{base}/openai/deployments/{model}/chat/completions`, `api-key` auth.
* `custom` — listed with a setup hint but intentionally unsupported
  (Bedrock SigV4, Vertex OAuth, Copilot device flow, GitLab Duo, SAP, Modal,
  DigitalOcean routers, Cloudflare account APIs). `--validate` tells you why.

```bash
python -m opencode_py --list-providers            # all 80+ with protocol + endpoint
python -m opencode_py --provider opencode --save-config   # OpenCode Zen
python -m opencode_py --provider ollama --set model=qwen3-coder --save-config
python -m opencode_py --provider azure --base-url https://<res>.openai.azure.com \
  --model <deployment> --save-config
```

Highlights:

* `opencode` — **OpenCode Zen**, `https://opencode.ai/zen/v1`, key `OPENCODE_API_KEY`
  (or `--api-key`), models as `opencode/<id>` e.g. `opencode/gpt-5-nano`.
  Full model list: `curl https://opencode.ai/zen/v1/models`.
* `opencode-go` — OpenCode Go plan, `https://opencode.ai/zen/go/v1`, same key.
* Cloud: `openai anthropic deepseek groq together fireworks openrouter xai mistral
  moonshot minimax zai deepinfra cerebras nvidia nebius gemini huggingface
  github-models cohere perplexity upstage writer ai21 ...` (see `--list-providers`).
* Local, no key: `ollama lmstudio llamacpp atomic-chat`.
* Endpoint varies per account: `databricks scaleway stackit ovhcloud poolside snowflake scx` —
  pick the id, then set `--base-url` (validate tells you exactly this).

Precedence stays: explicit `--base-url/--api-key` > env (`OPENCODE_API_KEY`,
`<PROVIDER>_API_KEY`, `OPENAI_*`) > config file > provider catalog default.
Switching `--provider` without `--base-url` follows the new endpoint.
`--validate` fails non-zero with the reason (unknown id, custom protocol,
empty base/model).

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
