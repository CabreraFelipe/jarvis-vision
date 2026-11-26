import io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch,Mock
from memory import Memory
from assistant_core import AssistantCore
from diagnostics import ollama_status,collect

class SelectiveMemoryTests(unittest.TestCase):
    def setUp(self):
        d=tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
        self.m=Memory(Path(d.name)/'memory.sqlite3')
        self.m.add('Estudio medicina en Montevideo')
        self.m.add('Prefiero música house clásico')
        self.m.configure(True,'Normal')
    def test_accent_insensitive_search(self):
        self.assertEqual(len(self.m.search('MUSICA')),1)
    def test_relevant_only(self):
        self.assertEqual(self.m.snapshot('música house')[1],('Prefiero música house clásico',))
        self.assertEqual(self.m.snapshot('qué hora es')[1],())
    def test_edit_preserves_id_and_others(self):
        i=self.m.search('medicina')[0][0]
        self.assertTrue(self.m.edit(i,'Estudio medicina y sistemas'))
        self.assertEqual(self.m.search('sistemas')[0][0],i)
        self.assertEqual(len(self.m.items()),2)
        with self.assertRaises(ValueError): self.m.edit(i,'Prefiero música house clásico')
    def test_disabled_recall(self):
        self.m.configure(False,'Normal')
        self.assertEqual(self.m.snapshot('medicina')[1],())
        self.assertEqual(len(self.m.search('medicina')),1)
    def test_core_privacy_even_if_caller_passes_notes(self):
        c=AssistantCore(Mock(return_value='ok'))
        self.assertEqual(c.prepare('hola','Sin cámara',use_context=False,memories=['nota']).memories,())

class DiagnosticsTests(unittest.TestCase):
    def test_local_model(self):
        opener=Mock(); opener.open.return_value=io.BytesIO(json.dumps({'models':[{'name':'gemma3:4b'}]}).encode())
        with patch('diagnostics.urllib.request.build_opener',return_value=opener):
            self.assertEqual(ollama_status(),('Disponible','Instalado'))
        opener.open.assert_called_once_with('http://127.0.0.1:11434/api/tags',timeout=3)
    def test_offline(self):
        opener=Mock(); opener.open.side_effect=OSError('offline')
        with patch('diagnostics.urllib.request.build_opener',return_value=opener):
            self.assertEqual(ollama_status()[1],'No comprobado')
    def test_missing_model(self):
        opener=Mock(); opener.open.return_value=io.BytesIO(b'{"models":[]}')
        with patch('diagnostics.urllib.request.build_opener',return_value=opener):
            self.assertEqual(ollama_status(),('Disponible','No encontrado'))
    def test_collect_no_creation(self):
        with tempfile.TemporaryDirectory() as d,patch('diagnostics.ollama_status',return_value=('Disponible','Instalado')):
            rows=dict(collect(d,'0.4.4'))
            self.assertEqual(rows['Memoria local'],'Sin base creada')
            self.assertEqual(list(Path(d).iterdir()),[])

if __name__=='__main__': unittest.main()
