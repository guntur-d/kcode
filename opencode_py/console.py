"""Plain-console fallback REPL (works everywhere, incl. legacy conhost)."""
import sys

from .commands import QUIT, handle_command


def run_console(agent, stdin=None, stdout=None):
    # type: (object, object, object) -> int
    inp = stdin or sys.stdin
    out = stdout or sys.stdout
    out.write("kcode [%s/%s] @ %s (type /help, /quit)\n" % (
        getattr(agent, "model", "?"), getattr(agent, "agent", "build"),
        getattr(agent, "cwd", "?")))
    out.flush()
    while True:
        try:
            out.write("\n> ")
            out.flush()
            line = inp.readline()
            if not line:
                break
            reply = handle_command(agent, line.strip())
            if reply == QUIT:
                break
            if reply is not None:
                if line.strip():
                    out.write("%s\n" % reply)
                continue

            def _on_tool(name, args, result):
                # type: (str, dict, str) -> None
                out.write("\n[tool %s] %s\n" % (name, str(result)[:2000]))

            out.write("...\n")
            out.flush()
            ans = agent.ask(line.strip(), on_tool=_on_tool)  # type: ignore[attr-defined]
            out.write("\n%s\n" % ans)
            out.flush()
        except KeyboardInterrupt:
            break
        except Exception as e:
            out.write("\n[error] %s\n" % e)
            out.flush()
    return 0
