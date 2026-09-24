# Plano de testes da API

## Objetivo

Os testes abaixo verificam as buscas e os erros previstos no enunciado. A execução e os resultados ficam nos arquivos de evidências.

## Pré-condições para execução

- API Flask iniciada pelo Gunicorn e conectada ao PostgreSQL de teste.
- Banco populado com registros conhecidos para nome, cargo, UF e órgão.
- Respostas de sucesso e erro disponíveis em JSON.
- Contagens do banco registradas antes dos testes de segurança para confirmar sua integridade ao final.

## Consultas funcionais

| ID | Cenário | Requisição ou condição | Resultado esperado |
|---|---|---|---|
| API-01 | Busca por nome | `GET /api/servidores?nome=<nome>` | Retorna em JSON somente os registros compatíveis com o nome. |
| API-02 | Busca por cargo | `GET /api/servidores?cargo=<cargo>` | Retorna em JSON somente os registros do cargo informado. |
| API-03 | Busca por UF | `GET /api/servidores?uf=<uf>` | Retorna em JSON somente os registros da UF informada. |
| API-04 | Busca por órgão | `GET /api/servidores?orgao=<orgao>` | Retorna em JSON somente os registros do órgão informado. |
| API-05 | Filtros combinados | Informar dois ou mais entre nome, cargo, UF e órgão | Retorna somente registros que atendem simultaneamente aos filtros. |
| API-06 | Busca por similaridade | `GET /api/servidores?similar=<nome>&limit=100` | Retorna nomes similares em JSON, respeitando o limite máximo de 100 registros. |
| API-07 | Nome com vários registros | Buscar um nome presente mais de uma vez | Retorna os registros encontrados de forma paginada, sem descartar homônimos. |

## Entradas inválidas e respostas de erro

| ID | Cenário | Entrada ou condição | Resultado esperado |
|---|---|---|---|
| ERR-01 | String inválida | Filtro vazio, apenas espaços ou conteúdo que não atende ao formato aceito | Rejeita a entrada com erro controlado em JSON e não executa uma busca ampla acidental. |
| ERR-02 | Tentativa de SQL injection | Enviar nos filtros os payloads definidos em `QA-02` | Não executa comandos fornecidos pelo usuário, não altera o banco e responde de forma controlada. |
| ERR-03 | Nome não encontrado | Buscar nome válido ausente da base | Informa em JSON que nenhum registro foi encontrado. |
| ERR-04 | Cargo inválido | Informar cargo que não atende ao formato aceito | Rejeita o parâmetro com erro controlado em JSON. |
| ERR-05 | UF inválida | Informar sigla inexistente ou fora do formato de duas letras | Rejeita o parâmetro com erro controlado em JSON. |
| ERR-06 | Órgão inválido | Informar órgão que não atende ao formato aceito | Rejeita o parâmetro com erro controlado em JSON. |
| ERR-07 | Página inexistente | Acessar uma rota inexistente da API ou uma página fora da faixa disponível | Retorna erro de recurso não encontrado em JSON, sem expor detalhes internos. |
| ERR-08 | Timeout da busca | Forçar consulta acima do tempo limite configurado | Interrompe a operação e retorna erro controlado, mantendo o serviço disponível. |
| ERR-09 | Excesso de buscas simultâneas | Ultrapassar o limite de concorrência definido para a plataforma | Limita ou rejeita o excedente de forma controlada, sem derrubar a API. |
| ERR-10 | Parâmetro desconhecido | Enviar parâmetro que não pertence ao contrato de busca | Rejeita a requisição com mensagem em JSON que identifica o parâmetro inválido. |
| ERR-11 | Valor de limite inválido | Enviar `limit` não numérico, menor que 1 ou maior que 100 | Rejeita ou restringe o valor de forma controlada, sem retornar mais de 100 registros. |
| ERR-12 | Combinação inválida | Combinar filtros com valores incompatíveis ou malformados | Rejeita a requisição com erro controlado em JSON. |

## Verificações comuns

Em cada cenário devem ser registrados:

- rota, parâmetros e método utilizados;
- código HTTP e corpo JSON recebidos;
- tempo de resposta;
- quantidade de registros retornados;
- mensagens de erro sem stack trace, consulta SQL ou credenciais;
- disponibilidade da API após timeout, sobrecarga e entradas hostis;
- integridade e contagens do banco após os testes de segurança.

## Execução posterior

- `QA-02` detalhará os payloads de SQL injection, sem executá-los antecipadamente.
- `QA-03` executará os cenários de concorrência e registrará as medições de carga.
- `QA-05` executará os cenários funcionais e de erro contra a API pronta.
- `QA-06` executará os casos de SQL injection em todos os endpoints.

Registrar a resposta de cada caso e o resultado obtido.
