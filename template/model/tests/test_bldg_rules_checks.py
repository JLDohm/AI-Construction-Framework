"""Tests of the bldg library: rule files and the check runner."""

import textwrap
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest

from bldg import checks
from bldg.checks import Result, Rules, check
from bldg.elements import Building, Level, Provisional, Stair
from bldg.geometry import Pt
from bldg.rules import RuleBook, RuleError, load_rules

RISER = """
[[rule]]
id = "riser-max"
code = "IRC 2021"
section = "R311.7.5.1"
title = "Stair riser height, maximum"
value = {value}
units = "in"
source = "test"
verified = {verified}
"""


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text), encoding="utf-8")


def book(tmp_path: Path, value: float = 7.75, verified: str = "true") -> RuleBook:
    write(tmp_path / "rules" / "irc" / "stairs.toml", RISER.format(value=value, verified=verified))
    return load_rules(tmp_path / "rules")


def stair(*risers: float) -> Building:
    b = Building(name="t", levels=[Level(id="L1", elevation=0), Level(id="L2", elevation=sum(risers))])
    b.stairs = [
        Stair(
            id="S1", level_from="L1", level_to="L2", start=Pt(0, 0), end=Pt(100, 0), width=36,
            risers=risers, treads=(10.0,) * (len(risers) - 1), headroom=80,
        )
    ]  # fmt: skip
    return b


@check("T-1.1", rules=["riser-max"])
def risers_ok(b: Building, r: Rules) -> Iterator[Result]:
    """Riser height"""
    limit = r.value("riser-max")
    for s in b.stairs:
        for i, h in enumerate(s.risers, 1):
            yield Result(f"{s.id} riser {i}", h <= limit, str(h), f"<= {limit}")


def cdef(fn: object) -> checks.CheckDef:
    found = getattr(fn, "__bldg_check__", None)
    assert isinstance(found, checks.CheckDef)
    return found


# Rules


def test_rule_loads_with_citation(tmp_path: Path) -> None:
    rule = book(tmp_path)["riser-max"]
    assert rule.num() == 7.75
    assert rule.cite == "IRC 2021 R311.7.5.1"
    assert rule.origin == "irc/stairs.toml"


def test_zero_value_is_not_filled_in(tmp_path: Path) -> None:
    rule = book(tmp_path, value=0)["riser-max"]
    assert not rule.filled
    with pytest.raises(RuleError, match="not filled in"):
        rule.num()


def test_missing_field_and_duplicate_id_are_errors(tmp_path: Path) -> None:
    write(tmp_path / "rules" / "a.toml", '[[rule]]\nid = "x"\nvalue = 1\n')
    with pytest.raises(RuleError, match="missing code"):
        load_rules(tmp_path / "rules")
    (tmp_path / "rules" / "a.toml").unlink()
    book(tmp_path)
    write(tmp_path / "rules" / "zz.toml", RISER.format(value=8, verified="true"))
    with pytest.raises(RuleError, match="duplicate rule id"):
        load_rules(tmp_path / "rules")


def test_local_amendment_replaces_rule(tmp_path: Path) -> None:
    book(tmp_path)
    write(tmp_path / "rules" / "local" / "amend.toml", RISER.format(value=7.5, verified="true") + "amends = true\n")
    rule = load_rules(tmp_path / "rules")["riser-max"]
    assert rule.num() == 7.5
    assert rule.amended


def test_only_local_rules_may_amend(tmp_path: Path) -> None:
    book(tmp_path)
    write(tmp_path / "rules" / "other.toml", RISER.format(value=7.5, verified="true") + "amends = true\n")
    with pytest.raises(RuleError, match="only rules/local/ may amend"):
        load_rules(tmp_path / "rules")


# Checks


