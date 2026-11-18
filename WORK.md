---
this_file: WORK.md
---
# Implementation verification

The implementation and review sections below are historical snapshots. The
final 1.0.0 delivery section records the completed release and current limits.

Implemented the three distributions and external CLI in an isolated development
checkout. No existing application was replaced or launched by this implementation
pass; no MCP request was sent.

- `./test.sh -q`: 45 tests pass on Python 3.11.16; 94.95% combined coverage;
  installer 93%, automation 100%, CLI 99%. Ruff passes.
- `ALLOW_DEV=1 ./build.sh`: three wheels and three sdists build from genuine
  hatch-vcs metadata; Twine metadata checks pass. These are development artifacts,
  not published releases. Nested packages build their wheels from their sdists.
- Installer/CLI subprocess tests cover four appcast channels, compatible full
  installer selection, malformed feeds, HTTPS redirects, download length/hash,
  existing-install preservation, detach after copy failure, Inno arguments,
  Windows elevation requirement and all CLI routes.
- Actual Remopy source confirms native launch/submit is macOS-only; Windows
  submission invokes FontLab's executable directly. MCP clients are reused.
- The actual Inno source requires admin by default and has no per-user override;
  installation therefore refuses a non-elevated Windows terminal before download.
- OIDC workflow and uploader generated from local pypitrust's add_upload_helper;
  no publisher registration or release was performed in this pass.

At this implementation checkpoint, Windows behavior, live MCP and PyPI
distribution verification were pending. The controller results and final
delivery below supersede these earlier limits.

## Review fixes

`./test.sh -q` after review round1:45 passed in0.38s,94.95% combined coverage,
Ruff pass. macOS DMG attach now supplies the affirmative licence input required
by the official image; an existing regression verifies the input and detach on
copy failure. CLI run delegates to Remopy execute_script to retain __file__ and
UTF-8 BOM handling. Captured subprocess stderr is shown with safe byte decoding;
two focused cases cover bytes and text stderr. Real installation recheck remains
controller-owned; no native application was launched in this pass.

## Controller verification and release helper

The independent source review approved the corrected implementation. Controller
verification passes all 45 tests at 94.95% combined coverage plus Ruff. All four
actual macOS/Windows release/beta appcasts resolved build 9809. The actual macOS
installer download matched its declared 269,168,520 bytes. Using that retained
download, the corrected installer attached the image, copied build 9809 to a
private destination, detached it and detected the installed app. A second call
reused that app without fetching the feed. The owner's running build 9813 was
neither replaced nor launched.

Added pypitrust's existing `release.sh` template, substituting only the package
name; `publish.sh` now runs it before uploading the three packages. This provides
the same `uvx gitnextver` semver bump/commit/push flow as the sibling packages.
No release helper, tag push or publication was executed by this authoring pass.
At that authoring checkpoint, the first 1.0.0 release was planned but unpublished.

Real Windows elevated installation and native execution remain untested. Native
MCP is not exercised against build 9813 because of its reported bridge crash.


## Final 1.0.0 delivery — 2026-11-18

Reviewed source commit `dbc1119edf4cb034e01a8b82a6a20e34ff904c5b` was integrated
into upstream main and tagged `v1.0.0` using `gitnextver`. The
[GitHub release](https://github.com/Fontlab/fontlab-pypi/releases/tag/v1.0.0)
contains all six artifacts. Downloaded release assets and all six PyPI files
match the reviewed local SHA-256 hashes.

- Published [fontlab](https://pypi.org/project/fontlab/1.0.0/),
  [fontgate](https://pypi.org/project/fontgate/1.0.0/) and
  [fontpr](https://pypi.org/project/fontpr/1.0.0/) 1.0.0 through PyPI OIDC.
  Initial pending publishers were registered and used one at a time because
  PyPI rejected duplicate pending repository/workflow/environment identities.
- [Source CI](https://github.com/Fontlab/fontlab-pypi/actions/runs/44411835581)
  passed all six Windows/macOS/Linux and Python 3.11/3.13 combinations for the
  exact source commit. OIDC uploads passed for
  [fontlab](https://github.com/Fontlab/fontlab-pypi/actions/runs/44411866460),
  [fontgate](https://github.com/Fontlab/fontlab-pypi/actions/runs/44412108265) and
  [fontpr](https://github.com/Fontlab/fontlab-pypi/actions/runs/44412316256).
- All three final source archives rebuilt successfully. All three released
  wheels installed in a clean arm64 Python 3.11 environment.
- A separate clean arm64 Python 3.12 environment installed all three 1.0.0
  packages from PyPI. Metadata versions and the imported package origin matched
  that environment; the two stubs raised the expected explanatory ImportErrors.
  The released CLI detected and reused the isolated build 9809 installation
  without downloading. The owner's build 9813 remained unchanged.
- An earlier default Python 3.11 environment resolved to x86_64 and failed to
  build the transitive cryptography dependency. The explicit arm64 installation
  passed without changing package dependencies.

Real Windows elevated installation, launch and script submission remain untested.
Native MCP execution remains untested on a build with a working bridge; the
known 9813 bridge crash was not exercised. CI does not establish these native
outcomes. Current Sparkle signatures are not cryptographically verified; the
installer checks HTTPS, declared length and SHA-256 when the feed supplies one.
