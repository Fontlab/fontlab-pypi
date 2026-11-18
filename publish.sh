#!/usr/bin/env bash
# this_file: publish.sh
set -euo pipefail
cd "$(dirname "$0")"
./release.sh "${1:-patch}"
tag="$(git describe --tags --exact-match HEAD)"
exec scripts/pypi-upload.sh "dist/$tag/"*.whl "dist/$tag/"*.tar.gz
