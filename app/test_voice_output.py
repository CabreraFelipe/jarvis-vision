import json,tempfile,unittest,subprocess
from pathlib import Path
from unittest.mock import patch,Mock,MagicMock
import voice_output as v

class VoiceOutputTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.base=Path(temp.name)
        self.folder=v.model_folder(self.base);self.folder.mkdir(parents=True)
        self.name='es-test.onnx';self.model=self.folder/self.name;self.model.write_bytes(b'mock')
        Path(str(self.model)+'.json').write_text(json.dumps({'audio':{'sample_rate':22050}}))
    def test_default_uses_existing_voice(self):
        with patch('voice.speak') as speak:
            v.speak(self.base,v.DEFAULT,'hola')
        speak.assert_called_once_with('hola')
    def test_roundtrip_and_invalid_config(self):
        path=self.base/'voice_preferences.json'
        self.assertEqual(v.load(path),v.DEFAULT);v.save(path,{'engine':'Piper local','model':self.name})
        self.assertEqual(v.load(path),{'engine':'Piper local','model':self.name})
        path.write_text('invalid');self.assertEqual(v.load(path),v.DEFAULT)
    def test_traversal_rejected(self):
        self.assertEqual(v.normalize({'engine':'Piper local','model':'../x.onnx'})['model'],'')
        with self.assertRaises(ValueError):v.model_info(self.base,'../x.onnx')
    def test_missing_json_rejected(self):
        Path(str(self.model)+'.json').unlink()
        self.assertEqual(v.models(self.base),[])
        with self.assertRaises(ValueError):v.model_info(self.base,self.name)
    def test_pcm_private_stdin(self):
        with patch('voice_output.subprocess.run',return_value=subprocess.CompletedProcess([],0,stdout=b'\x00\x00')) as run:
            self.assertEqual(v.synthesize(self.base,self.name,'hola privado'),(b'\x00\x00',22050))
        args=run.call_args.args[0];kw=run.call_args.kwargs
        self.assertNotIn('hola privado',args);self.assertEqual(kw['input'],b'hola privado\n')
        self.assertIn('--output-raw',args);self.assertIn('-I',args);self.assertNotIn('shell',kw)
        self.assertEqual(list(self.base.glob('*.wav')),[])
    def test_invalid_audio_rejected(self):
        with patch('voice_output.subprocess.run',return_value=subprocess.CompletedProcess([],0,stdout=b'x')):
            with self.assertRaises(ValueError):v.synthesize(self.base,self.name,'hola')
    def test_failure_no_silent_fallback(self):
        with patch('voice_output.subprocess.run',return_value=subprocess.CompletedProcess([],1,stdout=b'')),patch('voice.speak') as system:
            with self.assertRaises(RuntimeError):v.speak(self.base,{'engine':'Piper local','model':self.name},'hola')
        system.assert_not_called()
    def test_timeout(self):
        with patch('voice_output.subprocess.run',side_effect=subprocess.TimeoutExpired('piper',90)):
            with self.assertRaises(RuntimeError):v.synthesize(self.base,self.name,'hola')
    def test_invalid_rate(self):
        Path(str(self.model)+'.json').write_text('{"audio":{"sample_rate":999999}}')
        with self.assertRaises(ValueError):v.model_info(self.base,self.name)
    def test_playback(self):
        import sys
        sd=MagicMock();stream=sd.RawOutputStream.return_value.__enter__.return_value
        with patch.dict(sys.modules,{'sounddevice':sd}),patch('voice_output.synthesize',return_value=(b'\x00\x00',22050)):
            v.speak(self.base,{'engine':'Piper local','model':self.name},'hola')
        sd.RawOutputStream.assert_called_once_with(samplerate=22050,channels=1,dtype='int16');stream.write.assert_called_once_with(b'\x00\x00')
if __name__=='__main__':unittest.main()
