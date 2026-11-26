import unittest
from voice import WakeCommand
class Wake041(unittest.TestCase):
    def test_variants(self):
        for name in ['Járvis','yervis','harvis','yar vis','asistente']:
            self.assertEqual(WakeCommand().feed('Hola, '+name+' ¿qué ves?',1),'qué ves')
    def test_split(self):
        w=WakeCommand(); self.assertIsNone(w.feed('hola',1)); self.assertEqual(w.feed('yarvis qué ves',2),'qué ves')
    def test_split_timeout(self):
        w=WakeCommand(); w.feed('hola',1); self.assertIsNone(w.feed('yarvis qué ves',4))
    def test_not_activated(self):
        for text in ['hola','asistente','hola amigos','dijo hola jarvis','hola jarvisito']:
            w=WakeCommand(); self.assertIsNone(w.feed(text,1)); self.assertIsNone(w.until)
    def test_fallback_two_turns(self):
        w=WakeCommand(); self.assertIsNone(w.feed('hola asistente',1)); self.assertEqual(w.feed('qué ves',2),'qué ves')
if __name__=='__main__': unittest.main()
