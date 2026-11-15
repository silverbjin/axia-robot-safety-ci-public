#!/usr/bin/env python3
"""Owner-only instructor D04-D08 closed/superseded branch cleanup.

NO private GitHub Actions. Requires existing 'gh auth login' access to the
private instructor repository. Default audit, --apply deletes only if
historical source PR is closed, successor PR is in main, original branch
HEAD unchanged, no open PR depends on it, and required code survives main.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import quote

REPO = "silverbjin/axia-robot-safety-instructor"
# (original PR, successor merged PR); None means original was a no-PR plan.
PROVENANCE = {
 "docs/d05-3h-live-teaching-script-20261113": (130, 178),
 "docs/d05-lecture-plan-20261112": (None, 178),
 "docs/d06-classroom-materials-20261113": (142, 179),
 "docs/d07-classroom-20261114": (159, 180),
 "feature/d08-online-integration-20261110": (89, 181),
 "fix/d05-instructor-live-valid-distance-before-fault-20261113": (126, 126),
 "plan/d05-live-demo-two-changes-20261113": (123, 124),
 "release/d05-instructor-integration-20261113": (124, 124),
}
# PR-less planning branch: two original docs survive byte-identical; demo guide
# was intentionally superseded by the later VALID-before-fault version.
NO_PR_BRANCH = "docs/d05-lecture-plan-20261112"
NO_PR_HEAD = "2ca47804b44314c47130e7ea0b7b7b91c9f61d95"
RETAINED_BLOBS = {
 "training/block_B/instructor/D05_LECTURE_PLAN_AND_SCRIPT_20261113_KO.md":
   "a8085cdb5e7322a6444630b4b1266588620815bf",
 "training/block_B/instructor/D05_SOLUTION_GUIDE_KO.md":
   "d54f1ef1b3e788cf8d6dbdc22a18678cc3f8eea2",
}
def api(path, method="GET"):
    p = subprocess.run(["gh","api","-X",method,path],
                       capture_output=True,text=True,timeout=60)
    if p.returncode:
        raise RuntimeError(path+" "+p.stderr.strip()[:250])
    return json.loads(p.stdout) if p.stdout.strip() else None

def open_prs():
    result=[]
    for i in range(1,21):
        x=api(f"repos/{REPO}/pulls?state=open&per_page=100&page={i}")
        result.extend(x)
        if len(x)<100:return result
    raise RuntimeError("OPEN_PR_LIST_TRUNCATED")

def in_open_pr(name):
    for pr in open_prs():
        for side in ("head","base"):
            p=pr.get(side) or {}
            if p.get("ref")==name and (p.get("repo") or {}).get("full_name")==REPO:
                return True
    return False

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply",action="store_true")
    parser.add_argument("--out",type=Path,default=Path("axia_d04_d08_instructor_superseded.json"))
    args=parser.parse_args(argv)
    main_sha=api(f"repos/{REPO}/branches/main")["commit"]["sha"]
    result={"schema":"axia.instructor_superseded.v1","repo":REPO,
            "main_sha":main_sha,"mode":"APPLY" if args.apply else "AUDIT",
            "deleted":[],"eligible":[],"preserved":[]}
    def persist():
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    for name,(original,successor) in PROVENANCE.items():
        entry={"branch":name,"source_pr":original,"merged_successor_pr":successor}
        try:
            if in_open_pr(name):
                raise RuntimeError("OPEN_PR_HEAD_OR_BASE")
            b=api(f"repos/{REPO}/branches/{quote(name,safe='/')}")
            entry["head_sha"]=b["commit"]["sha"]
            if b.get("protected"):
                raise RuntimeError("PROTECTED")
            if original is None:
                if name!=NO_PR_BRANCH or entry["head_sha"]!=NO_PR_HEAD:
                    raise RuntimeError("UNKNOWN_PLAN_SHA")
                for path,expected in RETAINED_BLOBS.items():
                    c=api(f"repos/{REPO}/contents/{path}?ref=main")
                    if c["sha"]!=expected:
                        raise RuntimeError("OLD_PLAN_FILE_NOT_RETAINED:"+path)
                # A newer instructor demo guide must exist, replacing old plan.
                api(f"repos/{REPO}/contents/training/block_B/instructor/D05_INSTRUCTOR_DEMO_GUIDE_KO.md?ref=main")
            else:
                pr=api(f"repos/{REPO}/pulls/{original}")
                if pr["state"]!="closed" or pr["head"]["ref"]!=name:
                    raise RuntimeError("SOURCE_PR_OPEN_OR_REF_CHANGED")
                if (pr["head"]["repo"] or {}).get("full_name")!=REPO or pr["head"]["sha"]!=entry["head_sha"]:
                    raise RuntimeError("SOURCE_PR_SHA_MISMATCH")
            done=api(f"repos/{REPO}/pulls/{successor}")
            if not done["merged"] or not done["merge_commit_sha"]:
                raise RuntimeError("SUCCESSOR_NOT_MERGED")
            c=api(f"repos/{REPO}/compare/{done['merge_commit_sha']}...main")
            if c["behind_by"]!=0:
                raise RuntimeError("SUCCESSOR_NOT_ANCESTOR_OF_MAIN")
            if api(f"repos/{REPO}/branches/main")["commit"]["sha"]!=main_sha:
                raise RuntimeError("MAIN_MOVED")
            entry["main_successor_sha"]=done["merge_commit_sha"]
            if args.apply:
                # Double-check the ref, then delete by exact existing name.
                b2=api(f"repos/{REPO}/branches/{quote(name,safe='/')}")
                if b2["commit"]["sha"]!=entry["head_sha"]:
                    raise RuntimeError("BRANCH_MOVED")
                api(f"repos/{REPO}/git/refs/heads/{quote(name,safe='/')}",method="DELETE")
                result["deleted"].append(entry)
                print("AXIA_INSTRUCTOR_SUPERSEDED_DELETED",name,entry["head_sha"],flush=True)
            else:
                result["eligible"].append(entry)
                print("AXIA_INSTRUCTOR_SUPERSEDED_AUDIT_ONLY",name,flush=True)
        except Exception as exc:
            result["preserved"].append({**entry,"reason":str(exc)})
            print("AXIA_INSTRUCTOR_SUPERSEDED_PRESERVED",name,str(exc),flush=True)
        persist()
    print("AXIA_INSTRUCTOR_SUPERSEDED_RESULT", "deleted",len(result["deleted"]),
          "eligible",len(result["eligible"]),"preserved",len(result["preserved"]),
          "evidence",args.out,flush=True)
    return int(bool(result["preserved"]))

if __name__=="__main__":
    sys.exit(main())
