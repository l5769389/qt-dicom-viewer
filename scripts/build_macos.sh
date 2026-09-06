#!/bin/bash
set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "This script must run on macOS." >&2
    exit 1
fi
if ! command -v uv >/dev/null 2>&1; then
    echo "Install uv, reopen the terminal, and try again." >&2
    exit 1
fi
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"
export UV_PROJECT_ENVIRONMENT="$project_dir/.venv-build-macos"
exec uv run --locked --python 3.13 --no-dev --group build --no-editable python scripts/build_macos.py "$@"
