#!/usr/bin/env bash
# Motion audit wrapper for render paths (WARNING-ONLY by default).
# Usage: audit_warn.sh PATH_TO_COMP [--strict]
# Exit codes: 0 (always in default mode, even on findings); non-zero only in strict mode with FAIL findings.
set -euo pipefail

COMP_PATH="${1:-}"
STRICT="${REELSMITH_AUDIT_STRICT:-0}"
[ "${2:-}" = "--strict" ] && STRICT=1

if [ -z "$COMP_PATH" ]; then
  echo "motion audit SKIPPED: no path provided" >&2
  exit 0
fi

HERE="$(cd "$(dirname "$0")" && pwd)"
PYTHON="${PYTHON:-python3}"

# Run audit and capture exit code (don't let set -e abort on non-zero)
set +e
"$PYTHON" "$HERE/review.py" audit "$COMP_PATH"
rc=$?
set -e

# review.py audit exit codes: 0 = clean/WARN, 1 = FAIL, other = error/missing
case $rc in
  0)
    # Output already printed by review.py; add wrapper summary
    echo "motion audit: complete (WARNING-ONLY mode)"
    exit 0
    ;;
  1)
    # Findings already printed by review.py
    echo "motion audit: FAIL findings detected (WARNING-ONLY mode, render continues)"
    if [ "$STRICT" = "1" ]; then
      echo "motion audit FAILED in strict mode (REELSMITH_AUDIT_STRICT=1)" >&2
      exit 1
    fi
    exit 0
    ;;
  *)
    echo "motion audit ERROR: exit $rc (WARNING-ONLY mode, render continues)" >&2
    exit 0
    ;;
esac
