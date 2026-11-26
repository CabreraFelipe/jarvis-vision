import unittest, tempfile, time, json, io, threading
from pathlib import Path
from unittest.mock import patch
import numpy as np
import cv2
import camera, vision

class FakeCap:
    instances=[]
    limit=(640,480)
    def __init__(self,index,backend):
        self.index=index; self.backend=backend; self.width=640; self.height=480; self.released=False; self.instances.append(self)
    def isOpened(self): return self.index in (0,1)
    def set(self,p,v):
        if p==cv2.CAP_PROP_FRAME_WIDTH: self.width=int(v)
        if p==cv2.CAP_PROP_FRAME_HEIGHT: self.height=int(v)
        return True
    def get(self,p): return cv2.VideoWriter_fourcc(*'MJPG')
    def read(self):
        time.sleep(.005)
        w=min(self.width,self.limit[0]); h=min(self.height,self.limit[1]); return True,np.full((h,w,3),self.index,dtype=np.uint8)
    def release(self): self.released=True

class Tests(unittest.TestCase):
    def setUp(self): FakeCap.instances=[]; FakeCap.limit=(640,480)
    def test_legacy_config(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'camera_config.json'; p.write_text('{"camera":1}')
            a,b,profiles=camera.load_config(p); self.assertEqual((a['index'],b['index']),(1,0)); self.assertEqual(a['resolution'],'Automática')
            a.update(resolution='1280x720',fps=15,format='MJPG'); camera.save_config(p,a,b,{'1':a}); self.assertEqual(camera.load_config(p),(a,b,{'1':a}))
    def test_invalid_config(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'c.json'; p.write_text('{"primary":{"index":true,"resolution":[],"fps":60.0}}'); a,b,_=camera.load_config(p); self.assertEqual(a,camera.normalize({}))
    @patch('camera.cv2.VideoCapture',FakeCap)
    def test_auto_vga(self):
        cap,frame=camera.open_camera(camera.normalize({})); self.assertEqual(frame.shape[:2],(480,640)); cap.release(); self.assertTrue(all(c.released for c in FakeCap.instances))
    @patch('camera.cv2.VideoCapture',FakeCap)
    def test_auto_hd(self):
        FakeCap.limit=(1280,720); cap,frame=camera.open_camera(camera.normalize({})); self.assertEqual(frame.shape[:2],(720,1280)); cap.release()
    @patch('camera.cv2.VideoCapture',FakeCap)
    def test_auto_full_hd(self):
        FakeCap.limit=(1920,1080); cap,frame=camera.open_camera(camera.normalize({})); self.assertEqual(frame.shape[:2],(1080,1920)); self.assertEqual(len(FakeCap.instances),1); cap.release()
    @patch('camera.cv2.VideoCapture',FakeCap)
    def test_explicit_reports_actual(self):
        cap,frame=camera.open_camera(camera.normalize({'resolution':'1920x1080'})); self.assertEqual(frame.shape[:2],(480,640)); cap.release()
    @patch('camera.cv2.VideoCapture',FakeCap)
    def test_bad_index(self):
        with self.assertRaises(RuntimeError): camera.open_camera(camera.normalize({'index':3}))
        self.assertTrue(all(c.released for c in FakeCap.instances))
    @patch('camera.cv2.VideoCapture',FakeCap)
    def test_cancel(self):
        stop=threading.Event(); stop.set()
        with self.assertRaises(RuntimeError): camera.open_camera(camera.normalize({}),stop)
        self.assertEqual(FakeCap.instances,[])
    @patch('camera.cv2.VideoCapture',FakeCap)
    def test_two_sessions(self):
        sessions=[camera.Capture(camera.normalize({'index':i,'resolution':'640x480'})) for i in (0,1)]
        try:
            deadline=time.monotonic()+3
            while time.monotonic()<deadline and not all(s.snapshot()[5] for s in sessions): time.sleep(.01)
            for i,s in enumerate(sessions): self.assertEqual(int(s.snapshot()[0][0,0,0]),i)
            sessions[0].stop.set(); sessions[0].thread.join(2); self.assertIsNone(sessions[0].snapshot()[0]); self.assertTrue(sessions[1].snapshot()[5])
        finally:
            for s in sessions: s.stop.set(); s.thread.join(2)
        self.assertTrue(all(c.released for c in FakeCap.instances))
    def test_vision_local(self):
        class Opener:
            def open(self,req,timeout):
                assert req.full_url=='http://127.0.0.1:11434/api/chat'; payload=json.loads(req.data); assert payload['messages'][-1]['images']; return io.BytesIO(b'{"message":{"content":"respuesta"}}')
        with patch('vision.urllib.request.build_opener',return_value=Opener()): self.assertEqual(vision.ask_vision(np.zeros((16,16,3),dtype=np.uint8),'hola'),'respuesta')

if __name__=='__main__': unittest.main(verbosity=2)
