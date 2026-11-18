---
this_file: DEPENDENCIES.md
---
# Dependencies

- Python 3.11+: standard-library HTTPS, XML, hashing, subprocess and file APIs.
- fontlab-remopy >=2.0.12: shared startup readiness, MCP setup and authenticated client.
- hatchling and hatch-vcs: package builds and versions from shared semver git tags.
- pytest/pytest-cov and ruff: focused checks; not runtime dependencies.
- pypitrust: generated multi-package OIDC publishing helper, maintained upstream.
- macOS hdiutil/ditto and the Windows Inno installer: native installation tools.
