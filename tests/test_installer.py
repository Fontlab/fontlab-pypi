# this_file: tests/test_installer.py
import hashlib
import io
import plistlib
import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest

from fontlab import installer as i


def feed(items):
    return (
        '<rss xmlns:sparkle="http://www.andymatuschak.org/xml-namespaces/sparkle"><channel>'
        + items
        + "</channel></rss>"
    ).encode()


def item(version="9809", url="https://example.com/app.dmg", extra="", minimum=""):
    return f'<item><sparkle:version>{version}</sparkle:version>{minimum}<enclosure url="{url}" length="3" {extra}/></item>'


def mac_app(path):
    (path / "Contents/MacOS").mkdir(parents=True)
    (path / "Contents/MacOS/FontLab 9").touch()
    (path / "Contents/Info.plist").write_bytes(
        plistlib.dumps({"CFBundleIdentifier": "com.fontlab.fontlab9"})
    )


def test_parse_chooses_latest_compatible_full_installer():
    data = feed(
        item("9808")
        + item(
            "9810",
            minimum="<sparkle:minimumSystemVersion>99.0</sparkle:minimumSystemVersion>",
        )
        + item("9900", extra='sparkle:deltaFrom="9809"')
        + item()
    )
    assert i.parse_appcast(data, "mac", "15.0").version == "9809"


def test_parse_windows_enclosure_version():
    data = feed(
        '<item><enclosure url="https://example.com/a.exe" sparkle:version="9.0.9809" sha256="'
        + "a" * 64
        + '"/></item>'
    )
    result = i.parse_appcast(data, "win")
    assert result.version == "9.0.9809" and result.sha256 == "a" * 64


@pytest.mark.parametrize(
    "data,system",
    [
        (feed(item(url="http://example.com/a.dmg")), "mac"),
        (feed(item(version="bad")), "mac"),
        (feed(item(extra='sha256="bad"')), "mac"),
        (feed(item().replace('length="3"', 'length="0"')), "mac"),
        (feed(item().replace("<sparkle:version>9809</sparkle:version>", "")), "mac"),
        (feed(item()), "other"),
        (feed(item()), "win"),
    ],
)
def test_parse_rejects_invalid_or_missing_installer(data, system):
    with pytest.raises(ValueError):
        i.parse_appcast(data, system)


@pytest.mark.parametrize(
    "system,beta,channel",
    [
        ("darwin", False, "mac"),
        ("darwin", True, "mac-beta"),
        ("win32", False, "win"),
        ("win32", True, "win-beta"),
    ],
)
def test_latest_uses_all_four_official_channels(monkeypatch, system, beta, channel):
    monkeypatch.setattr(i.sys, "platform", system)
    monkeypatch.setattr(i.platform, "mac_ver", lambda: ("15.0", (), ""))
    response = io.BytesIO(
        feed(
            item(
                url="https://example.com/a.dmg"
                if system == "darwin"
                else "https://example.com/a.exe"
            )
        )
    )
    opening = Mock(return_value=response)
    monkeypatch.setattr(i, "_open", opening)
    i.latest_release(beta=beta)
    opening.assert_called_once_with(
        f"https://download.fontlab.com/fontlab-9/{channel}/appcast.xml"
    )


def test_latest_rejects_huge_appcast(monkeypatch):
    monkeypatch.setattr(i, "_platform", lambda: "mac")
    monkeypatch.setattr(i, "_open", lambda _: io.BytesIO(b"x" * 2_000_001))
    with pytest.raises(ValueError, match="2 MB"):
        i.latest_release()


def test_unsupported_platform(monkeypatch):
    monkeypatch.setattr(i.sys, "platform", "linux")
    with pytest.raises(NotImplementedError):
        i.install()


def test_download_checks_length_and_hash(monkeypatch, tmp_path):
    monkeypatch.setattr(i, "_open", lambda _: io.BytesIO(b"abc"))
    i._download(
        i.Release("1", "https://example.com/a", 3, hashlib.sha256(b"abc").hexdigest()),
        tmp_path / "a",
    )
    for release in [
        i.Release("1", "https://e/a", 2),
        i.Release("1", "https://e/a", 4),
        i.Release("1", "https://e/a", 3, "0" * 64),
    ]:
        with pytest.raises(ValueError):
            i._download(release, tmp_path / "a")


