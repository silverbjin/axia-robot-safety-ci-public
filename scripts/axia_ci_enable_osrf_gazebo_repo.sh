#!/usr/bin/env bash
# Official OSRF Ubuntu Noble Gazebo Harmonic apt source.
# CI-container-only and fail closed. No user WSL2 changes. No apt-key.
set -Eeuo pipefail

if [[ $# == 1 && "$1" == '--self-check' ]]; then
  echo 'AXIA_OSRF_REPO_CONTRACT_OK NO_APT_MUTATION'
  exit 0
fi
[[ $# == 0 ]] || { echo 'Only --self-check or no args' >&2; exit 2; }
# shellcheck disable=SC1091
source /etc/os-release
[[ "$ID" == 'ubuntu' && "$VERSION_ID" == '24.04' ]] || {
  echo 'AXIA_OSRF_REPO_BLOCKED_NOT_UBUNTU_NOBLE' >&2
  exit 2
}
[[ "$(id -u)" -eq 0 ]] || { echo 'AXIA_OSRF_REPO_BLOCKED_NOT_ROOT' >&2; exit 2; }

apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
  ca-certificates curl gnupg >/dev/null
KEYRING='/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg'
SOURCE_LIST='/etc/apt/sources.list.d/gazebo-stable.list'
KEYFILE="$(mktemp)"
trap 'rm -f -- "$KEYFILE"' EXIT

curl --proto '=https' --tlsv1.2 -fSL --retry 3 --connect-timeout 15 \
  --max-time 60 'https://packages.osrfoundation.org/gazebo.gpg' \
  -o "$KEYFILE"
gpg --batch --quiet --show-keys "$KEYFILE" >/dev/null || {
  echo 'AXIA_OSRF_REPO_BLOCKED_INVALID_GPG_KEY' >&2
  exit 2
}
install -m 0644 "$KEYFILE" "$KEYRING"
printf 'deb [arch=%s signed-by=%s] https://packages.osrfoundation.org/gazebo/ubuntu-stable noble main\n' \
  "$(dpkg --print-architecture)" "$KEYRING" > "$SOURCE_LIST"
apt-get update -qq

for PACKAGE in libgz-sim8 libsdformat14; do
  if [[ -z "$(apt-cache madison "$PACKAGE")" ]]; then
    echo "AXIA_OSRF_REPO_BLOCKED_NO_PUBLISHED_PACKAGE=$PACKAGE" >&2
    exit 2
  fi
done
echo 'AXIA_OSRF_REPO_READY_SIGNED_UBUNTU_NOBLE'
echo 'AXIA_OSRF_EXACT_OWNER_VERSION_STILL_REQUIRES_PRIVATE_PIN_CHECK'