def test_at_the_limit_passes_and_one_past_fails(tmp_path: Path) -> None:
    rules = book(tmp_path)
    assert checks.run(stair(7.75, 7.75), rules, [cdef(risers_ok)]).ok
    report = checks.run(stair(7.75, 7.8), rules, [cdef(risers_ok)])
    assert not report.ok
    failed = [r.element for r in report.outcomes[0].results if not r.passed]
    assert failed == ["S1 riser 2"]
    assert report.outcomes[0].cites == ["IRC 2021 R311.7.5.1"]


def test_check_that_finds_nothing_fails(tmp_path: Path) -> None:
    report = checks.run(Building(name="empty"), book(tmp_path), [cdef(risers_ok)])
    assert report.outcomes[0].status == "error"
    assert "found nothing to check" in report.outcomes[0].error


def test_unfilled_rule_is_an_error_not_a_pass(tmp_path: Path) -> None:
    report = checks.run(stair(7.0, 7.0), book(tmp_path, value=0), [cdef(risers_ok)])
    assert report.outcomes[0].status == "error"
    assert "not filled in" in report.outcomes[0].error


def test_missing_rule_is_an_error(tmp_path: Path) -> None:
    report = checks.run(stair(7.0, 7.0), load_rules(tmp_path / "none"), [cdef(risers_ok)])
    assert "no rule 'riser-max'" in report.outcomes[0].error


def test_undeclared_rule_cannot_be_read(tmp_path: Path) -> None:
    @check("T-1.2", requirements=["R-1"])
    def sneaky(b: Building, r: Rules) -> Iterator[Result]:
        """Uses a rule it didn't declare"""
        yield Result("x", r.value("riser-max") > 0, "", "")

    report = checks.run(stair(7.0, 7.0), book(tmp_path), [cdef(sneaky)])
    assert "not declared" in report.outcomes[0].error


def test_unverified_rules_warn_but_block_a_release(tmp_path: Path) -> None:
    rules = book(tmp_path, verified="false")
    working = checks.run(stair(7.0, 7.0), rules, [cdef(risers_ok)])
    assert working.ok
    assert [r.id for r in working.unverified] == ["riser-max"]
    assert not checks.run(stair(7.0, 7.0), rules, [cdef(risers_ok)], release=True).ok


def test_provisional_assumptions_warn_but_block_a_release(tmp_path: Path) -> None:
    b = stair(7.0, 7.0)
    b.provisional.append(Provisional("P-1", "rim joist 2x10, sound", "E-4 inspection opening"))
    working = checks.run(b, book(tmp_path), [cdef(risers_ok)])
    assert working.ok
    text = checks.format_report(working)
    assert "PROVISIONAL" in text and "P-1: rim joist 2x10, sound (until E-4" in text
    assert text.endswith("model problem(s)") and "passed (provisional)" in text
    release = checks.run(b, book(tmp_path), [cdef(risers_ok)], release=True)
    assert not release.ok
    assert "not allowed in a release" in checks.format_report(release)


def test_provisional_ids_are_checked(tmp_path: Path) -> None:
    b = stair(7.0, 7.0)
    b.provisional += [Provisional("A1", "x", "y"), Provisional("P-2", "x", "y"), Provisional("P-2", "", "y")]
    problems = "\n".join(b.problems())
    assert "id must look like P-1" in problems
    assert "P-2: duplicate id" in problems
    assert "say what is assumed" in problems


def test_model_problems_fail_the_report(tmp_path: Path) -> None:
    b = stair(7.0, 7.0)
    b.levels.append(Level(id="L1", elevation=0))
    assert not checks.run(b, book(tmp_path), []).ok


def test_check_must_cite_and_be_named_by_plan_id() -> None:
    with pytest.raises(ValueError, match="must cite"):
        check("T-1.1")
    with pytest.raises(ValueError, match="must look like"):
        check("riser", rules=["x"])
    with pytest.raises(ValueError, match="look like R-3"):
        check("T-1.1", requirements=["3"])