def test_open_sets_user_agent_and_refuses_http_redirect(monkeypatch):
    response = Mock(url="https://example.com/a")
    opening = Mock(return_value=response)
    monkeypatch.setattr(i.urllib.request, "urlopen", opening)
    assert i._open("https://example.com/a") is response
    assert opening.call_args.args[0].get_header("User-agent") == "FontLab-Python/1"
    response.url = "http://example.com/a"
    with pytest.raises(ValueError, match="HTTPS"):
        i._open("https://example.com/a")
    response.close.assert_called_once()


def test_existing_mac_install_is_preserved(monkeypatch, tmp_path):
    monkeypatch.setattr(i.sys, "platform", "darwin")
    app = tmp_path / "FontLab 9.app"
    mac_app(app)
    monkeypatch.setattr(
        i, "latest_release", Mock(side_effect=AssertionError("must not download"))
    )
    assert i.ensure_installed(destination=app, beta=True) == app


def test_invalid_existing_destination_is_rejected(monkeypatch, tmp_path):
    monkeypatch.setattr(i.sys, "platform", "darwin")
    with pytest.raises(FileExistsError):
        i.install(destination=tmp_path)


def test_mac_mount_is_detached_after_copy_failure(monkeypatch, tmp_path):
    def run(command, **kwargs):
        if command[1] == "attach":
            mac_app(tmp_path / "mount/FontLab 9.app")
        if command[0] == "ditto":
            raise subprocess.CalledProcessError(1, command)

    runner = Mock(side_effect=run)
    monkeypatch.setattr(i.subprocess, "run", runner)
    with pytest.raises(subprocess.CalledProcessError):
        i._install_mac(tmp_path / "a.dmg", tmp_path / "target.app", tmp_path)
    assert runner.call_args_list[0].kwargs["input"] == b"Y\n"
    assert runner.call_args.args[0][:2] == ["hdiutil", "detach"]
    assert not (tmp_path / "target.app").exists()


def test_mac_install_stages_and_preserves_existing_destination(monkeypatch, tmp_path):
    monkeypatch.setattr(i.sys, "platform", "darwin")

    def run(command, **kwargs):
        if command[1] == "attach":
            mac_app(tmp_path / "mount/FontLab 9.app")
        if command[0] == "ditto":
            mac_app(Path(command[2]))

    monkeypatch.setattr(i.subprocess, "run", run)
    target = tmp_path / "apps/FontLab 9.app"
    i._install_mac(tmp_path / "a.dmg", target, tmp_path)
    assert i.find_installed(target) == target


def test_windows_install_flags_do_not_restart_or_close_apps(monkeypatch, tmp_path):
    runner = Mock()
    monkeypatch.setattr(i.subprocess, "run", runner)
    i._install_windows(
        tmp_path / "installer.exe", tmp_path / "Fontlab/FontLab 9/FontLab 9.exe"
    )
    command = runner.call_args.args[0]
    assert {
        "/VERYSILENT",
        "/NORESTART",
        "/NOCLOSEAPPLICATIONS",
        "/NORESTARTAPPLICATIONS",
    } <= set(command)
    assert command[-1] == f"/DIR={tmp_path / 'Fontlab/FontLab 9'}"
    assert runner.call_args.kwargs["timeout"] == 600


def test_install_downloads_and_checks_result(monkeypatch, tmp_path):
    monkeypatch.setattr(i.sys, "platform", "win32")
    target = tmp_path / "FontLab 9.exe"
    monkeypatch.setattr(i, "_is_admin", lambda: True)
    monkeypatch.setattr(
        i, "latest_release", Mock(return_value=i.Release("1", "https://example.com/a"))
    )
    monkeypatch.setattr(i, "_download", Mock())
    monkeypatch.setattr(
        i, "_install_windows", lambda _installer, destination: destination.touch()
    )
    assert i.install(destination=target) == target
    target.unlink()
    monkeypatch.setattr(i, "_install_windows", lambda *_: None)
    with pytest.raises(RuntimeError, match="without creating"):
        i.install(destination=target)


def test_default_windows_destination_requires_programfiles(monkeypatch, tmp_path):
    monkeypatch.setattr(i.sys, "platform", "win32")
    monkeypatch.delenv("ProgramFiles", raising=False)
    with pytest.raises(OSError):
        i.default_destination()
    monkeypatch.setenv("ProgramFiles", str(tmp_path))
    assert i.default_destination() == tmp_path / "Fontlab/FontLab 9/FontLab 9.exe"


def test_windows_install_requires_elevation_before_download(monkeypatch, tmp_path):
    monkeypatch.setattr(i.sys, "platform", "win32")
    monkeypatch.setattr(i, "_is_admin", lambda: False)
    with pytest.raises(PermissionError, match="elevated"):
        i.install(destination=tmp_path / "FontLab 9.exe")
