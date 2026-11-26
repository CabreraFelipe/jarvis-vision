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
    def test_extended_phonetics_and_unicode(self):
        for name in ['llarbis','charbis','jar bis','yar-bis','Járvis','Ja\u0301rvis']:
            self.assertEqual(WakeCommand().feed('Hola, '+name+' ¿qué ves?',1),'qué ves')
    def test_split_name_after_greeting(self):
        w=WakeCommand(); self.assertIsNone(w.feed('hola jar',1))
        self.assertEqual(w.feed('vis qué ves',2),'qué ves')
    def test_three_segments(self):
        w=WakeCommand(); self.assertIsNone(w.feed('hola',1))
        self.assertIsNone(w.feed('yar',2))
        self.assertIsNone(w.feed('bis',3))
        self.assertEqual(w.feed('qué ves',4),'qué ves')
    def test_partial_timeout_and_unrelated_segment(self):
        w=WakeCommand(); w.feed('hola jar',1); self.assertIsNone(w.feed('vis qué ves',3))
        w.feed('hola jar',4); self.assertIsNone(w.feed('otra cosa',5))
        self.assertIsNone(w.feed('vis qué ves',5.5)); self.assertIsNone(w.until)
    def test_partial_never_activates_alone(self):
        for text in ['jar','vis','hola jar','hola jarvisito','hola jarvis-otro','hola charlista']:
            w=WakeCommand(); self.assertIsNone(w.feed(text,1)); self.assertIsNone(w.until)
    def test_bare_name_optional_and_standalone(self):
        w=WakeCommand(); self.assertIsNone(w.feed('JARVIS',1)); self.assertIsNone(w.until)
        w=WakeCommand(allow_bare=True); self.assertIsNone(w.feed('JARVIS',1))
        self.assertEqual(w.feed('qué ves',2),'qué ves')
    def test_bare_rejects_ambient_sentences(self):
        for text in ['JARVIS está ahí','dijo jarvis','hola','asistente','arvis','jarvisito']:
            w=WakeCommand(allow_bare=True); self.assertIsNone(w.feed(text,1)); self.assertIsNone(w.until)
    def test_bare_timeout(self):
        w=WakeCommand(allow_bare=True); w.feed('yarvis',1)
        self.assertIsNone(w.feed('otra pregunta',9)); self.assertIsNone(w.until)
if __name__=='__main__': unittest.main()
