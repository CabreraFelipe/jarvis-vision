import unittest,threading
from unittest.mock import patch
import numpy as np
import cv2
import camera
from jarvis_vision import preview_frame
from test_jarvis import FakeCap

class BackendCap(FakeCap):
    limit=(1920,1080)
    instances=[]
    def read(self):
        return True,np.zeros((min(self.height,1080),min(self.width,1920),3),np.uint8)

class PerformanceTests(unittest.TestCase):
    def setUp(self): BackendCap.instances=[]
    @patch('camera.cv2.VideoCapture',BackendCap)
    def test_full_hd_fast_msmf(self):
        with patch('camera.measure_capture',side_effect=lambda cap,frame,stop:(frame,5 if cap.backend==cv2.CAP_DSHOW else 30)):
            cap,frame=camera.open_camera(camera.normalize({}))
        self.assertEqual(cap.backend,cv2.CAP_MSMF)
        self.assertEqual(frame.shape[:2],(1080,1920))
        cap.release();self.assertTrue(all(c.released for c in BackendCap.instances))
    @patch('camera.cv2.VideoCapture',BackendCap)
    def test_balanced_downshift(self):
        with patch('camera.measure_capture',side_effect=lambda cap,frame,stop:(frame,5 if frame.shape[0]>720 else 30)):
            cap,frame=camera.open_camera(camera.normalize({}))
        self.assertEqual(frame.shape[:2],(720,1280));cap.release()
    @patch('camera.cv2.VideoCapture',BackendCap)
    def test_quality_retains_full_hd(self):
        with patch('camera.measure_capture',side_effect=lambda cap,frame,stop:(frame,5 if frame.shape[0]>720 else 30)):
            cap,frame=camera.open_camera(camera.normalize({'resolution':'Auto calidad'}))
        self.assertEqual(frame.shape[:2],(1080,1920));cap.release()
    @patch('camera.cv2.VideoCapture',BackendCap)
    def test_manual_backend(self):
        with patch('camera.measure_capture',side_effect=lambda cap,frame,stop:(frame,30)):
            cap,frame=camera.open_camera(camera.normalize({'backend':'Media Foundation','resolution':'1920x1080'}))
        self.assertEqual(cap.backend,cv2.CAP_MSMF);cap.release()
        self.assertTrue(all(c.backend==cv2.CAP_MSMF for c in BackendCap.instances))
    def test_preview_preserves_original(self):
        frame=np.ones((1080,1920,3),np.uint8)
        display,scale=preview_frame(frame,640,480)
        self.assertEqual(display.shape[:2],(360,640));self.assertAlmostEqual(scale,1/3)
        display[:]=0;self.assertTrue(np.all(frame==1))
    def test_legacy_defaults(self):
        self.assertEqual(camera.normalize({'fps':30})['backend'],'Automático')
    def test_cancel_probe(self):
        stop=threading.Event();stop.set()
        frame=np.zeros((2,2,3),np.uint8)
        class NoRead:
            def read(self):raise AssertionError('cancelled')
        _,fps=camera.measure_capture(NoRead(),frame,stop)
        self.assertEqual(fps,0)
class NativeOnlyCap(FakeCap):
    instances=[]
    def __init__(self,index,backend):
        super().__init__(index,backend);self.changed=False
    def set(self,p,v): self.changed=True;return False
    def read(self):
        if self.changed:return False,None
        return True,np.zeros((480,640,3),np.uint8)

class CompatibilityTests(unittest.TestCase):
    @patch('camera.cv2.VideoCapture',NativeOnlyCap)
    def test_native_mode_never_changes_properties(self):
        NativeOnlyCap.instances=[]
        cap,frame=camera.open_camera(camera.normalize({'resolution':'Compatibilidad'}))
        self.assertEqual(frame.shape[:2],(480,640));self.assertFalse(cap.changed)
        self.assertEqual(len(NativeOnlyCap.instances),1);cap.release()
    @patch('camera.cv2.VideoCapture',BackendCap)
    def test_secondary_retains_performance_path(self):
        config=camera.normalize({'index':1,'resolution':'640x480'})
        with patch('camera.measure_capture',side_effect=lambda cap,frame,stop:(frame,30)) as probe, patch('camera.open_compatible_camera',side_effect=AssertionError('must not change working path')):
            cap,frame=camera.open_camera(config)
        probe.assert_called();self.assertEqual(cap.index,1);self.assertEqual(frame.shape[:2],(480,640));cap.release()
    @patch('camera.cv2.VideoCapture',BackendCap)
    def test_performance_failure_falls_back_to_legacy(self):
        with patch('camera.measure_capture',side_effect=lambda cap,frame,stop:(frame,0)):
            cap,frame=camera.open_camera(camera.normalize({'resolution':'640x480','backend':'DirectShow'}))
        self.assertEqual(cap.backend,cv2.CAP_DSHOW);self.assertEqual(frame.shape[:2],(480,640));cap.release()
    @patch('camera.cv2.VideoCapture',BackendCap)
    def test_secondary_speed_profile(self):
        config=camera.normalize({'index':1,'resolution':'Auto fluidez'})
        with patch('camera.measure_capture',return_value=(np.zeros((720,1280,3),np.uint8),30)) as probe:
            cap,frame=camera.open_camera(config)
        probe.assert_called();self.assertEqual(frame.shape[:2],(720,1280));cap.release()
    @patch('camera.cv2.VideoCapture',BackendCap)
    def test_compatibility_respects_manual_backend(self):
        cap,frame=camera.open_camera(camera.normalize({'resolution':'Compatibilidad','backend':'Media Foundation'}))
        self.assertEqual(cap.backend,cv2.CAP_MSMF);cap.release()
    def test_cancel_does_not_fallback(self):
        stop=threading.Event();stop.set()
        with patch('camera.open_compatible_camera') as legacy:
            with self.assertRaises(RuntimeError):camera.open_camera(camera.normalize({}),stop)
            legacy.assert_not_called()
if __name__=='__main__':unittest.main()
