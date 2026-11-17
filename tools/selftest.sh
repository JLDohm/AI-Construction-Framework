#!/usr/bin/env bash
# Test the framework: set up a scratch project with new-project.sh and run its checks.
#   tools/selftest.sh [scratch-dir]     (default: a new temporary folder, removed afterwards)
# Also checks that every shell script in the framework passes shfmt and ShellCheck.
set -euo pipefail

here=$(cd "$(dirname "$0")/.." && pwd)
fail=0
step() { echo "== $*"; }
bad() {
  echo "✗ $*" >&2
  fail=1
}

step "shfmt and ShellCheck"
mapfile -t scripts < <(
  cd "$here"
  {
    git ls-files --cached --others --exclude-standard -- '*.sh'
    find template -path '*/.githooks/*' -type f ! -name '*.md'
  } | sort -u
)
for s in "${scripts[@]}"; do
  (cd "$here" && shfmt -i 2 -d "$s" >/dev/null) || bad "shfmt: $s (fix with shfmt -i 2 -w $s)"
  # Hooks source .githooks/lib.sh relative to the project root, so check them from the folder
  # that becomes the project root. The .d fragments are sourced, so they have no shebang.
  case "$s" in
  template/*) root=template ;;
  codes/* | jurisdictions/* | trades/*) root=$(cut -d/ -f1-2 <<<"$s") ;;
  *) root=. ;;
  esac
  (cd "$here/$root" && shellcheck -s bash -x "${s#"$root"/}") || bad "shellcheck: $s"
done

step "code packs ship every rule unverified (only the owner verifies, in their project)"
if found=$(grep -rln '^verified = true' "$here"/codes/*/model/rules "$here"/jurisdictions); then bad "verified rules in a pack: $found"; fi

