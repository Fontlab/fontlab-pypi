# this_file: src/fontlab/__init__.py
"""External FontLab installation and automation; not the native in-app API."""

from .automation import connect, launch, submit_script
from .installer import ensure_installed, install, latest_release

__all__ = [
    "connect",
    "ensure_installed",
    "install",
    "latest_release",
    "launch",
    "submit_script",
]
