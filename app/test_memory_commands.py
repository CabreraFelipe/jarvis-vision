import tempfile,unittest
from pathlib import Path
from unittest.mock import Mock
from memory import Memory
from memory_commands import parse,execute,Command

class CommandTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Memory(Path(self.tmp.name)/'memory.sqlite3')
        self.confirm=Mock(return_value=True)
    def test_explicit_commands_only(self):
        self.assertEqual(parse('JARVIS, recordá que Estudio Medicina.'),Command('add','Estudio Medicina.'))
        self.assertEqual(parse('¿Qué sabés sobre mí?'),Command('list'))
        self.assertEqual(parse('Cambiá tu estilo a conversacional.'),Command('style','Conversacional'))
        for text in ('No recordá que esto','Explicá cómo recordar que estudio','Él dijo recordá que estudio','¿Qué es memoria?'):
            self.assertIsNone(parse(text))
    def test_add_requires_confirmation(self):
        self.confirm.return_value=False
        self.assertEqual(execute(self.store,parse('Recordá que me gusta el cine'),self.confirm),'Recuerdo no guardado.')
        self.assertFalse(self.store.path.exists())
        self.confirm.return_value=True
        execute(self.store,parse('Recordá que me gusta el cine'),self.confirm)
        self.assertEqual(self.store.items()[0][1],'me gusta el cine')
        self.assertFalse(self.store.settings()[0])
    def test_exact_removal_and_confirmation(self):
        self.store.add('Me gusta el cine.')
        self.store.add('Me gusta el cine francés.')
        execute(self.store,parse('Olvidá cine'),self.confirm)
        self.confirm.assert_not_called()
        self.assertEqual(len(self.store.items()),2)
        self.confirm.return_value=False
        execute(self.store,parse('Olvidá me gusta el cine'),self.confirm)
        self.assertEqual(len(self.store.items()),2)
        self.confirm.return_value=True
        execute(self.store,parse('Olvidá me gusta el cine'),self.confirm)
        self.assertEqual([t for _,t in self.store.items()],['Me gusta el cine francés.'])
    def test_style_preserves_memory_and_consent(self):
        self.store.add('nota')
        self.store.configure(True,'Normal',True)
        execute(self.store,parse('Cambiá estilo a conciso'),self.confirm)
        self.assertEqual(self.store.settings(),(True,'Conciso'))
        self.assertTrue(self.store.semantic_enabled())
        self.assertEqual(len(self.store.items()),1)
    def test_oversize_does_not_write(self):
        execute(self.store,Command('add','x'*301),self.confirm)
        self.confirm.assert_not_called()
        self.assertFalse(self.store.path.exists())
    def test_ambiguous_exact_normalized(self):
        self.store.add('Café')
        self.store.add('Cafe')
        execute(self.store,parse('Olvidá cafe'),self.confirm)
        self.confirm.assert_not_called()
        self.assertEqual(len(self.store.items()),2)

if __name__=='__main__':unittest.main()
