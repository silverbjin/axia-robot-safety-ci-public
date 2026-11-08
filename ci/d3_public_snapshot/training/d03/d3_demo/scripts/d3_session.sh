#!/usr/bin/env bash
# Create or inspect an isolated classroom session (no ROS side effects).
set -Eeuo pipefail
ROOT="$HOME/axia_d3_classroom"
ENVFILE="$ROOT/d3_session.env"
case "${1:---init}" in
  --init)
    mkdir -p "$ROOT/evidence"
    chmod 700 "$ROOT" "$ROOT/evidence"
    if [[ -e "$ENVFILE" ]]; then
      [[ -f "$ENVFILE" && ! -L "$ENVFILE" ]] || { echo '[BLOCKED] unsafe session env'; exit 2; }
      echo "[EXISTS] $ENVFILE (preserved; no overwrites)"
    else
      DOMAIN="${AXIA_D3_DOMAIN_ID:-174}"
      [[ "$DOMAIN" =~ ^[0-9]+$ ]] && (( 10#$DOMAIN >= 0 && 10#$DOMAIN <= 232 )) || {
        echo '[BLOCKED] AXIA_D3_DOMAIN_ID must be 0..232'; exit 2;
      }
      export GZ_PARTITION="axia_d3_${UID}_$(date -u +%Y%m%dT%H%M%SZ)"
      export D3_EVIDENCE="$ROOT/evidence/d3_$(date -u +%Y%m%dT%H%M%SZ).jsonl"
      umask 077
      {
        printf 'export ROS_DOMAIN_ID=%q\n' "$DOMAIN"
        printf 'export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST\n'
        printf 'export GZ_PARTITION=%q\n' "$GZ_PARTITION"
        printf 'export D3_EVIDENCE=%q\n' "$D3_EVIDENCE"
        printf 'export AXIA_P0_SIM_ONLY=1\n'
        printf 'export TURTLEBOT3_MODEL=waffle\n'
      } > "$ENVFILE"
      echo "[CREATED] $ENVFILE"
    fi
    echo '[NEXT] In EACH instructor terminal: source "$HOME/axia_d3_classroom/d3_session.env"'
    ;;
  --new-evidence)
    [[ -f "$ENVFILE" && ! -L "$ENVFILE" ]] || { echo '[BLOCKED] initialize first'; exit 2; }
    source "$ENVFILE"
    NEW="$ROOT/evidence/d3_$(date -u +%Y%m%dT%H%M%SZ)_${RANDOM}_${RANDOM}.jsonl"
    [[ ! -e "$NEW" ]] || { echo '[BLOCKED] collision'; exit 2; }
    umask 077
    # Preserve the P1 ROS domain and Gazebo partition for an already-running simulation.
    python3 - "$ENVFILE" "$NEW" <<'PYENV'
import pathlib,sys
p=pathlib.Path(sys.argv[1]); s=p.read_text()
lines=[x for x in s.splitlines() if not x.startswith('export D3_EVIDENCE=')]
import shlex
lines.append('export D3_EVIDENCE='+shlex.quote(sys.argv[2]))
p.write_text('\n'.join(lines)+'\n')
PYENV
    echo "[NEW_EVIDENCE] $NEW"
    echo '[NEXT] Source the updated session env in every new terminal'
    ;;
  --show)
    [[ -f "$ENVFILE" && ! -L "$ENVFILE" ]] || { echo '[BLOCKED] initialize session first'; exit 2; }
    # shellcheck disable=SC1090
    source "$ENVFILE"
    printf 'ROS_DOMAIN_ID=%s\nGZ_PARTITION=%s\nD3_EVIDENCE=%s\n' "$ROS_DOMAIN_ID" "$GZ_PARTITION" "$D3_EVIDENCE"
    ;;
  *) echo 'Usage: bash training/d03/d3_demo/scripts/d3_session.sh [--init|--show|--new-evidence]' >&2; exit 64;;
esac