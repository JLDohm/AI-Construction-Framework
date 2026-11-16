#!/usr/bin/env bash
# Release a drawing set: tools/release.sh <permit|ifc> <rev>
# Checks everything (unverified rule values fail), builds, and freezes the set in
# model/releases/<kind>-<rev>/ with a MANIFEST.txt. Commit it; the owner merges and tags it.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)/model"
if [[ ! -x .venv/bin/python ]]; then
  echo "✗ model/.venv is missing. Install: cd model && python3 -m venv .venv && .venv/bin/pip install -r requirements.lock" >&2
  exit 1
fi
exec .venv/bin/python -m bldg release "$@"
