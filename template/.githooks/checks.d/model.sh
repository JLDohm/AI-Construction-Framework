# Building-model checks, sourced by .githooks/pre-commit (which provides run, run_checks, need and skip_note).
# shellcheck disable=SC2034  # "failed" is read by .githooks/pre-commit, which sources this file.
# Every commit: ruff format and lint, mypy, the building model's compliance checks
# (python -m bldg check), and pytest. CONST_LONG=1 (set by .githooks/verify) also runs the long-run tests.
if [[ ! -f model/pyproject.toml ]]; then
  skip_note "Model: no model/pyproject.toml yet"
else
  # The tools live in model/.venv of the real repository (verify runs on a clean copy without it).
  model_bin="${CONST_REPO:-$PWD}/model/.venv/bin"
  if [[ ! -x "$model_bin/python" ]]; then
    echo "✗ model/.venv is missing, so the model checks could not run. Install:" >&2
    echo "    cd model && python3 -m venv .venv && .venv/bin/pip install -r requirements.lock" >&2
    failed=1
  elif [[ ! -x "$model_bin/ruff" || ! -x "$model_bin/mypy" || ! -x "$model_bin/pytest" ]]; then
    echo "✗ ruff, mypy or pytest isn't in model/.venv. Install: cd model && .venv/bin/pip install -r requirements.lock" >&2
    failed=1
  elif pushd model >/dev/null; then
    run "$model_bin/ruff" format --check .
    run "$model_bin/ruff" check .
    run "$model_bin/mypy" .
    if [[ -d bldg ]]; then
      run_checks "$model_bin/python" -m bldg check
    else
      skip_note "Model: no bldg package yet, so no compliance checks"
    fi
    model_sets=("not longrun")
    if [[ "${CONST_LONG:-}" == "1" ]]; then model_sets+=("longrun"); fi
    for model_set in "${model_sets[@]}"; do
      echo "→ pytest -q -m \"$model_set\" (model)"
      "$model_bin/pytest" -q -p no:warnings -m "$model_set"
      model_rc=$?
      # Exit code 5 means "no tests collected", which is fine early on.
      if [[ $model_rc -ne 0 && $model_rc -ne 5 && "${CONST_FAILING_CHECKS:-}" == "1" ]]; then
        echo "• tests failed, as expected before the design is drawn"
      elif [[ $model_rc -ne 0 && $model_rc -ne 5 ]]; then
        echo "✗ failed: pytest -m \"$model_set\" (model)" >&2
        failed=1
      fi
    done
    popd >/dev/null || exit 1
  fi
fi
