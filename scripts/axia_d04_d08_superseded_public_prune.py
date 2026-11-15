#!/usr/bin/env python3
"""Prune only 2 D04 public CI historical branches with explicit merged successor.

Original PR must be CLOSED, branch immutable at original PR head,
successor PR MERGED and its merge commit in current main, no open PR usage.
Every delete writes original SHA + PR provenance to audit. No ROS/Goal.
"""
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import quote

REPO = "silverbjin/axia-robot-safety-ci-public"
SUPERSEDED = {
    "preflight/d04-gazebo-rgb-20261108": (7, 8),
    "preflight/d04-p1-yolo-integration-20261108": (11, 14),
}

def api(path, method="GET"):
    p = subprocess.run(["gh", "api", "-X", method, path],
                       capture_output=True, text=True, timeout=60)
    if p.returncode:
        raise RuntimeError(path + " " + p.stderr[:200])
    return json.loads(p.stdout) if p.stdout.strip() else None

def list_open_prs():
    result = []
    for i in range(1, 20):
        a = api(f"repos/{REPO}/pulls?state=open&per_page=100&page={i}")
        result.extend(a)
        if len(a) < 100:
            return result
    raise RuntimeError("OPEN_PR_LIST_TRUNCATED")

def main():
    out = Path("axia_d04_d08_superseded_public_branch_cleanup.json")
    main = api(f"repos/{REPO}/branches/main")["commit"]["sha"]
    report = {"repo": REPO, "main_sha": main, "scope": "2 explicitly superseded",
              "deleted": [], "blocked": []}
    for branch, (original, successor) in SUPERSEDED.items():
        entry = {"branch": branch, "original_pr": original, "successor_pr": successor}
        try:
            src = api(f"repos/{REPO}/pulls/{original}")
            dst = api(f"repos/{REPO}/pulls/{successor}")
            if src["state"] != "closed":
                raise RuntimeError("ORIGINAL_PR_STILL_OPEN")
            if not dst["merged"] or not dst["merge_commit_sha"]:
                raise RuntimeError("SUCCESSOR_PR_NOT_MERGED")
            if src["head"]["ref"] != branch:
                raise RuntimeError("ORIGINAL_PR_HEAD_MISMATCH")
            if src["head"]["repo"]["full_name"] != REPO:
                raise RuntimeError("ORIGINAL_PR_OTHER_REPO")
            b = api(f"repos/{REPO}/branches/{quote(branch, safe='/')}")
            entry["sha"] = b["commit"]["sha"]
            if b["commit"]["sha"] != src["head"]["sha"] or b.get("protected"):
                raise RuntimeError("BRANCH_CHANGED_OR_PROTECTED")
            if any(
                br.get(part, {}).get("ref") == branch and
                (br.get(part, {}).get("repo") or {}).get("full_name") == REPO
                for br in list_open_prs() for part in ("head", "base")
            ):
                raise RuntimeError("ACTIVE_OPEN_PR_DEPENDS_ON_REF")
            if api(f"repos/{REPO}/branches/main")["commit"]["sha"] != main:
                raise RuntimeError("MAIN_MOVED")
            comp = api(
                f"repos/{REPO}/compare/{dst['merge_commit_sha']}...main")
            if comp["behind_by"] != 0:
                raise RuntimeError("SUCCESSOR_NOT_ANCESTOR_OF_MAIN")
            entry["successor_main_sha"] = dst["merge_commit_sha"]
            api(f"repos/{REPO}/git/refs/heads/{quote(branch, safe='/')}",
                method="DELETE")
            report["deleted"].append(entry)
            print("AXIA_PUBLIC_SUPERSEDED_BRANCH_DELETED", branch,
                  original, successor, flush=True)
        except Exception as exc:
            entry["error"] = str(exc)
            report["blocked"].append(entry)
            print("AXIA_PUBLIC_SUPERSEDED_BLOCKED", branch, exc, flush=True)
        finally:
            out.write_text(json.dumps(report, indent=2) + "\n")
    print("AXIA_PUBLIC_SUPERSEDED_PRUNE_RESULT", "deleted",
          len(report["deleted"]), "blocked", len(report["blocked"]), flush=True)
    return int(bool(report["blocked"]))

if __name__ == "__main__":
    sys.exit(main())
