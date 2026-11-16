"""Rule values: numbers from the building code with their section, and whether the owner has
checked them against their own copy of the code. Never code text: it is copyrighted.

Rules live in TOML files under `rules/` (the code pack's folder, e.g. `rules/irc-2021/`).
Local amendments live in `rules/local/`, are loaded last, and replace a rule with the same id
when they say `amends = true`:

    [[rule]]
    id = "R311.7.5.1-riser-max"
    code = "IRC 2021"
    section = "R311.7.5.1"
    title = "Stair riser height, maximum"   # in your own words
    value = 7.75                            # 0 = not filled in yet
    units = "in"
    source = "IRC 2021 R311.7.5.1"           # where the number comes from
    verified = false                        # true once the owner has checked it
"""

import tomllib
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REQUIRED = ("id", "code", "section", "title", "units", "source", "verified")
ALLOWED = {*REQUIRED, "value", "table", "amends", "note"}


class RuleError(Exception):
    """A rule file is malformed, or a rule is missing or not filled in."""


@dataclass(frozen=True)
class Rule:
    id: str
    code: str
    section: str
    title: str
    units: str
    source: str
    verified: bool
    origin: str  # the file it came from, relative to the rules folder
    value: float | None = None
    table: tuple[Mapping[str, Any], ...] = ()
    note: str = ""
    amended: bool = False  # true if a local amendment replaced the model code's value

    @property
    def cite(self) -> str:
        """How findings cite this rule, e.g. "IRC 2021 R311.7.5.1"."""
        return f"{self.code} {self.section}"

    @property
    def filled(self) -> bool:
        """False while the value is still 0 or missing (never guess it)."""
        return bool(self.table) or (self.value is not None and self.value != 0)

    def num(self) -> float:
        """The rule's single value. Raises RuleError if it isn't filled in yet."""
        if self.value is None or not self.filled:
            raise RuleError(f"rule {self.id} ({self.cite}) is not filled in yet")
        return self.value

    def lookup(self, result: str, **keys: object) -> float:
        """One cell of a table rule: the `result` column of the row matching every key.
        Raises RuleError if no row matches, or the cell is 0 (not filled in yet)."""
        rows = [row for row in self.table if all(row.get(k) == v for k, v in keys.items())]
        wanted = ", ".join(f"{k}={v!r}" for k, v in keys.items())
        if not rows:
            raise RuleError(f"rule {self.id} ({self.cite}) has no row for {wanted}: add it from the code")
        if len(rows) > 1:
            raise RuleError(f"rule {self.id} ({self.cite}) has {len(rows)} rows for {wanted}")
        cell = rows[0].get(result, 0)
        if isinstance(cell, bool) or not isinstance(cell, int | float) or cell == 0:
            raise RuleError(f"rule {self.id} ({self.cite}): {result} for {wanted} is not filled in yet")
        return float(cell)


class RuleBook(Mapping[str, Rule]):
    def __init__(self, rules: Mapping[str, Rule]) -> None:
        self._rules = dict(rules)

    def __getitem__(self, rule_id: str) -> Rule:
        try:
            return self._rules[rule_id]
        except KeyError:
            raise RuleError(f"no rule {rule_id!r} in rules/") from None

    def __contains__(self, rule_id: object) -> bool:
        return rule_id in self._rules

    def __iter__(self) -> Iterator[str]:
        return iter(self._rules)

    def __len__(self) -> int:
        return len(self._rules)


def _parse(raw: Mapping[str, Any], origin: str) -> tuple[Rule, bool]:
    where = f"{origin}, rule {raw.get('id', '?')!r}"
    missing = [k for k in REQUIRED if k not in raw]
    if missing:
        raise RuleError(f"{where}: missing {', '.join(missing)}")
    unknown = sorted(set(raw) - ALLOWED)
    if unknown:
        raise RuleError(f"{where}: unknown field(s) {', '.join(unknown)}")
    if not isinstance(raw["verified"], bool):
        raise RuleError(f"{where}: verified must be true or false")
    value = raw.get("value")
    if value is not None and (isinstance(value, bool) or not isinstance(value, int | float)):
        raise RuleError(f"{where}: value must be a number")
    table = raw.get("table", [])
    if not isinstance(table, list) or not all(isinstance(row, dict) for row in table):
        raise RuleError(f"{where}: table must be a list of rows")
    if value is None and "table" not in raw:
        raise RuleError(f"{where}: needs a value (0 if not filled in yet) or a table ([] if not filled in yet)")
    rule = Rule(
        id=str(raw["id"]),
        code=str(raw["code"]),
        section=str(raw["section"]),
        title=str(raw["title"]),
        units=str(raw["units"]),
        source=str(raw["source"]),
        verified=raw["verified"],
        origin=origin,
        value=None if value is None else float(value),
        table=tuple(table),
        note=str(raw.get("note", "")),
    )
    return rule, bool(raw.get("amends", False))


def load_rules(
    root: Path, jurisdiction: Path | None = None, *, codes: Sequence[str] | None = None, amendments: bool = True
) -> RuleBook:
    """Load the code's rule files under `root` (only the `codes` subfolders if given, else every
    folder but local/), then the jurisdiction's design values (the [[rule]] entries of
    jurisdiction/jurisdiction.toml), then `root/local/` last, as amendments (unless `amendments` is
    false: local amendments change the enforced code, not a preferred one)."""
    local = root / "local"
    if not root.is_dir():
        files: list[Path] = []
    elif codes is None:
        files = sorted(p for p in root.rglob("*.toml") if local not in p.parents)
    else:
        files = [p for code in codes for p in sorted((root / code).rglob("*.toml"))]
    if jurisdiction is not None and jurisdiction.is_file():
        files.append(jurisdiction)
    if amendments and local.is_dir():
        files += sorted(local.rglob("*.toml"))
    rules: dict[str, Rule] = {}
    for path in files:
        origin = str(path.relative_to(root)) if root in path.parents else f"../{path.parent.name}/{path.name}"
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as e:
            raise RuleError(f"{origin}: {e}") from None
        for raw in data.get("rule", []):
            rule, amends = _parse(raw, origin)
            if amends:
                if local not in path.parents:
                    raise RuleError(f"{origin}: only rules/local/ may amend ({rule.id})")
                if rule.id not in rules:
                    raise RuleError(f"{origin}: amends {rule.id!r}, which doesn't exist")
                rule = Rule(**{**rule.__dict__, "amended": True})
            elif rule.id in rules:
                raise RuleError(f"{origin}: duplicate rule id {rule.id!r} (also in {rules[rule.id].origin})")
            rules[rule.id] = rule
    return RuleBook(rules)
