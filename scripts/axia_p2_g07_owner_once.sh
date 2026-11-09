#!/usr/bin/env bash
# Public bootstrap only. P2 G07 physical obstacle demo; no automatic Goal consent.
set -Eeuo pipefail
umask 077
readonly REPO='silverbjin/axia-robot-safety-instructor'
readonly BRANCH='fix/p2-g07-fresh-zone-observation-20261110'
readonly SHA='0af856dbf5dfcbbce62a6e6bd3242a25c91a343d'
if [[ "${1:-}" == '--self-check' ]]; then
  [[ $# == 1 && "$SHA" =~ ^[0-9a-f]{40}$ ]] || exit 2
  printf 'P2_L3_OWNER_PUBLIC_BOOTSTRAP_CONTRACT_OK private_sha=%s L3_NOT_RUN\n' "$SHA"
  exit 0
fi
[[ $# == 0 ]] || {
  echo 'P2_L3_BLOCKED: unsupported arguments';exit 2;
}
[[ -t 0 && -t 1 && -r /dev/tty ]] || {
  echo 'P2_L3_BLOCKED: real Owner controlling TTY required' >&2;exit 2;
}
for app in gh git bash mktemp;do
  command -v "$app" >/dev/null || { echo "P2_L3_BLOCKED: $app absent" >&2; exit 2; }
done
gh auth status >/dev/null 2>&1 || { echo 'P2_L3_BLOCKED: GitHub private auth';exit 2; }
SRC="$(mktemp -d "$HOME/.axia_p2_l3_checkout_XXXXXXXX")"
cleanup() {
  local rc=$?
  trap - EXIT INT TERM
  # Never remove the current shell working directory; fixes old getcwd warning.
  cd "$HOME" || cd /
  if [[ -n "${SRC:-}" && "$SRC" == "$HOME"/.axia_p2_l3_checkout_* && -d "$SRC" ]];then
    rm -rf -- "$SRC"
  fi
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
printf 'AXIA_P2_L3_PRIVATE_SOURCE_SHA=%s\n' "$SHA"
if ! gh repo clone "$REPO" "$SRC/instructor" -- --single-branch --branch "$BRANCH" --depth 1;then
  echo 'P2_L3_BLOCKED: private clone failed' >&2;exit 2;
fi
[[ "$(git -C "$SRC/instructor" rev-parse HEAD)" == "$SHA" ]] || {
  echo 'P2_L3_BLOCKED: expected private SHA mismatch' >&2;exit 2;
}
[[ -z "$(git -C "$SRC/instructor" status --porcelain)" ]] || {
  echo 'P2_L3_BLOCKED: private checkout dirty' >&2;exit 2;
}
export AXIA_P2_OWNER_PINNED_SHA="$SHA"
# Execute in the real terminal; never pipe through tee or supply implicit YES.
bash "$SRC/instructor/scripts/p2_owner_l3_wsl2.sh" --case G07
