# Rule values

One folder per code pack (e.g. `irc-2021/`), plus `local/` for the jurisdiction's amendments.
The format is described at the top of `bldg/rules.py`.

- Numbers, units and section IDs only. Never copy code text: it is copyrighted.
- `verified = false` until the owner has checked the value against their own copy of the code.
  A release refuses any unverified rule a check uses.
- `value = 0` means "not filled in yet". A check that uses it fails; never guess it.
- Don't change a value to make a design pass. Change it only when the owner corrects it,
  and record the correction in `docs/decisions.md`.
