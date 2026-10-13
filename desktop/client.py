"""Cliente HTTP usado pela interface desktop, sem acesso direto ao banco."""

import json
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen


class ApiError(Exception):
    pass


def search(api_url, filters, page=1):
    base = api_url.strip().rstrip('/')
    try:
        address = urlsplit(base)
        valid = address.scheme in ('http', 'https') and address.hostname and address.port != 0
    except ValueError:
        valid = False
    if not valid or address.query or address.fragment or address.username or address.password:
        raise ApiError('Informe o endereço HTTP ou HTTPS da API, sem credenciais ou parâmetros.')
    # urlencode preserva acentos e envia % como parte do filtro, sem montar a URL à mão.
    params = {key: value.strip() for key, value in filters.items() if value.strip()}
    if not any(params.get(key) for key in ('nome', 'similar', 'cargo', 'uf', 'orgao')):
        raise ApiError('Preencha pelo menos um filtro para buscar.')
    params.update(page=page, page_size=10)
    request = Request(f'{base}/api/servidores?{urlencode(params)}', headers={'Accept': 'application/json'})
    try:
        with urlopen(request, timeout=10) as response:
            status, body = response.status, response.read()
    except HTTPError as error:
        with error:
            status, body = error.code, error.read()
    except (TimeoutError, socket.timeout):
        raise ApiError('A consulta demorou demais. Tente novamente.') from None
    except (URLError, OSError):
        raise ApiError('Não foi possível conectar à API. Confira o endereço e se o serviço está ativo.') from None
    try:
        payload = json.loads(body)
        if not isinstance(payload, dict) or not isinstance(payload.get('mensagem'), str):
            raise ValueError
        # Sem registros é um estado da busca; rota ou página inexistente é erro.
        if status == 404 and payload.get('dados') is None and payload['mensagem'] not in ('pagina inexistente', 'recurso nao encontrado'):
            return {'dados': [], 'paginacao': {'pagina': 1, 'total_registros': 0, 'total_paginas': 0}}
        if status != 200 or payload.get('sucesso') is not True:
            raise ApiError(payload['mensagem'])
        rows, pagination = payload['dados'], payload['paginacao']
        if not isinstance(rows, list) or not isinstance(pagination, dict):
            raise ValueError
        for row in rows:
            if not isinstance(row, dict) or any(not isinstance(row.get(key), str) for key in ('nome', 'cargo', 'orgao')):
                raise ValueError
            if row.get('uf') is not None and not isinstance(row['uf'], str):
                raise ValueError
        for key in ('pagina', 'total_registros', 'total_paginas'):
            if type(pagination.get(key)) is not int or pagination[key] < (1 if key == 'pagina' else 0):
                raise ValueError
        return payload
    except (ValueError, KeyError, TypeError):
        raise ApiError('A API retornou uma resposta inválida. Confira o endereço do serviço.') from None
