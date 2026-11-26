import unittest,tempfile,time,os
from pathlib import Path
from unittest.mock import Mock
from instance_focus import poll_focus

class FocusTests(unittest.TestCase):
    def test_missing(self):
        with tempfile.TemporaryDirectory() as d:
            root=Mock();self.assertFalse(poll_focus(root,Path(d)));self.assertEqual(root.mock_calls,[])
    def test_signal(self):
        with tempfile.TemporaryDirectory() as d:
            store=Path(d); signal=store/'focus-request.json';signal.write_text('{}')
            root=Mock();self.assertTrue(poll_focus(root,store))
            root.deiconify.assert_called_once();root.lift.assert_called_once();root.focus_set.assert_called_once()
            self.assertFalse(signal.exists());self.assertFalse(poll_focus(root,store))
    def test_old_signal(self):
        with tempfile.TemporaryDirectory() as d:
            store=Path(d); signal=store/'focus-request.json';signal.write_text('{}')
            old=time.time()-30;os.utime(signal,(old,old))
            root=Mock();self.assertFalse(poll_focus(root,store));self.assertEqual(root.mock_calls,[])
    def test_lock_untouched(self):
        with tempfile.TemporaryDirectory() as d:
            store=Path(d);lock=store/'manager.lock';lock.write_bytes(b'0')
            (store/'focus-request.json').write_text('{}')
            self.assertTrue(poll_focus(Mock(),store));self.assertEqual(lock.read_bytes(),b'0')
if __name__=='__main__':unittest.main()
