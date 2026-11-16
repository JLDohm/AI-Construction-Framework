#!/usr/bin/env bash
# Set up a construction project to use const-framework, or add trades to one that already does.
#   ./new-project.sh <project-dir> [--name "Project Name"] [--code CODE] [--prefer CODE]
#                    [--jurisdiction NAME] [--trades TRADE[,TRADE...]] [--packs DIR]
# --code is the code in force; --prefer is the latest code, a design target the project also meets
# where that doesn't break the code in force. A jurisdiction pack sets both (its CODE and PREFER files).
# Works on a new folder or on an existing one. Existing files are never overwritten.
# The chosen packs are recorded in the project's packs.conf; later runs read it, so
# adding a trade is just: new-project.sh . --trades plumbing
# Packs can also come from other folders laid out like this one (codes/, jurisdictions/, trades/),
# e.g. a private folder for your own jurisdiction: --packs DIR (repeatable) or CONST_PACKS=DIR1:DIR2.
# The folders are recorded in packs.conf, so later runs find the same packs.
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)

# Pack folders, searched in order: --packs, CONST_PACKS, packs.conf (later), then this framework.
roots=()
add_root() {
  local d
  [[ -n "$1" ]] || return 0
  if [[ ! -d "$1" ]]; then
    echo "pack folder not found: $1" >&2
    exit 1
  fi
  d=$(cd "$1" && pwd)
  if [[ " ${roots[*]} " != *" $d "* ]]; then roots+=("$d"); fi
}

# find_pack KIND NAME  - the folder of a pack, from the first pack folder that has it.
find_pack() {
  local r
  for r in "${roots[@]}" "$here"; do
    if [[ -d "$r/$1/$2" ]]; then
      echo "$r/$1/$2"
      return 0
    fi
  done
  return 1
}

# list_packs KIND  - the packs of one kind (codes, jurisdictions, trades) in every pack folder.
list_packs() {
  local r
  for r in "${roots[@]}" "$here"; do
    if [[ -d "$r/$1" ]]; then find "$r/$1" -mindepth 1 -maxdepth 1 -type d -printf '%f\n'; fi
  done | sort -u | xargs
}

usage() {
  echo "usage: $0 <project-dir> [--name \"Project Name\"] [--code CODE] [--prefer CODE] [--jurisdiction NAME] [--trades TRADE[,TRADE...]] [--packs DIR]" >&2
  echo "codes:         $(list_packs codes)" >&2
  echo "jurisdictions: $(list_packs jurisdictions)" >&2
  echo "trades:        $(list_packs trades)" >&2
  exit 1
}

dir="" name="" code="" prefer="" jurisdiction="" trades=""
while [[ $# -gt 0 ]]; do
  case "$1" in
  --name | --code | --prefer | --jurisdiction | --trades | --packs)
    [[ $# -ge 2 ]] || usage
    case "$1" in
    --packs) add_root "$2" ;;
    --name) name=$2 ;;
    --code) code=$2 ;;
    --prefer) prefer=$2 ;;
    --jurisdiction) jurisdiction=$2 ;;
    --trades) trades="${trades:+$trades,}$2" ;;
    esac
    shift 2
    ;;
  -h | --help) usage ;;
  -*)
    echo "unknown option: $1" >&2
    usage
    ;;
  *)
    [[ -z "$dir" ]] || usage
    dir=$1
    shift
    ;;
  esac
done
[[ -n "$dir" ]] || usage
IFS=: read -r -a env_roots <<<"${CONST_PACKS:-}"
for r in "${env_roots[@]}"; do add_root "$r"; done

mkdir -p "$dir"
cd "$dir"
name=${name:-$(basename "$PWD")}
folder=$(basename "$PWD")
today=$(date +%F)

# What an earlier run chose (packs.conf: key=value lines).
conf_get() {
  if [[ -f packs.conf ]]; then sed -n "s/^$1=//p" packs.conf | tail -n 1; fi
}
old_code=$(conf_get code)
old_prefer=$(conf_get prefer)
old_jurisdiction=$(conf_get jurisdiction)
old_trades=$(conf_get trades)
IFS=: read -r -a conf_roots <<<"$(conf_get packs)"
for r in "${conf_roots[@]}"; do add_root "$r"; done

# The code edition and the jurisdiction are fixed once chosen: changing them later
# changes every compliance check, so it is a recorded decision done by hand, not by this script.
pick_fixed() {
  local kind=$1 old=$2 new=$3 default=$4
  if [[ -n "$old" && -n "$new" && "$new" != "$old" ]]; then
    echo "This project already uses $kind '$old'. Changing it is a decision for docs/decisions.md;" >&2
    echo "edit packs.conf and the copied files by hand if that is really what you want." >&2
    exit 1
  fi
  echo "${new:-${old:-$default}}"
}
jurisdiction=$(pick_fixed "jurisdiction" "$old_jurisdiction" "$jurisdiction" TEMPLATE)
# A jurisdiction pack may name the code it enforces (CODE) and the latest code to design to (PREFER).
jdir=$(find_pack jurisdictions "$jurisdiction") || {
  echo "unknown jurisdiction: $jurisdiction (choices: $(list_packs jurisdictions))" >&2
  exit 1
}
pack_file() { if [[ -f "$jdir/$1" ]]; then tr -d '[:space:]' <"$jdir/$1"; fi; }
required=$(pack_file CODE)
if [[ -n "$required" && -n "$code" && "$code" != "$required" ]]; then
  echo "Jurisdiction $jurisdiction enforces $required (see $jdir/PACK.md), not $code." >&2
  exit 1
