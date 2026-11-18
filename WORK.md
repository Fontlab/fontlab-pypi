---
this_file: WORK.md
---
# Implementation verification

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

Windows behavior, live MCP and actual PyPI distribution verification remain
acceptance tasks in TODO.md. The controller results below supersede the earlier
implementation-pass limits.

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
The first 1.0.0 release remains planned, not published.

Real Windows elevated installation and native execution remain untested. Native
MCP is not exercised against build 9813 because of its reported bridge crash.
