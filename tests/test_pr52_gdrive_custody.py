"""L0 only: independent secure Drive custody file handling; NO real credentials."""
from pathlib import Path
import importlib.util
import os
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
spec=importlib.util.spec_from_file_location("pr52_custody",ROOT/"scripts/pr52_gdrive_custody.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

ENV={"CI":"true","GITHUB_ACTIONS":"true",
     "GITHUB_REPOSITORY":"silverbjin/axia-robot-safety-ci-public",
     "GITHUB_REF":"refs/heads/feat/secure-instructor-cloud-bridge",
     "GITHUB_ACTOR":"silverbjin","GITHUB_RUN_ID":"423001","GITHUB_RUN_ATTEMPT":"1"}


class CustodySecurityTest(unittest.TestCase):
    def test_git_run_context_and_exact_remote_scope(self):
        self.assertEqual(mod.remote_object(ENV,mod.PIN),
             "axia_drive:AXIA-P1-T08-private-evidence/"+mod.PIN+
             "/run-423001-attempt-1/g00-evidence.tar.gz.age")
        for k,v in [("GITHUB_ACTOR","untrusted"),("GITHUB_REPOSITORY","fork/repo"),
                    ("GITHUB_REF","refs/heads/main"),("GITHUB_ACTIONS","false")]:
            obj=dict(ENV);obj[k]=v
            with self.subTest(k=k),self.assertRaises(mod.CustodyBlocked):
                mod.remote_object(obj,mod.PIN)
        with self.assertRaises(mod.CustodyBlocked):
            mod.remote_object(ENV,"0"*39)

    def test_symlinks_are_not_archived_or_dereferenced(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root);runs=[]
            for i in range(3):
                r=p/f"run{i}";r.mkdir();(r/"receipt.json").write_text('{"status":"TEST"}')
                runs.append(r)
            tar=p/"archive.tar.gz"
            self.assertEqual(mod.build_archive(runs,tar,{"test":True}),3)
            (runs[1]/"escape").symlink_to("/etc/passwd")
            with self.assertRaises(mod.CustodyBlocked) as cm:
                mod.build_archive(runs,tar,{"test":True})
            self.assertEqual(cm.exception.code,"ORIGINAL_SYMLINK_DENIED")

    def test_missing_credentials_and_quota_are_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            for secrets in ({},{'AXIA_GDRIVE_RCLONE_CONFIG_B64':'garbage',
                           'AXIA_GDRIVE_AGE_RECIPIENT':'age1invalid'}):
                with self.assertRaises(mod.CustodyBlocked):
                    mod.configure(p,secrets)
        self.assertGreater(mod.MARGIN,64*1024*1024)

    def test_never_publish_original_or_age_secret(self):
        src=(ROOT/"scripts/pr52_gdrive_custody.py").read_text()
        self.assertIn('original_g00_rechecked',src)
        self.assertIn("R06_RAW_CUSTODY_REVIEW_PENDING",src)
        self.assertIn('"raw_restored":False',src)
        self.assertIn('"owner_private_key_in_ci":False',src)
        self.assertIn("GITHUB_RUN_ATTEMPT",src)
        self.assertNotIn("print(secret)",src)
        self.assertNotIn("print(decoded)",src)
        self.assertIn('encrypted=temp/"probe.txt.age"',src)
        self.assertIn('"age_encrypted_canary_roundtrip":True',src)
        self.assertNotIn('"copyto",str(data),key',src)
        self.assertNotIn("upload-artifact",src)
        self.assertNotIn("rclone sync",src)


if __name__=="__main__":
    unittest.main()
