#!/usr/bin/env bash
# Public, synthetic fixture-only D03 directory comparison.
set -Eeuo pipefail
if [[ "$#" -ne 2 || ! -d "${1:-}" || ! -d "${2:-}" ]]; then
  echo "usage: bash d03_mirror_compare.sh STUDENT_DIR INSTRUCTOR_MIRROR_DIR" >&2
  exit 2
fi
diff -qr "$1" "$2"
