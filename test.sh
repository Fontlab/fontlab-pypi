#!/usr/bin/env bash
# this_file: test.sh
set -euo pipefail
cd "$(dirname "$0")"
uv run --no-project --python 3.11 --with pytest --with pytest-cov pytest --cov=src/fontlab --cov-fail-under=80 "$@"
uvx ruff check src tests examples
