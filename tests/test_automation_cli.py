# this_file: tests/test_automation_cli.py
import dataclasses
import json
import runpy
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest

from fontlab import automation as a
from fontlab import cli


@dataclasses.dataclass
class Result:
    value: int = 1
    stdout: str = ""
    stderr: str = ""


def test_mac_launch_and_submission_reuse_remopy(monkeypatch, tmp_path):
    app = tmp_path / "FontLab 9.app"
    monkeypatch.setattr(a.sys, "platform", "darwin")
    monkeypatch.setattr(a, "ensure_installed", Mock(return_value=app))
    remote = SimpleNamespace(
        launch=Mock(), submit_script=Mock(return_value="submission")
    )
    monkeypatch.setitem(sys.modules, "fontlab_remopy", remote)
    assert a.launch() == app
    source = tmp_path / "script.vfpy"
    source.touch()
    assert a.submit_script(source) == "submission"
    remote.launch.assert_called_once_with(app=app)
    remote.submit_script.assert_called_once_with(source, app=app)


def test_windows_launch_and_submission_use_argument_lists(monkeypatch, tmp_path):
    app = tmp_path / "FontLab 9.exe"
    monkeypatch.setattr(a.sys, "platform", "win32")
    monkeypatch.setattr(a, "ensure_installed", Mock(return_value=app))
    runner = Mock()
    monkeypatch.setattr(a.subprocess, "Popen", runner)
    assert a.launch() == app
    source = tmp_path / "a.vfpy"
    source.touch()
    assert a.submit_script(source)["execution_verified"] is False
    assert runner.call_args.args[0] == [str(app), str(source)]
    with pytest.raises(ValueError):
        a.submit_script(tmp_path)


def test_connect_uses_discovered_bridge_after_readiness(monkeypatch, tmp_path):
    monkeypatch.setattr(a.sys, "platform", "win32")
    app = tmp_path / "FontLab 9.exe"
    monkeypatch.setattr(a, "ensure_installed", Mock(return_value=app))
    remote = Mock()
    discovery = SimpleNamespace(find_bridge=Mock(return_value="bridge.exe"))
    monkeypatch.setitem(sys.modules, "fontlab_remopy", remote)
    monkeypatch.setitem(sys.modules, "fontlab_remopy.discovery", discovery)
    a.connect(timeout=4)
    assert remote.method_calls == [
        call.ensure_ready(app=app, command="bridge.exe", timeout=4),
        call.FontLab(command="bridge.exe", timeout=4),
    ]
    remote.FontLab.assert_called_once_with(command="bridge.exe", timeout=4)
    remote.reset_mock()
    discovery.find_bridge.return_value = None
    with pytest.raises(FileNotFoundError, match="submit_script"):
        a.connect()
    remote.ensure_ready.assert_not_called()
    remote.FontLab.assert_not_called()


@pytest.mark.parametrize("platform", ["darwin", "win32"])
def test_connect_uses_selected_application_bridge(monkeypatch, tmp_path, platform):
    app = tmp_path / ("FontLab 9.app" if platform == "darwin" else "FontLab 9.exe")
    bridge = (
        app / "Contents/MacOS/fontlab-mcp"
        if platform == "darwin"
        else app.parent / "fontlab-mcp.exe"
    )
    bridge.parent.mkdir(parents=True, exist_ok=True)
    bridge.touch()
    bridge.chmod(0o755)
    monkeypatch.setattr(a.sys, "platform", platform)
    monkeypatch.setattr(a, "ensure_installed", Mock(return_value=app))
    remote = SimpleNamespace(FontLab=Mock(), ensure_ready=Mock())
    discovery = SimpleNamespace(find_bridge=Mock())
    monkeypatch.setitem(sys.modules, "fontlab_remopy", remote)
    monkeypatch.setitem(sys.modules, "fontlab_remopy.discovery", discovery)

    a.connect(beta=True, destination=app, timeout=7)

    a.ensure_installed.assert_called_once_with(beta=True, destination=app)
    discovery.find_bridge.assert_not_called()
    remote.ensure_ready.assert_called_once_with(app=app, command=str(bridge), timeout=7)
    remote.FontLab.assert_called_once_with(command=str(bridge), timeout=7)


def test_connect_readiness_timeout_prevents_client_creation(monkeypatch, tmp_path):
    app = tmp_path / "FontLab 9.exe"
    monkeypatch.setattr(a, "ensure_installed", Mock(return_value=app))
    remote = SimpleNamespace(
        FontLab=Mock(), ensure_ready=Mock(side_effect=TimeoutError("startup timed out"))
    )
    discovery = SimpleNamespace(find_bridge=Mock(return_value="bridge.exe"))
    monkeypatch.setitem(sys.modules, "fontlab_remopy", remote)
    monkeypatch.setitem(sys.modules, "fontlab_remopy.discovery", discovery)

    with pytest.raises(TimeoutError, match="startup timed out"):
        a.connect(timeout=1)

    remote.ensure_ready.assert_called_once_with(app=app, command="bridge.exe", timeout=1)
    remote.FontLab.assert_not_called()


