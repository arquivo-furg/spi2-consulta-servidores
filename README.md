# Consulta de servidores públicos

Trabalho de Sistemas para Internet II, desenvolvido por Pedro Machado, Marcos
Freitas e Alexsander Santos. A aplicação consulta informações dos conjuntos de
Aposentados e Carreiras/Cargos do Portal Brasileiro de Dados Abertos.

- `backend/`: API em Python, Flask e Gunicorn.
- `frontend/`: interface em React, TypeScript e Tailwind.
- `desktop/`: cliente Python/Tkinter para Windows e Linux, usando a mesma API.
- `db/`: tabelas, índices e scripts de tratamento e importação.
- `docs/`: documentação e relatório.

## Primeira execução

Para a web e a importação pelo container, instale Docker com o plugin Compose.
No Windows, inicie o Docker Desktop com containers Linux. Não é necessário
instalar Node, PostgreSQL ou Python no computador para esse caminho.
Baixe e extraia o projeto (ou clone o repositório) e entre na raiz.
Antes da primeira execução, coloque os datasets baixados manualmente nestas pastas:

```text
dados/
  aposentados/APOSENTADOS_MMYYYY.csv
  carreiras/CARREIRA_MMYYYY.txt
```

O recorte é de setembro de 2025 a agosto de 2026. Use os arquivos mensais
completos das duas fontes disponíveis no período, não apenas um par mensal.
Na coleta, agosto de 2026 estava indisponível; os 22 arquivos de setembro de
2025 a julho de 2026 somam cerca de 2,2 GB. Mantenha também o arquivo vazio
de Aposentados de dezembro de 2025. Os endereços HTTP e as competências estão
na [análise dos datasets](docs/analise-datasets.md).

Se os arquivos já estiverem em outra pasta ou em um pendrive, copie os CSVs
para `dados/aposentados/` e os TXTs para `dados/carreiras/`, mantendo os nomes.
O tratamento não move os arquivos brutos; ele lê essas pastas e organiza os
registros no banco.

Para baixar os arquivos, há também um script opcional com duas listas de
links HTTP fixos. Com Python instalado, execute `python db/baixar_dados.py`.
Ele cria as duas pastas e mantém os arquivos que já existem. Esse script não
é executado pelo Compose e não é necessário se os dados já estiverem disponíveis.

Os arquivos brutos e o banco preenchido não vêm no Git ou no ZIP. Eles podem
ser baixados da fonte ou copiados de uma coleta já realizada. A aplicação
não baixa arquivos do portal durante a inicialização.

Com o Docker em execução e os dados na pasta, rode:

```bash
docker compose up --build
```

Interface: http://localhost:5173. API: http://localhost:8000/health.
O Compose fornece valores locais para o banco. Um arquivo `.env` pode
substituí-los; os nomes das variáveis estão em `.env.example`. Não é obrigatório
criar um `.env` para testar com os valores locais. As portas 8000, 5173 e 5433
precisam estar livres; `DB_HOST_PORT` permite mudar só a porta publicada do banco.

A primeira inicialização trata todos os meses locais, gera um CSV temporário
e importa os registros no PostgreSQL. Aguarde a conclusão mostrada nos logs;
a API e o frontend só são liberados depois da carga. Se faltarem arquivos ou
o tratamento não produzir registros válidos, a inicialização informa o erro.

O tratamento remove repetições de nome, cargo, órgão e UF entre competências.
Mudanças nesses campos permanecem como registros distintos. Os arquivos brutos
são lidos sem alterações, e o CSV intermediário é descartado ao terminar.

Nas próximas inicializações, o banco já preenchido é reutilizado, sem tratar
ou importar novamente. Retome os mesmos contêineres com `stop/start` para preservar a carga.

### Conferir o funcionamento

Abra http://localhost:5173, escolha uma UF existente no arquivo importado e clique
em Buscar. Confira os resultados e a próxima página. A rota
http://localhost:8000/health deve responder com `sucesso: true`.
Para verificar o estado dos serviços, use `docker compose ps`;
para interromper e retomar os mesmos containers, use `docker compose stop`
e depois `docker compose start`.

Faça backup antes de remover um banco necessário.

O cliente desktop é executado fora do Docker. Os pacotes Windows e Linux
incluem seu próprio Python/Tkinter; para rodar ou compilar pelo código, siga
[as instruções do desktop](desktop/README.md). A API e os dados continuam necessários.

## Documentação

- [API e exemplos](backend/README.md)
- [Execução e compilação do desktop](desktop/README.md)
- [Campos dos conjuntos públicos](docs/mapeamento-campos.md)
- [Plano de testes](docs/plano-testes.md)
- [Relatório](docs/relatorio-final.pdf)


## Contribuições

Cada entrega é desenvolvida em uma branch. Use Conventional Commits, por
exemplo `feat(frontend): adiciona paginação`. Pedro revisa e integra as
alterações em `dev`. Uma branch pode reunir vários commits relacionados.
As tarefas de infraestrutura, banco/API, interfaces, testes, desktop e relatório
são mapeadas no Jira.
