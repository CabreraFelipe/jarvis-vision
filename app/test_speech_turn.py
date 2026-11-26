import unittest,json
from unittest.mock import Mock
from voice import SpeechTurn

class SpeechTurnTests(unittest.TestCase):
    def recognizer(self,accepted,segments,final=''):
        r=Mock();r.AcceptWaveform.side_effect=accepted;r.Result.side_effect=[json.dumps({'text':s}) for s in segments];r.FinalResult.return_value=json.dumps({'text':final});return r
    def test_fixed_mode_keeps_segments(self):
        r=self.recognizer([True,False,True],['uno','dos'],'tres');t=SpeechTurn(r)
        self.assertFalse(t.feed(b'a'));self.assertFalse(t.feed(b'b'));self.assertFalse(t.feed(b'c'))
        self.assertEqual(t.finish(),'uno dos tres')
    def test_natural_mode_stops_at_nonempty_endpoint(self):
        r=self.recognizer([True,False,True],['','pregunta']);t=SpeechTurn(r,True)
        self.assertFalse(t.feed(b'a'));self.assertFalse(t.feed(b'b'));self.assertTrue(t.feed(b'c'))
        self.assertEqual(t.finish(),'pregunta');r.FinalResult.assert_not_called()
    def test_timeout_preserves_final(self):
        r=self.recognizer([False],[],'sin pausa');t=SpeechTurn(r,True);t.feed(b'a')
        self.assertEqual(t.finish(),'sin pausa')
    def test_cancel_discards_all(self):
        r=self.recognizer([True],['privado'],'otro');t=SpeechTurn(r);t.feed(b'a')
        self.assertEqual(t.finish(True),'');r.FinalResult.assert_not_called()
    def test_empty_audio(self):
        r=self.recognizer([True],[''],'');t=SpeechTurn(r,True)
        self.assertFalse(t.feed(b'a'));self.assertEqual(t.finish(),'')
    def test_finish_idempotent(self):
        r=self.recognizer([],[],'hola');t=SpeechTurn(r,True)
        self.assertEqual(t.finish(),'hola');self.assertEqual(t.finish(),'hola');r.FinalResult.assert_called_once()

if __name__=='__main__':unittest.main()
