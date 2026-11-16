# Building-model formatter, sourced by .githooks/format (which provides run, need and skip_note).
# shellcheck disable=SC2034  # "failed" is read by .githooks/format, which sources this file.
if [[ ! -f model/pyproject.toml ]]; then
  skip_note "Model: no model/pyproject.toml yet"
elif [[ -x model/.venv/bin/ruff ]]; then
  # Sort imports (a lint rule in ruff), then format.
  run model/.venv/bin/ruff check --select I --fix model
  run model/.venv/bin/ruff format model
else
  echo "✗ ruff isn't in model/.venv. Install: cd model && .venv/bin/pip install -r requirements.lock" >&2
  failed=1
fi
