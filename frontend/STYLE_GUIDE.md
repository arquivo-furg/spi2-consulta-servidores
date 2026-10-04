# Guia de estilo do frontend

A identidade visual toma como referência as páginas de [Aposentados](https://dados.gov.br/dados/conjuntos-dados/gestao-de-pessoas-executivo-federal--aposentados) e [Carreiras e Cargos](https://dados.gov.br/dados/conjuntos-dados/gestao-de-pessoas-executivo-federal---carreiras--cargos) do Portal Brasileiro de Dados Abertos. Usamos azul, amarelo e fundo claro, seguindo a referência do portal. Os títulos e os espaços entre os elementos organizam a tela.

## Paleta

| Token | Cor | Uso |
|---|---|---|
| `primary` | `#0C326F` | Títulos, botões principais e ícones de destaque |
| `primary-hover` | `#0C4196` | Estado de interação dos elementos principais |
| `link` | `#1351B4` | Links e ações textuais |
| `highlight` | `#ECDA3C` | Detalhes gráficos e sinalização secundária |
| `highlight-strong` | `#F9E74D` | Etiquetas e destaques sobre o azul principal |
| `highlight-hover` | `#FFE80E` | Estado de interação dos destaques amarelos |
| `surface` | `#FFFFFF` | Painéis e áreas de conteúdo |
| `canvas` | `#F7FAFC` | Fundo geral das páginas |
| `heading` | `#000000` | Títulos quando o azul principal não for usado |
| `body` | `#464646` | Texto corrido |
| `muted` | `#6B6B6B` | Metadados e textos secundários não essenciais |
| `disabled` | `#B0B0B0` | Estados desabilitados |
| `border` | `#E7E7E7` | Divisores e contornos sutis |

Use texto branco sobre o azul principal e texto azul principal sobre os amarelos. Reserve `muted` para textos secundários e `disabled` para controles inativos; informações essenciais devem usar `body` ou uma cor mais escura.

## Tipografia

A família principal é `Inter`, com fontes sem serifa do sistema como alternativas. Use pesos `400`, `500` e `600`.

| Finalidade | Tamanho |
|---|---|
| Título principal | `30px` |
| Título de painel | `23px` |
| Conteúdo destacado | `18px` |
| Texto e metadados | `15px` |
| Microtexto | `12px` a `13px` |

## Formas e superfícies

- Painéis usam fundo branco, borda sutil e raio de `15px`.
- Etiquetas e botões em formato de pílula usam raio total.
- A hierarquia deve vir de cor, tipografia e espaçamento, com pouco ou nenhum uso de sombra.
- Estados de interação mantêm contraste visível por meio das cores `primary-hover` e `highlight-hover`.

Os tokens estão declarados no tema do Tailwind e ficam disponíveis em utilitários como `bg-primary`, `text-body`, `border-border`, `rounded-panel` e `rounded-pill`.
