"""RED: one Owner invocation for only remaining G06/G07, with per-case consent."""
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"axia_p2_remaining_owner_l3_once.sh"
PIN="1216d8589b2a8ac4c7e75aedaa7854eb7b2470b3"


def run(*args):
    return subprocess.run(["bash",str(SCRIPT),*args],
                          input="",capture_output=True,text=True,timeout=8)


def test_remaining_wrapper_exists_and_is_bash_valid():
    assert SCRIPT.is_file(), "RED: G06/G07 single-entry bootstrap not implemented"
    subprocess.run(["bash","-n",str(SCRIPT)],check=True,timeout=8)


def test_self_check_is_readonly_and_pinned():
    r=run("--self-check")
    assert r.returncode==0,r.stderr
    assert PIN in r.stdout and "L3_NOT_RUN" in r.stdout
    assert "G06" in r.stdout and "G07" in r.stdout


def test_arguments_do_not_allow_case_override_or_implicit_yes():
    for arg in (("--case","G05"),("--case","G06"),("--case","G07"),
                ("--yes",),("--all",),("--self-check","anything")):
        assert run(*arg).returncode!=0,arg


def test_no_tty_fails_before_gh_access_and_goal():
    r=run()
    assert r.returncode!=0
    assert "TTY" in r.stderr and "Cloning into" not in r.stdout+r.stderr


def test_exact_source_two_isolated_runner_cases_and_no_unsafe_approval():
    s=SCRIPT.read_text()
    assert "readonly SHA='"+PIN+"'" in s
    assert "integration/p1-p2-mvp-shell-consent-20261110" in s
    for fragment in ("gh auth status","rev-parse HEAD","status --porcelain",
                     "AXIA_P2_OWNER_PINNED_SHA","/dev/tty",
                     "G06 G07","--case", "p2_owner_l3_wsl2.sh"):
        assert fragment in s
    assert "G05" not in s
    assert "yes |" not in s.lower()
    assert "echo YES-" not in s
