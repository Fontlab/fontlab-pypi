# this_file: src/fontlab/installer.py
"""Install official FontLab 9 downloads without replacing an existing application."""

from __future__ import annotations

import ctypes
import hashlib
import os
import platform
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

SPARKLE = "{http://www.andymatuschak.org/xml-namespaces/sparkle}"
DOWNLOAD_TIMEOUT = 60
INSTALL_TIMEOUT = 600


@dataclass(frozen=True)
class Release:
    """A full installer selected from an official platform appcast."""

    version: str
    url: str
    length: int | None = None
    sha256: str | None = None


def _platform() -> str:
    if sys.platform not in {"darwin", "win32"}:
        raise NotImplementedError(
            "FontLab 9 installation supports macOS and Windows only"
        )
    return "mac" if sys.platform == "darwin" else "win"


def _version(value: str) -> tuple[int, ...]:
    if not re.fullmatch(r"\d+(?:\.\d+)*", value):
        raise ValueError(f"Invalid appcast version: {value!r}")
    return tuple(map(int, value.split(".")))


def parse_appcast(data: bytes, system: str, system_version: str = "") -> Release:
    """Choose the newest compatible full enclosure, never a delta update."""
    if system not in {"mac", "win"}:
        raise ValueError(f"Unsupported appcast platform: {system}")
    releases = []
    for item in ET.fromstring(data).findall("./channel/item"):
        minimum = item.findtext(f"{SPARKLE}minimumSystemVersion")
        if minimum and system_version and _version(system_version) < _version(minimum):
            continue
        for enclosure in item.findall("enclosure"):
            if enclosure.get(f"{SPARKLE}deltaFrom"):
                continue
            url = enclosure.get("url", "")
            extension = ".dmg" if system == "mac" else ".exe"
            if not urllib.parse.urlsplit(url).path.lower().endswith(extension):
                continue
            if urllib.parse.urlsplit(url).scheme != "https":
                raise ValueError("FontLab installer URL must use HTTPS")
            version = enclosure.get(f"{SPARKLE}version") or item.findtext(
                f"{SPARKLE}version"
            )
            if not version:
                raise ValueError("Appcast installer has no version")
            length = (
                int(enclosure.attrib["length"])
                if "length" in enclosure.attrib
                else None
            )
            digest = enclosure.get("sha256") or enclosure.get(f"{SPARKLE}sha256")
            if length is not None and length <= 0:
                raise ValueError("Appcast installer length must be positive")
            if digest and not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
                raise ValueError("Invalid appcast SHA-256 digest")
            releases.append((_version(version), Release(version, url, length, digest)))
    if not releases:
        raise ValueError("Appcast contains no compatible full FontLab installer")
    return max(releases, key=lambda candidate: candidate[0])[1]


def _open(url: str):
    response = urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": "FontLab-Python/1"}),
        timeout=DOWNLOAD_TIMEOUT,
    )
    if urllib.parse.urlsplit(response.url).scheme != "https":
        response.close()
        raise ValueError("Download redirected away from HTTPS")
    return response


def latest_release(*, beta: bool = False) -> Release:
    """Read the official release or beta appcast for this operating system."""
    system = _platform()
    channel = system + ("-beta" if beta else "")
    url = f"https://download.fontlab.com/fontlab-9/{channel}/appcast.xml"
    with _open(url) as response:
        data = response.read(2_000_001)
    if len(data) > 2_000_000:
        raise ValueError("FontLab appcast exceeds 2 MB")
    version = platform.mac_ver()[0] if system == "mac" else ""
    return parse_appcast(data, system, version)


def default_destination() -> Path:
    """Return the user Applications path or the Windows installer default."""
    if _platform() == "mac":
        return Path.home() / "Applications" / "FontLab 9.app"
    programs = os.environ.get("ProgramFiles")
    if not programs:
        raise OSError("ProgramFiles is unavailable; pass an explicit destination")
    return Path(programs) / "Fontlab" / "FontLab 9" / "FontLab 9.exe"


