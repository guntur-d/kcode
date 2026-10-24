"""Smoke tests — stdlib unittest, Python 3.8 compatible."""
import ast
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestPy38Syntax(unittest.TestCase):
    def test_files_parse_as_38(self):
        pyfiles = []
        for root, _d, files in os.walk(os.path.join(ROOT, "opencode_py")):
            for fn in files:
                if fn.endswith(".py"):
                    pyfiles.append(os.path.join(root, fn))
        self.assertTrue(pyfiles)
        for fp in pyfiles:
            with open(fp, "r", encoding="utf-8") as f:
                src = f.read()
            try:
                ast.parse(src, filename=fp, feature_version=(3, 8))
            except TypeError:
                # very old python without feature_version: plain parse
                ast.parse(src, filename=fp)
            except SyntaxError as e:
                self.fail("not 3.8-compatible %s: %s" % (fp, e))

    def test_no_new_syntax(self):
        banned = ["import tomllib", "asyncio.to_thread", "match ", "str | None", "int | str", "list["]
        for root, _d, files in os.walk(os.path.join(ROOT, "opencode_py")):
            for fn in files:
                if fn.endswith(".py"):
                    with open(os.path.join(root, fn), encoding="utf-8") as f:
                        src = f.read()
                    for b in banned:
                        self.assertNotIn(b, src, "%s contains %r" % (fn, b))


class TestTools(unittest.TestCase):
    def test_read_write_edit_bash(self):
        sys.path.insert(0, ROOT)
        from opencode_py import tools
        import tempfile
        d = tempfile.mkdtemp()
        p = os.path.join(d, "a.txt")
        self.assertIn("wrote", tools.tool_write(p, "hello\nworld\n", cwd=d))
        self.assertIn("hello", tools.tool_read(p, cwd=d))
        tools.tool_edit(p, "world", "there", cwd=d)
        self.assertIn("there", tools.tool_read(p, cwd=d))
        out = tools.tool_bash("echo hi", cwd=d)
        self.assertIn("hi", out)
        self.assertIn("a.txt", tools.tool_glob("*.txt", cwd=d))
        self.assertIn("a.txt", tools.tool_grep("there", cwd=d))


class TestCli(unittest.TestCase):
    def test_version(self):
        sys.path.insert(0, ROOT)
        from opencode_py.cli import build_parser
        args = build_parser().parse_args(["--version"])
        self.assertTrue(args.version)


class TestConfigFile(unittest.TestCase):
    def _isolated_home(self):
        import tempfile
        tmp = tempfile.mkdtemp()
        os.environ["OPENCODE_PY_HOME"] = tmp
        for k in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL"):
            os.environ.pop(k, None)
        return tmp

    def _restore(self):
        os.environ.pop("OPENCODE_PY_HOME", None)
        for k in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL"):
            os.environ.pop(k, None)

    def test_save_load_api_key_base_url(self):
        sys.path.insert(0, ROOT)
        self._isolated_home()
        try:
            from opencode_py import config
            cfg = config.load_config({})
            cfg.update({"base_url": "http://localhost:11434/v1",
                        "api_key": "sk-test123",
                        "model": "llama3",
                        "agent": "build"})
            path = config.save_config(cfg)
            self.assertTrue(os.path.exists(path))
            with open(path, "r", encoding="utf-8") as f:
                import json
                saved = json.load(f)
            self.assertEqual(saved["api_key"], "sk-test123")
            self.assertEqual(saved["base_url"], "http://localhost:11434/v1")
            reloaded = config.load_config({})
            self.assertEqual(reloaded["api_key"], "sk-test123")
            self.assertEqual(reloaded["base_url"], "http://localhost:11434/v1")
            # env overrides file
            os.environ["OPENAI_API_KEY"] = "sk-env"
            reloaded2 = config.load_config({})
            self.assertEqual(reloaded2["api_key"], "sk-env")
        finally:
            self._restore()

    def test_validate_rejects_bad_url_and_agent(self):
        sys.path.insert(0, ROOT)
        self._isolated_home()
        try:
            from opencode_py import config
            bad = {"base_url": "ftp://x", "api_key": "", "model": "", "agent": "evil"}
            errors = config.validate(bad)
            self.assertTrue(len(errors) >= 2)
            good = {"base_url": "https://api.openai.com/v1", "api_key": "k",
                    "model": "m", "agent": "plan"}
            self.assertEqual(config.validate(good), [])
            # normalize repairs agent instead of crashing
            cfg = config.normalize(dict(bad))
            self.assertEqual(cfg["agent"], "build")
        finally:
            self._restore()

    def test_corrupt_file_backed_up_not_crash(self):
        sys.path.insert(0, ROOT)
        tmp = self._isolated_home()
        try:
            from opencode_py import config
            path = config.config_path()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write("{not json!!!")
            cfg = config.load_config({})
            self.assertEqual(cfg["base_url"], config.DEFAULT_BASE_URL)
            backups = [n for n in os.listdir(tmp) if n.startswith("config.json.corrupt.")]
            self.assertTrue(backups)
        finally:
            self._restore()

    def test_set_unset_roundtrip(self):
        sys.path.insert(0, ROOT)
        self._isolated_home()
        try:
            from opencode_py.cli import build_parser, handle_config_commands
            from opencode_py import config
            args = build_parser().parse_args(["--set", "model=llama3", "--set", "agent=plan"])
            rc = handle_config_commands(args, config.load_config({}))
            self.assertEqual(rc, 0)
            self.assertEqual(config.load_config({})["model"], "llama3")
            args2 = build_parser().parse_args(["--unset", "api_key"])
            rc2 = handle_config_commands(args2, config.load_config({}))
            self.assertEqual(rc2, 0)
            self.assertEqual(config.load_config({})["api_key"], "")
            args3 = build_parser().parse_args(["--set", "nope=x"])
            rc3 = handle_config_commands(args3, config.load_config({}))
            self.assertEqual(rc3, 2)
        finally:
            self._restore()


