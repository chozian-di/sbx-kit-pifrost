#!/usr/bin/env bash
# Compile project Python sources without writing bytecode into the WSL/virtiofs
# checkout. The workspace can contain an unrecoverable __pycache__ entry whose
# filesystem operations return EIO.
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
CACHE_DIR=$(mktemp -d "${TMPDIR:-/tmp}/sbx-kit-pifrost-pycache.XXXXXX")
trap 'rm -rf "$CACHE_DIR"' EXIT

PYTHONPYCACHEPREFIX="$CACHE_DIR" \
  python3 -m py_compile "$ROOT/scripts/render-kit-set.py"

echo "Python bytecode compilation succeeded (temporary cache: $CACHE_DIR)"
