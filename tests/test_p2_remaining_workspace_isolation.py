"""Actual git+PTY regression: G06 build artifacts must not dirty the G07 checkout.

Exercises public bootstrap with a dummy local Git repo, not private code:
no ROS, Gazebo, Nav2 Goal, Fault, external network or owner approval.
"""
import os
from pathlib import Path
import pty
import select
import signal
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts" / "axia_p2_remaining_owner_l3_once.sh"
PIN = "1216d8589b2a8ac4c7e75aedaa7854eb7b2470b3"
BRANCH = "integration/p1-p2-mvp-shell-consent-20261110"


def git(*args, cwd=None):
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def run_pty(program, env):
    pid, master = pty.fork()
    if pid == 0:
        try:
            os.execve("/bin/bash", ["bash", str(program)], env)
        except BaseException:
            os._exit(127)
    chunks, status = [], None
    end = time.monotonic() + 15
    try:
        while time.monotonic() < end:
            r, _, _ = select.select([master], [], [], 0.1)
            if r:
                try:
                    chunks.append(os.read(master, 32768))
                except OSError:
                    pass
            done, st = os.waitpid(pid, os.WNOHANG)
            if done:
                status = st
                break
        if status is None:
            os.kill(pid, signal.SIGKILL)
            os.waitpid(pid, 0)
            raise AssertionError("Dummy case runner timed out")
    finally:
        os.close(master)
    return os.waitstatus_to_exitcode(status), b"".join(chunks).decode(errors="replace")


def simulate(tmp_path, fail_case="", wrapper=WRAPPER):
    origin = tmp_path / "origin"
    origin.mkdir()
    git("init", "-q", "-b", BRANCH, str(origin))
    git("config", "user.email", "ci@example.invalid", cwd=origin)
    git("config", "user.name", "CI", cwd=origin)
    (origin / "scripts").mkdir()
    fake_owner = '''#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
[[ "$1" == --case && "$2" =~ ^G0[67]$ ]] || exit 3
[[ -z "$(git -C "$root" status --porcelain)" ]] || {
  echo "DIRTY_CASE=$2"; exit 4;
}
printf '%s|%s\\n' "$2" "$root" >> "$AXIA_TEST_CASE_LOG"
mkdir -p "$root/build" "$root/install" "$root/log"
echo generated > "$root/build/generated.txt"
if [[ "$2" == "${AXIA_TEST_FAIL_CASE:-}" ]]; then exit 8; fi
'''
    (origin / "scripts" / "p2_owner_l3_wsl2.sh").write_text(fake_owner)
    git("add", ".", cwd=origin)
    git("commit", "-qm", "dummy source", cwd=origin)
    sha = git("rev-parse", "HEAD", cwd=origin)
    source = wrapper.read_text()
    assert source.count(PIN) == 1
    copy = tmp_path / "wrapper.sh"
    # Replace only the SHA in a temporary testing copy; production pin stays immutable.
    copy.write_text(source.replace(PIN, sha))

    fakebin = tmp_path / "bin"
    fakebin.mkdir()
    gh = fakebin / "gh"
    gh.write_text('''#!/usr/bin/env bash
set -euo pipefail
if [[ "$1" == auth && "$2" == status ]]; then exit 0; fi
if [[ "$1" == repo && "$2" == clone ]]; then
  exec git clone -q --depth 1 -b "$AXIA_TEST_BRANCH" "file://$AXIA_TEST_LOCAL_ORIGIN" "$4"
fi
exit 6
''')
    gh.chmod(0o755)
    home = tmp_path / "home"
    home.mkdir()
    log = tmp_path / "cases.log"
    env = dict(os.environ, HOME=str(home),
               PATH=str(fakebin) + ":" + os.environ["PATH"],
               AXIA_TEST_BRANCH=BRANCH,
               AXIA_TEST_LOCAL_ORIGIN=str(origin),
               AXIA_TEST_CASE_LOG=str(log),
               AXIA_TEST_FAIL_CASE=fail_case)
    rc, output = run_pty(copy, env)
    entries = [line.strip().split("|") for line in log.read_text().splitlines()] if log.exists() else []
    return rc, output, entries


def test_g06_generated_build_does_not_dirty_g07(tmp_path):
    rc, out, entries = simulate(tmp_path)
    assert rc == 0, out
    assert [r[0] for r in entries] == ["G06", "G07"], out
    assert entries[0][1] != entries[1][1], "Cases must have isolated actual Git worktrees"
    assert "P2_REMAINING_OWNER_BLOCKED_CASE" not in out


def test_g06_failure_never_starts_g07(tmp_path):
    rc, out, entries = simulate(tmp_path, fail_case="G06")
    assert rc != 0
    assert [r[0] for r in entries] == ["G06"]
    assert "P2_REMAINING_OWNER_BLOCKED_CASE=G06" in out

def test_g07_only_fresh_shallow_checkout(tmp_path):
    # Recommended next Owner action runs G07 only; do not repeat valid G06.
    # Mock the private runner and gh authentication, but use real shallow Git
    # clone, a real controlling PTY and the exact public bootstrap logic.
    wrapper = ROOT / "scripts" / "axia_p2_g07_owner_l3_once.sh"
    rc, out, entries = simulate(tmp_path, wrapper=wrapper)
    assert rc == 0, out
    assert [x[0] for x in entries] == ["G07"]
    assert "DIRTY_CASE=G07" not in out
