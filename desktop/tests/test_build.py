from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build


class BuildTests(unittest.TestCase):
    def test_missing_tk_stops_before_generating_executable(self):
        # ImportError reproduz o Python instalado sem o pacote de Tkinter.
        with patch('build.platform.system', return_value='Linux'), \
                patch('build.subprocess.run') as installer, \
                patch.object(build.importlib, 'import_module', side_effect=ImportError('No module named tkinter')):
            with self.assertRaisesRegex(SystemExit, 'python3-tkinter'):
                build.main()
        installer.assert_not_called()

    def test_broken_tcl_also_stops_build(self):
        from tkinter import TclError
        tkinter = MagicMock()
        tkinter.Tcl.side_effect = TclError('init.tcl ausente')
        with patch('build.importlib.import_module', return_value=tkinter):
            with self.assertRaisesRegex(SystemExit, 'init.tcl ausente'):
                build.check_tkinter()

    def test_tcl_check_does_not_create_a_window(self):
        tkinter = MagicMock()
        with patch('build.importlib.import_module', return_value=tkinter):
            build.check_tkinter()
        tkinter.Tcl.return_value.eval.assert_called_once_with('info patchlevel')
        tkinter.Tk.assert_not_called()

    def test_build_uses_same_python_that_passed_preflight(self):
        with patch('build.platform.system', return_value='Windows'), \
                patch('build.check_tkinter') as preflight, \
                patch('build.subprocess.run') as installer:
            build.main()
        preflight.assert_called_once()
        command = installer.call_args.args[0]
        self.assertEqual(command[:3], [sys.executable, '-m', 'PyInstaller'])
        self.assertIn('--onefile', command)


if __name__ == '__main__':
    unittest.main()
