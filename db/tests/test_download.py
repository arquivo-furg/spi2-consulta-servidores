from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from baixar_dados import APOSENTADOS, CARREIRAS, baixar_dados


class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.folder = Path(self.directory.name)
        self.addCleanup(self.directory.cleanup)

    def fake_download(self, url, path):
        Path(path).write_bytes(b'dados ficticios')

    def test_fixed_lists_cover_the_same_eleven_months(self):
        self.assertEqual(len(APOSENTADOS), 11)
        self.assertEqual(len(CARREIRAS), 11)
        self.assertTrue(all(link.startswith('http://repositorio.dados.gov.br/') for link in APOSENTADOS + CARREIRAS))
        self.assertEqual([link.rsplit('_', 1)[1][:6] for link in APOSENTADOS],
                         [link.rsplit('_', 1)[1][:6] for link in CARREIRAS])

    def test_download_creates_the_two_folders_and_files(self):
        with patch('baixar_dados.urlretrieve', side_effect=self.fake_download) as download:
            baixar_dados(self.folder)
        self.assertEqual(download.call_count, 22)
        self.assertEqual(len(list((self.folder/'aposentados').glob('*.csv'))), 11)
        self.assertEqual(len(list((self.folder/'carreiras').glob('*.txt'))), 11)
        self.assertEqual(list(self.folder.rglob('*.part')), [])

    def test_existing_empty_file_is_preserved(self):
        folder = self.folder/'aposentados'
        folder.mkdir()
        empty = folder/'APOSENTADOS_122025.csv'
        empty.touch()
        with patch('baixar_dados.urlretrieve', side_effect=self.fake_download) as download:
            baixar_dados(self.folder)
        self.assertEqual(download.call_count, 21)
        self.assertEqual(empty.stat().st_size, 0)

    def test_interrupted_download_is_not_a_complete_csv(self):
        def interrupt(url, path):
            Path(path).write_bytes(b'incompleto')
            raise URLError('conexao interrompida')
        with patch('baixar_dados.urlretrieve', side_effect=interrupt), self.assertRaises(URLError):
            baixar_dados(self.folder)
        self.assertFalse((self.folder/'aposentados/APOSENTADOS_092025.csv').exists())
