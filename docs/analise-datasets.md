# Análise inicial dos datasets

## Escopo e fontes

Em 13/09/2026 foram baixados e inspecionados os recursos mensais regulares dos conjuntos [Gestão de Pessoas - Aposentados](https://dados.gov.br/dados/conjuntos-dados/gestao-de-pessoas-executivo-federal--aposentados) e [Gestão de Pessoas - Carreiras/Cargos](https://dados.gov.br/dados/conjuntos-dados/gestao-de-pessoas-executivo-federal---carreiras--cargos), considerando o período de setembro de 2025 a agosto de 2026.

Os downloads partiram dos endereços HTTP do repositório oficial e seguiram o redirecionamento fornecido pelo servidor. A estrutura foi confrontada com os dicionários de dados de [Aposentados](http://repositorio.dados.gov.br/segrt/1.20180829-DadosRecursos-Aposentados.pdf) e [Carreiras/Cargos](http://repositorio.dados.gov.br/segrt/2.20190709-DadosRecursos-Carreiras.pdf).

O script `db/baixar_dados.py` reúne os links usados em duas listas fixas e cria as pastas para os arquivos. Seu uso é opcional; os mesmos endereços podem ser baixados manualmente.

Padrões dos endereços consultados:

- setembro a dezembro de 2025: `http://repositorio.dados.gov.br/segrt/APOSENTADOS_MM2025.csv` e `http://repositorio.dados.gov.br/segrt/CARREIRA_MM2025.txt`;
- janeiro a agosto de 2026: `http://repositorio.dados.gov.br/segrt/Aposentados/2026/APOSENTADOS_MM2026.csv` e `http://repositorio.dados.gov.br/segrt/Cargos%20e%20Carreiras/2026/CARREIRA_MM2026.txt`.

Os dados brutos contêm nomes e CPFs descaracterizados. Por isso, foram mantidos apenas no ambiente local e nenhum registro pessoal foi incluído nesta análise.

## Disponibilidade e volume

As contagens abaixo excluem cabeçalhos e linhas de identificação. Os onze recursos disponíveis de Aposentados totalizaram 2.639.896 bytes; os onze de Carreiras/Cargos, 2.215.743.148 bytes.

| Competência | Aposentados: bytes / registros | Carreiras/Cargos: bytes / registros |
|---|---:|---:|
| 09/2025 | 318.010 / 770 | 201.911.606 / 1.088.364 |
| 10/2025 | 327.096 / 792 | 202.595.662 / 1.090.280 |
| 11/2025 | 353.115 / 855 | 202.748.554 / 1.091.102 |
| 12/2025 | 0 / 0 | 202.862.136 / 1.092.065 |
| 01/2026 | 281.666 / 682 | 200.216.065 / 1.082.247 |
| 02/2026 | 179.242 / 434 | 200.377.570 / 1.083.120 |
| 03/2026 | 221.368 / 536 | 200.314.300 / 1.082.778 |
| 04/2026 | 232.106 / 562 | 200.669.500 / 1.084.698 |
| 05/2026 | 242.844 / 588 | 200.781.425 / 1.085.303 |
| 06/2026 | 204.848 / 496 | 201.425.595 / 1.088.785 |
| 07/2026 | 279.601 / 677 | 201.840.735 / 1.091.029 |
| 08/2026 | indisponível (HTTP 404) | indisponível (HTTP 404) |

O recurso de Aposentados de dezembro de 2025 existe no índice oficial, mas é um arquivo vazio. Em 13/09/2026, os dois recursos de agosto de 2026 ainda não estavam publicados; os diretórios oficiais terminavam em julho e os endereços esperados retornavam HTTP 404.

## Estrutura de Aposentados

- Formato CSV sem cabeçalho.
- Codificação Latin-1, incompatível com leitura direta como UTF-8.
- Dezoito campos separados por ponto e vírgula.
- Cada linha observada possui 412 bytes antes da quebra LF e termina com um byte NUL.

Campos, na ordem definida pelo dicionário:

1. Nome
2. CPF
3. Matrícula do Servidor
4. Nome do órgão
5. Sigla do órgão
6. Código do órgão superior
7. Cargo
8. Classe
9. Padrão
10. Referência
11. Nível
12. Tipo de Aposentadoria
13. Fundamentação da inatividade
14. Nome Diploma Legal
15. Data de publicação do Diploma Legal
16. Ocorrência de ingresso no serviço público
17. Data da ocorrência de ingresso no serviço público
18. Valor do Rendimento Líquido

## Estrutura de Carreiras/Cargos

- Formato TXT em Latin-1, com campos separados por ponto e vírgula.
- Oito campos de dados e um ponto e vírgula ao final de cada linha; um parser ingênuo produzirá um nono valor vazio.
- Nos recursos de 2025, o cabeçalho ocupa a primeira linha.
- Nos recursos de 2026, a primeira linha identifica a competência no formato `CARREIRA.MMYYYY` e o cabeçalho ocupa a segunda linha.
- O campo de mês aparece vazio em uma pequena parcela dos registros. Em setembro de 2025 também foram observadas as formas `9` e `09`; nas demais competências preenchidas, o valor usa dois dígitos.

Campos, na ordem definida pelo dicionário:

1. Nome
2. CPF
3. Código da Carreira
4. Descrição do Cargo/Emprego
5. UF da UPAG de vinculação
6. Denominação do Órgão de atuação
7. Mês de referência
8. Valor da Remuneração

## Pontos de atenção

- A leitura precisa informar explicitamente a codificação Latin-1.
- Aposentados não fornece cabeçalho; os nomes das colunas devem seguir a ordem do dicionário.
- Carreiras/Cargos exige tratamento diferente para as linhas iniciais de 2025 e 2026 e deve ignorar o campo vazio criado pelo delimitador final.
- A competência 12/2025 de Aposentados não possui registros e as competências 08/2026 ainda dependem de publicação pela fonte oficial.
