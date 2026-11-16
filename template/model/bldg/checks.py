"""Compliance and fit checks, and the runner behind `python -m bldg check`.

A check is a function in the project's `checks/` folder, named by its check-plan ID and
citing the rules (or owner requirements) it enforces:

    @check("T-2.1", rules=["R311.7.5.1-riser-max"])
    def riser_height(b: Building, r: Rules) -> Iterator[Result]:
        limit = r.value("R311.7.5.1-riser-max")
        for s in b.stairs:
            for i, h in enumerate(s.risers, 1):
                yield Result(f"stair {s.id} riser {i}", h <= limit, fmt_in(h), f"<= {fmt_in(limit)}")

A check can only read the rules it declares, so the report's citations are always right.
A check that yields nothing fails: say "not applicable" with a passing Result instead.
"""

import importlib
import re
import sys
import tomllib
from collections.abc import Callable, Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from bldg.elements import Building
from bldg.rules import Rule, RuleBook, RuleError

CHECK_ID = re.compile(r"^T-\d+\.\d+[a-z]?$")
REQUIREMENT_ID = re.compile(r"^R-\d+$")
_ATTR = "__bldg_check__"


@dataclass(frozen=True)
class Result:
    """One element against one limit."""

    element: str
    passed: bool
    measured: str
    limit: str
    note: str = ""


class Rules:
    """The rules one check declared, and nothing else."""

    def __init__(self, book: RuleBook, declared: Sequence[str]) -> None:
        self._book = book
        self._declared = tuple(declared)

    def __getitem__(self, rule_id: str) -> Rule:
        if rule_id not in self._declared:
            raise RuleError(f"rule {rule_id!r} is used but not declared in @check(rules=...)")
        return self._book[rule_id]

    def value(self, rule_id: str) -> float:
        return self[rule_id].num()


CheckFn = Callable[[Building, Rules], Iterable[Result]]


@dataclass(frozen=True)
class CheckDef:
    id: str
    title: str
    rules: tuple[str, ...]
    requirements: tuple[str, ...]
    fn: CheckFn
    module: str


def check(
    check_id: str, *, rules: Sequence[str] = (), requirements: Sequence[str] = ()
) -> Callable[[CheckFn], CheckFn]:
    """Register a check under its check-plan ID. It must cite rules, requirements, or both."""
    if not CHECK_ID.match(check_id):
        raise ValueError(f"check id {check_id!r} must look like T-2.1 (phase.case)")
    if not rules and not requirements:
        raise ValueError(f"check {check_id} must cite rules=[...] or requirements=[...]")
    bad = [r for r in requirements if not REQUIREMENT_ID.match(r)]
    if bad:
        raise ValueError(f"check {check_id}: requirement ids look like R-3, got {bad}")

    def wrap(fn: CheckFn) -> CheckFn:
        doc = (fn.__doc__ or fn.__name__).strip().splitlines()[0]
        setattr(fn, _ATTR, CheckDef(check_id, doc, tuple(rules), tuple(requirements), fn, fn.__module__))
        return fn

    return wrap


def discover(folder: Path) -> list[CheckDef]:
    """Import every module in the checks folder (a package named after the folder) and
    collect its checks, sorted by ID."""
    package = folder.name
    parent = str(folder.parent.resolve())
    if parent not in sys.path:
        sys.path.insert(0, parent)
    importlib.invalidate_caches()  # the folder may be newer than Python's cached directory listings
    found: dict[str, CheckDef] = {}
    for path in sorted(folder.glob("*.py")):
        if path.name.startswith("_"):
            continue
        module = importlib.import_module(f"{package}.{path.stem}")
        for obj in vars(module).values():
            cdef = getattr(obj, _ATTR, None)
            if not isinstance(cdef, CheckDef) or cdef.module != module.__name__:
                continue
            if cdef.id in found:
                raise ValueError(f"check {cdef.id} is defined twice: {found[cdef.id].module} and {cdef.module}")
            found[cdef.id] = cdef
    return sorted(found.values(), key=lambda c: _sort_key(c.id))


def _sort_key(check_id: str) -> tuple[int, int, str]:
    phase, case = check_id[2:].split(".")
    digits = re.match(r"\d+", case)
    return int(phase), int(digits.group() if digits else 0), case


Status = Literal["pass", "fail", "error", "waived"]


@dataclass(frozen=True)
class Waiver:
    """A preferred-code check set aside, because meeting it would break the enforced code (or for
    another reason the owner decided). Lives in checks/waivers.toml; names its decision (D-x)."""

    check: str
    decision: str
    reason: str


def load_waivers(path: Path) -> dict[str, Waiver]:
    """Read checks/waivers.toml: [[waiver]] entries with check, decision and reason."""
    if not path.is_file():
        return {}
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"{path.name}: {e}") from None
    out: dict[str, Waiver] = {}
    for raw in data.get("waiver", []):
        missing = [k for k in ("check", "decision", "reason") if not str(raw.get(k, "")).strip()]
        if missing:
            raise ValueError(f"{path.name}: waiver {raw.get('check', '?')!r} needs {', '.join(missing)}")
        w = Waiver(str(raw["check"]), str(raw["decision"]), str(raw["reason"]))
        if w.check in out:
            raise ValueError(f"{path.name}: two waivers for {w.check}")
        out[w.check] = w
    return out


@dataclass
class Outcome:
    check: CheckDef
    cites: list[str]
    results: list[Result] = field(default_factory=list)
    error: str = ""
    preferred: bool = False  # run against the preferred (latest) code, not the enforced one
    waiver: Waiver | None = None

    @property
    def status(self) -> Status:
        if self.error:
            raw: Status = "error"
        else:
            raw = "pass" if all(r.passed for r in self.results) else "fail"
        return "waived" if raw != "pass" and self.preferred and self.waiver else raw