fi
code=$(pick_fixed "code" "$old_code" "${code:-$required}" irc-2021)
prefer=$(pick_fixed "preferred code" "$old_prefer" "${prefer:-$(pack_file PREFER)}" "")
if [[ "$prefer" == "$code" ]]; then prefer=""; fi

# Trades add up: the ones already installed plus any new ones, without repeats.
trade_list=()
IFS=, read -r -a wanted <<<"${old_trades:+$old_trades,}$trades"
for t in "${wanted[@]}"; do
  [[ -n "$t" ]] || continue
  if [[ " ${trade_list[*]} " != *" $t "* ]]; then trade_list+=("$t"); fi
done

# Check every pack name before changing anything.
check_pack() {
  if ! find_pack "$1" "$2" >/dev/null; then
    echo "unknown ${1%s}: $2 (choices: $(list_packs "$1"))" >&2
    exit 1
  fi
}
check_pack codes "$code"
if [[ -n "$prefer" ]]; then check_pack codes "$prefer"; fi
check_pack jurisdictions "$jurisdiction"
for t in "${trade_list[@]}"; do check_pack trades "$t"; done

# Copy one source tree into the project without overwriting anything.
# PACK.md (and a jurisdiction's CODE) at a pack's root describe the pack for the framework and are not copied.
added=()
copy_tree() {
  local root=$1 src rel
  while IFS= read -r -d '' src; do
    rel=${src#"$root/"}
    if [[ "$rel" == "PACK.md" || "$rel" == "CODE" || "$rel" == "PREFER" ]]; then continue; fi
    if [[ -e "$rel" ]]; then
      echo "• kept existing $rel"
    else
      mkdir -p "$(dirname "$rel")"
      sed -e "s/{{PROJECT}}/$name/g" -e "s/{{FOLDER}}/$folder/g" -e "s/{{DATE}}/$today/g" \
        -e "s/{{CODE}}/$code/g" -e "s/{{JURISDICTION}}/$jurisdiction/g" -e "s|{{FRAMEWORK}}|$here|g" "$src" >"$rel"
      if [[ -x "$src" ]]; then chmod +x "$rel"; fi
      added+=("$rel")
    fi
    # -L: packs may share a file through a symlink. Tool caches are never copied.
  done < <(find -L "$root" \( -name .ruff_cache -o -name __pycache__ -o -name .pytest_cache -o -name .mypy_cache -o -name .venv \) -prune -o -type f -print0)
}

copy_tree "$here/template"
copy_tree "$(find_pack codes "$code")"
if [[ -n "$prefer" ]]; then copy_tree "$(find_pack codes "$prefer")"; fi
copy_tree "$jdir"
for t in "${trade_list[@]}"; do copy_tree "$(find_pack trades "$t")"; done

trades_csv=$(
  IFS=,
  echo "${trade_list[*]}"
)
{
  echo "# Packs this project was set up with, by const-framework's new-project.sh."
  echo "# code: the code in force (must be met). prefer: the latest code, also met wherever that"
  echo "# doesn't break the code in force (exceptions: model/checks/waivers.toml, each with a decision)."
  echo "# Add a trade with: new-project.sh . --trades <trade>. Don't change code, prefer or jurisdiction"
  echo "# here without a decision in docs/decisions.md."
  echo "code=$code"
  echo "prefer=$prefer"
  echo "jurisdiction=$jurisdiction"
  echo "trades=$trades_csv"
  echo "# Extra pack folders (besides the framework), searched first."
  echo "packs=$(
    IFS=:
    echo "${roots[*]}"
  )"
} >packs.conf
echo "✓ added ${#added[@]} files (code $code${prefer:+, designing to $prefer too}, jurisdiction $jurisdiction, trades: ${trades_csv:-none})"
if [[ "$jurisdiction" == "TEMPLATE" ]]; then
  echo "• jurisdiction is the blank TEMPLATE: fill in jurisdiction/ from official sources in phase 0"
fi
if [[ ${#trade_list[@]} -eq 0 ]]; then
  echo "• no trades chosen yet (choices: $(list_packs trades)); add them with --trades"
fi

if [[ ! -d .git ]]; then
  git init -q -b main
  echo "✓ created git repository (branch main)"
elif ! git rev-parse -q --verify HEAD >/dev/null && [[ "$(git branch --show-current)" != "main" ]]; then
  git symbolic-ref HEAD refs/heads/main
  echo "✓ renamed the empty repository's branch to main"
fi
git config core.hooksPath .githooks
echo "✓ git hooks enabled (.githooks/)"

if ! git rev-parse -q --verify HEAD >/dev/null; then
  git add -A
  ALLOW_MAIN=1 git commit -q --no-verify -m "Start $name with const-framework"
  echo "✓ first commit made on main"
else
  echo "• repository already has commits; review and commit the new files on a branch:"
  printf '    %s\n' "${added[@]}" packs.conf
fi

echo
echo "Next: cd $PWD && claude    (start Claude in this folder so it loads CLAUDE.md and the skills)"
echo "Then say: start phase 0"
