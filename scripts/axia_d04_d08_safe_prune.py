#!/usr/bin/env python3
"""AXIA D04-D08 branch prune: only Git ancestors of main; never active PR refs.

Authentication: gh auth login (Owner), or GH_TOKEN in PUBLIC GitHub Actions.
Default is AUDIT. --apply deletes only refs with ahead_by==0 vs main,
and checks branch SHA, main SHA, protection and live PR references again.
Superseded/cherry-picked branches with ahead_by>0 stay visible for review.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import quote

REPOS = (
    "silverbjin/axia-robot-safety-instructor",
    "silverbjin/axia-robot-safety-student",
    "silverbjin/axia-robot-safety-ci-public",
)
MATCH = re.compile(r"d0[4-8]|day0[4-8]|block[-_]?b", re.I)

def scoped(name):
    return name != "main" and bool(MATCH.search(name))

def open_pr_ref(name, pulls, repo):
    return any(
        p.get(side, {}).get("ref") == name
        and (p.get(side, {}).get("repo") or {}).get("full_name") == repo
        for p in pulls for side in ("head", "base")
    )

def api(path, method="GET"):
    proc = subprocess.run(
        ["gh", "api", "-X", method, path], capture_output=True,
        text=True, timeout=60)
    if proc.returncode:
        raise RuntimeError("GitHub " + method + " " + path + ": " +
                           proc.stderr.strip()[:250])
    return json.loads(proc.stdout) if proc.stdout.strip() else None

def listing(repo, kind):
    results = []
    for page in range(1, 21):
        sep = "&" if "?" in kind else "?"
        rows = api(f"repos/{repo}/{kind}{sep}per_page=100&page={page}")
        if not isinstance(rows, list):
            raise RuntimeError("BAD_GITHUB_LIST:" + kind)
        results.extend(rows)
        if len(rows) < 100:
            return results
    raise RuntimeError("LIST_EXCEEDS_2000:" + kind)

def write_report(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf8", dir=path.parent, delete=False
    ) as fh:
        json.dump(payload, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
        tmp = fh.name
    os.replace(tmp, path)

def inventory(repo):
    info = api("repos/" + repo)
    if info.get("default_branch") != "main":
        raise RuntimeError("MAIN_REQUIRED:" + repo)
    main = api(f"repos/{repo}/branches/main")["commit"]["sha"]
    pulls = listing(repo, "pulls?state=open")
    branches = listing(repo, "branches")
    result = dict(repo=repo, main_sha=main, eligible=[], preserved=[],
                  deleted=[], failed=[])
    for b in branches:
        name = b["name"]
        if not scoped(name):
            continue
        item = dict(branch=name, head_sha=b["commit"]["sha"])
        if b.get("protected"):
            item["reason"] = "BRANCH_PROTECTED"
        elif name.startswith("ops/") or open_pr_ref(name, pulls, repo):
            item["reason"] = "OPEN_PR_HEAD_OR_BASE"
        else:
            try:
                cmp = api(f"repos/{repo}/compare/main...{quote(name, safe='/')}")
                item["ahead_by"] = cmp["ahead_by"]
                item["behind_by"] = cmp["behind_by"]
                if cmp["ahead_by"] == 0:
                    result["eligible"].append(item)
                    continue
                item["reason"] = "UNMERGED_OR_CHERRY_PICKED"
            except Exception as exc:
                item["reason"] = "COMPARE_BLOCKED"
                item["error"] = str(exc)
        result["preserved"].append(item)
    return result

def prune(entry, report, output):
    repo = entry["repo"]
    main = entry["main_sha"]
    if api(f"repos/{repo}/branches/main")["commit"]["sha"] != main:
        raise RuntimeError("MAIN_MOVED_DURING_AUDIT:" + repo)
    for item in entry["eligible"]:
        name, expected = item["branch"], item["head_sha"]
        try:
            # Fail closed if an open PR appeared, or ref changed since audit.
            if open_pr_ref(name, listing(repo, "pulls?state=open"), repo):
                raise RuntimeError("NEW_OPEN_PR")
            b = api(f"repos/{repo}/branches/{quote(name, safe='/')}")
            if b["commit"]["sha"] != expected or b.get("protected"):
                raise RuntimeError("REF_MOVED_OR_PROTECTED")
            if api(f"repos/{repo}/branches/main")["commit"]["sha"] != main:
                raise RuntimeError("MAIN_MOVED")
            cmp = api(f"repos/{repo}/compare/main...{quote(name, safe='/')}")
            if cmp["ahead_by"] != 0:
                raise RuntimeError("NEW_UNMERGED_COMMIT")
            api(f"repos/{repo}/git/refs/heads/{quote(name, safe='/')}",
                method="DELETE")
            entry["deleted"].append(item)
            print("AXIA_BRANCH_DELETED", repo, name, expected, flush=True)
        except Exception as exc:
            entry["failed"].append({**item, "error": str(exc)})
            print("AXIA_BRANCH_DELETE_BLOCKED", repo, name, str(exc),
                  flush=True)
        finally:
            write_report(output, report)

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", choices=REPOS, action="append")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--out", type=Path)
    a = p.parse_args(argv)
    out = a.out or Path.cwd() / (
        "axia_d04_d08_cleanup_" +
        dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") +
        ".json"
    )
    report = dict(
        schema="axia.day_branch_prune.v1",
        mode="APPLY" if a.apply else "AUDIT",
        scope="D04-D08 / only exact main ancestor and no open PR reference",
        repos=[],
    )
    try:
        for repo in a.repo or REPOS:
            item = inventory(repo)
            report["repos"].append(item)
            write_report(out, report)
            print("AXIA_BRANCH_AUDIT", repo, "eligible",
                  len(item["eligible"]), "preserved",
                  len(item["preserved"]), flush=True)
        if a.apply:
            for entry in report["repos"]:
                prune(entry, report, out)
    except Exception as exc:
        report["fatal"] = str(exc)
        write_report(out, report)
        print("AXIA_BRANCH_FATAL", str(exc), file=sys.stderr)
        return 2
    write_report(out, report)
    failed = sum(len(r["failed"]) for r in report["repos"])
    deleted = sum(len(r["deleted"]) for r in report["repos"])
    print("AXIA_BRANCH_CLEANUP_" + ("APPLY" if a.apply else "AUDIT") +
          "_COMPLETE", "deleted", deleted, "failed", failed, "audit", out)
    return int(failed > 0)

if __name__ == "__main__":
    sys.exit(main())

# Cleanup pass 2: PR #42/#43/#44/#45/#48 verified main ancestors and closed.
