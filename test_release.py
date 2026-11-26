import json,tempfile,unittest,zipfile,hashlib
from pathlib import Path
from unittest.mock import patch
from manager import Manager
from build_release import build,ROOT
class ReleaseTests(unittest.TestCase):
    def setUp(self):
        p=patch('manager.verify_artifact'); self.verify=p.start(); self.addCleanup(p.stop)
    def test_remote_flow(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); pkg,feed=build('CabreraFelipe/jarvis-vision',root/'dist'); m=Manager(root/'user')
            marker=m.root/'camera_config.json'; marker.write_text('preserve')
            m.set_feed('https://github.com/CabreraFelipe/jarvis-vision/releases/latest/download/feed.json')
            with patch('manager.fetch',side_effect=[json.dumps(feed).encode(),pkg.read_bytes()]):
                self.assertEqual(m.download(m.check()),feed['version'])
            self.assertEqual(self.verify.call_count,2);self.assertEqual(marker.read_text(),'preserve');self.assertEqual(m.verified(feed['version']).name,feed['version'])
            with patch('manager.fetch',return_value=json.dumps(feed).encode()):self.assertIsNone(m.check())
    def test_corrupt_download(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); pkg,feed=build('CabreraFelipe/jarvis-vision',root/'dist');m=Manager(root/'user')
            with patch('manager.fetch',return_value=b'corrupt'):
                with self.assertRaises(ValueError):m.download(feed)
            self.assertIsNone(m.state()['active'])
    def test_upgrade_rollback_and_user_data(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); pkg,feed=build('CabreraFelipe/jarvis-vision',root/'dist'); m=Manager(root/'user')
            prior=root/'prior.zip'
            with zipfile.ZipFile(pkg) as z, zipfile.ZipFile(prior,'w') as old:
                manifest=json.loads(z.read('release.json')); current=feed['version']; parts=list(map(int,current.split('.'))); prior_version='0.4.4' if current=='0.5.0' else ('.'.join(map(str,[parts[0],parts[1],parts[2]-1])) if parts[2] else '.'.join(map(str,[parts[0],parts[1]-1,0]))); manifest['version']=prior_version
                for name in manifest['files']:
                    data=z.read('app/'+name)
                    if name=='jarvis_vision.py':data=data.replace(f"VERSION='{current}'".encode(),f"VERSION='{prior_version}'".encode())
                    manifest['files'][name]=hashlib.sha256(data).hexdigest();old.writestr('app/'+name,data)
                old.writestr('release.json',json.dumps(manifest))
            m.install(prior)
            markers={'camera_config.json':b'preferences','modelos/model.bin':b'voice','capturas/photo.jpg':b'photo','yolo11n.pt':b'weights','jarvis_memory.sqlite3':b'local memory bytes','speech_input.json':b'input prefs'}
            for name,data in markers.items():
                p=m.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
            with patch('manager.fetch',return_value=pkg.read_bytes()):self.assertEqual(m.download(feed),current)
            self.assertEqual(m.rollback(),prior_version);self.assertEqual(m.rollback(),current)
            for name,data in markers.items():self.assertEqual((m.root/name).read_bytes(),data)
    def test_reproducible_build(self):
        with tempfile.TemporaryDirectory() as d:
            p1,f1=build('CabreraFelipe/jarvis-vision',Path(d)/'one');p2,f2=build('CabreraFelipe/jarvis-vision',Path(d)/'two')
            self.assertEqual(p1.read_bytes(),p2.read_bytes());self.assertEqual(f1,f2)
    def test_corrupt_update_preserves_active(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);pkg,feed=build('CabreraFelipe/jarvis-vision',root/'dist');m=Manager(root/'user');m.install(pkg)
            with patch('manager.fetch',return_value=b'corrupt'):
                with self.assertRaises(ValueError):m.download(feed)
            self.assertEqual(m.state()['active'],feed['version']);m.verified(feed['version'])
if __name__=='__main__':unittest.main()
