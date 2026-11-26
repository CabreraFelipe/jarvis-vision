import unittest,threading,time
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
class SlowNativeCap(NativeOnlyCap):
    instances=[]
    def __init__(self,index,backend):
        super().__init__(index,backend);self.reads=0
    def read(self):
        self.reads+=1
        if self.reads<=4:return False,None
        return super().read()

class RecoveryTests(unittest.TestCase):
    @patch('camera.cv2.VideoCapture',SlowNativeCap)
    def test_slow_native_keeps_same_handle(self):
        SlowNativeCap.instances=[]
        cap,frame=camera.open_camera(camera.normalize({'index':1,'resolution':'Compatibilidad','backend':'DirectShow'}))
        self.assertEqual(len(SlowNativeCap.instances),1);self.assertEqual(cap.reads,5);self.assertFalse(cap.changed)
        self.assertEqual(frame.shape[:2],(480,640));cap.release()
    def test_cancel_before_wait(self):
        stop=threading.Event();stop.set()
        with patch.object(FakeCap,'read',side_effect=AssertionError('must not read')):
            self.assertIsNone(camera.wait_first_frame(FakeCap(1,cv2.CAP_DSHOW),stop))
    def test_initial_failure_retries_same_config(self):
        cfg=camera.normalize({'index':1,'resolution':'Inicio rápido','backend':'DirectShow'})
        cap=FakeCap(1,cv2.CAP_DSHOW);_,frame=cap.read()
        with patch('camera.open_compatible_camera',side_effect=[RuntimeError('USB starting'),(cap,frame)]) as open_:
            s=camera.Capture(cfg)
            try:
                end=time.monotonic()+3
                while time.monotonic()<end and not s.snapshot()[5]:time.sleep(.02)
                self.assertTrue(s.snapshot()[5]);self.assertEqual(open_.call_count,2)
                self.assertTrue(all(call.args[0]==cfg for call in open_.call_args_list))
            finally:s.stop.set();s.thread.join(2)
        self.assertTrue(cap.released)
    def test_interruption_releases_before_reopen(self):
        cfg=camera.normalize({'index':1,'resolution':'Compatibilidad'})
        cap=FakeCap(1,cv2.CAP_DSHOW);next_cap=FakeCap(1,cv2.CAP_DSHOW);_,frame=cap.read()
        cap.read=lambda:(False,None)
        calls=[]
        def open_(config,stop):
            calls.append(config)
            if len(calls)==1:return cap,frame
            self.assertTrue(cap.released);return next_cap,frame
        with patch('camera.open_camera',side_effect=open_):
            s=camera.Capture(cfg)
            try:
                end=time.monotonic()+3
                while time.monotonic()<end and (len(calls)<2 or not s.snapshot()[5]):time.sleep(.02)
                self.assertEqual(len(calls),2);self.assertTrue(s.snapshot()[5])
            finally:s.stop.set();s.thread.join(2)
        self.assertTrue(next_cap.released)
    def test_retry_limit_and_normal_path(self):
        for mode,expected in [('Inicio rápido',3),('640x480',1)]:
            with patch('camera.open_camera',side_effect=RuntimeError('not available')) as open_:
                s=camera.Capture(camera.normalize({'resolution':mode}));s.thread.join(4)
                self.assertFalse(s.thread.is_alive());self.assertEqual(open_.call_count,expected)
                self.assertFalse(s.snapshot()[5])
    def test_cancel_prevents_retry(self):
        def fail(config,stop):stop.set();raise RuntimeError('cancelled')
        with patch('camera.open_camera',side_effect=fail) as open_:
            s=camera.Capture(camera.normalize({'resolution':'Compatibilidad'}));s.thread.join(2)
            self.assertEqual(open_.call_count,1);self.assertEqual(s.snapshot()[3],'Desactivada')
class RememberedStartTests(unittest.TestCase):
    def cfg(self):
        return camera.normalize({'index':1,'resolution':'Compatibilidad','backend':'DirectShow'})
    @patch('camera.cv2.VideoCapture',NativeOnlyCap)
    def test_remembered_native_single_open(self):
        NativeOnlyCap.instances=[];cfg=self.cfg();recipes=[]
        cap,frame=camera.open_compatible_camera(cfg,on_recipe=recipes.append);cap.release()
        NativeOnlyCap.instances=[]
        cap,frame=camera.open_compatible_camera(cfg,remembered=recipes[0])
        self.assertEqual(len(NativeOnlyCap.instances),1);self.assertFalse(cap.changed);cap.release()
    @patch('camera.cv2.VideoCapture',NativeOnlyCap)
    def test_failed_recipe_releases_then_falls_back(self):
        NativeOnlyCap.instances=[];cfg=self.cfg()
        recipe={'backend':cv2.CAP_DSHOW,'mode':(640,480),'format':'MJPG','native':False}
        with patch('camera.wait_first_frame',side_effect=lambda cap,stop=None:None if cap.changed else np.zeros((480,640,3),np.uint8)):
            cap,frame=camera.open_compatible_camera(cfg,remembered=recipe)
        self.assertEqual(len(NativeOnlyCap.instances),2);self.assertTrue(NativeOnlyCap.instances[0].released);self.assertFalse(cap.changed);cap.release()
    def test_wrong_backend_and_normal_profile_ignore_recipe(self):
        cfg=self.cfg();recipe={'backend':cv2.CAP_MSMF,'mode':None,'format':'Automático','native':True}
        self.assertIsNone(camera.valid_recipe(cfg,recipe))
        self.assertIsNone(camera.valid_recipe(dict(cfg,backend='Automático'),dict(recipe,backend=cv2.CAP_DSHOW)))
        self.assertIsNone(camera.valid_recipe(dict(cfg,resolution='Automática'),dict(recipe,backend=cv2.CAP_DSHOW)))
    def test_config_key_includes_index_format_fps_and_backend(self):
        cfg=self.cfg()
        for changes in ({'index':2},{'fps':15},{'format':'MJPG'},{'backend':'Media Foundation'},{'resolution':'Inicio rápido'}):
            self.assertNotEqual(camera.recipe_key(cfg),camera.recipe_key(dict(cfg,**changes)))
    @patch('camera.cv2.VideoCapture',NativeOnlyCap)
    def test_quick_start_native_without_property_changes(self):
        cfg=dict(self.cfg(),resolution='Inicio rápido')
        cap,frame=camera.open_camera(cfg)
        self.assertFalse(cap.changed);cap.release()
    def test_cache_roundtrip(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'camera_start_cache.json';cfg=self.cfg()
            r={'backend':cv2.CAP_DSHOW,'mode':(640,480),'format':'MJPG','native':False}
            camera.save_start_cache(p,{camera.recipe_key(cfg):r})
            self.assertEqual(camera.valid_recipe(cfg,camera.load_start_cache(p)[camera.recipe_key(cfg)]),r)
if __name__=='__main__':unittest.main()