def find_installed(destination: str | Path | None = None) -> Path | None:
    """Find an explicit install, or the normal user/system FontLab 9 install."""
    candidates = (
        [Path(destination).expanduser()] if destination else [default_destination()]
    )
    if destination is None and _platform() == "mac":
        candidates.append(Path("/Applications/FontLab 9.app"))
    if destination is None and _platform() == "win":
        for variable in ("ProgramFiles", "ProgramFiles(x86)"):
            if os.environ.get(variable):
                candidates.append(
                    Path(os.environ[variable])
                    / "Fontlab"
                    / "FontLab 9"
                    / "FontLab 9.exe"
                )
    for candidate in candidates:
        executable = (
            candidate / "Contents/MacOS/FontLab 9"
            if _platform() == "mac"
            else candidate
        )
        if executable.is_file():
            return candidate
    return None


def _download(release: Release, target: Path) -> None:
    digest = hashlib.sha256()
    total = 0
    with _open(release.url) as response, target.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            total += len(chunk)
            if release.length is not None and total > release.length:
                raise ValueError("Installer exceeds the appcast length")
            output.write(chunk)
            digest.update(chunk)
    if release.length is not None and total != release.length:
        raise ValueError("Installer download length does not match the appcast")
    if release.sha256 and digest.hexdigest().lower() != release.sha256.lower():
        raise ValueError("Installer SHA-256 does not match the appcast")


def _install_mac(installer: Path, destination: Path, scratch: Path) -> None:
    mount = scratch / "mount"
    mount.mkdir()
    subprocess.run(
        [
            "hdiutil",
            "attach",
            "-nobrowse",
            "-readonly",
            "-mountpoint",
            str(mount),
            str(installer),
        ],
        check=True,
        timeout=INSTALL_TIMEOUT,
        capture_output=True,
        input=b"Y\n",
    )
    try:
        applications = list(mount.glob("*.app"))
        if len(applications) != 1:
            raise ValueError("FontLab disk image must contain exactly one application")
        info = plistlib.loads((applications[0] / "Contents/Info.plist").read_bytes())
        if (
            not str(info.get("CFBundleIdentifier", ""))
            .lower()
            .startswith("com.fontlab")
        ):
            raise ValueError("Downloaded application is not a FontLab bundle")
        destination.parent.mkdir(parents=True, exist_ok=True)
        staged = scratch / destination.name
        subprocess.run(
            ["ditto", str(applications[0]), str(staged)],
            check=True,
            timeout=INSTALL_TIMEOUT,
        )
        if destination.exists():
            raise FileExistsError(
                f"Refusing to replace existing application: {destination}"
            )
        shutil.move(str(staged), str(destination))
    finally:
        subprocess.run(
            ["hdiutil", "detach", str(mount)],
            check=True,
            timeout=60,
            capture_output=True,
        )


def _is_admin() -> bool:
    return bool(ctypes.windll.shell32.IsUserAnAdmin())


def _install_windows(installer: Path, destination: Path) -> None:
    subprocess.run(
        [
            str(installer),
            "/VERYSILENT",
            "/SP-",
            "/SUPPRESSMSGBOXES",
            "/NORESTART",
            "/NOCANCEL",
            "/NOCLOSEAPPLICATIONS",
            "/NORESTARTAPPLICATIONS",
            f"/DIR={destination.parent}",
        ],
        check=True,
        timeout=INSTALL_TIMEOUT,
    )


def install(*, beta: bool = False, destination: str | Path | None = None) -> Path:
    """Install when absent; preserve any existing installation without upgrading."""
    system = _platform()
    existing = find_installed(destination)
    if existing:
        return existing
    target = (
        Path(destination).expanduser().absolute()
        if destination
        else default_destination()
    )
    if target.exists():
        raise FileExistsError(
            f"Destination exists but is not a FontLab install: {target}"
        )
    if system == "win" and not _is_admin():
        raise PermissionError(
            "FontLab’s Windows installer requires an elevated terminal; run as administrator"
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    if not os.access(target.parent, os.W_OK):
        raise PermissionError(
            f"Installation destination is not writable: {target.parent}"
        )
    release = latest_release(beta=beta)
    with tempfile.TemporaryDirectory(prefix="fontlab-install-") as directory:
        scratch = Path(directory)
        installer = scratch / ("FontLab.dmg" if system == "mac" else "FontLab.exe")
        _download(release, installer)
        if system == "mac":
            _install_mac(installer, target, scratch)
        else:
            _install_windows(installer, target)
    if find_installed(target) is None:
        raise RuntimeError(f"Installer finished without creating FontLab at {target}")
    return target


def ensure_installed(
    *, beta: bool = False, destination: str | Path | None = None
) -> Path:
    """Return a usable installation, installing the selected channel if absent."""
    return install(beta=beta, destination=destination)
