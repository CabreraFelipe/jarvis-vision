import unittest
from voice_followup import Followup,stop_phrase
class FollowupTests(unittest.TestCase):
    def test_default_inactive(self):
        f=Followup();self.assertFalse(f.take())
    def test_only_after_answer(self):
        f=Followup();e=f.initial();self.assertFalse(f.take());f.accepted(e);self.assertTrue(f.take());self.assertFalse(f.take())
    def test_limit(self):
        f=Followup();e=f.initial()
        for _ in range(5):f.accepted(e);self.assertTrue(f.take())
        f.accepted(e);self.assertFalse(f.take())
    def test_reset_rejects_old_answer(self):
        f=Followup();e=f.initial();f.reset();f.accepted(e);self.assertFalse(f.take())
    def test_reactivation(self):
        f=Followup();old=f.initial();new=f.initial();f.accepted(old);self.assertFalse(f.take());f.accepted(new);self.assertTrue(f.take())
    def test_stop_exact(self):
        self.assertTrue(stop_phrase('¡Dejá de escuchar!') is False)
        for phrase in ('Deja de escuchar','Terminar conversación.','JARVIS, termina la conversación','Cancelar micrófono'):
            self.assertTrue(stop_phrase(phrase),phrase)
        self.assertFalse(stop_phrase('Explicame cómo terminar conversación'))
if __name__=='__main__':unittest.main()
