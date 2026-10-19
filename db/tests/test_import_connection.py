import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from psycopg.conninfo import conninfo_to_dict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from import_data import database_connection_string


class ImportConnectionTests(unittest.TestCase):
    def test_explicit_url_has_priority(self):
        with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://outro/banco'}, clear=True):
            self.assertEqual(database_connection_string('postgresql://escolhido/banco'), 'postgresql://escolhido/banco')

    def test_database_url_environment_remains_supported(self):
        with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://ambiente/banco'}, clear=True):
            self.assertEqual(database_connection_string(None), 'postgresql://ambiente/banco')

    def test_compose_environment_provides_connection(self):
        env = {'DB_HOST': 'db', 'DB_PORT': '5432', 'DB_NAME': 'servidores',
               'DB_USER': 'servidores', 'DB_PASSWORD': "senha local com ' e ="}
        with patch.dict(os.environ, env, clear=True):
            fields = conninfo_to_dict(database_connection_string(None))
        self.assertEqual(fields, {'host': 'db', 'port': '5432', 'dbname': 'servidores',
                                  'user': 'servidores', 'password': env['DB_PASSWORD']})

    def test_partial_environment_is_rejected(self):
        with patch.dict(os.environ, {'DB_HOST': 'db'}, clear=True):
            with self.assertRaisesRegex(ValueError, 'DB_PASSWORD'):
                database_connection_string(None)


if __name__ == '__main__':
    unittest.main()