def test_discover_collects_checks_and_refuses_duplicates(tmp_path: Path) -> None:
    pkg = tmp_path / f"chk_{uuid.uuid4().hex}"
    body = """
        from bldg.checks import Result, check

        @check("{id}", requirements=["R-1"])
        def c(b, r):
            yield Result("x", True, "", "")
    """
    write(pkg / "__init__.py", "")
    write(pkg / "phase_2.py", body.format(id="T-2.10"))
    write(pkg / "phase_1.py", body.format(id="T-2.9"))
    assert [c.id for c in checks.discover(pkg)] == ["T-2.9", "T-2.10"]

    dup = tmp_path / f"chk_{uuid.uuid4().hex}"
    write(dup / "__init__.py", "")
    write(dup / "a.py", body.format(id="T-1.1"))
    write(dup / "b.py", body.format(id="T-1.1"))
    with pytest.raises(ValueError, match="defined twice"):
        checks.discover(dup)


def test_format_report_shows_failures_and_unverified(tmp_path: Path) -> None:
    report = checks.run(stair(7.75, 8.0), book(tmp_path, verified="false"), [cdef(risers_ok)])
    text = checks.format_report(report)
    assert "✗ T-1.1  Riser height  [IRC 2021 R311.7.5.1]" in text
    assert "FAIL S1 riser 2: 8.0, limit <= 7.75" in text
    assert "riser-max (IRC 2021 R311.7.5.1) in model/rules/irc/stairs.toml" in text


# Tables

SPANS = """
[[rule]]
id = "spans"
code = "IRC 2021"
section = "Table R507.6"
title = "Deck joist spans"
units = "in"
source = "test"
verified = true
table = [
  { species_grade = "SP #2", size = "2x8", spacing = 16, span = 142 },
  { species_grade = "SP #2", size = "2x10", spacing = 16, span = 0 },
  { species_grade = "SP #2", size = "2x12", spacing = 16, span = 200 },
  { species_grade = "SP #2", size = "2x12", spacing = 16, span = 201 },
]
"""


def test_table_lookup(tmp_path: Path) -> None:
    write(tmp_path / "rules" / "spans.toml", SPANS)
    rule = load_rules(tmp_path / "rules")["spans"]
    assert rule.lookup("span", species_grade="SP #2", size="2x8", spacing=16.0) == 142
    with pytest.raises(RuleError, match="no row for species_grade='SP #2', size='2x6'"):
        rule.lookup("span", species_grade="SP #2", size="2x6", spacing=16)
    with pytest.raises(RuleError, match="span for .* is not filled in"):
        rule.lookup("span", species_grade="SP #2", size="2x10", spacing=16)
    with pytest.raises(RuleError, match="2 rows"):
        rule.lookup("span", species_grade="SP #2", size="2x12", spacing=16)


def test_empty_table_loads_as_not_filled_in(tmp_path: Path) -> None:
    write(tmp_path / "rules" / "spans.toml", SPANS.split("table = [")[0] + "table = []\n")
    rule = load_rules(tmp_path / "rules")["spans"]
    assert not rule.filled


def test_jurisdiction_values_load_between_code_and_local(tmp_path: Path) -> None:
    book(tmp_path)
    jur = tmp_path / "jurisdiction" / "jurisdiction.toml"
    frost = RISER.format(value=42, verified="false").replace('"riser-max"', '"frost-depth"')
    write(jur, '[codes]\nresidential = "test"\n' + frost)
    rules = load_rules(tmp_path / "rules", jur)
    assert rules["frost-depth"].num() == 42
    assert rules["frost-depth"].origin == "../jurisdiction/jurisdiction.toml"
    write(tmp_path / "rules" / "local" / "a.toml", frost.replace("42", "48") + "amends = true\n")
    assert load_rules(tmp_path / "rules", jur)["frost-depth"].num() == 48


# The latest code as a design target (packs.conf: prefer)


def latest(tmp_path: Path, value: float) -> RuleBook:
    write(tmp_path / "latest" / "irc" / "stairs.toml", RISER.format(value=value, verified="true"))
    return load_rules(tmp_path / "latest")


