# shellcheck shell=bash
# Helpers shared by .githooks/pre-commit, format and verify (sourced, not run).
# shellcheck disable=SC2034  # "failed" is read by the scripts that source this file.

failed=0

# run CMD...  - run a step; record a failure without stopping the others.
run() {
  echo "→ $*"
  if ! "$@"; then
    echo "✗ failed: $*" >&2
    failed=1
  fi
}

# run_checks CMD...  - run a check step. Under CONST_FAILING_CHECKS=1 (the failing-checks commit only),
# failures are shown but don't block the commit; every other step still must pass.
run_checks() {
  if [[ "${CONST_FAILING_CHECKS:-}" != "1" ]]; then
    run "$@"
    return
  fi
  echo "→ $* (failing-checks commit: failures allowed)"
  if ! "$@"; then echo "• checks failed, as expected before the design is drawn"; fi
}

# need TOOL HINT  - true if TOOL is installed; otherwise a failure with an install hint.
# A missing tool is a failure: a check that didn't run is not a pass.
need() {
  if command -v "$1" >/dev/null 2>&1; then return 0; fi
  echo "✗ $1 is not installed, so its step could not run. Install: $2" >&2
  failed=1
  return 1
}

# skip_note TEXT  - say why a step didn't apply (not a failure).
skip_note() { echo "• $*"; }

# source_all DIR  - source every *.sh file in DIR.
source_all() {
  local f found=0
  for f in "$1"/*.sh; do
    [[ -e "$f" ]] || continue
    found=1
    # shellcheck source=/dev/null
    source "$f"
  done
  if [[ $found -eq 0 ]]; then skip_note "no steps installed ($1/ is empty)"; fi
}
