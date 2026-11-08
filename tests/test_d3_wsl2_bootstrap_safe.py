"""D3 bootstrap regression tests. Mock GitHub with throwaway local Git remotes.

Runs without ROS / Gazebo / GitHub authentication; no real user checkout touched.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parent.parent / 'scripts/d3_wsl2_bootstrap_safe.sh'
BRANCH = 'feat/d3-intrusion-scan-stop-demo-20261108'


def git(*args, cwd=None):
    return subprocess.run(['git', *map(str,args)], cwd=cwd, text=True, capture_output=True, check=True).stdout.strip()


class D3BootstrapTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='axia-d3-regress-')
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name) / 'owner-home'
        self.home.mkdir()
        self.src = Path(self.tmp.name) / 'source'
        self.src.mkdir()
        git('init', '-q', '-b', 'old-branch', cwd=self.src)
        git('config', 'user.name', 'D3 Test', cwd=self.src)
        git('config', 'user.email', 'd3@example.invalid', cwd=self.src)
        (self.src/'readme').write_text('old branch\n')
        git('add', '.', cwd=self.src)
        git('commit', '-q', '-m', 'old branch', cwd=self.src)
        git('switch', '-q', '-c', BRANCH, cwd=self.src)
        marker = self.src/'training/d03/d3_demo/scripts/d3_wsl2_prepare_once.sh'
        marker.parent.mkdir(parents=True)
        marker.write_text('#!/usr/bin/env bash\nexit 0\n')
        git('add', '.', cwd=self.src)
        git('commit', '-q', '-m', 'D3 pinned feature', cwd=self.src)
        self.pin = git('rev-parse', 'HEAD', cwd=self.src)
        self.remote = Path(self.tmp.name) / 'remote.git'
        git('clone', '-q', '--bare', self.src, self.remote)
        self.work = self.home/'axia_d3_classroom'
        self.root = self.work/'axia-d3-instructor'
        self.env = os.environ.copy()
        self.env.update(HOME=str(self.home), AXIA_D3_TEST_MODE='1',
                        AXIA_D3_TEST_REMOTE=str(self.remote),
                        AXIA_D3_TEST_BRANCH=BRANCH, AXIA_D3_TEST_SHA=self.pin)

    def run_bootstrap(self, env=None):
        return subprocess.run(['bash', str(SCRIPT), '--checkout-only'],
                              text=True, capture_output=True, env=env or self.env, timeout=15)

    def clone_root(self, branch=BRANCH):
        self.work.mkdir(parents=True, exist_ok=True)
        git('clone', '-q', '-b', branch, self.remote, self.root)

    def resolved_root(self):
        envf=self.work/'d3_checkout.env'
        self.assertTrue(envf.is_file())
        script=f'source {str(envf)!r}; printf "%s" "$AXIA_D3_REPO_ROOT"'
        return Path(subprocess.check_output(['bash','-c',script],text=True).strip())

    def assert_pinned(self, checkout):
        self.assertEqual(git('rev-parse','HEAD',cwd=checkout), self.pin)
        self.assertEqual(git('branch','--show-current',cwd=checkout), BRANCH)
        self.assertTrue((checkout/'training/d03/d3_demo/scripts/d3_wsl2_prepare_once.sh').is_file())

    def test_missing_checkout_clones_pinned_branch_and_persists_launcher(self):
        r=self.run_bootstrap()
        self.assertEqual(r.returncode,0,r.stderr+r.stdout)
        self.assertEqual(self.resolved_root(),self.root)
        self.assert_pinned(self.root)
        self.assertTrue((self.work/'axia-d3-prepare.sh').is_file())

    def test_existing_wrong_branch_is_preserved_and_new_checkout_is_used(self):
        self.clone_root('old-branch')
        before=git('rev-parse','HEAD',cwd=self.root)
        r=self.run_bootstrap()
        self.assertEqual(r.returncode,0,r.stderr+r.stdout)
        self.assertEqual(git('branch','--show-current',cwd=self.root),'old-branch')
        self.assertEqual(git('rev-parse','HEAD',cwd=self.root),before)
        other=self.resolved_root()
        self.assertNotEqual(other,self.root)
        self.assert_pinned(other)

    def test_existing_dirty_target_is_preserved(self):
        self.clone_root()
        (self.root/'uncommitted.txt').write_text('do not discard\n')
        r=self.run_bootstrap()
        self.assertEqual(r.returncode,0,r.stderr+r.stdout)
        self.assertTrue((self.root/'uncommitted.txt').is_file())
        self.assertNotEqual(self.resolved_root(),self.root)
        self.assert_pinned(self.resolved_root())

    def test_existing_nonrepo_directory_is_preserved(self):
        self.root.mkdir(parents=True)
        (self.root/'my_notes.txt').write_text('do not touch')
        r=self.run_bootstrap()
        self.assertEqual(r.returncode,0,r.stderr+r.stdout)
        self.assertEqual((self.root/'my_notes.txt').read_text(),'do not touch')
        self.assert_pinned(self.resolved_root())

    def test_wrong_origin_is_preserved(self):
        self.clone_root()
        git('remote','set-url','origin','https://example.invalid/other.git',cwd=self.root)
        r=self.run_bootstrap()
        self.assertEqual(r.returncode,0,r.stderr+r.stdout)
        self.assertEqual(git('remote','get-url','origin',cwd=self.root),'https://example.invalid/other.git')
        self.assert_pinned(self.resolved_root())

    def test_correct_clean_checkout_is_reused_idempotently(self):
        self.clone_root()
        r1=self.run_bootstrap()
        r2=self.run_bootstrap()
        self.assertEqual(r1.returncode,0,r1.stderr+r1.stdout)
        self.assertEqual(r2.returncode,0,r2.stderr+r2.stdout)
        self.assertEqual(self.resolved_root(),self.root)
        self.assert_pinned(self.root)

    def test_pin_mismatch_blocks_without_moving_head(self):
        self.clone_root()
        before=git('rev-parse','HEAD',cwd=self.root)
        env=dict(self.env, AXIA_D3_TEST_SHA='0'*40)
        r=self.run_bootstrap(env)
        self.assertNotEqual(r.returncode,0)
        self.assertIn('PIN_MISMATCH',r.stdout+r.stderr)
        self.assertEqual(git('rev-parse','HEAD',cwd=self.root),before)

    def test_child_script_failure_does_not_kill_interactive_parent(self):
        env=dict(self.env, AXIA_D3_TEST_SHA='0'*40)
        cmd=f'bash {str(SCRIPT)!r} --checkout-only; echo OWNER_TERMINAL_SURVIVED'
        r=subprocess.run(['bash','-c',cmd],env=env,capture_output=True,text=True,timeout=15)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn('OWNER_TERMINAL_SURVIVED',r.stdout)

    def test_environment_symlink_is_not_overwritten(self):
        self.work.mkdir(parents=True)
        target=self.home/'sentinel'
        target.write_text('KEEP_MINE\n')
        (self.work/'d3_checkout.env').symlink_to(target)
        r=self.run_bootstrap()
        self.assertNotEqual(r.returncode,0)
        self.assertEqual(target.read_text(),'KEEP_MINE\n')

    def test_workdir_symlink_is_not_followed(self):
        target=self.home/'special'
        target.mkdir()
        self.work.symlink_to(target, target_is_directory=True)
        r=self.run_bootstrap()
        self.assertNotEqual(r.returncode,0)
        self.assertFalse((target/'d3_checkout.env').exists())

    def test_shell_script_syntax_and_no_destructive_reset(self):
        self.assertTrue(SCRIPT.exists())
        subprocess.run(['bash','-n',str(SCRIPT)],check=True)
        code=SCRIPT.read_text()
        self.assertNotIn('reset --hard',code)
        self.assertNotIn('clean -fd',code)
        self.assertNotIn('rm -rf',code)


if __name__ == '__main__':
    unittest.main()
