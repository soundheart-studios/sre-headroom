#!/usr/bin/env bash
# Usage: adr-index.sh <adr-dir> [--check]   exit 0 ok, 1 stale index, 2 invalid frontmatter/unknown tag
set -euo pipefail
here="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
[[ $# -ge 1 ]] || { echo "usage: adr-index.sh <adr-dir> [--check]" >&2; exit 2; }
exec python3 "$here/adrlib.py" index "$@"
