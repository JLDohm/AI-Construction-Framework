"""python -m bldg build | check [--release] [-v] | rules [--todo] | release <permit|ifc> <rev>

Run from anywhere; paths are relative to the model folder (the folder holding bldg/).
"""

import argparse
import datetime
import hashlib
import importlib
import re
import subprocess
import sys
from pathlib import Path

from bldg import checks, draw, takeoff
from bldg.elements import Building
from bldg.rules import RuleBook, RuleError, load_rules

MODEL = Path(__file__).resolve().parent.parent
OUT = MODEL / "out"
RELEASES = MODEL / "releases"
JURISDICTION = MODEL.parent / "jurisdiction" / "jurisdiction.toml"
PACKS = MODEL.parent / "packs.conf"
DECISIONS = MODEL.parent / "docs" / "decisions.md"
WAIVERS = MODEL / "checks" / "waivers.toml"


def packs() -> dict[str, str]:
    """packs.conf: code (enforced), prefer (the latest code, a design target), jurisdiction, trades."""
    if not PACKS.is_file():
        return {}
    pairs = (line.split("=", 1) for line in PACKS.read_text(encoding="utf-8").splitlines() if "=" in line)
    return {k.strip(): v.strip() for k, v in pairs if not k.strip().startswith("#")}


def rule_books() -> tuple[RuleBook, RuleBook | None]:
    """The enforced code's rules (with the jurisdiction's values and local amendments), and the
    preferred code's rules (with the jurisdiction's values), if packs.conf names one."""
    conf = packs()
    code, prefer = conf.get("code"), conf.get("prefer")
    enforced = load_rules(MODEL / "rules", JURISDICTION, codes=[code] if code else None)
    if not prefer:
        return enforced, None
    return enforced, load_rules(MODEL / "rules", JURISDICTION, codes=[prefer], amendments=False)


KINDS = {"permit": "PERMIT SET", "ifc": "ISSUED FOR CONSTRUCTION"}


def load_building() -> Building:
    if str(MODEL) not in sys.path:
        sys.path.insert(0, str(MODEL))
    project = importlib.import_module("project")
    b = project.building()
    if not isinstance(b, Building):
        raise TypeError("project.building() must return a bldg.elements.Building")
    return b


def run_checks(b: Building, *, release: bool) -> checks.Report:
    enforced, preferred = rule_books()
    found = checks.discover(MODEL / "checks") if (MODEL / "checks").is_dir() else []
    text = DECISIONS.read_text(encoding="utf-8") if DECISIONS.is_file() else ""
    decisions = set(re.findall(r"^## (D-\d+)\b", text, flags=re.MULTILINE))
    return checks.run(
        b,
        enforced,
        found,
        release=release,
        preferred=preferred,
        waivers=checks.load_waivers(WAIVERS),
        decisions=decisions,
    )


def build(b: Building, out: Path, title_block: str) -> list[Path]:
    files = draw.write_sheets(b, out / "drawings", title_block)
    csv = out / "takeoff.csv"
    takeoff.write_csv(takeoff.takeoff(b), csv)
    return [*files, csv]


def git(*args: str) -> str:
    done = subprocess.run(["git", "-C", str(MODEL), *args], capture_output=True, text=True, check=True)
    return done.stdout.strip()


def cmd_build() -> int:
    b = load_building()
    stamp = f"WORKING COPY: not for permit or construction. {datetime.date.today().isoformat()}"
    files = build(b, OUT, stamp)
    sheets = sum(1 for f in files if f.suffix == ".pdf")
    print(f"✓ built {sheets} sheet(s) and the takeoff in {OUT.relative_to(MODEL.parent)}/")
    return 0


def cmd_check(*, release: bool, verbose: bool) -> int:
    report = run_checks(load_building(), release=release)
    print(checks.format_report(report, verbose=verbose))
    OUT.mkdir(exist_ok=True)
    (OUT / "check-report.txt").write_text(checks.format_report(report, verbose=True) + "\n", encoding="utf-8")
    return 0 if report.ok else 1


