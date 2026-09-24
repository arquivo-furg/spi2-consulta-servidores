# Casos de teste de SQL injection

## Objetivo

Estes casos verificam se os filtros da API tratam toda entrada como dado e nunca como parte de um comando SQL. A execução ocorrerá somente em ambiente de teste, durante `QA-06`, quando os endpoints estiverem disponíveis.

## Preparação

1. Iniciar a API e um PostgreSQL exclusivo para testes.
2. Registrar as contagens das tabelas `servidor`, `cargo`, `orgao` e `uf`.
3. Confirmar que as tabelas e os registros de referência existem.
4. Definir a URL da API em `BASE_URL`.
5. Enviar os valores com codificação de parâmetro, sem montar a URL manualmente.

Exemplo de chamada:

```bash
curl --get --data-urlencode "nome=<PAYLOAD>" "$BASE_URL/api/servidores"
```

## Payloads

| ID | Payload | Tentativa representada |
|---|---|---|
| SQLI-01 | `'` | Quebra simples de literal de texto. |
| SQLI-02 | `' OR '1'='1' --` | Condição sempre verdadeira. |
| SQLI-03 | `nome' --` | Encerramento do valor seguido de comentário. |
| SQLI-04 | `' UNION SELECT NULL --` | Inclusão de uma consulta por `UNION`. |
| SQLI-05 | `'; DROP TABLE servidor; --` | Execução de uma segunda instrução destrutiva. |
| SQLI-06 | `' OR pg_sleep(5) IS NULL --` | Injeção baseada em tempo. |
| SQLI-07 | `%27%20OR%20%271%27%3D%271%27%20--` | Forma codificada da condição sempre verdadeira. |
| SQLI-08 | `" OR "1"="1` | Variação com aspas duplas. |

## Matriz de execução

Cada payload deve ser enviado separadamente em todos os filtros implementados:

| Filtro | Chamada planejada |
|---|---|
| Nome | `GET /api/servidores?nome=<PAYLOAD>` |
| Cargo | `GET /api/servidores?cargo=<PAYLOAD>` |
| UF | `GET /api/servidores?uf=<PAYLOAD>` |
| Órgão | `GET /api/servidores?orgao=<PAYLOAD>` |
| Similaridade | `GET /api/servidores?similar=<PAYLOAD>&limit=100` |

Também deve ser testada uma requisição combinada na qual apenas um dos filtros contém o payload, alternando o campo contaminado a cada execução.

## Resultado esperado

Para todos os casos:

- nenhuma instrução fornecida pelo usuário é executada;
- a API retorna resposta controlada em JSON, sem stack trace ou consulta SQL;
- uma condição sempre verdadeira não amplia indevidamente o conjunto de resultados;
- a tentativa baseada em tempo não provoca a espera solicitada pelo payload;
- nenhuma tabela, coluna ou registro é criado, alterado ou removido;
- a API permanece disponível após a requisição.

## Evidências a registrar em `QA-06`

- ID do caso, filtro testado e payload enviado;
- código HTTP, corpo JSON e tempo de resposta;
- contagens das quatro tabelas antes e depois da bateria;
- confirmação da existência das tabelas após o payload destrutivo;
- resultado aprovado, reprovado ou bloqueado, sem registrar credenciais.

Os payloads são casos de teste planejados. Este documento não afirma que eles já foram executados.
