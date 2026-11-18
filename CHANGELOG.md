---
this_file: CHANGELOG.md
---
# Changelog

## Unreleased

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
