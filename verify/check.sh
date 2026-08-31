#!/usr/bin/env bash
# check.sh — re-validate every route shipped in this repo.
#
# Each route is replayed edge by edge against data/graph.json by verify/validate.ts,
# which shares no code with any solver. A route that does not reproduce its
# expected score means the data in this repo is not the data that was measured.
set -uo pipefail
cd "$(dirname "$0")/.."

RUNNER=${RUNNER:-}
if [ -z "$RUNNER" ]; then
  if command -v bun >/dev/null 2>&1; then RUNNER="bun"
  else RUNNER="node --experimental-strip-types"; fi
fi
echo "runner: $RUNNER"

# route file : expected groups claimed : expected exit code
CASES="
best-315-partial:315:1
best-319-partial:319:1
best-320-contested:320:1
best-321-alt:321:1
best-321-partial:321:1
best-321-third:321:1
"

fail=0
while IFS=: read -r name want_score want_exit; do
  [ -z "$name" ] && continue
  out=$($RUNNER verify/validate.ts "routes/$name.json" 2>&1); code=$?
  got=$(printf '%s' "$out" | grep -oE '[0-9]+/322 groups claimed' | grep -oE '^[0-9]+')
  if [ "$got" = "$want_score" ] && [ "$code" = "$want_exit" ]; then
    printf '  ok   %-22s %s/322  exit=%s\n' "$name" "$got" "$code"
  else
    printf '  FAIL %-22s got %s/322 exit=%s, want %s/322 exit=%s\n' \
           "$name" "${got:-?}" "$code" "$want_score" "$want_exit"
    fail=1
  fi
done <<< "$CASES"

# Every `fact N` cited by a door must exist as a row in FACTS.md.
if [ -f FACTS.md ]; then
  ids=$(grep -oE '^\| *[0-9]+ *\|' FACTS.md | grep -oE '[0-9]+' | sort -n | uniq)
  missing=""
  for n in $(grep -rhoE 'facts? [0-9]+' README.md THE-*.md routes/README.md 2>/dev/null | grep -oE '[0-9]+' | sort -n | uniq); do
    echo "$ids" | grep -qx "$n" || missing="$missing $n"
  done
  if [ -n "$missing" ]; then echo "  FAIL cited but absent from FACTS.md:$missing"; fail=1
  else echo "  ok   every cited fact resolves"; fi
else
  echo "  FAIL FACTS.md is missing"; fail=1
fi

if [ "$fail" = 0 ]; then echo "all 6 routes reproduce their measured score"; else echo "CHECK FAILED"; fi
exit "$fail"
