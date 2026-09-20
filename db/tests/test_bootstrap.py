import csv
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bootstrap import prepare_database


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        env = patch.dict(os.environ, DB_HOST='db', DB_PORT='5432', DB_NAME='servidores',
                         DB_USER='servidores', DB_PASSWORD='senha de teste')
        env.start()
        self.addCleanup(env.stop)
        connection = patch('bootstrap.psycopg.connect')
        self.database = connection.start().return_value.__enter__.return_value
        self.database.execute.return_value.fetchone.return_value = (False,)
        self.addCleanup(connection.stop)
        prepare = patch('bootstrap.subprocess.run', side_effect=self.write_prepared)
        self.prepare = prepare.start()
        self.addCleanup(prepare.stop)
        load = patch('bootstrap.import_data', return_value={'servidor': 1})
        self.load = load.start()
        self.addCleanup(load.stop)

    def write_prepared(self, command, **kwargs):
        destination = Path(command[command.index('--saida') + 1])
        with destination.open('w', encoding='utf-8', newline='') as target:
            writer = csv.writer(target)
            writer.writerow(['nome'])
            writer.writerow(['SERVIDOR EXEMPLO'])

    def test_existing_database_does_not_need_raw_files(self):
        self.database.execute.return_value.fetchone.return_value = (True,)
        prepare_database(Path('/pasta-inexistente'))
        self.prepare.assert_not_called()
        self.load.assert_not_called()

    def test_empty_database_prepares_both_folders_then_imports(self):
        prepare_database(Path('/dados'))
        command = self.prepare.call_args.args[0]
        self.assertIn(str(Path('/dados/aposentados')), command)
        self.assertIn(str(Path('/dados/carreiras')), command)
        self.load.assert_called_once()

    def test_failed_preparation_does_not_import(self):
        self.prepare.side_effect = subprocess.CalledProcessError(2, ['prepare_data.py'])
        with self.assertRaises(subprocess.CalledProcessError):
            prepare_database(Path('/dados'))
        self.load.assert_not_called()

    def test_no_valid_rows_does_not_import(self):
        self.prepare.side_effect = lambda command, **kwargs: Path(command[-1]).write_text('nome\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'não produziram registros'):
            prepare_database(Path('/dados'))
        self.load.assert_not_called()

    def test_import_failure_is_not_reported_as_success(self):
        self.load.side_effect = ValueError('tabelas de destino devem estar vazias')
        with self.assertRaisesRegex(ValueError, 'tabelas de destino'):
            prepare_database(Path('/dados'))
