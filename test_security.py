import json,tempfile,unittest,subprocess
from pathlib import Path
from unittest.mock import patch
from manager import Manager, TRUSTED_FEED, TRUSTED_REPO, TRUSTED_WORKFLOW, verify_artifact, migrate_manager
from build_release import build

class SecurityTests(unittest.TestCase):
    def setUp(self):
        d=tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
        self.root=Path(d.name); self.pkg,self.feed=build(TRUSTED_REPO,self.root/'dist')
        self.m=Manager(self.root/'user'); self.m.set_feed(TRUSTED_FEED)
    def test_instance_contention_does_not_unlock(self):
        from manager import instance_lock,InstanceBusy,request_focus,consume_focus
        with instance_lock(self.m.store):
            with self.assertRaises(InstanceBusy):
                with instance_lock(self.m.store): pass
            self.assertTrue(request_focus(self.m.store))
            self.assertTrue(consume_focus(self.m.store))
            self.assertFalse(consume_focus(self.m.store))
            with self.assertRaises(InstanceBusy):
                with instance_lock(self.m.store): pass
        with instance_lock(self.m.store): pass
    def test_expired_focus_signal(self):
        import os,time
        from manager import request_focus,consume_focus
        self.assertTrue(request_focus(self.m.store))
        p=self.m.store/'focus-request.json'; old=time.time()-30
        os.utime(p,(old,old))
        self.assertFalse(consume_focus(self.m.store));self.assertFalse(p.exists())
    def test_focus_only_changes_signal(self):
        from manager import request_focus,consume_focus
        self.m.install(self.pkg); before=self.m.statefile.read_bytes()
        self.assertTrue(request_focus(self.m.store));self.assertTrue(consume_focus(self.m.store))
        self.assertEqual(self.m.statefile.read_bytes(),before)
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
        with patch('manager.shutil.which',return_value=str(self.root/'gh')), patch('manager.subprocess.run',side_effect=[subprocess.CompletedProcess([],0,stdout=b'gh version 2.102.0 (2026-09-30)'),subprocess.CompletedProcess([],1)]) as run:
            with self.assertRaises(ValueError): verify_artifact(self.pkg)
            args=run.call_args.args[0]
            self.assertIn(TRUSTED_REPO,args); self.assertIn(TRUSTED_WORKFLOW,args)
            self.assertIn('refs/heads/main',args); self.assertIn('--deny-self-hosted-runners',args)
    def test_cli_timeout(self):
        with patch('manager.shutil.which',return_value=str(self.root/'gh')), patch('manager.subprocess.run',side_effect=subprocess.TimeoutExpired('gh',90)):
            with self.assertRaises(ValueError): verify_artifact(self.pkg)
    def test_cli_success(self):
        with patch('manager.shutil.which',return_value=str(self.root/'gh')), patch('manager.subprocess.run',side_effect=[subprocess.CompletedProcess([],0,stdout=b'gh version 2.102.0 (2026-09-30)'),subprocess.CompletedProcess([],0)]):
            verify_artifact(self.pkg)
    def test_quiet_process_options(self):
        import os
        from manager import quiet_process_options
        expected={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {}
        self.assertEqual(quiet_process_options(),expected)
    def test_outdated_cli(self):
        with patch('manager.shutil.which',return_value=str(self.root/'gh')), patch('manager.subprocess.run',return_value=subprocess.CompletedProcess([],0,stdout=b'gh version 2.101.0 (2026-09-29)')) as run:
            with self.assertRaisesRegex(ValueError,'2.102.0'): verify_artifact(self.pkg)
            self.assertEqual(run.call_count,1)
    def prepare_migration(self):
        self.m.install(self.pkg)
        target=self.m.store/'manager.py'; target.write_bytes(b'# original manager')
        marker=self.m.root/'camera_config.json'; marker.write_bytes(b'preferences')
        source=self.root/'candidate.py'; source.write_bytes(b'# new manager')
        return target,marker,source
    def test_migration_preserves_state_and_backup(self):
        target,marker,source=self.prepare_migration()
        state=self.m.statefile.read_bytes(); feed=self.m.feedfile.read_bytes()
        with patch('manager.verify_artifact') as verify:
            self.assertTrue(migrate_manager(self.m.root,source))
            self.assertFalse(migrate_manager(self.m.root,source))
            self.assertEqual(verify.call_count,2)
        self.assertEqual(target.read_bytes(),source.read_bytes())
        self.assertEqual(marker.read_bytes(),b'preferences')
        self.assertEqual(self.m.statefile.read_bytes(),state)
        self.assertEqual(self.m.feedfile.read_bytes(),feed)
        self.assertEqual([p.read_bytes() for p in self.m.store.glob('manager-backup-*.py')],[b'# original manager'])
    def test_migration_rejects_unsigned(self):
        target,marker,source=self.prepare_migration()
        with patch('manager.verify_artifact',side_effect=ValueError('bad')):
            with self.assertRaises(ValueError): migrate_manager(self.m.root,source)
        self.assertEqual(target.read_bytes(),b'# original manager')
        self.assertEqual(marker.read_bytes(),b'preferences')
    def test_migration_failed_replace(self):
        target,marker,source=self.prepare_migration()
        with patch('manager.verify_artifact'), patch('manager.os.replace',side_effect=OSError('blocked')):
            with self.assertRaises(OSError): migrate_manager(self.m.root,source)
        self.assertEqual(target.read_bytes(),b'# original manager')
        self.assertEqual(marker.read_bytes(),b'preferences')
    def test_migration_rejects_other_directory(self):
        with self.assertRaises(ValueError): migrate_manager(self.root,self.pkg)
        self.assertFalse((self.root/'.jarvis').exists())
    def test_high_water_rejects_old_feed(self):
        from manager import atomic_json
        parts=list(map(int,self.feed['version'].split('.')))
        highest='.'.join(map(str,[parts[0],parts[1],parts[2]+1]))
        atomic_json(self.m.statefile,{'active':self.feed['version'],'previous':None,'highest':highest})
        with patch('manager.fetch',return_value=json.dumps(self.feed).encode()),patch('manager.verify_artifact'):
            self.assertIsNone(self.m.check())
        with self.assertRaises(ValueError): self.m.install(self.pkg)
    def test_offline_leaves_installed_version(self):
        self.m.install(self.pkg)
        with patch('manager.fetch',side_effect=OSError('offline')):
            with self.assertRaises(OSError): self.m.check()
        self.assertEqual(self.m.verified(self.feed['version']).name,self.feed['version'])

if __name__=='__main__': unittest.main()
