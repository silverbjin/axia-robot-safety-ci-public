#!/usr/bin/env python3
"""P4 G12 student repository full reachable Git history *heuristic security* audit.

Scans all refs actually fetched into a read-only checkout: paths, symlinks and
selected secret text patterns across every unique historical Git tree. This
does NOT prove absence of semantic instructor solutions, credentials absent from
the signatures, deleted unreferenced Git objects, or future pushes. It never
updates student or instructor repositories and cannot approve a release.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path

FORBIDDEN_COMPONENTS = frozenset({
    "instructor", "instructor_solution", "solutions", "solution", "hidden_tests",
    "private_keys", "secrets", ".ssh", ".aws", ".gnupg", "owner_raw",
})
FORBIDDEN_FILENAMES = frozenset({".env", ".git-credentials", ".netrc", "id_rsa", "id_ed25519"})
FORBIDDEN_SUFFIXES = (".pem", ".p12", ".pfx", ".key", ".db3", ".sqlite3", ".tar.gz")
# Git extended regular expressions; matches only high-signal credential patterns.
SECRET_PATTERN = (
    r"-----BEGIN ((RSA|EC|DSA|OPENSSH) )?PRIVATE KEY-----"
    r"|ghp_[[:alnum:]]{20,}"
    r"|github_pat_[[:alnum:]_]{40,}"
    r"|AKIA[0-9A-Z]{16}"
)
SHA40 = re.compile(r"^[a-f0-9]{40}$")


def git(repo: Path, *argv: str, ok=(0,)) -> subprocess.CompletedProcess:
    process = subprocess.run(["git", "-C", str(repo), *argv],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode not in ok:
        # Do not print potentially sensitive Git stderr, ref paths or file content.
        raise ValueError("GIT_OPERATION_FAILED")
    return process


def scan_repo(repo: Path, *, required_refs: set[str] | None = None,
              expected_heads: dict[str, str] | None = None) -> dict:
    repo = Path(repo)
    git(repo, "rev-parse", "--git-dir")
    ref_lines = git(repo, "for-each-ref", "--format=%(refname) %(objectname)").stdout.decode().splitlines()
    refs = {}
    for line in ref_lines:
        ref, _, sha = line.partition(" ")
        if ref and SHA40.fullmatch(sha):
            refs[ref] = sha
    problems: set[tuple[str, str]] = set()
    for ref in required_refs or set():
        if ref not in refs:
            problems.add(("REQUIRED_REF_MISSING", ref))
    for ref, sha in (expected_heads or {}).items():
        if refs.get(ref) != sha or not SHA40.fullmatch(sha):
            problems.add(("EXPECTED_SHA_MISMATCH", ref))

    commits = git(repo, "rev-list", "--all").stdout.decode().splitlines()
    if not commits:
        problems.add(("NO_REACHABLE_COMMITS", "EMPTY"))
    unique_trees = set()
    for sha in commits:
        if not SHA40.fullmatch(sha):
            raise ValueError("INVALID_COMMIT_SHA")
        tree = git(repo, "rev-parse", sha + "^{tree}").stdout.decode().strip()
        if not SHA40.fullmatch(tree):
            raise ValueError("INVALID_TREE_SHA")
        unique_trees.add(tree)

    for tree in sorted(unique_trees):
        entries = git(repo, "ls-tree", "-r", "-z", "--full-tree", tree).stdout
        for entry in entries.split(b"\x00"):
            if not entry:
                continue
            header, _, name = entry.partition(b"\t")
            mode = header.split(b" ", 1)[0].decode("ascii")
            path = name.decode("utf-8", errors="surrogateescape")
            parts = [piece.casefold() for piece in path.split("/")]
            basename = parts[-1]
            if mode == "120000":
                problems.add(("GIT_SYMLINK", path))
            if mode == "160000":
                problems.add(("EXTERNAL_GITLINK_REVIEW", path))
            if (any(x in FORBIDDEN_COMPONENTS for x in parts)
                    or basename in FORBIDDEN_FILENAMES
                    or basename.endswith(FORBIDDEN_SUFFIXES)):
                problems.add(("FORBIDDEN_HISTORY_PATH", path))

        # `git grep` reads only historical tracked text blobs, does not print the secret.
        grep = git(repo, "grep", "-I", "-l", "-E", "-e", SECRET_PATTERN, tree, "--", ok=(0, 1))
        if grep.returncode == 0:
            # Files with matching text are counted, but never disclose matches.
            for item in grep.stdout.decode("utf-8", errors="replace").splitlines():
                problems.add(("SECRET_CONTENT_PATTERN", item))

    ref_snapshot = "\n".join(sorted(f"{key} {value}" for key, value in refs.items()))
    return {
        "schema": "axia_p4_g12_student_git_history_l0_v1",
        "status": "BLOCKED" if problems else "HISTORY_METADATA_PASS_SCOPED",
        "formal_g12_accepted": False,
        "student_release_approved": False,
        "repo_mutated": False,
        "refs_count": len(refs),
        "commit_count": len(commits),
        "unique_tree_count": len(unique_trees),
        "ref_snapshot_sha256": hashlib.sha256(ref_snapshot.encode()).hexdigest(),
        "finding_count": len(problems),
        "finding_types": sorted({kind for kind, _ in problems}),
        "coverage": "ALL_FETCHED_REACHABLE_REFS_PATHS_AND_SELECTED_TEXT_PATTERNS_ONLY",
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("worktree")
    parser.add_argument("--expect-main")
    parser.add_argument("--expect-d03")
    arguments = parser.parse_args(argv)
    required = set()
    expected = {}
    for ref, sha in (("refs/remotes/origin/main", arguments.expect_main),
                     ("refs/remotes/origin/D03", arguments.expect_d03)):
        if sha is not None:
            required.add(ref)
            expected[ref] = sha
    try:
        result = scan_repo(Path(arguments.worktree), required_refs=required,
                           expected_heads=expected)
    except (ValueError, OSError):
        print("AXIA_P4_G12_HISTORY_SCAN_ERROR_FAIL_CLOSED", file=sys.stderr)
        return 2
    # Deliberately no paths, usernames, source lines, or matching secret text.
    print("AXIA_P4_G12_HISTORY_L0_" + result["status"]
          + " refs=" + str(result["refs_count"])
          + " commits=" + str(result["commit_count"])
          + " unique_trees=" + str(result["unique_tree_count"])
          + " findings=" + str(result["finding_count"])
          + " types=" + ",".join(result["finding_types"])
          + " snapshot_sha256=" + result["ref_snapshot_sha256"]
          + " FORMAL_G12_NOT_ACCEPTED")
    return 0 if result["status"] == "HISTORY_METADATA_PASS_SCOPED" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
