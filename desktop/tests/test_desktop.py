import json
from pathlib import Path
import sys
import time
from unittest import TestCase, main
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit
from io import BytesIO

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from client import ApiError, search


ROW = {'id': 1, 'nome': 'SERVIDOR DE TESTE', 'cargo': 'ANALISTA', 'uf': None, 'orgao': 'ORGAO TESTE'}


def payload(page=1, total=21):
    return {'sucesso': True, 'mensagem': 'registro encontrado', 'dados': [ROW],
            'paginacao': {'pagina': page, 'tamanho_pagina': 10,
                          'total_registros': total, 'total_paginas': (total + 9) // 10}}


class Response:
    status = 200

    def __init__(self, value):
        self.value = value

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self):
        return json.dumps(self.value).encode()


def http_error(code, message):
    return HTTPError('http://localhost/api/servidores', code, '', {},
                     BytesIO(json.dumps({'sucesso': False, 'mensagem': message, 'dados': None}).encode()))


# As respostas HTTP são simuladas aqui para conferir o cliente sem depender da API ativa.
class ClientTests(TestCase):
    def test_exact_filters_and_pagination_are_encoded(self):
        with patch('client.urlopen', return_value=Response(payload(2))) as request:
            result = search('http://localhost:8000/', {'nome': ' ANA ÁVILA ', 'uf': 'RS', 'orgao': 'A & B'}, 2)
        params = parse_qs(urlsplit(request.call_args.args[0].full_url).query)
        self.assertEqual(params, {'nome': ['ANA ÁVILA'], 'uf': ['RS'], 'orgao': ['A & B'], 'page': ['2'], 'page_size': ['10']})
        self.assertEqual(result['paginacao']['pagina'], 2)

    def test_similarity_patterns_and_limit(self):
        with patch('client.urlopen', return_value=Response(payload())) as request:
            search('https://exemplo.test', {'similar': '%ANA%SILVA%', 'limit': '20'})
        query = parse_qs(urlsplit(request.call_args.args[0].full_url).query)
        self.assertEqual(query['similar'], ['%ANA%SILVA%'])
        self.assertEqual(query['limit'], ['20'])
        self.assertNotIn('nome', query)

    def test_missing_filter_does_not_call_api(self):
        with patch('client.urlopen') as request, self.assertRaisesRegex(ApiError, 'pelo menos um filtro'):
            search('http://localhost:8000', {'nome': '  '})
        request.assert_not_called()

    def test_invalid_api_addresses(self):
        for address in ('file:///etc/passwd', '', 'http://', 'http://localhost:bad',
                        'http://u:p@localhost', 'http://localhost?x=1', 'http://localhost#hash'):
            with self.subTest(address=address), self.assertRaises(ApiError):
                search(address, {'uf': 'RS'})

    def test_no_results_404(self):
        with patch('client.urlopen', side_effect=http_error(404, 'nome nao encontrado')):
            self.assertEqual(search('http://localhost', {'nome': 'A'})['dados'], [])

    def test_missing_page_and_route_are_not_empty_results(self):
        for message in ('pagina inexistente', 'recurso nao encontrado'):
            with self.subTest(message=message), patch('client.urlopen', side_effect=http_error(404, message)):
                with self.assertRaisesRegex(ApiError, message):
                    search('http://localhost', {'uf': 'RS'}, 99)

    def test_api_error_messages(self):
        for code in (400, 429, 500, 504):
            with self.subTest(code=code), patch('client.urlopen', side_effect=http_error(code, f'erro {code}')):
                with self.assertRaisesRegex(ApiError, f'erro {code}'):
                    search('http://localhost', {'uf': 'RS'})

    def test_connection_error(self):
        with patch('client.urlopen', side_effect=URLError('offline')), self.assertRaisesRegex(ApiError, 'conectar'):
            search('http://localhost', {'uf': 'RS'})

    def test_timeout(self):
        with patch('client.urlopen', side_effect=TimeoutError), self.assertRaisesRegex(ApiError, 'demorou'):
            search('http://localhost', {'uf': 'RS'})

    def test_malformed_response(self):
        for value in ({}, [], {'mensagem': 'ok', 'sucesso': True, 'dados': [None]},
                      {**payload(), 'paginacao': {'pagina': -1}},
                      {**payload(), 'dados': [{**ROW, 'uf': 5}]}):
            with self.subTest(value=value), patch('client.urlopen', return_value=Response(value)):
                with self.assertRaisesRegex(ApiError, 'resposta inválida'):
                    search('http://localhost', {'uf': 'RS'})


if __name__ == '__main__':
    main()
