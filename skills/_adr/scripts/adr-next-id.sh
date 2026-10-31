#!/usr/bin/env bash
# Usage: adr-next-id.sh <adr-dir>   prints next id (max + 1) for that scope
set -euo pipefail
here="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
exec python3 "$here/adrlib.py" next-id "$@"