def test_design_must_meet_both_codes(tmp_path: Path) -> None:
    enforced, newer = book(tmp_path), latest(tmp_path, 7.5)
    report = checks.run(stair(7.5, 7.5), enforced, [cdef(risers_ok)], preferred=newer)
    assert report.ok
    assert [(o.check.id, o.preferred) for o in report.outcomes] == [("T-1.1", False), ("T-1.1", True)]
    report = checks.run(stair(7.75, 7.75), enforced, [cdef(risers_ok)], preferred=newer)
    assert not report.ok  # meets the enforced code, not the latest
    assert [o.status for o in report.outcomes] == ["pass", "fail"]
    assert "(latest code)" in checks.format_report(report)


def test_a_waiver_names_its_decision(tmp_path: Path) -> None:
    enforced, newer = book(tmp_path), latest(tmp_path, 7.5)
    waiver = checks.Waiver("T-1.1", "D-3", "the enforced code wins")
    report = checks.run(
        stair(7.75, 7.75), enforced, [cdef(risers_ok)], preferred=newer, waivers={"T-1.1": waiver}, decisions={"D-3"}
    )
    assert report.ok
    assert report.outcomes[1].status == "waived"
    assert "waived: D-3, the enforced code wins" in checks.format_report(report)
    unknown = checks.run(
        stair(7.75, 7.75), enforced, [cdef(risers_ok)], preferred=newer, waivers={"T-1.1": waiver}, decisions={"D-1"}
    )
    assert "decision D-3 is not in docs/decisions.md" in "\n".join(unknown.problems)


def test_a_waiver_never_excuses_the_enforced_code(tmp_path: Path) -> None:
    enforced, newer = book(tmp_path), latest(tmp_path, 8.0)
    waiver = checks.Waiver("T-1.1", "D-3", "x")
    report = checks.run(stair(7.9, 7.9), enforced, [cdef(risers_ok)], preferred=newer, waivers={"T-1.1": waiver})
    assert [o.status for o in report.outcomes] == ["fail", "pass"]
    assert not report.ok
    assert "no longer needed" in "\n".join(report.problems)  # the latest-code check passes


def test_checks_the_latest_code_lacks_run_once(tmp_path: Path) -> None:
    write(tmp_path / "empty" / "x.toml", "")
    report = checks.run(stair(7.0, 7.0), book(tmp_path), [cdef(risers_ok)], preferred=load_rules(tmp_path / "empty"))
    assert [o.preferred for o in report.outcomes] == [False]


def test_load_waivers(tmp_path: Path) -> None:
    write(tmp_path / "w.toml", '[[waiver]]\ncheck = "T-1.1"\ndecision = "D-3"\nreason = "conflict"\n')
    assert checks.load_waivers(tmp_path / "w.toml")["T-1.1"].decision == "D-3"
    write(tmp_path / "bad.toml", '[[waiver]]\ncheck = "T-1.1"\n')
    with pytest.raises(ValueError, match="needs decision, reason"):
        checks.load_waivers(tmp_path / "bad.toml")


def test_rulebook_membership_does_not_raise(tmp_path: Path) -> None:
    rules = book(tmp_path)
    assert "riser-max" in rules
    assert "nope" not in rules


def test_codes_select_folders_and_amendments_can_be_left_out(tmp_path: Path) -> None:
    book(tmp_path)
    write(tmp_path / "rules" / "other" / "x.toml", RISER.format(value=9, verified="true"))
    assert load_rules(tmp_path / "rules", codes=["irc"])["riser-max"].num() == 7.75
    assert load_rules(tmp_path / "rules", codes=["other"])["riser-max"].num() == 9
    write(tmp_path / "rules" / "local" / "a.toml", RISER.format(value=7.5, verified="true") + "amends = true\n")
    assert load_rules(tmp_path / "rules", codes=["irc"])["riser-max"].num() == 7.5
    assert load_rules(tmp_path / "rules", codes=["irc"], amendments=False)["riser-max"].num() == 7.75
