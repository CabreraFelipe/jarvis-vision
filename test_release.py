import json,tempfile,unittest,zipfile,hashlib
from pathlib import Path
from unittest.mock import patch
from manager import Manager
from build_release import build,ROOT
class ReleaseTests(unittest.TestCase):
    def test_remote_flow(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); pkg,feed=build('CabreraFelipe/jarvis-vision',root/'dist'); m=Manager(root/'user')
            marker=m.root/'camera_config.json'; marker.write_text('preserve')
            m.set_feed('https://github.com/CabreraFelipe/jarvis-vision/releases/latest/download/feed.json')
            with patch('manager.fetch',side_effect=[json.dumps(feed).encode(),pkg.read_bytes()]):
                self.assertEqual(m.download(m.check()),feed['version'])
            self.assertEqual(marker.read_text(),'preserve');self.assertEqual(m.verified(feed['version']).name,feed['version'])
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
                manifest=json.loads(z.read('release.json')); manifest['version']='0.4.2'
                for name in manifest['files']:
                    data=z.read('app/'+name)
                    if name=='jarvis_vision.py':data=data.replace(b"VERSION='0.4.3'",b"VERSION='0.4.2'")
                    manifest['files'][name]=hashlib.sha256(data).hexdigest();old.writestr('app/'+name,data)
                old.writestr('release.json',json.dumps(manifest))
            m.install(prior)
            markers={'camera_config.json':b'preferences','modelos/model.bin':b'voice','capturas/photo.jpg':b'photo','yolo11n.pt':b'weights'}
            for name,data in markers.items():
                p=m.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
            with patch('manager.fetch',return_value=pkg.read_bytes()):self.assertEqual(m.download(feed),'0.4.3')
            self.assertEqual(m.rollback(),'0.4.2');self.assertEqual(m.rollback(),'0.4.3')
            for name,data in markers.items():self.assertEqual((m.root/name).read_bytes(),data)
    def test_reproducible_build(self):
        with tempfile.TemporaryDirectory() as d:
            p1,f1=build('CabreraFelipe/jarvis-vision',Path(d)/'one');p2,f2=build('CabreraFelipe/jarvis-vision',Path(d)/'two')
            self.assertEqual(p1.read_bytes(),p2.read_bytes());self.assertEqual(f1,f2)
    def test_corrupt_update_preserves_active(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);pkg,feed=build('CabreraFelipe/jarvis-vision',root/'dist');m=Manager(root/'user');m.install(pkg)
            with patch('manager.fetch',return_value=b'corrupt'):
                with self.assertRaises(ValueError):m.download(dict(feed,version='0.4.4'))
            self.assertEqual(m.state()['active'],feed['version']);m.verified(feed['version'])
if __name__=='__main__':unittest.main()
