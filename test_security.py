import json,tempfile,unittest,subprocess
from pathlib import Path
from unittest.mock import patch
from manager import Manager, TRUSTED_FEED, TRUSTED_REPO, TRUSTED_WORKFLOW, verify_artifact
from build_release import build

class SecurityTests(unittest.TestCase):
    def setUp(self):
        d=tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
        self.root=Path(d.name); self.pkg,self.feed=build(TRUSTED_REPO,self.root/'dist')
        self.m=Manager(self.root/'user'); self.m.set_feed(TRUSTED_FEED)
    def test_reject_wrong_feed(self):
        with self.assertRaises(ValueError): self.m.set_feed('https://example.com/feed.json')
        self.assertEqual(self.m.feed(),TRUSTED_FEED)
    def test_unsigned_feed(self):
        with patch('manager.fetch',return_value=json.dumps(self.feed).encode()), patch('manager.verify_artifact',side_effect=ValueError('bad')):
            with self.assertRaises(ValueError): self.m.check()
        self.assertIsNone(self.m.state()['active'])
    def test_signed_feed_wrong_url(self):
        with patch('manager.fetch',return_value=json.dumps(dict(self.feed,url='https://example.com/a.zip')).encode()), patch('manager.verify_artifact'):
            with self.assertRaises(ValueError): self.m.check()
    def test_unsigned_zip(self):
        with patch('manager.fetch',return_value=self.pkg.read_bytes()), patch('manager.verify_artifact',side_effect=ValueError('bad')):
            with self.assertRaises(ValueError): self.m.download(self.feed)
        self.assertIsNone(self.m.state()['active'])
    def test_unsigned_local_zip(self):
        with patch('manager.verify_artifact',side_effect=ValueError('bad')):
            with self.assertRaises(ValueError): self.m.install_local(self.pkg)
        self.assertIsNone(self.m.state()['active'])
    def test_missing_cli(self):
        with patch('manager.shutil.which',return_value=None):
            with self.assertRaises(ValueError): verify_artifact(self.pkg)
    def test_cli_failure(self):
        with patch('manager.shutil.which',return_value=str(self.root/'gh')), patch('manager.subprocess.run',return_value=subprocess.CompletedProcess([],1)) as run:
            with self.assertRaises(ValueError): verify_artifact(self.pkg)
            args=run.call_args.args[0]
            self.assertIn(TRUSTED_REPO,args); self.assertIn(TRUSTED_WORKFLOW,args)
            self.assertIn('refs/heads/main',args); self.assertIn('--deny-self-hosted-runners',args)
    def test_cli_timeout(self):
        with patch('manager.shutil.which',return_value=str(self.root/'gh')), patch('manager.subprocess.run',side_effect=subprocess.TimeoutExpired('gh',90)):
            with self.assertRaises(ValueError): verify_artifact(self.pkg)
    def test_cli_success(self):
        with patch('manager.shutil.which',return_value=str(self.root/'gh')), patch('manager.subprocess.run',return_value=subprocess.CompletedProcess([],0)):
            verify_artifact(self.pkg)
    def test_high_water_rejects_old_feed(self):
        from manager import atomic_json
        atomic_json(self.m.statefile,{'active':'0.4.2','previous':None,'highest':'0.4.4'})
        with patch('manager.fetch',return_value=json.dumps(self.feed).encode()),patch('manager.verify_artifact'):
            self.assertIsNone(self.m.check())
        with self.assertRaises(ValueError): self.m.install(self.pkg)
    def test_offline_leaves_installed_version(self):
        self.m.install(self.pkg)
        with patch('manager.fetch',side_effect=OSError('offline')):
            with self.assertRaises(OSError): self.m.check()
        self.assertEqual(self.m.verified(self.feed['version']).name,self.feed['version'])

if __name__=='__main__': unittest.main()
