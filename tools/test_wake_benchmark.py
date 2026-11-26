import json,tempfile,unittest,wave
from pathlib import Path
from unittest.mock import Mock
from wake_benchmark import evaluate_clip,report

class BenchmarkTests(unittest.TestCase):
    def clip(self,root,channels=1):
        p=Path(root)/'test.wav'
        with wave.open(str(p),'wb') as w:
            w.setnchannels(channels); w.setsampwidth(2); w.setframerate(16000)
            w.writeframes(b'\0'*(1600*2*channels))
        return p
    def test_greeting_detected_without_command(self):
        with tempfile.TemporaryDirectory() as d:
            rec=Mock();rec.AcceptWaveform.return_value=True;rec.Result.return_value=json.dumps({'text':'hola jarvis'})
            self.assertTrue(evaluate_clip(self.clip(d),lambda rate:rec))
    def test_unrelated_final_result(self):
        with tempfile.TemporaryDirectory() as d:
            rec=Mock();rec.AcceptWaveform.return_value=False;rec.FinalResult.return_value=json.dumps({'text':'hola amigos'})
            self.assertFalse(evaluate_clip(self.clip(d),lambda rate:rec))
    def test_reject_stereo(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):evaluate_clip(self.clip(d,2),Mock())
    def test_metrics(self):
        r=report([True,False,True],[False,True,False,False],bool)
        self.assertEqual((r['detected'],r['missed'],r['false_activation_clips']),(2,1,1))
        self.assertEqual(r['false_positive_clip_rate'],.25)
    def test_empty_group(self):
        with self.assertRaises(ValueError):report([],['a'],bool)
if __name__=='__main__':unittest.main()
