import csv
import io
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prepare_data import prepare_file, source_files


class PeriodPreparationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.folder = Path(self.directory.name)
        self.addCleanup(self.directory.cleanup)

    def source(self, name, nome='SERVIDOR EXEMPLO', cargo='TECNICO'):
        path = self.folder / name
        row = [nome, '00000000000', '1', cargo, 'RS', 'ORGAO EXEMPLO', '09', '0', '']
        # Dados fictícios; o cabeçalho de 2025 não traz a linha de competência.
        with path.open('w', encoding='latin-1', newline='') as target:
            writer = csv.writer(target, delimiter=';')
            writer.writerow(['Nome', 'CPF', 'Codigo', 'Cargo', 'UF', 'Orgao', 'Mes', 'Valor', ''])
            writer.writerow(row)
        return path

    def test_folder_collects_all_monthly_files(self):
        first = self.source('CARREIRA_092025.txt')
        second = self.source('CARREIRA_102025.txt')
        self.assertEqual(source_files(self.folder, 'CARREIRA', 'txt'), {'092025': first, '102025': second})

    def test_single_file_remains_supported(self):
        path = self.source('CARREIRA_092025.txt')
        self.assertEqual(source_files(path, 'CARREIRA', 'txt'), {'092025': path})

    def test_duplicate_across_months_is_written_only_once(self):
        first = self.source('CARREIRA_092025.txt')
        second = self.source('CARREIRA_102025.txt')
        seen = set()
        output = io.StringIO()
        writer = csv.writer(output)
        self.assertEqual(prepare_file(first, 'carreiras', writer, seen)['tratados'], 1)
        result = prepare_file(second, 'carreiras', writer, seen)
        self.assertEqual(result['duplicados'], 1)
        self.assertEqual(result['tratados'], 0)
        self.assertEqual(len(output.getvalue().splitlines()), 1)

    def test_changed_cargo_is_not_discarded_as_duplicate(self):
        first = self.source('CARREIRA_092025.txt')
        second = self.source('CARREIRA_102025.txt', cargo='ANALISTA')
        seen = set()
        writer = csv.writer(io.StringIO())
        self.assertEqual(prepare_file(first, 'carreiras', writer, seen)['tratados'], 1)
        self.assertEqual(prepare_file(second, 'carreiras', writer, seen)['tratados'], 1)

    def test_empty_source_is_kept_in_the_monthly_inventory(self):
        path = self.folder / 'APOSENTADOS_122025.csv'
        path.touch()
        self.assertEqual(source_files(self.folder, 'APOSENTADOS', 'csv'), {'122025': path})
        result = prepare_file(path, 'aposentados', csv.writer(io.StringIO()))
        self.assertEqual(result['registros_origem'], 0)
        self.assertEqual(result['tratados'], 0)

    def test_missing_sources_fail_before_preparing_output(self):
        with self.assertRaisesRegex(ValueError, 'nenhum arquivo'):
            source_files(self.folder, 'APOSENTADOS', 'csv')
