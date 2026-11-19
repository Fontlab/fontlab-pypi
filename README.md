---
this_file: README.md
---
# FontLab for external Python

Install FontLab 9 and automate its desktop application from ordinary Python.
Version 1.0.2 is published as [fontlab](https://pypi.org/project/fontlab/1.0.2/),
[fontgate](https://pypi.org/project/fontgate/1.0.2/) and
[fontpr](https://pypi.org/project/fontpr/1.0.2/); the
[GitHub release](https://github.com/Fontlab/fontlab-pypi/releases/tag/v1.0.2)
contains all three wheels and source archives.

```bash
uv pip install fontlab
fontlab-cli latest --beta
fontlab-cli install --beta
fontlab-cli launch
fontlab-cli submit my-script.vfpy
fontlab-cli eval 'fontlab.__name__'
fontlab-cli run automation.py
fontlab-cli tools
fontlab-cli call list_fonts --arguments '{}'
```

`install`, `launch`, `submit` and remote commands install FontLab automatically
when it is absent. `--beta` selects the beta appcast for a new installation;
an existing installation is reused unchanged, even if older or newer than the
feed. There is no automatic upgrade or downgrade. `latest` only reads the feed.
All command options follow the command name; `--verbose` shows a traceback.

On macOS, the default new destination is `~/Applications/FontLab 9.app`.
An existing `/Applications/FontLab 9.app` is also recognized. To select a different
bundle, pass `--destination '/path/to/FontLab 9.app'`.
On Windows, run installation from an **elevated terminal**: the shipped Inno
installer requires administrator privileges. Its default is
`%ProgramFiles%\Fontlab\FontLab 9\FontLab 9.exe`. `--destination` takes the full
executable path. Silent flags suppress setup UI and prohibit restarts or closing
applications; they cannot bypass Windows UAC. Normal launch and automation do not
need elevation after installation. Linux is unsupported.

Downloads use the official platform appcasts over HTTPS, bounded network and
installer waits, and enclosure length checks. A SHA-256 is checked if supplied
by the feed. Current feeds supply Sparkle signatures, **not SHA-256 hashes**;
this package does not verify those signatures. The unattended macOS installer automatically accepts the disk image’s licence
prompt. Use installation only if you accept FontLab’s licence terms; activation
and entitlement remain separate. The disk image is detached on copy failure. Existing destination files are never replaced intentionally.

```python
import fontlab

fontlab.launch(beta=True)
with fontlab.connect(timeout=30) as app:
    print(app.eval('fontlab.__name__'))
    print(app.fonts())
```

Automation uses [fontlab-remopy](https://github.com/fontlabcom/fontlab-remopy),
including its authenticated MCP transport and execution result handling.
`connect`, `run`, `eval`, `tools` and `call` wait for FontLab's native MCP
catalogue before sending the requested operation. Remopy first opens FontLab
with one special `.vfpy` setup macro that enables external MCP access and sets
`generalHideWarningDialogs=True`. It confirms macro execution, then waits for
MCP readiness. `--timeout` bounds startup readiness
(30 seconds by default) and applies separately to each subsequent remote call.
Only readiness checks repeat; scripts and tool calls are never retried.
The setup macro changes the MCP and warning preferences persistently. A modal
startup dialog shown before FontLab accepts scripts still needs dismissal;
the macro cannot run until then.

The same bootstrap is available through Remopy's public synchronous helper,
which calls its public `setup_mcp` operation before any readiness probe:

```python
from fontlab_remopy import ensure_ready

ensure_ready(timeout=30)
```

`run` returns JSON with `value`, `stdout` and `stderr`; remote scripts assign
`result` for a return value. `submit` hands a `.vfpy` file to FontLab and does
not claim execution finished. On Windows file submission uses FontLab's executable.
A native MCP bridge must be present for `run`, `eval`, `tools` and `call`;
otherwise use `submit`.
Timeouts can mean an operation executed without a response: inspect the host
before repeating a mutating command. FontLab 9.1.9813 has a reported native bridge
crash; use script submission on affected builds rather than MCP commands.

This is **not** the native `fontlab` binary API. Use these packages only in an
external Python environment, never install them in FontLab's embedded Python.
Inside FontLab, its native `fontlab`, `fontgate` and `fontpr` modules provide the
real font-editing API. Outside it, the `fontgate` and `fontpr` PyPI distributions
are explanatory stubs that raise `ImportError`. They do not emulate native types.
FontLab licensing and activation remain the normal desktop application's process;
installation does not grant a licence or bypass activation.

## Development and releases

```bash
./test.sh -q
ALLOW_DEV=1 ./build.sh   # development version from git
./release.sh          # commit, patch bump, push and build all three packages
./publish.sh          # release, then upload all three through PyPI OIDC
./publish.sh minor    # or major
```

`release.sh` reuses pypitrust's `uvx gitnextver` flow: it fetches, fast-forwards
the tracked branch, commits pending changes, bumps the semver tag and pushes
through installed hooks. A clean, already tagged HEAD is reused. Run it only
from a reviewed release checkout. `publish.sh` runs this release step first.

All three packages use the same repository tags through hatch-vcs. Build artifacts
are collected in `dist/vMAJOR.MINOR.PATCH` (`dist/dev` for development). Publishing uses the multi-package upload helper generated
by [pypitrust](https://github.com/twardoch/pypitrust). All three projects now
have Trusted Publishers for repository `Fontlab/fontlab-pypi`, workflow
`pypi-upload.yml`, environment `pypi`; `./publish.sh` publishes them together.
The initial release registered and uploaded `fontlab`, then `fontgate`, then
`fontpr`, because PyPI rejects simultaneous pending publishers with identical
repository/workflow/environment tuples. Each upload converted its pending
publisher before the next registration.
The helper retains failed staging drafts for retry. No PyPI API token is required.

Actual desktop installation, host automation and PyPI publication are separate
checks; see [WORK.md](WORK.md) for the verified scope and [TODO.md](TODO.md)
for outstanding acceptance checks.
