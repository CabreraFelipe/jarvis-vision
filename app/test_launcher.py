import tempfile,unittest
from pathlib import Path
from windows_launcher import shortcut_paths,SCRIPT

class LauncherTests(unittest.TestCase):
    def test_managed_paths_with_spaces(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'JARVIS Vision'; manager=root/'.jarvis'/'manager.py'
            manager.parent.mkdir(parents=True); manager.write_text('# manager')
            executable=Path(d)/'Python 3'/'python.exe'; executable.parent.mkdir()
            pythonw=executable.with_name('pythonw.exe'); pythonw.write_bytes(b'')
            self.assertEqual(shortcut_paths(root,executable),(root.resolve(),manager.resolve(),pythonw.resolve()))
    def test_missing_manager_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError): shortcut_paths(d,Path(d)/'python.exe')
    def test_missing_pythonw_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); manager=root/'.jarvis'/'manager.py'
            manager.parent.mkdir(); manager.write_text('# manager')
            with self.assertRaises(ValueError): shortcut_paths(root,root/'python.exe')
    def test_script_uses_fixed_desktop_link_and_environment(self):
        self.assertIn("SpecialFolders.Item('Desktop')",SCRIPT)
        self.assertIn("'JARVIS.lnk'",SCRIPT)
        self.assertIn('$env:JARVIS_SHORTCUT_MANAGER',SCRIPT)
        self.assertIn('$env:JARVIS_SHORTCUT_PYTHONW',SCRIPT)

if __name__=='__main__': unittest.main()
