#!/usr/bin/env bash
# Usage: adr-resolve.sh --tags t1,t2 [--files f1 f2 ...] [--repo-dir docs/adr]
# Prints accepted, tag-matched ADR rules (repo first; superseded globals dropped). Read-only.
set -euo pipefail
here="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
exec python3 "$here/adrlib.py" resolve "$@"
