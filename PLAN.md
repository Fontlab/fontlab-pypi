---
this_file: PLAN.md
---
# Package design

Three distributions share the repository's semver tags and hatch-vcs version.
`fontlab` provides external automation and the `fontlab-cli` entry point;
`fontgate` and `fontpr` raise an actionable ImportError outside FontLab.
The installed native `fontlab` binary is a different API: these wheels belong
in external Python environments, never in FontLab's embedded Python.

The installer reads the appropriate official Sparkle appcast, selects the newest
compatible full installer, downloads over HTTPS with a timeout and length/hash
checks, then installs. macOS uses hdiutil and ditto in a user destination; Windows uses Inno
Setup's unattended switches from an elevated terminal (the installer requires admin). Existing applications are preserved. Installation
is explicit through `install`, or automatic before launch/submit/remote calls.
Remopy owns MCP transport and result handling. Windows launch/script submission
use the installed executable because Remopy's native launch supports macOS only.

The implementation affects package exports, CLI arguments, installer tests,
standalone stub tests, three wheel/sdist configurations, build/publish scripts,
and documentation/examples. No pre-existing production code or callers exist.

Release design reuses pypitrust's `release.sh` and `uvx gitnextver` for automatic
semver bumping, commit/push and three-package builds. `publish.sh` then sends the
tagged artifacts through the existing multi-package OIDC upload helper. Initial
pending publishers are bootstrapped one project at a time.

Remaining native checks: verify elevated silent installation, launch and script
submission on a real Windows host; verify MCP automation on a FontLab build with
a working bridge. These checks are separate from the completed package delivery.
Current appcast Sparkle signatures remain an explicitly documented verification
limit; HTTPS, declared length and any supplied SHA-256 are checked.