def cmd_rules(*, todo: bool) -> int:
    """List rule values, so the owner can verify them against the code, section by section."""
    enforced, preferred = rule_books()
    book = dict(enforced)
    if preferred is not None:  # the preferred code's own values (design values are shared)
        book |= {f"{r.id} (latest code)": r for r in preferred.values() if not r.origin.startswith("../")}
    shown = 0
    for rule in sorted(book.values(), key=lambda r: (r.origin, r.section, r.id)):
        state = "not filled in" if not rule.filled else ("verified" if rule.verified else "UNVERIFIED")
        if todo and state == "verified":
            continue
        if rule.table:
            value = f"table, {len(rule.table)} row(s)"
        else:
            value = f"{rule.value:g} {rule.units}" if rule.value is not None else "-"
        amended = " (local amendment)" if rule.amended else ""
        print(f"{state:13}  {rule.cite:24} {value:22} {rule.id}  [{rule.origin}]{amended}")
        shown += 1
    print(f"{shown} of {len(book)} rule(s) shown" + (" (not yet verified or filled in)" if todo else ""))
    return 0


def cmd_release(kind: str, rev: str) -> int:
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9.]*", rev):
        print(f"✗ revision {rev!r}: use capital letters and numbers, e.g. A, B, 1, 2.1", file=sys.stderr)
        return 1
    name = f"{kind}-{rev}"
    dest = RELEASES / name
    if dest.exists():
        print(
            f"✗ {dest.relative_to(MODEL.parent)} already exists. Releases are never changed: use a new revision.",
            file=sys.stderr,
        )
        return 1
    if git("status", "--porcelain"):
        print("✗ commit everything first: a release must match a commit exactly (see git status).", file=sys.stderr)
        return 1
    b = load_building()
    report = run_checks(b, release=True)
    if not report.ok:
        print(checks.format_report(report))
        print(f"✗ {name} not released: every check must pass and every rule used must be verified.", file=sys.stderr)
        return 1
    commit = git("rev-parse", "HEAD")
    today = datetime.date.today().isoformat()
    files = build(b, dest, f"{KINDS[kind]}, REV {rev}, {today}, commit {commit[:10]}")
    (dest / "check-report.txt").write_text(checks.format_report(report, verbose=True) + "\n", encoding="utf-8")
    files.append(dest / "check-report.txt")
    rules = sorted({c for o in report.outcomes if not o.preferred for c in o.cites if not c.startswith("R-")})
    latest = sorted({c for o in report.outcomes if o.preferred for c in o.cites if not c.startswith("R-")})
    waived = [f"{o.check.id} ({o.waiver.decision})" for o in report.outcomes if o.status == "waived" and o.waiver]
    lines = [
        f"release:  {name} ({KINDS[kind].lower()})",
        f"project:  {b.name}" + (f", {b.address}" if b.address else ""),
        f"date:     {today}",
        f"commit:   {commit}",
        f"checks:   {len(report.outcomes)} passed",
        "cites:    " + ("; ".join(rules) or "none"),
        "latest:   " + ("; ".join(latest) or "no preferred code"),
        "waived:   " + (", ".join(waived) or "none"),
        "",
        "sha256                                                            file",
    ]
    for f in sorted(files):
        lines.append(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.relative_to(dest)}")
    (dest / "MANIFEST.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"✓ released {name} to {dest.relative_to(MODEL.parent)}/ ({len(files)} files + MANIFEST.txt)")
    print(
        f"  Next: commit it (docs(phase-N): release {name}); after the owner merges, they tag it: git tag {name} main"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m bldg", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build", help="draw every sheet and write the takeoff to out/")
    p_check = sub.add_parser("check", help="run the compliance checks")
    p_check.add_argument("--release", action="store_true", help="also fail on unverified rule values")
    p_check.add_argument("-v", "--verbose", action="store_true", help="show every result, not only failures")
    p_rules = sub.add_parser("rules", help="list rule values with their sections and verified state")
    p_rules.add_argument("--todo", action="store_true", help="only rules not yet verified or filled in")
    p_rel = sub.add_parser("release", help="check, build and freeze a drawing set in releases/")
    p_rel.add_argument("kind", choices=sorted(KINDS))
    p_rel.add_argument("rev")
    args = parser.parse_args(argv)
    try:
        if args.cmd == "build":
            return cmd_build()
        if args.cmd == "check":
            return cmd_check(release=args.release, verbose=args.verbose)
        if args.cmd == "rules":
            return cmd_rules(todo=args.todo)
        return cmd_release(args.kind, args.rev)
    except RuleError as e:
        print(f"✗ rules: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
