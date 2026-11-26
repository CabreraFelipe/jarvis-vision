import unittest
from unittest.mock import Mock
from assistant_core import AssistantCore

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.provider=Mock(return_value='respuesta')
        self.core=AssistantCore(self.provider)
    def test_text_without_camera(self):
        request=self.core.prepare('  hola  ','Sin cámara')
        self.assertEqual(self.core.answer(request),'respuesta')
        self.provider.assert_called_once_with(None,'hola',[])
        self.assertEqual(self.core.conversation.snapshot(),[])
        self.assertTrue(self.core.accept(request,'respuesta'))
    def test_snapshot_frame(self):
        frame=bytearray(b'original')
        request=self.core.prepare('qué ves','Cámara 1',frame)
        frame[:]=b'modified'
        self.core.answer(request)
        self.assertEqual(self.provider.call_args.args[0],bytearray(b'original'))
    def test_history_snapshot(self):
        one=self.core.prepare('primera','Sin cámara')
        self.core.accept(one,'uno')
        two=self.core.prepare('segunda','Sin cámara')
        self.core.accept(two,'dos')
        self.core.answer(two)
        self.assertEqual(self.provider.call_args.args[2],[{'role':'user','content':'[Sin cámara] primera'},{'role':'assistant','content':'uno'}])
    def test_context_disabled(self):
        self.core.accept(self.core.prepare('primera','Sin cámara'),'uno')
        request=self.core.prepare('privada','Sin cámara',use_context=False)
        self.core.answer(request)
        self.assertEqual(self.provider.call_args.args[2],[])
        self.assertFalse(self.core.accept(request,'dos'))
    def test_context_disabled_after_request(self):
        request=self.core.prepare('pregunta','Sin cámara')
        self.assertFalse(self.core.accept(request,'respuesta',context_enabled=False))
    def test_clear_discards_stale_result(self):
        request=self.core.prepare('pregunta','Sin cámara')
        self.core.clear()
        self.assertFalse(self.core.accept(request,'respuesta'))
        self.assertEqual(self.core.conversation.snapshot(),[])
    def test_provider_failure_does_not_store(self):
        self.provider.side_effect=RuntimeError('offline')
        with self.assertRaises(RuntimeError):
            self.core.answer(self.core.prepare('pregunta','Sin cámara'))
        self.assertEqual(self.core.conversation.snapshot(),[])
    def test_empty_question(self):
        with self.assertRaises(ValueError):
            self.core.prepare('  ','Sin cámara')
        self.provider.assert_not_called()
    def test_context_remains_bounded(self):
        for i in range(12):
            self.core.accept(self.core.prepare(str(i),'Sin cámara'),'respuesta')
        self.assertEqual(len(self.core.conversation.snapshot()),8)

if __name__=='__main__': unittest.main()
