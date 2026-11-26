import json,tempfile,unittest,threading
from pathlib import Path
from unittest.mock import Mock,patch
import speech_input as s
import voice,camera
from test_jarvis import FakeCap
class InputTests(unittest.TestCase):
    def devices(self):
        sd=Mock();sd.query_hostapis.return_value=[{'name':'WASAPI'}]
        sd.query_devices.return_value=[{'name':'webcam','hostapi':0,'max_input_channels':1},{'name':'headset','hostapi':0,'max_input_channels':1}]
        return sd
    def test_selection_and_reorder(self):
        sd=self.devices();saved=s.inputs(sd)[1];self.assertEqual(s.resolve_device(sd,saved),1)
        sd.query_devices.return_value.reverse();self.assertEqual(s.resolve_device(sd,saved),0)
    def test_missing_input_never_silently_switches(self):
        sd=self.devices()
        with self.assertRaises(RuntimeError):s.resolve_device(sd,{'index':4,'name':'missing','host':'WASAPI'})
    def test_default_preserved(self):
        self.assertEqual(s.normalize({}),s.DEFAULT);self.assertIsNone(s.resolve_device(self.devices(),None))
    def test_persist(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'speech_input.json';choice={'model':'Completo','device':s.inputs(self.devices())[0]}
            s.save(p,choice);self.assertEqual(s.load(p),choice)
    def test_model_selection(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d);s.model_path(base,'Completo').mkdir(parents=True)
            sd=self.devices();sd.query_devices.side_effect=[sd.query_devices.return_value,{'name':'headset','default_samplerate':16000}]
            selected={'model':'Completo','device':{'index':1,'name':'headset','host':'WASAPI'}}
            model=Mock();rec=Mock()
            with patch.object(voice,'_model',None),patch.object(voice,'_model_path',None):
                _,rate,index,name=voice.recognizer_input(sd,model,rec,selected,base)
            model.assert_called_once_with(str(s.model_path(base,'Completo')));self.assertEqual((rate,index,name),(16000,1,'headset'))
    @patch('camera.cv2.VideoCapture',FakeCap)
    def test_quick_start_skips_benchmark(self):
        config=camera.normalize({'index':1,'resolution':'Inicio rápido','backend':'DirectShow'})
        with patch('camera.measure_capture',side_effect=AssertionError('no benchmark')):
            cap,frame=camera.open_camera(config)
        self.assertEqual(cap.index,1);cap.release()
    def test_normal_camera_path_unchanged(self):
        with patch('camera.open_performance_camera',return_value=('cap','frame')) as normal,patch('camera.open_compatible_camera') as fallback:
            cfg=camera.normalize({'index':1});self.assertEqual(camera.open_camera(cfg),('cap','frame'))
            normal.assert_called_once_with(cfg,None);fallback.assert_not_called()
if __name__=='__main__':unittest.main()
