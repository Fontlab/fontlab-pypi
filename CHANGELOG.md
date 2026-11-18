---
this_file: CHANGELOG.md
---
# Changelog

## Unreleased — Issue 274

- Route `connect` and the CLI's `run`, `eval`, `tools` and `call` commands
  through Remopy's bounded native startup and MCP bootstrap before creating
  the operation client. Readiness failures prevent user operations; user
  scripts and tool calls execute once.
- Show setup exception notes in normal CLI errors so the retained evidence path
  and uncertainty guidance remain visible; verbose mode still raises the error.
- Require Remopy 2.0.12 or newer for its shared macOS/Windows readiness API.
  Source verification: 50 tests pass, automation coverage 100%, combined
  coverage 95.00%, Ruff passes. Native startup and installed release checks
  remain open in TODO.

## 1.0.0 — 2026-11-18

- Implemented external `fontlab` API and `fontlab-cli` installation, launch,
  script submission and Remopy remote operations.
- Added official release/beta appcast selection for macOS and Windows,
  HTTPS downloads with length/optional SHA-256 checks, DMG installation and
  elevated unattended Inno installation, preserving existing applications.
- Added explanatory native-only `fontgate` and `fontpr` distributions.
- Added shared hatch-vcs versioning, three-package builds and pypitrust OIDC helper.

- Reused pypitrust's semver release helper; publishing now runs its
  `uvx gitnextver` commit/bump/push/build flow before OIDC upload.
- Corrected unattended DMG licence acceptance, preserved Remopy file-execution
  semantics and exposed captured subprocess errors; 45 tests and Ruff pass.
- Verified the four live feeds and a real macOS installer download, followed by
  isolated copy/detach/reuse; the running application was preserved.

- Published all three 1.0.0 distributions to PyPI and created the GitHub release;
  all six published artifact hashes match the reviewed builds.
- Passed source CI on Windows, macOS and Linux with Python 3.11 and 3.13;
  rebuilt all three source archives and verified clean arm64 wheel/PyPI installs.
