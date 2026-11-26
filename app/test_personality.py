import tempfile,unittest
from pathlib import Path
from unittest.mock import Mock
from personality import DEFAULT,validate,instruction
from memory import Memory
from assistant_core import AssistantCore

class PersonalityTests(unittest.TestCase):
    def test_defaults_and_invalid(self):
        self.assertEqual(instruction(DEFAULT),'')
        for values in ((),['hack']*5,DEFAULT+('extra',)):
            with self.assertRaises(ValueError):validate(values)
    def test_persistence_and_no_memory_activation(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'memory.sqlite3';store=Memory(path)
            self.assertEqual(store.personality(),DEFAULT)
            self.assertFalse(path.exists())
            profile=('Formal','Sin humor','Breve','Usted','Solo responder')
            store.set_personality(profile)
            self.assertEqual(Memory(path).personality(),profile)
            self.assertEqual(store.settings(),(False,'Normal'))
            self.assertFalse(store.suggestions_enabled())
            self.assertFalse(store.semantic_enabled())
            self.assertIn('registro formal',instruction(profile))
            self.assertIn('usted',instruction(profile))
            with self.assertRaises(ValueError):store.set_personality(('x',)*5)
            self.assertEqual(store.personality(),profile)
    def test_core_default_unchanged_and_profile_independent(self):
        provider=Mock(return_value='ok');core=AssistantCore(provider)
        core.answer(core.prepare('hola','Sin cámara'))
        provider.assert_called_once_with(None,'hola',[])
        profile=('Formal','Sin humor','Breve','Usted','Solo responder')
        request=core.prepare('hola','Sin cámara',use_context=False,memories=['privado'],personality=profile)
        core.answer(request)
        provider.assert_called_with(None,'hola',[],style='Normal',memories=(),personality=profile)

if __name__=='__main__':unittest.main()
