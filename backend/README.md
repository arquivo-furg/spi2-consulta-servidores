# Contrato da API

Todas as respostas usam JSON com as chaves `sucesso`, `mensagem` e `dados`.
Respostas de busca bem-sucedidas mantêm `dados` como uma lista, inclusive quando
há somente um registro.

## Sucesso

```json
{
  "sucesso": true,
  "mensagem": "registro encontrado",
  "dados": [
    {
      "id": 1,
      "nome": "Nome do servidor",
      "cargo": "Cargo",
      "uf": "RS",
      "orgao": "Orgao"
    }
  ]
}
```

Uma busca paginada também inclui:

```json
{
  "paginacao": {
    "pagina": 1,
    "tamanho_pagina": 20,
    "total_registros": 35,
    "total_paginas": 2
  }
}
```

## Erro

```json
{
  "sucesso": false,
  "mensagem": "nome nao encontrado",
  "dados": null
}
```

Entradas e parâmetros inválidos retornam `400`. Recursos, registros e páginas
inexistentes retornam `404`. Excesso de buscas simultâneas retorna `429` e
timeout da consulta retorna `504`.

## Endpoints

- `GET /health`: informa a disponibilidade da API.
- `GET /api/servidores`: consulta servidores pelos parâmetros `nome`, `cargo`,
  `uf`, `orgao`, `similar`, `limit`, `page` e `page_size`.
