# Building-model dependency audit, sourced by .githooks/verify (which provides run, need and skip_note).
# shellcheck disable=SC2034  # "failed" is read by .githooks/verify, which sources this file.
if [[ ! -f model/pyproject.toml ]]; then
  skip_note "Model: no model/pyproject.toml yet"
elif [[ ! -f model/requirements.lock ]]; then
  echo "✗ model/requirements.lock is missing. Run: model/.venv/bin/pip freeze > model/requirements.lock, and commit it." >&2
  failed=1
elif [[ -x model/.venv/bin/pip-audit ]]; then
  run model/.venv/bin/pip-audit -r model/requirements.lock
else
  echo "✗ pip-audit is not installed in model/.venv. Install: model/.venv/bin/pip install pip-audit" >&2
  failed=1
fi
