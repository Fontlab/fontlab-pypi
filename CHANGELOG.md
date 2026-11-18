---
this_file: CHANGELOG.md
---
# Changelog

## 1.0.2 — 2026-11-19

- Route `connect` and the CLI's `run`, `eval`, `tools` and `call` commands
  through Remopy's bounded native startup and MCP bootstrap before creating
  the operation client. Readiness failures prevent user operations; user
  scripts and tool calls execute once.
- Show setup exception notes in normal CLI errors so the retained evidence path
  and uncertainty guidance remain visible, including notes on the direct
  cancellation cause of an asyncio timeout; verbose mode still raises the error.
- Require Remopy 2.0.12 or newer for its shared macOS/Windows readiness API.
  Source verification: 51 tests pass, automation coverage 100%, combined
  coverage 95.02%, Ruff passes. Native startup checks remain open in TODO.
- Published all three 1.0.2 packages from source
  `3cb604419516ab068a92ebbf938a614e43f126b3` after Remopy 2.0.12 from
  `2ed7cd2`. Source CI passed all six OS/Python combinations and the
  [OIDC upload](https://github.com/Fontlab/fontlab-pypi/actions/runs/44419239311)
  succeeded.
- Verified a clean arm64 Python 3.12 PyPI installation with normal dependency
  resolution to Remopy 2.0.12. All eight wheel/sdist downloads across the four
  distributions match PyPI digests and GitHub release assets; the six consumer
  artifacts also match the local builds.
- Verified the installed `tools`, `eval`, `run` and `call` routes with real MCP
  SDK framing and relay subprocesses: one confirmed setup submission, recovered
  catalogue and no replayed user operations. Native launch/submission remained
  fixture boundaries; real macOS/Windows acceptance remains open.

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
