#!/usr/bin/env bash
# AXIA D10 instructor WSL2 one-shot: pinned public renderer + local private reference score CSV.
set -Eeuo pipefail

: "${AXIA_D10_REPLAY_PUBLIC_SHA:?Set verified immutable AXIA_D10_REPLAY_PUBLIC_SHA (40-hex Git commit SHA)}"
if [[ ! "$AXIA_D10_REPLAY_PUBLIC_SHA" =~ ^[0-9a-f]{40}$ ]]; then
  echo 'D10_PUBLIC_SHA_INVALID: need full immutable 40-char hex SHA' >&2;exit 2
fi
PUBLIC_REPO='silverbjin/axia-robot-safety-ci-public'
URL="https://raw.githubusercontent.com/${PUBLIC_REPO}/${AXIA_D10_REPLAY_PUBLIC_SHA}/d10/replay"
CACHE="$HOME/.cache/axia_d10_replay/$AXIA_D10_REPLAY_PUBLIC_SHA"
mkdir -p "$CACHE"
for name in build_replay.py replay_template.html; do
  tmp="$CACHE/${name}.part-$$"
  curl -fL --retry 3 --retry-delay 2 --max-time 90 "$URL/$name" -o "$tmp"
  test -s "$tmp"
  mv -f -- "$tmp" "$CACHE/$name"
done
python3 -m py_compile "$CACHE/build_replay.py"

BLOCK_C="${AXIA_D10_INSTRUCTOR_BLOCK_C:-}"
if [[ -z "$BLOCK_C" ]]; then
  for p in \
    "$PWD" \
    "$HOME/axia_d10_course/axia-robot-safety-instructor/training/block_C" \
    "$HOME/axia_d09_course/axia-robot-safety-instructor/training/block_C" \
    "$HOME/axia-robot-safety-instructor/training/block_C"; do
    if [[ -f "$p/fixtures/test_mixed.csv" && -f "$p/day10/reference_outputs/if_scores_test.csv" ]]; then
      BLOCK_C="$p"; break
    fi
  done
fi
if [[ -z "$BLOCK_C" ]]; then
  echo 'D10_PRIVATE_SOURCE_NOT_FOUND: checking private instructor clone permission' >&2
  if command -v gh >/dev/null 2>&1; then
    gh auth status || { echo 'D10_PRIVATE_AUTH_HOLD: run gh auth login once (not a data/model failure)' >&2;exit 3; }
    mkdir -p "$HOME/axia_d10_course"
    git clone https://github.com/silverbjin/axia-robot-safety-instructor.git \
      "$HOME/axia_d10_course/axia-robot-safety-instructor"
    BLOCK_C="$HOME/axia_d10_course/axia-robot-safety-instructor/training/block_C"
  else
    echo 'D10_PRIVATE_CLONE_HOLD: install/authenticate gh or set AXIA_D10_INSTRUCTOR_BLOCK_C' >&2
    exit 3
  fi
fi
for f in "$BLOCK_C/fixtures/test_mixed.csv" "$BLOCK_C/fixtures/scenario_manifest.json" \
         "$BLOCK_C/day10/reference_outputs/if_scores_test.csv"; do
  test -s "$f" || { echo "D10_PRIVATE_INPUT_MISSING: $f" >&2; exit 3; }
done
OUTPUT="${AXIA_D10_REPLAY_OUT:-$HOME/axia_d10_course/AXIA_D10_LIVE_REPLAY_INSTRUCTOR.html}"
mkdir -p "$(dirname "$OUTPUT")"
REPORT="$(dirname "$OUTPUT")/axia_d10_replay_build.log"
{
  echo "D10_REPLAY_OWNER_PUBLIC_SHA=$AXIA_D10_REPLAY_PUBLIC_SHA"
  echo 'D10_REPLAY_PROVENANCE=INSTRUCTOR_C03_REFERENCE'
  echo "D10_REPLAY_PRIVATE_BLOCK_C=$BLOCK_C"
  if git -C "$BLOCK_C" rev-parse HEAD >/dev/null 2>&1; then
    echo "D10_REPLAY_PRIVATE_SHA=$(git -C "$BLOCK_C" rev-parse HEAD)"
  fi
  python3 "$CACHE/build_replay.py" \
    --raw "$BLOCK_C/fixtures/test_mixed.csv" \
    --scores "$BLOCK_C/day10/reference_outputs/if_scores_test.csv" \
    --manifest "$BLOCK_C/fixtures/scenario_manifest.json" \
    --out "$OUTPUT" \
    --score-source INSTRUCTOR_C03_REFERENCE \
    --expect-baseline
  printf 'D10_REPLAY_HTML_SHA256='; sha256sum "$OUTPUT" | awk '{print $1}'
} 2>&1 | tee "$REPORT"
# Keep evidence small: no raw / model / full HTML embedded in diagnostic archive.
tar -czf "$(dirname "$OUTPUT")/axia_d10_replay_minimal_logs.tar.gz" -C "$(dirname "$OUTPUT")" "$(basename "$REPORT")"
echo "D10_REPLAY_OWNER_GENERATED=$OUTPUT"
echo "D10_REPLAY_OWNER_LOG_ARCHIVE=$(dirname "$OUTPUT")/axia_d10_replay_minimal_logs.tar.gz"
if [[ "${AXIA_D10_REPLAY_OWNER_OPEN:-1}" == 1 ]]; then
  if command -v wslpath >/dev/null 2>&1 && command -v explorer.exe >/dev/null 2>&1; then
    explorer.exe "$(wslpath -w "$OUTPUT")" || echo 'D10_BROWSER_OPEN_HOLD: open the HTML from Windows Explorer'
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$OUTPUT" >/dev/null 2>&1 || echo 'D10_BROWSER_OPEN_HOLD: double-click the HTML manually'
  else
    echo 'D10_BROWSER_OPEN_HOLD: open generated HTML with Edge or Chrome'
  fi
fi