@dataclass
class Report:
    problems: list[str]  # model errors (duplicate ids, broken references), bad or stale waivers
    outcomes: list[Outcome]
    unverified: list[Rule]  # enforced-code rules used by checks that the owner hasn't verified yet
    release: bool
    unverified_preferred: list[Rule] = field(default_factory=list)  # warned about, never blocking

    @property
    def ok(self) -> bool:
        if self.problems or any(o.status not in ("pass", "waived") for o in self.outcomes):
            return False
        return not (self.release and self.unverified)


def _run_one(building: Building, book: RuleBook, cdef: CheckDef, used: dict[str, Rule], preferred: bool) -> Outcome:
    cites: list[str] = []
    error = ""
    for rule_id in cdef.rules:
        try:
            rule = book[rule_id]
        except RuleError as e:
            error = str(e)
            continue
        used[rule.id] = rule
        cites.append(rule.cite + (" (local amendment)" if rule.amended else ""))
        if not rule.filled:
            error = f"rule {rule.id} ({rule.cite}) is not filled in yet (value 0): never guess it"
    cites += list(cdef.requirements)
    outcome = Outcome(cdef, cites, error=error, preferred=preferred)
    if not error:
        try:
            outcome.results = list(cdef.fn(building, Rules(book, cdef.rules)))
            if not outcome.results:
                outcome.error = "found nothing to check (yield a passing Result saying why it doesn't apply)"
        except Exception as e:  # noqa: BLE001 - any failure in a check is reported, not raised
            outcome.error = f"{type(e).__name__}: {e}"
    return outcome


def run(
    building: Building,
    book: RuleBook,
    checks: Sequence[CheckDef],
    *,
    release: bool = False,
    preferred: RuleBook | None = None,
    waivers: Mapping[str, Waiver] | None = None,
    decisions: Collection[str] | None = None,
) -> Report:
    """Run every check against the enforced code's rules (`book`), and, when a preferred (latest)
    code is given, again against its rules: the design should meet both. A preferred-code failure
    counts unless a waiver names the decision that set it aside. Problems in the model, missing or
    unfilled rules, exceptions and checks that find nothing are all failures, never skipped."""
    waivers = waivers or {}
    outcomes: list[Outcome] = []
    used: dict[str, Rule] = {}
    used_preferred: dict[str, Rule] = {}
    problems = building.problems()
    for cdef in checks:
        outcomes.append(_run_one(building, book, cdef, used, preferred=False))
        if preferred is not None and cdef.rules and all(rule_id in preferred for rule_id in cdef.rules):
            outcome = _run_one(building, preferred, cdef, used_preferred, preferred=True)
            outcome.waiver = waivers.get(cdef.id)
            outcomes.append(outcome)
    ran = {o.check.id for o in outcomes if o.preferred}
    for w in waivers.values():
        if w.check not in ran:
            problems.append(f"waiver for {w.check}: no preferred-code check with that id ran")
        if decisions is not None and w.decision not in decisions:
            problems.append(f"waiver for {w.check}: decision {w.decision} is not in docs/decisions.md")
    for o in outcomes:
        if o.waiver and o.status == "waived":
            continue
        if o.waiver:
            problems.append(f"waiver for {o.check.id} is no longer needed (the check passes): remove it")
    unverified = sorted((r for r in used.values() if not r.verified), key=lambda r: r.id)
    unverified_pref = sorted((r for r in used_preferred.values() if not r.verified), key=lambda r: r.id)
    return Report(problems, outcomes, unverified, release, unverified_pref)


_MARK = {"pass": "✓", "fail": "✗", "error": "✗", "waived": "~"}


def _where(rule: Rule) -> str:
    """The rule's file, from the project root."""
    return rule.origin[3:] if rule.origin.startswith("../") else f"model/rules/{rule.origin}"


def format_report(report: Report, *, verbose: bool = False) -> str:
    """The report as text: failures always; every result with verbose."""
    lines: list[str] = []
    for p in report.problems:
        lines.append(f"✗ model: {p}")
    for o in report.outcomes:
        c = o.check
        latest = "  (latest code)" if o.preferred else ""
        lines.append(f"{_MARK[o.status]} {c.id}  {c.title}{latest}  [{'; '.join(o.cites)}]")
        if o.status == "waived" and o.waiver:
            lines.append(f"    waived: {o.waiver.decision}, {o.waiver.reason}")
        if o.error:
            lines.append(f"    error: {o.error}")
        for r in o.results:
            if verbose or not r.passed:
                mark = "ok  " if r.passed else "FAIL"
                note = f"  ({r.note})" if r.note else ""
                lines.append(f"    {mark} {r.element}: {r.measured}, limit {r.limit}{note}")
    if report.unverified:
        what = "✗ not allowed in a release" if report.release else "• warning"
        lines.append(f"{what}: {len(report.unverified)} rule value(s) not verified against the code yet:")
        lines += [f"    {r.id} ({r.cite}) in {_where(r)}" for r in report.unverified]
    if report.unverified_preferred:
        n = len(report.unverified_preferred)
        lines.append(f"• note: {n} latest-code rule value(s) not verified yet (they don't block a release)")
    passed = sum(o.status in ("pass", "waived") for o in report.outcomes)
    if not report.outcomes:
        lines.append("• no checks yet (add them in checks/, from the phase spec's check plan)")
    verdict = "✓ all checks passed" if report.ok else "✗ checks failed"
    lines.append(f"{verdict}: {passed}/{len(report.outcomes)} checks passed, {len(report.problems)} model problem(s)")
    return "\n".join(lines)
