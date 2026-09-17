# Mapeamento dos campos da aplicação

## Escopo

Este documento define a correspondência dos campos `nome`, `cargo`, `uf` e `orgao` com os conjuntos de Aposentados e Carreiras/Cargos. Os nomes e as posições seguem os dicionários oficiais de [Aposentados](http://repositorio.dados.gov.br/segrt/1.20180829-DadosRecursos-Aposentados.pdf) e [Carreiras/Cargos](http://repositorio.dados.gov.br/segrt/2.20190709-DadosRecursos-Carreiras.pdf).

| Campo da aplicação | Aposentados | Carreiras/Cargos |
|---|---|---|
| `nome` | Campo 1 — `Nome` | Campo 1 — `Nome` |
| `cargo` | Campo 7 — `Cargo` | Campo 4 — `Descrição do Cargo/Emprego` |
| `uf` | Indisponível | Campo 5 — `UF da UPAG de vinculação` |
| `orgao` | Campo 4 — `Nome do órgão` | Campo 6 — `Denominação do Órgão de atuação` |

## Nome

- **Aposentados:** usar o campo `Nome`, que identifica o aposentado.
- **Carreiras/Cargos:** usar o campo `Nome`, que identifica o servidor ou empregado público.

## Cargo

- **Aposentados:** usar o campo `Cargo`, que contém o nome do cargo do qual ocorreu a aposentadoria.
- **Carreiras/Cargos:** usar o campo `Descrição do Cargo/Emprego`, que contém o nome do cargo ou emprego público ocupado.

## UF

- **Aposentados:** não há campo de UF no dicionário. Esse valor não será obtido nem inferido a partir de outros campos desse conjunto.
- **Carreiras/Cargos:** usar o campo `UF da UPAG de vinculação`, que contém a sigla da unidade federativa da unidade pagadora.

## Órgão

- **Aposentados:** usar o campo `Nome do órgão`, que identifica o órgão ao qual o aposentado está vinculado.
- **Carreiras/Cargos:** usar o campo `Denominação do Órgão de atuação`, que identifica o órgão ao qual o servidor ou empregado está vinculado.

Campos como CPF, matrícula, remuneração e demais informações presentes nas fontes não fazem parte deste mapeamento.