if [[ $# -ge 1 ]]; then
  proj=$1
else
  tmp=$(mktemp -d)
  trap 'rm -rf "$tmp"' EXIT
  proj=$tmp/selftest-project
fi

step "new-project.sh into $proj"
"$here/new-project.sh" "$proj" --name "Selftest Shed" --trades framing,foundation >/dev/null
for f in packs.conf .githooks/pre-commit .githooks/checks.d/model.sh .gitignore; do
  [[ -e "$proj/$f" ]] || bad "missing $f"
done
grep -qx 'trades=framing,foundation' "$proj/packs.conf" || bad "packs.conf trades wrong: $(cat "$proj/packs.conf")"
find "$proj" -name PACK.md | grep -q . && bad "PACK.md was copied into the project"

step "model tools (a shared environment, rebuilt when requirements.lock changes)"
lock=$here/template/model/requirements.lock
venv=${CONST_SELFTEST_VENV:-${XDG_CACHE_HOME:-$HOME/.cache}/const-framework/model-venv-$(sha256sum "$lock" | cut -c1-12)}
if [[ ! -x "$venv/bin/python" ]]; then
  echo "• creating $venv (one time)"
  python3 -m venv "$venv"
  "$venv/bin/pip" install -q -r "$lock"
fi
ln -s "$venv" "$proj/model/.venv"

step "adding a trade later keeps the earlier ones"
"$here/new-project.sh" "$proj" --trades electrical,plumbing >/dev/null
grep -qx 'trades=framing,foundation,electrical,plumbing' "$proj/packs.conf" || bad "trades after re-run: $(cat "$proj/packs.conf")"

step "changing the jurisdiction is refused"
if "$here/new-project.sh" "$proj" --jurisdiction OTHER >/dev/null 2>&1; then bad "jurisdiction change was allowed"; fi

step "packs from another folder: a jurisdiction sets its code pack and the latest code"
# A made-up pack folder, like a private one: a state code (a renamed copy of irc-2021) and a town.
packs=$(dirname "$proj")/selftest-packs
mkdir -p "$packs/codes" "$packs/jurisdictions/test-town"
cp -r "$here/codes/irc-2021" "$packs/codes/old-code"
mv "$packs/codes/old-code/model/rules/irc-2021" "$packs/codes/old-code/model/rules/old-code"
mv "$packs/codes/old-code/.claude/skills/irc-2021-practice" "$packs/codes/old-code/.claude/skills/old-code-practice"
sed -i 's/^name: irc-2021-practice$/name: old-code-practice/' "$packs/codes/old-code/.claude/skills/old-code-practice/SKILL.md"
sed -i -e 's/^code = "IRC 2021"$/code = "OLD 2015"/' -e 's/^source = "IRC 2021 /source = "OLD 2015 /' "$packs"/codes/old-code/model/rules/old-code/*.toml
cp -r "$here/jurisdictions/TEMPLATE/." "$packs/jurisdictions/test-town/"
echo old-code >"$packs/jurisdictions/test-town/CODE"
echo irc-2021 >"$packs/jurisdictions/test-town/PREFER"
town=$(dirname "$proj")/selftest-town
"$here/new-project.sh" "$town" --packs "$packs" --jurisdiction test-town >/dev/null
grep -qx 'code=old-code' "$town/packs.conf" || bad "test-town didn't select old-code: $(cat "$town/packs.conf")"
grep -qx 'prefer=irc-2021' "$town/packs.conf" || bad "test-town didn't prefer irc-2021: $(cat "$town/packs.conf")"
grep -qx "packs=$packs" "$town/packs.conf" || bad "packs.conf didn't record the pack folder: $(cat "$town/packs.conf")"
[[ ! -e "$town/docs/owner.md" ]] || bad "an owner profile appeared without one in the pack folder"
mkdir -p "$packs/owner/docs"
echo "# Owner: 1 Example Rd, Test Town" >"$packs/owner/docs/owner.md"
owned=$(dirname "$proj")/selftest-owned
"$here/new-project.sh" "$owned" --packs "$packs" --jurisdiction test-town >/dev/null
grep -q "1 Example Rd" "$owned/docs/owner.md" 2>/dev/null || bad "the owner profile wasn't copied from the pack folder"
[[ ! -e "$proj/docs/owner.md" ]] || bad "a project without pack folders got an owner profile"
[[ -d "$town/model/rules/old-code" && -d "$town/model/rules/irc-2021" && ! -e "$town/CODE" && ! -e "$town/PREFER" ]] ||
  bad "the test-town project has the wrong files"
"$here/new-project.sh" "$town" --trades framing >/dev/null || bad "adding a trade without --packs failed (packs.conf should supply the folder)"
if "$here/new-project.sh" "$(dirname "$proj")/selftest-mismatch" --packs "$packs" --jurisdiction test-town --code irc-2021 >/dev/null 2>&1; then
  bad "test-town with irc-2021 as the code in force was allowed"
fi
if "$here/new-project.sh" "$(dirname "$proj")/selftest-nopacks" --jurisdiction test-town >/dev/null 2>&1; then
  bad "test-town was found without its pack folder"
fi
ln -s "$venv" "$town/model/.venv"
out=$(cd "$town/model" && .venv/bin/python -m bldg rules --todo 2>&1) || bad "bldg rules failed in the test-town project: $out"
[[ "$out" == *"not filled in"*"frost-depth"* && "$out" == *"OLD 2015 R311.7.5.1"* ]] || bad "test-town rules listing unexpected: $out"
(cd "$town/model" && .venv/bin/pytest -q -p no:warnings >/dev/null 2>&1) || bad "the model tests fail in the test-town project"
cat >"$town/model/checks/phase_1.py" <<'PY'
"""Selftest fixture."""

from collections.abc import Iterator

from bldg.checks import Result, Rules, check
from bldg.elements import Building
from bldg_checks import irc


@check("T-1.1", rules=irc.CEILINGS)
def ceilings(b: Building, r: Rules) -> Iterator[Result]:
    """Ceiling heights"""
    yield from irc.ceilings(b, r)
PY
out=$(cd "$town/model" && .venv/bin/python -m bldg check 2>&1)
[[ "$out" == *"T-1.1  Ceiling heights  [OLD 2015 R305.1]"* && "$out" == *"T-1.1  Ceiling heights  (latest code)  [IRC 2021 R305.1]"* ]] ||
  bad "the test-town checks didn't run against both codes: $out"
rm "$town/model/checks/phase_1.py"

step "every placeholder was filled in"
if left=$(grep -rl '{{' "$proj" "$town" --exclude-dir=.git); then bad "unfilled {{…}} in: $left"; fi
grep -qF "$here/new-project.sh . --trades" "$proj/CLAUDE.md" || bad "the project CLAUDE.md doesn't name this framework's folder"

step "agents and skills"
for f in "$proj"/.claude/agents/*.md "$proj"/.claude/skills/*/SKILL.md; do
  [[ -e "$f" ]] || continue
  want=$(basename "$f" .md)
  [[ "$want" == SKILL ]] && want=$(basename "$(dirname "$f")")
  [[ "$(head -n 1 "$f")" == "---" ]] || bad "no frontmatter: ${f#"$proj"/}"
  grep -qx "name: $want" "$f" || bad "frontmatter name isn't $want: ${f#"$proj"/}"
  grep -q '^description: .\{40,\}' "$f" || bad "missing or short description: ${f#"$proj"/}"
done
for a in "$proj"/.claude/agents/*.md; do
  n=$(basename "$a" .md)
  grep -q "\*\*$n\*\* agent" "$proj/CLAUDE.md" || bad "CLAUDE.md's roles table doesn't list the $n agent"
done
[[ -f "$proj/.claude/skills/phase/SKILL.md" ]] || bad "the phase skill is missing"

step "phase dependencies"
# try_phase N EXPECT [REASON]  - commit on a phase-N branch; EXPECT is "allowed" or "blocked",
# and a blocked commit's message must contain REASON.
try_phase() {
  local rc=0 out
  out=$(
    cd "$proj"
    git switch -q -c "phase-$1-selftest"
    git commit -q --allow-empty -m "selftest phase $1" 2>&1 >/dev/null
  ) || rc=$?
  (
    cd "$proj"
    git switch -q main
    git branch -q -D "phase-$1-selftest"
  )
  case "$2:$rc" in
  allowed:0) ;;
  blocked:[1-9]*) [[ "$out" == *"$3"* ]] || bad "phase $1 was blocked, but not for: $3 (got: $out)" ;;
  *) bad "phase $1 should be $2 (got: $out)" ;;
  esac
}
try_phase 1 blocked "phase 0 (brief planned)"
plan=$proj/docs/build-plan.md
cp "$plan" "$proj/plan.orig"
# A plan where design, permits and work overlap. The example table below it must be ignored.
awk '/^\| 0 \|/ { print "| 0 | brief | brief | g | owner | — | — | done |"
                  print "| 1 | structure | design | g | owner | 0 | R-1 | ready to merge |"
                  print "| 2 | permit | permit | g | owner | 1 | — | ready to merge |"
                  print "| 3 | electrical | design | g | owner | 1 | R-2 | planned |"
                  print "| 4 | foundation | build | g | sub | 2 | R-1 | planned |"
                  print "| 5 | framing | build | g | sub | 4, 3 | R-1 | planned |"
                  print "| 6 | footings | build | g | owner | 1 | R-1 | waiting |"
                  print "| 7 | deck | build | g | owner | 6 | R-1 | planned |"
                  print "| 8 | typo | build | g | owner | 9 | R-1 | planned |"
                  next }
     /^\| 1 \| … \|/ { next }
     { print }' "$proj/plan.orig" >"$plan"
try_phase 3 allowed                                   # its design dependency is ready to merge
try_phase 4 blocked "phase 2 (permit ready to merge)" # released, not issued
try_phase 5 blocked "phase 4 (build planned)"
try_phase 7 blocked "phase 6 (build waiting)" # waiting on an inspection
try_phase 8 blocked "phase 9 (not in the build plan)"
try_phase 9 blocked "phase 9 is not in docs/build-plan.md"
sed -i 's/^| 2 | permit | permit | g | owner | 1 | — | ready to merge |/| 2 | permit | permit | g | owner | 1 | — | done |/' "$plan"
try_phase 4 allowed # the permit is issued
mv "$proj/plan.orig" "$plan"

step "project checks"
(
  cd "$proj"
  git switch -q -c phase-0-brief
  .githooks/pre-commit
) || bad "pre-commit failed in the scratch project"
(
  cd "$proj"
  git switch -q main
  if git commit -q --allow-empty -m "should be blocked" 2>/dev/null; then exit 1; fi
) || bad "a commit on main was not blocked"

step "model: the irc-2021 pack catches seeded defects; releases need verified rules and no provisional assumptions"
m=$proj/model
cat >"$m/checks/phase_1.py" <<'PY'
"""Selftest fixture: checks from the irc-2021 pack."""

from collections.abc import Iterator

from bldg.checks import Result, Rules, check
from bldg.elements import Building
from bldg_checks import irc


@check("T-1.1", rules=irc.RISERS)
def risers(b: Building, r: Rules) -> Iterator[Result]:
    """Stair risers"""
    yield from irc.risers(b, r)


@check("T-1.2", rules=irc.EGRESS)
def egress(b: Building, r: Rules) -> Iterator[Result]:
    """Emergency escape openings"""
    yield from irc.egress(b, r)


@check("T-1.3", rules=irc.CEILINGS)
def ceilings(b: Building, r: Rules) -> Iterator[Result]:
    """Ceiling heights"""
    yield from irc.ceilings(b, r)
PY
cat >"$m/project.py" <<'PY'
"""Selftest fixture: a bedroom over a crawlspace, reached by one stair."""

from bldg.elements import Building, Level, Opening, OpeningKind, Room, RoomUse, Stair, Wall
from bldg.geometry import Pt, rect
from bldg.units import ft

RISER = 7.5  # in
RISERS = 4
CEILING = ft(8)
WINDOW_CLEAR_WIDTH = 36  # in, from the window's data sheet
WINDOW_CLEAR_HEIGHT = 24  # in


def building() -> Building:
    b = Building(name="Selftest Shed")
    b.levels = [Level(id="grade", elevation=0), Level(id="floor", elevation=RISER * RISERS)]
    b.rooms = [
        Room(id="R1", name="Bedroom", level="floor", outline=rect(0, 0, ft(10), ft(11)), use=RoomUse.SLEEPING,
             ceiling_height=CEILING)
    ]  # fmt: skip
    b.walls = [Wall(id="W1", level="floor", start=Pt(0, 0), end=Pt(ft(10), 0), thickness=4.5, height=CEILING)]
    b.openings = [
        Opening(id="N1", wall="W1", kind=OpeningKind.WINDOW, offset=36, rough_width=40, rough_height=50,
                sill_height=24, clear_width=WINDOW_CLEAR_WIDTH, clear_height=WINDOW_CLEAR_HEIGHT, egress=True,
                serves=("R1",))
    ]  # fmt: skip
    b.stairs = [
        Stair(id="S1", level_from="grade", level_to="floor", start=Pt(0, -40), end=Pt(0, 0), width=36,
              risers=(RISER,) * RISERS, treads=(10.0,) * (RISERS - 1), headroom=80, handrail_height=36)
    ]  # fmt: skip
    return b
PY
# commit_model MESSAGE  - commit everything on the selftest-model branch; prints the hook's output.
commit_model() { (cd "$proj" && git add -A && git commit -q -m "$1" 2>&1); }
# seed NAME SED-EXPR EXPECTED...  - apply a one-line defect to project.py; the commit must fail and
# its output must contain each EXPECTED string. Then undo it.
seed() {
  local name=$1 expr=$2 out want
  shift 2
  cp "$m/project.py" "$m/project.py.good"
  sed -i "$expr" "$m/project.py"
  cmp -s "$m/project.py" "$m/project.py.good" && bad "seeding $name changed nothing"
  if out=$(commit_model "seeded: $name"); then
    bad "$name was committed"
  else
    for want in "$@"; do [[ "$out" == *"$want"* ]] || bad "$name: the failure didn't say: $want"; done
  fi
  mv "$m/project.py.good" "$m/project.py"
  (cd "$proj" && git add -A) # the refused commit left the defect staged
}
(cd "$proj" && git switch -q -c selftest-model)
out=$(commit_model "a compliant bedroom and stair") || bad "the compliant model didn't commit: $out"
seed "an 8 in riser" 's/^RISER = 7.5 /RISER = 8.0 /' \
  "T-1.1  Stair risers  [IRC 2021 R311.7.5.1" 'FAIL stair S1 riser 1: 8", limit <= 7 3/4"'
seed "a 5.0 sq ft egress window" 's/^WINDOW_CLEAR_WIDTH = 36 /WINDOW_CLEAR_WIDTH = 30 /' \
  "IRC 2021 R310.2.1" "FAIL opening N1 clear area: 5.00 sq ft, limit >= 5.7 sq ft"
seed "a 6 ft 10 in ceiling" 's/^CEILING = ft(8)$/CEILING = ft(6, 10)/' \
  "T-1.3  Ceiling heights  [IRC 2021 R305.1]" "FAIL room R1 ceiling: 6'-10\", limit >= 7'-0\""
if out=$(cd "$proj" && tools/release.sh permit A 2>&1); then
  bad "a release with unverified rules was allowed"
else
  [[ "$out" == *"not allowed in a release"*"riser-max (IRC 2021 R311.7.5.1)"* ]] || bad "unverified-rule refusal unclear: $out"
fi
sed -i 's/^verified = false/verified = true/' "$m"/rules/irc-2021/*.toml
out=$(commit_model "rules verified by the owner") || bad "verified rules didn't commit: $out"
cp "$m/project.py" "$m/project.py.good"
sed -i -e 's/OpeningKind, Room, /OpeningKind, Provisional, Room, /' \
  -e 's/^    return b$/    b.provisional = [Provisional("P-1", "floor 30 in above grade", "E-1 measurement")]\n    return b/' \
  "$m/project.py"
out=$(commit_model "a provisional assumption") || bad "a provisional model didn't commit (it should only warn): $out"
[[ "$out" == *"PROVISIONAL"*"P-1: floor 30 in above grade (until E-1 measurement)"* ]] ||
  bad "the provisional warning is missing from the commit output: $out"
if out=$(cd "$proj" && tools/release.sh permit A 2>&1); then
  bad "a release with a provisional assumption was allowed"
else
  [[ "$out" == *"not allowed in a release"*"P-1"* ]] || bad "provisional refusal unclear: $out"
fi
mv "$m/project.py.good" "$m/project.py"
out=$(commit_model "P-1 replaced by the measurement") || bad "removing P-1 didn't commit: $out"
if out=$(cd "$proj" && tools/release.sh permit A 2>&1); then
  for f in MANIFEST.txt check-report.txt takeoff.csv drawings/A-1.pdf drawings/A-1.dxf; do
    [[ -s "$m/releases/permit-A/$f" ]] || bad "release permit-A has no $f"
  done
  grep -q "^commit:   $(cd "$proj" && git rev-parse HEAD)$" "$m/releases/permit-A/MANIFEST.txt" ||
    bad "MANIFEST.txt doesn't record the commit"
else
  bad "release permit-A failed: $out"
fi
out=$(commit_model "release permit-A") || bad "the release didn't commit: $out"
if (cd "$proj" && tools/release.sh permit A >/dev/null 2>&1); then bad "permit-A was released twice"; fi

echo
if [[ $fail -ne 0 ]]; then
  echo "✗ selftest failed" >&2
  exit 1
fi
echo "✓ selftest passed"
