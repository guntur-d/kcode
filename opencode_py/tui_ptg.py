"""PyTermGUI TUI. Lazy import so Python 3.8 + missing dep still works via fallback."""
import sys


def run_ptg(agent):
    # type: (object) -> int
    try:
        import pytermgui as ptg  # type: ignore
    except Exception as e:
        print("PyTermGUI unavailable (%s), falling back to plain console." % e)
        from .console import run_console

        return run_console(agent)

    # transcript buffer (plain text; TIM markup escaped by user content)
    lines = ["[bold green]opencode-py[/] model=%s agent=%s" % (
        getattr(agent, "model", "?"), getattr(agent, "agent", "?"))]
    lines.append("Type a message, Enter to send. /quit exits, /agent toggles plan/build.")

    manager = ptg.WindowManager()
    # input field must be created before callback closure uses it
    input_field = ptg.InputField(prompt="> ")

    output = ptg.Label("\n".join(lines[-60:]), parent_align=0)
    output_box = ptg.Container(output)
    btn = ptg.Button("Send", lambda *_: _send())

    def _redraw():
        # type: () -> None
        output.value = "\n".join(lines[-80:])

    def _append(role, text):
        # type: (str, str) -> None
        # keep it short for old terminals
        t = (text or "").replace("[", "(").replace("]", ")")
        if len(t) > 4000:
            t = t[:4000] + "... [truncated]"
        lines.append("")
        lines.append("[bold]%s:[/] %s" % (role, t))
        _redraw()

    def _send(*_args):
        # type: (*object) -> None
        from .commands import QUIT, handle_command

        text = (input_field.value or "").strip()
        if not text:
            return
        input_field.value = ""
        reply = handle_command(agent, text)
        if reply == QUIT:
            manager.stop()
            return
        if reply is not None:
            _append("sys", reply)
            return
        _append("you", text)
        _append("sys", "... thinking ...")

        def _on_tool(name, args, result):
            # type: (str, dict, str) -> None
            lines.append("[dim]tool %s:[/] %s" % (name, str(result)[:800].replace("[", "(")))

        try:
            ans = agent.ask(text, on_tool=_on_tool)  # type: ignore[attr-defined]
        except Exception as e:
            ans = "[error] %s" % e
        # replace the thinking line
        if lines and lines[-2:] and "thinking" in lines[-1]:
            lines.pop()
        _append("agent", ans)

    input_field.bind(ptg.keys.ENTER, _send)

    win = ptg.Window(
        output_box,
        "",
        input_field,
        btn,
        width=100,
        box="SINGLE",
    )
    win.title = "kcode @ %s" % getattr(agent, "cwd", "?")
    manager.add(win)
    try:
        manager.run()
    except KeyboardInterrupt:
        pass
    return 0