class TestCommands(unittest.TestCase):
    def test_shared_slash_commands(self):
        sys.path.insert(0, ROOT)
        from opencode_py.commands import QUIT, handle_command

        class Fake(object):
            agent = "build"
            model = "m"

            def set_agent(self, name):
                self.agent = name

        a = Fake()
        self.assertEqual(handle_command(a, "/quit"), QUIT)
        self.assertIn("usage", handle_command(a, "/agent"))
        self.assertEqual(handle_command(a, "/agent plan"), "agent=plan")
        self.assertEqual(handle_command(a, "/model foo"), "model=foo")
        self.assertIsNone(handle_command(a, "hello world"))


class TestProviders(unittest.TestCase):
    def _iso(self):
        import tempfile
        os.environ["OPENCODE_PY_HOME"] = tempfile.mkdtemp()
        for k in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL", "OPENCODE_API_KEY"):
            os.environ.pop(k, None)

    def _restore(self):
        for k in ("OPENCODE_PY_HOME", "OPENAI_API_KEY", "OPENAI_BASE_URL",
                  "OPENAI_MODEL", "OPENCODE_API_KEY"):
            os.environ.pop(k, None)

    def test_catalog_has_75_plus(self):
        sys.path.insert(0, ROOT)
        from opencode_py import providers
        self.assertGreaterEqual(providers.count(), 75)
        self.assertIn("opencode", providers.provider_ids())
        self.assertIn("ollama", providers.provider_ids())

    def test_opencode_zen_base(self):
        sys.path.insert(0, ROOT)
        from opencode_py.providers import get_provider
        zen = get_provider("opencode")
        self.assertEqual(zen["base"], "https://opencode.ai/zen/v1")
        self.assertEqual(zen["key"], "OPENCODE_API_KEY")
        self.assertEqual(zen["proto"], "openai")

    def test_resolve_fills_provider_base(self):
        sys.path.insert(0, ROOT)
        from opencode_py.providers import resolve
        cfg = resolve({"provider": "ollama", "base_url": "", "api_key": ""}, "https://fallback")
        self.assertEqual(cfg["base_url"], "http://localhost:11434/v1")
        self.assertEqual(cfg["protocol"], "openai")
        # explicit base always wins
        cfg2 = resolve({"provider": "ollama", "base_url": "http://x:1/v1", "api_key": ""}, "https://fallback")
        self.assertEqual(cfg2["base_url"], "http://x:1/v1")

    def test_validate_unknown_and_custom(self):
        sys.path.insert(0, ROOT)
        self._iso()
        try:
            from opencode_py import config
            errs = config.validate({"provider": "nope", "base_url": "https://x",
                                    "model": "m", "agent": "build"})
            self.assertTrue(any("unknown provider" in e for e in errs))
            errs2 = config.validate({"provider": "bedrock", "base_url": "https://x",
                                     "model": "m", "agent": "build"})
            self.assertTrue(any("manual setup" in e for e in errs2))
            errs3 = config.validate({"provider": "opencode", "base_url": "https://opencode.ai/zen/v1",
                                     "model": "opencode/gpt-5-nano", "agent": "build"})
            self.assertEqual(errs3, [])
        finally:
            self._restore()

    def test_switching_provider_rebases(self):
        sys.path.insert(0, ROOT)
        self._iso()
        try:
            from opencode_py import config
            cfg = config.load_config({"provider": "ollama"})
            self.assertEqual(cfg["base_url"], "http://localhost:11434/v1")
            cfg2 = config.load_config({"provider": "ollama", "base_url": "http://mine/v1"})
            self.assertEqual(cfg2["base_url"], "http://mine/v1")
        finally:
            self._restore()

    def test_anthropic_and_azure_shapes(self):
        sys.path.insert(0, ROOT)
        from unittest import mock
        from opencode_py import llm
        with mock.patch("opencode_py.llm._post",
                        return_value={"content": [{"type": "text", "text": "hi"}]}) as m:
            r = llm.chat_completion("https://api.anthropic.com/v1", "k", "claude-x",
                                    [{"role": "system", "content": "s"},
                                     {"role": "user", "content": "q"}],
                                    protocol="anthropic")
            self.assertTrue(m.call_args[0][0].endswith("/messages"))
            self.assertEqual(m.call_args[0][1]["x-api-key"], "k")
            self.assertEqual(llm.extract_assistant(r)["content"], "hi")
        with mock.patch("opencode_py.llm._post",
                        return_value={"choices": [{"message": {"content": "ok"}}]}) as m2:
            llm.chat_completion("https://res.openai.azure.com", "k", "dep1",
                                [{"role": "user", "content": "q"}], protocol="azure")
            url = m2.call_args[0][0]
            self.assertIn("/openai/deployments/dep1/chat/completions", url)
            self.assertEqual(m2.call_args[0][1].get("api-key"), "k")

    def test_list_providers_command(self):
        sys.path.insert(0, ROOT)
        from opencode_py.cli import build_parser, handle_config_commands
        args = build_parser().parse_args(["--list-providers"])
        self.assertEqual(handle_config_commands(args, {}), 0)


if __name__ == "__main__":
    unittest.main()