@pytest.mark.parametrize(
    "operation",
    ["install", "launch", "latest", "submit", "run", "eval", "tools", "call"],
)
def test_cli_routes_operations(monkeypatch, tmp_path, capsys, operation):
    monkeypatch.setattr(cli.installer, "install", Mock(return_value=tmp_path))
    monkeypatch.setattr(
        cli.installer,
        "latest_release",
        Mock(return_value=cli.installer.Release("1", "https://e/a")),
    )
    monkeypatch.setattr(cli.automation, "launch", Mock(return_value=tmp_path))
    monkeypatch.setattr(cli.automation, "submit_script", Mock())
    client = Mock()
    client.execute_script.return_value = Result()
    client.eval.return_value = 1
    client.tool.return_value = {"answer": 1}
    client.tools.return_value = [SimpleNamespace(model_dump=lambda **_: {"name": "x"})]
    context = Mock()
    context.__enter__ = Mock(return_value=client)
    context.__exit__ = Mock(return_value=False)
    monkeypatch.setattr(cli.automation, "connect", Mock(return_value=context))
    source = tmp_path / "script.vfpy"
    source.write_text("result = 1")
    args = [operation, "--beta", "--destination", str(tmp_path)]
    if operation in {"submit", "run"}:
        args.append(str(source))
    if operation == "eval":
        args.append("1")
    if operation == "call":
        args.extend(["x", "--arguments", '{"foo": 2}'])
    assert cli.main(args) == 0
    assert json.loads(capsys.readouterr().out)
    if operation == "call":
        client.tool.assert_called_once_with("x", foo=2)
    if operation == "run":
        client.execute_script.assert_called_once_with(source)
    if operation == "eval":
        client.eval.assert_called_once_with("1")
    if operation == "tools":
        client.tools.assert_called_once_with()
    if operation in {"run", "eval", "tools", "call"}:
        cli.automation.connect.assert_called_once_with(
            beta=True, destination=tmp_path, timeout=30
        )


def test_cli_validates_before_connect(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(
        cli.automation, "connect", Mock(side_effect=AssertionError("must not connect"))
    )
    assert cli.main(["call", "x", "--arguments", "[]"]) == 1
    assert "JSON object" in capsys.readouterr().err
    assert cli.main(["run", str(tmp_path / "missing")]) == 1


def test_cli_failure_and_verbose(monkeypatch, capsys):
    monkeypatch.setattr(
        cli.installer, "install", Mock(side_effect=TimeoutError("deadline"))
    )
    assert cli.main(["install"]) == 1
    assert "unknown" in capsys.readouterr().err
    with pytest.raises(TimeoutError):
        cli.main(["install", "--verbose"])


@pytest.mark.parametrize("error_type", [TimeoutError, RuntimeError])
def test_cli_startup_failure_reports_notes_without_execution(
    monkeypatch, tmp_path, capsys, error_type
):
    error = error_type("startup failed")
    note = f"Setup outcome may be unknown; inspect {tmp_path / 'result.json'}"
    error.add_note(note)
    remote = SimpleNamespace(FontLab=Mock(), ensure_ready=Mock(side_effect=error))
    discovery = SimpleNamespace(find_bridge=Mock(return_value="bridge.exe"))
    monkeypatch.setitem(sys.modules, "fontlab_remopy", remote)
    monkeypatch.setitem(sys.modules, "fontlab_remopy.discovery", discovery)
    monkeypatch.setattr(a, "ensure_installed", Mock(return_value=tmp_path / "FontLab.exe"))

    assert cli.main(["eval", "1"]) == 1

    output = capsys.readouterr()
    assert output.out == ""
    assert "startup failed" in output.err
    assert note in output.err
    remote.ensure_ready.assert_called_once()
    remote.FontLab.assert_not_called()
    with pytest.raises(error_type) as caught:
        cli.main(["eval", "1", "--verbose"])
    assert caught.value is error
    assert capsys.readouterr().err == ""


@pytest.mark.parametrize("value", ["0", "-1", "nan", "inf"])
def test_cli_timeout_rejects_invalid_values(value):
    with pytest.raises(SystemExit):
        cli.main(["tools", "--timeout", value])


def test_stubs_raise_actionable_importerror():
    for name in ("fontgate", "fontpr"):
        path = (
            Path(__file__).parents[1] / "packages" / name / "src" / name / "__init__.py"
        )
        with pytest.raises(ImportError, match="only inside FontLab"):
            runpy.run_path(str(path))


@pytest.mark.parametrize("stderr", [b"attach canceled\xff\n", "attach canceled\n"])
def test_cli_reports_captured_subprocess_stderr(monkeypatch, capsys, stderr):
    error = subprocess.CalledProcessError(1, ["hdiutil", "attach"], stderr=stderr)
    monkeypatch.setattr(cli.installer, "install", Mock(side_effect=error))
    assert cli.main(["install"]) == 1
    assert "attach canceled" in capsys.readouterr().err
