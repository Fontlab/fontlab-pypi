#!/usr/bin/env bash
# this_file: build.sh
set -euo pipefail
cd "$(dirname "$0")"
if [[ "${ALLOW_DEV:-0}" != 1 ]]; then
  [[ -z "$(git status --porcelain)" ]] || { echo 'Build requires a clean tree' >&2; exit 1; }
  tag="$(git describe --tags --exact-match HEAD)"
  [[ "$tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo 'Build requires a vMAJOR.MINOR.PATCH tag' >&2; exit 1; }
fi
build_dir="$PWD/dist/${tag:-dev}"
uv build --out-dir "$build_dir"
uv build --directory packages/fontgate --out-dir "$build_dir"
uv build --directory packages/fontpr --out-dir "$build_dir"
uvx twine check "$build_dir"/*.whl "$build_dir"/*.tar.gz
