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

SKILL_ROOT="$ROOT/vendor/simple-english"
for relative in LICENSE SOURCE.txt \
    skills/simple-english/SKILL.md \
    skills/simple-english/references/rule-catalog.md \
    skills/simple-english/references/strict-vocabulary.md \
    skills/simple-english/references/use-cases.md \
    skills/simple-english/references/word-swaps.md; do
  test -f "$SKILL_ROOT/$relative"
done

grep -Fq 'dockerfile: sbx-kit-pifrost-opinions-chozian.dockerfile' \
  "$ROOT/sbx-kit-pifrost-opinions-chozian.yaml"
grep -Fq 'type: com.docker.sandbox/agent-skill@1' \
  "$ROOT/sbx-kit-pifrost-opinions-chozian.yaml"
grep -Fq 'path: /usr/local/share/sbx-kit-pifrost-opinions/simple-english' \
  "$ROOT/sbx-kit-pifrost-opinions-chozian.yaml"
grep -Fq 'COPY vendor/simple-english/skills/simple-english/ /usr/local/share/sbx-kit-pifrost-opinions/simple-english/' \
  "$ROOT/sbx-kit-pifrost-opinions-chozian.dockerfile"
if grep -Fq '/home/agent/.agents/skills/simple-english' \
  "$ROOT/sbx-kit-pifrost-opinions-chozian.dockerfile"; then
  echo "Simple English must use agent-skill@1 instead of the discovery path" >&2
  exit 1
fi
if grep -Fq 'Configure npm proxy' "$ROOT/sbx-kit-pifrost-pi-mixin.yaml"; then
  echo "Pi mixin must use upstream npm defaults" >&2
  exit 1
fi
grep -Fq 'version: "1.0.0"' \
  "$ROOT/sbx-kit-pifrost-opinions-chozian.yaml"
echo "Simple English vendor files and generated Dockerfile validated"
