import unittest,tempfile,threading,sys
from pathlib import Path
from unittest.mock import Mock,patch
import numpy as np
import whisper_input as w
import speech_input,voice

class WhisperTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.base=Path(tmp.name)
        self.path=self.base/'modelos'/'faster-whisper-small';self.path.mkdir(parents=True)
        for n in ('model.bin','config.json','tokenizer.json'):(self.path/n).write_bytes(b'mock')
        self.stop=threading.Event();self.pcm=np.full(16000,5000,dtype='<i2').tobytes()
    def test_local_only_and_spanish(self):
        model=Mock();model.transcribe.return_value=([Mock(text=' hola '),Mock(text=' mundo ')],None)
        package=Mock();package.WhisperModel.return_value=model
        with patch.dict(sys.modules,{'faster_whisper':package}),patch.object(w,'_model',None),patch.object(w,'_model_path',None):
            self.assertEqual(w.transcribe(self.base,self.pcm,16000,self.stop),'hola mundo')
        self.assertEqual(package.WhisperModel.call_args.args[0],str(self.path.resolve()))
        self.assertTrue(package.WhisperModel.call_args.kwargs['local_files_only'])
        self.assertEqual(model.transcribe.call_args.kwargs['language'],'es')
        self.assertTrue(model.transcribe.call_args.kwargs['vad_filter'])
        self.assertEqual(model.transcribe.call_args.args[0].dtype,np.float32)
    def test_silence_skips_model(self):
        with patch('whisper_input.local_model',side_effect=AssertionError('not needed')):
            self.assertEqual(w.transcribe(self.base,b'\x00\x00'*16000,16000,self.stop),'')
    def test_cancelled_skips_model(self):
        self.stop.set()
        self.assertEqual(w.transcribe(self.base,self.pcm,16000,self.stop),'')
    def test_cancel_during_segments(self):
        def segments():
            yield Mock(text='one')
            self.stop.set();yield Mock(text='two')
        model=Mock();model.transcribe.return_value=(segments(),None)
        with patch.object(w,'_model',model),patch.object(w,'_model_path',self.path.resolve()):
            self.assertEqual(w.transcribe(self.base,self.pcm,16000,self.stop),'')
    def test_requires_local_tokenizer(self):
        (self.path/'tokenizer.json').unlink()
        with self.assertRaises(RuntimeError):w.local_model(self.base)
    def test_bad_audio(self):
        for pcm,rate in [(b'x',16000),(self.pcm,1),(self.pcm*13,16000)]:
            with self.assertRaises(ValueError):w.transcribe(self.base,pcm,rate,self.stop)
    def test_persist_choice(self):
        path=self.base/'speech_input.json';cfg={'model':'Whisper small','device':None}
        speech_input.save(path,cfg);self.assertEqual(speech_input.load(path),cfg)
    def test_manual_dispatch_without_vosk(self):
        with patch('whisper_input.listen',return_value='hola') as listen:
            self.assertEqual(voice.listen(self.stop,settings={'model':'Whisper small'},base=self.base),'hola')
        self.assertEqual(listen.call_args.args[0],self.base)
    def test_old_default_preserved(self):
        self.assertEqual(speech_input.normalize(None),speech_input.DEFAULT)
if __name__=='__main__':unittest.main()
