# Validação do Docker Compose

Data da execução: 18/09/2026.

## Subida dos containers

O comando abaixo construiu as imagens e iniciou os três serviços sem erros:

```bash
docker compose up --build --detach
```

O comando `docker compose ps` confirmou `db`, `backend` e `frontend` no estado `running`.

## Comunicação na rede interna

A comunicação básica foi verificada pelos nomes dos serviços na rede padrão do Compose:

```text
db -> backend: 1 pacote transmitido, 1 recebido, 0% de perda
db -> frontend: 1 pacote transmitido, 1 recebido, 0% de perda
backend -> db: nome resolvido na rede interna
backend -> frontend: nome resolvido na rede interna
frontend -> db: nome resolvido na rede interna
frontend -> backend: nome resolvido na rede interna
```

Os containers permanecem com os comandos provisórios definidos no esqueleto da infraestrutura. A inicialização dos serviços da aplicação será feita nas tasks específicas de backend, banco e frontend.
