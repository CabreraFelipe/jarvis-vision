import tempfile,unittest
from pathlib import Path
from memory import Memory
from preference_learning import candidate,suggest

class SuggestionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Memory(Path(self.tmp.name)/'memory.sqlite3')
    def test_default_off_and_no_storage(self):
        self.assertIsNone(suggest(self.store,'Prefiero respuestas cortas.',True))
        self.assertFalse(self.store.path.exists())
    def test_opt_in_only_and_no_auto_write(self):
        self.store.configure(True,'Normal',suggestions=True)
        self.assertEqual(suggest(self.store,'Prefiero respuestas cortas.',True),'Prefiero respuestas cortas.')
        self.assertEqual(self.store.items(),[])
        self.assertIsNone(suggest(self.store,'Prefiero respuestas cortas.',False))
        self.store.add('prefiero respuestas cortas')
        self.assertIsNone(suggest(self.store,'Prefiero respuestas cortas.',True))
        self.store.configure(False,'Normal')
        self.assertFalse(self.store.suggestions_enabled())
        self.assertEqual(len(self.store.items()),1)
    def test_only_explicit_statements(self):
        self.assertEqual(candidate('Me gusta escuchar música house.'),'Me gusta escuchar música house.')
        for t in ('¿Prefiero respuestas cortas?','Él dijo que prefiero respuestas cortas','Prefiero respuestas cortas. Otra frase','Recordá que prefiero respuestas cortas','"Prefiero respuestas cortas"','Prefiero respuestas '+'x'*300,'Prefiero respuestas'):
            self.assertIsNone(candidate(t))
    def test_enable_requires_recall(self):
        self.store.configure(False,'Normal',suggestions=True)
        self.assertFalse(self.store.suggestions_enabled())

if __name__=='__main__':unittest.main()
