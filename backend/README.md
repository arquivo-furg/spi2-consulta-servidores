# API de consulta de servidores

A API fica disponível em `http://localhost:8000` quando o projeto é iniciado
com Docker Compose. Todas as respostas usam JSON com as chaves `sucesso`,
`mensagem` e `dados`.

## Verificar a API

### `GET /health`

Informa se a API está disponível.

```bash
curl http://localhost:8000/health
```

```json
{
  "sucesso": true,
  "mensagem": "api disponivel",
  "dados": {
    "status": "ok"
  }
}
```

## Consultar servidores

### `GET /api/servidores`

Consulta servidores por um ou mais filtros. Os filtros exatos podem ser
combinados e, nesse caso, o resultado precisa atender a todos eles.

| Parâmetro | Descrição | Regra |
|---|---|---|
| `nome` | Nome exato do servidor | Pode ser combinado com `cargo`, `uf` e `orgao` |
| `cargo` | Descrição exata do cargo | Pode ser combinado com os demais filtros |
| `uf` | Sigla da unidade federativa | Duas letras; a API normaliza para maiúsculas |
| `orgao` | Nome exato do órgão | Pode ser combinado com os demais filtros |
| `similar` | Nome aproximado para busca por similaridade | Pode ser combinado com os filtros exatos |
| `limit` | Limite da busca por similaridade | Inteiro de 1 a 100; padrão 100; exige `similar` |
| `page` | Página solicitada | Inteiro positivo; padrão 1 quando `page_size` é informado |
| `page_size` | Quantidade de registros por página | Inteiro de 1 a 100; padrão 100 quando `page` é informado |

Informe ao menos um dos filtros `nome`, `cargo`, `uf`, `orgao` ou `similar`.
A paginação é ativada quando `page` ou `page_size` está presente.

### Busca por nome exato

```bash
curl --get http://localhost:8000/api/servidores \
  --data-urlencode "nome=Nome do servidor"
```

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

Mesmo quando somente um registro é encontrado, `dados` permanece uma lista.

### Busca com filtros combinados

```bash
curl --get http://localhost:8000/api/servidores \
  --data-urlencode "cargo=Analista" \
  --data-urlencode "uf=RS" \
  --data-urlencode "orgao=Ministerio da Gestao"
```

### Busca por similaridade com paginação

```bash
curl --get http://localhost:8000/api/servidores \
  --data-urlencode "similar=Nome" \
  --data-urlencode "limit=20" \
  --data-urlencode "page=1" \
  --data-urlencode "page_size=10"
```

Uma resposta paginada inclui os totais da consulta:

```json
{
  "sucesso": true,
  "mensagem": "multiplos registros encontrados",
  "dados": [
    {
      "id": 1,
      "nome": "Nome do servidor",
      "cargo": "Cargo",
      "uf": "RS",
      "orgao": "Orgao"
    }
  ],
  "paginacao": {
    "pagina": 1,
    "tamanho_pagina": 10,
    "total_registros": 20,
    "total_paginas": 2
  }
}
```

## Respostas de erro

Erros usam o mesmo envelope JSON:

```json
{
  "sucesso": false,
  "mensagem": "nome nao encontrado",
  "dados": null
}
```

| Status | Situação |
|---|---|
| `400` | Filtro ou parâmetro inválido ou ausente |
| `404` | Rota, registro ou página inexistente |
| `405` | Método HTTP não permitido |
| `429` | Limite de buscas simultâneas excedido |
| `500` | Falha interna inesperada |
| `504` | Tempo limite da consulta excedido |
