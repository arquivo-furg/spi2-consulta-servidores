import unittest
from unittest.mock import MagicMock, patch

from psycopg.errors import QueryCanceled

from app import app


# Estes testes isolam a API com um cursor simulado; não acessam PostgreSQL real.
# O objetivo aqui é conferir parâmetros SQL e respostas, não testar o servidor do banco.
class SearchEndpointsTestCase(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    @staticmethod
    def database_cursor(mock_get_connection):
        # Reproduz os dois contextos: with conexão e with cursor.
        connection = MagicMock()
        cursor = MagicMock()
        mock_get_connection.return_value.__enter__.return_value = connection
        connection.cursor.return_value.__enter__.return_value = cursor
        return cursor

    def test_health_returns_success_envelope(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {
                "sucesso": True,
                "mensagem": "api disponivel",
                "dados": {"status": "ok"},
            },
        )

    @patch("app.get_connection")
    def test_exact_search_returns_serialized_result(self, mock_get_connection):
        cursor = self.database_cursor(mock_get_connection)
        cursor.fetchall.return_value = [
            (1, "Ana Silva", "Analista", "RS", "Ministerio da Gestao")
        ]

        response = self.client.get(
            "/api/servidores", query_string={"nome": "Ana Silva"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {
                "sucesso": True,
                "mensagem": "registro encontrado",
                "dados": [
                    {
                        "id": 1,
                        "nome": "Ana Silva",
                        "cargo": "Analista",
                        "uf": "RS",
                        "orgao": "Ministerio da Gestao",
                    }
                ],
            },
        )
        self.assertEqual(cursor.execute.call_args.args[1], ("Ana Silva",))

    @patch("app.get_connection")
    def test_combined_search_sends_all_filters_to_database(
        self, mock_get_connection
    ):
        cursor = self.database_cursor(mock_get_connection)
        cursor.fetchall.return_value = [
            (2, "Bruno Souza", "Tecnico", "SP", "Ministerio da Fazenda")
        ]

        response = self.client.get(
            "/api/servidores",
            query_string={
                "nome": "Bruno Souza",
                "cargo": "Tecnico",
                "uf": "sp",
                "orgao": "Ministerio da Fazenda",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            cursor.execute.call_args.args[1],
            (
                "Bruno Souza",
                "Tecnico",
                "SP",
                "Ministerio da Fazenda",
            ),
        )

    @patch("app.get_connection")
    def test_similar_search_returns_requested_page(self, mock_get_connection):
        # Cinco resultados, páginas de dois: a página 2 deve usar OFFSET 2.
        cursor = self.database_cursor(mock_get_connection)
        cursor.fetchone.return_value = (5,)
        cursor.fetchall.return_value = [
            (3, "Ana Costa", "Analista", "RJ", "Ministerio da Gestao"),
            (4, "Ana Lima", "Analista", "MG", "Ministerio da Gestao"),
        ]

        response = self.client.get(
            "/api/servidores",
            query_string={
                "similar": "Ana",
                "limit": "10",
                "page": "2",
                "page_size": "2",
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["mensagem"], "multiplos registros encontrados")
        self.assertEqual(len(body["dados"]), 2)
        self.assertEqual(
            body["paginacao"],
            {
                "pagina": 2,
                "tamanho_pagina": 2,
                "total_registros": 5,
                "total_paginas": 3,
            },
        )
        self.assertEqual(cursor.execute.call_count, 2)
        self.assertEqual(cursor.execute.call_args_list[0].args[1], ("Ana",))
        self.assertEqual(
            cursor.execute.call_args_list[1].args[1],
            ("Ana", "Ana", 2, 2),
        )

    @patch("app.get_connection")
    def test_empty_search_returns_not_found_envelope(self, mock_get_connection):
        cursor = self.database_cursor(mock_get_connection)
        cursor.fetchall.return_value = []

        response = self.client.get(
            "/api/servidores", query_string={"nome": "Pessoa Ausente"}
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.get_json(),
            {
                "sucesso": False,
                "mensagem": "nome nao encontrado",
                "dados": None,
            },
        )

    @patch("app.get_connection")
    def test_nonexistent_page_returns_not_found_envelope(
        self, mock_get_connection
    ):
        cursor = self.database_cursor(mock_get_connection)
        cursor.fetchone.return_value = (2,)

        response = self.client.get(
            "/api/servidores",
            query_string={"cargo": "Analista", "page": "2", "page_size": "2"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.get_json(),
            {
                "sucesso": False,
                "mensagem": "pagina inexistente",
                "dados": None,
            },
        )
        self.assertEqual(cursor.execute.call_count, 1)

    @patch("app.get_connection")
    def test_query_timeout_returns_gateway_timeout_envelope(
        self, mock_get_connection
    ):
        mock_get_connection.side_effect = QueryCanceled()

        response = self.client.get(
            "/api/servidores", query_string={"orgao": "Ministerio da Gestao"}
        )

        self.assertEqual(response.status_code, 504)
        self.assertEqual(
            response.get_json(),
            {
                "sucesso": False,
                "mensagem": "tempo limite da consulta excedido",
                "dados": None,
            },
        )

    def test_invalid_parameter_returns_bad_request_without_database(self):
        # Entrada rejeitada deve parar antes de abrir uma conexão com o banco.
        with patch("app.get_connection") as mock_get_connection:
            response = self.client.get(
                "/api/servidores", query_string={"ordenacao": "nome"}
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json(),
            {
                "sucesso": False,
                "mensagem": "parametro desconhecido: ordenacao",
                "dados": None,
            },
        )
        mock_get_connection.assert_not_called()

    def test_search_without_filter_returns_bad_request_without_database(self):
        with patch("app.get_connection") as mock_get_connection:
            response = self.client.get(
                "/api/servidores", query_string={"page": "1"}
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json(),
            {
                "sucesso": False,
                "mensagem": "informe ao menos um filtro",
                "dados": None,
            },
        )
        mock_get_connection.assert_not_called()

    def test_method_not_allowed_returns_error_envelope(self):
        response = self.client.post("/health")

        self.assertEqual(response.status_code, 405)
        self.assertEqual(
            response.get_json(),
            {
                "sucesso": False,
                "mensagem": "metodo nao permitido",
                "dados": None,
            },
        )

    @patch("app.get_connection")
    def test_unexpected_database_failure_returns_error_envelope(
        self, mock_get_connection
    ):
        mock_get_connection.side_effect = RuntimeError("database unavailable")
        propagate_exceptions = app.config["PROPAGATE_EXCEPTIONS"]
        app.config["PROPAGATE_EXCEPTIONS"] = False

        try:
            response = self.client.get(
                "/api/servidores", query_string={"nome": "Ana Silva"}
            )
        finally:
            app.config["PROPAGATE_EXCEPTIONS"] = propagate_exceptions

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.get_json(),
            {
                "sucesso": False,
                "mensagem": "erro interno do servidor",
                "dados": None,
            },
        )

    def test_concurrency_limit_returns_too_many_requests_envelope(self):
        with patch("app.search_slots") as mock_search_slots:
            mock_search_slots.acquire.return_value = False

            response = self.client.get(
                "/api/servidores", query_string={"nome": "Ana Silva"}
            )

        self.assertEqual(response.status_code, 429)
        self.assertEqual(
            response.get_json(),
            {
                "sucesso": False,
                "mensagem": "limite de buscas simultaneas excedido",
                "dados": None,
            },
        )
        mock_search_slots.release.assert_not_called()


if __name__ == "__main__":
    unittest.main()
