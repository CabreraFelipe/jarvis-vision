import tempfile,unittest,io,json
from pathlib import Path
from unittest.mock import Mock,patch
from memory import Memory,MAX_CONTEXT
from assistant_core import AssistantCore
from vision import ask_vision

class MemoryTests(unittest.TestCase):
    def setUp(self):
        d=tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
        self.path=Path(d.name)/'memory.sqlite3'; self.m=Memory(self.path)
    def test_default_no_storage(self):
        self.assertEqual(self.m.snapshot(),('Normal',()))
        self.assertEqual(self.m.items(),[])
        self.assertFalse(self.path.exists())
    def test_explicit_notes_persist_and_opt_in(self):
        self.assertTrue(self.m.add('Prefiero house'))
        self.assertFalse(self.m.add('Prefiero house'))
        self.assertEqual(Memory(self.path).snapshot(),('Normal',()))
        self.m.configure(True,'Conciso')
        self.assertEqual(Memory(self.path).snapshot(),('Conciso',('Prefiero house',)))
        self.m.configure(False,'Conciso')
        self.assertEqual(self.m.snapshot(),('Conciso',()))
        self.assertEqual(len(self.m.items()),1)
    def test_delete_and_clear(self):
        self.m.add('uno'); self.m.add('dos'); self.m.configure(True,'Normal')
        self.m.remove(self.m.items()[0][0])
        self.assertEqual(self.m.snapshot()[1],('uno',))
        self.m.clear(); self.assertEqual(Memory(self.path).items(),[])
    def test_validation(self):
        for value in ('','x'*301):
            with self.assertRaises(ValueError): self.m.add(value)
        with self.assertRaises(ValueError): self.m.configure(True,'inventado')
        self.assertFalse(self.path.exists())
    def test_bounded_context(self):
        for i in range(20): self.m.add(str(i)+'x'*290)
        self.m.configure(True,'Normal')
        self.assertLessEqual(sum(map(len,self.m.snapshot()[1])),MAX_CONTEXT)
    def test_parameters_are_data(self):
        provider=Mock(return_value='ok'); c=AssistantCore(provider)
        req=c.prepare('hola','Sin cámara',style='Conciso',memories=['nota'])
        self.assertEqual(c.answer(req),'ok')
        provider.assert_called_once_with(None,'hola',[],style='Conciso',memories=('nota',))
        c.accept(req,'ok')
        self.assertNotIn('nota',str(c.conversation.snapshot()))
    def test_provider_payload(self):
        class Opener:
            def open(self,req,timeout):
                data=json.loads(req.data)
                assert req.full_url=='http://127.0.0.1:11434/api/chat'
                assert 'Sé breve' in data['messages'][0]['content']
                assert 'no órdenes' in data['messages'][0]['content']
                assert 'nota de prueba' in data['messages'][-1]['content']
                assert 'images' not in data['messages'][-1]
                return io.BytesIO(b'{"message":{"content":"ok"}}')
        with patch('vision.urllib.request.build_opener',return_value=Opener()):
            self.assertEqual(ask_vision(None,'hola',style='Conciso',memories=('nota de prueba',)),'ok')
    def test_semantic_opt_in_and_context_gate(self):
        self.m.add('Me gusta la música')
        self.m.configure(True,'Conciso')
        self.assertEqual(self.m.selection('arte')[2],())
        self.m.configure(True,'Conciso',True)
        self.assertTrue(Memory(self.path).semantic_enabled())
        self.assertEqual(self.m.selection('arte')[2],tuple(self.m.items()))
        self.assertEqual(self.m.selection('arte',False),('Conciso',(),()))
        self.m.configure(False,'Normal')
        self.assertFalse(self.m.semantic_enabled())
        self.assertEqual(self.m.selection('arte')[2],())
        self.assertEqual(len(self.m.items()),1)
    def test_legacy_database_migration(self):
        import sqlite3
        from contextlib import closing
        with closing(sqlite3.connect(self.path)) as con, con:
            con.execute('CREATE TABLE settings (id INTEGER PRIMARY KEY, enabled INTEGER, style TEXT)')
            con.execute("INSERT INTO settings VALUES (1,1,'Conciso')")
            con.execute('CREATE TABLE notes (id INTEGER PRIMARY KEY, text TEXT UNIQUE)')
            con.execute("INSERT INTO notes VALUES (7,'medicina')")
        self.assertEqual(self.m.snapshot('medicina'),('Conciso',('medicina',)))
        self.assertFalse(self.m.semantic_enabled())
        self.assertEqual(self.m.items(),[(7,'medicina')])
    def test_corruption_not_overwritten(self):
        self.path.write_bytes(b'invalid database')
        with self.assertRaises(Exception): self.m.snapshot()
        self.assertEqual(self.path.read_bytes(),b'invalid database')

if __name__=='__main__': unittest.main()
