# this_file: src/fontlab/automation.py
"""Use Remopy for remote control and platform application launch support."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from .installer import ensure_installed


def launch(*, beta: bool = False, destination: str | Path | None = None) -> Path:
    """Ensure FontLab exists and request launch, without claiming readiness."""
    app = ensure_installed(beta=beta, destination=destination)
    if sys.platform == "darwin":
        from fontlab_remopy import launch as remote_launch

        remote_launch(app=app)
    else:
        subprocess.Popen([str(app)])
    return app


def submit_script(
    path: str | Path, *, beta: bool = False, destination: str | Path | None = None
) -> Any:
    """Request a .vfpy script; submission does not prove completed execution."""
    source = Path(path).expanduser().resolve(strict=True)
    if not source.is_file() or source.suffix.lower() != ".vfpy":
        raise ValueError("Script submission requires an existing .vfpy file")
    app = ensure_installed(beta=beta, destination=destination)
    if sys.platform == "darwin":
        from fontlab_remopy import submit_script as remote_submit

        return remote_submit(source, app=app)
    subprocess.Popen([str(app), str(source)])
    return {"path": str(source), "execution_verified": False}


def connect(
    *, beta: bool = False, destination: str | Path | None = None, timeout: float = 30
) -> Any:
    """Wait for native MCP readiness, then return Remopy's context manager.

    A timeout leaves execution outcome unknown; callers must inspect the host
    before repeating a mutating operation.
    """
    from fontlab_remopy import FontLab, ensure_ready
    from fontlab_remopy.discovery import find_bridge

    app = ensure_installed(beta=beta, destination=destination)
    candidate = (
        app / "Contents/MacOS/fontlab-mcp"
        if sys.platform == "darwin"
        else app.parent / "fontlab-mcp.exe"
    )
    command = (
        str(candidate)
        if candidate.is_file() and os.access(candidate, os.X_OK)
        else None
    )
    if command is None:
        command = find_bridge()
    if command is None:
        raise FileNotFoundError(
            "FontLab installed, but no native MCP bridge was found; use submit_script"
        )
    ensure_ready(app=app, command=str(command), timeout=timeout)
    return FontLab(command=str(command), timeout=timeout)
