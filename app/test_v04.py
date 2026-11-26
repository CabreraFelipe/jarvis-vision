import unittest, json, io
from unittest.mock import patch
from conversation import Conversation
from voice import WakeCommand
from vision import ask_vision
import numpy as np

class WakeTests(unittest.TestCase):
    def test_ignores_unaddressed(self):
        w=WakeCommand(); self.assertIsNone(w.feed('qué ves',1)); self.assertIsNone(w.feed('hola amigo',2))
    def test_single_phrase(self):
        self.assertEqual(WakeCommand().feed('hola yarvis qué ves',1),'qué ves')
    def test_two_phrases(self):
        w=WakeCommand(); self.assertIsNone(w.feed('hola jarvis',1)); self.assertEqual(w.feed('qué ves',5),'qué ves'); self.assertIsNone(w.feed('otra pregunta',6))
    def test_timeout(self):
        w=WakeCommand(); w.feed('hola jarvis',1); self.assertTrue(w.expire(9)); self.assertIsNone(w.feed('qué ves',10))
    def test_expire_on_feed(self):
        w=WakeCommand(); w.feed('hola jarvis',1); self.assertIsNone(w.feed('qué ves',20))
class ConversationTests(unittest.TestCase):
    def test_bounded(self):
        c=Conversation();
        for i in range(9): c.add(str(i),'a','Cámara 1',c.epoch)
        self.assertEqual(len(c.snapshot()),8); self.assertIn('5',c.snapshot()[0]['content']); self.assertTrue(all('images' not in m for m in c.snapshot()))
    def test_reset_rejects_inflight(self):
        c=Conversation(); e=c.epoch; c.clear(); self.assertFalse(c.add('q','a','Sin cámara',e)); self.assertEqual(c.snapshot(),[])
    def test_snapshot_independent(self):
        c=Conversation(); c.add('q','a','Sin cámara',0); s=c.snapshot(); s[0]['content']='changed'; self.assertNotEqual(c.snapshot(),s)
    def test_visual_payload(self):
        self.check_payload(np.zeros((16,16,3),dtype=np.uint8),True)
    def test_text_payload(self):
        self.check_payload(None,False)
    def check_payload(self,frame,visual):
        c=Conversation(); c.add('primera','respuesta','Sin cámara',0); expected=c.snapshot()
        class O:
            def open(self,req,timeout):
                payload=json.loads(req.data); assert req.full_url=='http://127.0.0.1:11434/api/chat'; assert payload['messages'][1:-1]==expected; assert ('images' in payload['messages'][-1])==visual; return io.BytesIO(b'{"message":{"content":"ok"}}')
        with patch('vision.urllib.request.build_opener',return_value=O()): self.assertEqual(ask_vision(frame,'segunda',expected),'ok')
if __name__=='__main__': unittest.main()
