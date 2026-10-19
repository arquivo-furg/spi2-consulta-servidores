import { StrictMode, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { AppLayout } from './components/AppLayout'
import { Pagination } from './components/Pagination'
import { ResultsList, type Servidor } from './components/ResultsList'
import {
  SearchForm,
  type SearchFormValues,
} from './components/SearchForm'
import './index.css'

const PAGE_SIZE = 10

interface ApiResponse {
  sucesso: boolean
  mensagem: string
  dados: Servidor[] | null
  paginacao?: {
    pagina: number
    tamanho_pagina: number
    total_registros: number
    total_paginas: number
  }
}

function isServidor(payload: unknown): payload is Servidor {
  if (!payload || typeof payload !== 'object') {
    return false
  }

  const candidate = payload as Partial<Servidor>

  return (
    typeof candidate.id === 'number' &&
    typeof candidate.nome === 'string' &&
    typeof candidate.cargo === 'string' &&
    (typeof candidate.uf === 'string' || candidate.uf === null) &&
    typeof candidate.orgao === 'string'
  )
}

function isPagination(payload: unknown): payload is ApiResponse['paginacao'] {
  if (!payload || typeof payload !== 'object') {
    return false
  }

  const candidate = payload as NonNullable<ApiResponse['paginacao']>

  return (
    typeof candidate.pagina === 'number' &&
    typeof candidate.tamanho_pagina === 'number' &&
    typeof candidate.total_registros === 'number' &&
    typeof candidate.total_paginas === 'number'
  )
}

// O JSON vem de fora do TypeScript; conferir o formato antes de usar na tela.
function isApiResponse(payload: unknown): payload is ApiResponse {
  if (!payload || typeof payload !== 'object') {
    return false
  }

  const candidate = payload as Partial<ApiResponse>

  if (
    typeof candidate.sucesso !== 'boolean' ||
    typeof candidate.mensagem !== 'string' ||
    !('dados' in candidate) ||
    (candidate.paginacao !== undefined &&
      !isPagination(candidate.paginacao))
  ) {
    return false
  }

  return candidate.sucesso
    ? Array.isArray(candidate.dados) && candidate.dados.every(isServidor)
    : candidate.dados === null
}

async function buscarServidores(page: number, values?: SearchFormValues) {
  const searchParams = new URLSearchParams()

  if (values) {
    // O mesmo campo de nome vira nome ou similar, conforme a opção do formulário.
    if (values.nome) {
      if (values.modoNome === 'similar') {
        searchParams.set('similar', values.nome)

        if (values.limite) {
          searchParams.set('limit', values.limite)
        }
      } else {
        searchParams.set('nome', values.nome)
      }
    }

    const exactFilters = [
      ['cargo', values.cargo],
      ['uf', values.uf],
      ['orgao', values.orgao],
    ]

    for (const [parameter, value] of exactFilters) {
      if (value) {
        searchParams.set(parameter, value)
      }
    }
  }

  searchParams.set('page', String(page))
  searchParams.set('page_size', String(PAGE_SIZE))

  let response: Response

  try {
    response = await fetch(`/api/servidores?${searchParams}`)
  } catch {
    throw new Error('Não foi possível conectar ao serviço de dados.')
  }

  let payload: unknown

  try {
    payload = await response.json()
  } catch {
    throw new Error('O serviço retornou uma resposta inválida.')
  }

  if (!isApiResponse(payload)) {
    throw new Error('O serviço retornou uma resposta inválida.')
  }

  // Busca sem registros vira lista vazia; página inexistente continua sendo erro.
  if (
    response.status === 404 &&
    !payload.sucesso &&
    payload.mensagem !== 'pagina inexistente'
  ) {
    return {
      resultados: [],
      totalPaginas: 0,
      totalResultados: 0,
    }
  }

  if (!response.ok || !payload.sucesso) {
    throw new Error(payload.mensagem || 'Não foi possível concluir a busca.')
  }

  return {
    resultados: payload.dados ?? [],
    totalPaginas: payload.paginacao?.total_paginas ?? 0,
    totalResultados: payload.paginacao?.total_registros ?? 0,
  }
}

function App() {
  const [filtros, setFiltros] = useState<SearchFormValues>()
  const [paginaAtual, setPaginaAtual] = useState(1)
  const [resultados, setResultados] = useState<Servidor[]>([])
  const [totalPaginas, setTotalPaginas] = useState(0)
  const [totalResultados, setTotalResultados] = useState(0)
  const [emCarregamento, setEmCarregamento] = useState(false)
  const [mensagemErro, setMensagemErro] = useState<string | null>(null)

  function atualizarResultados({
    resultados: novosResultados,
    totalPaginas: novoTotalPaginas,
    totalResultados: novoTotalResultados,
  }: Awaited<ReturnType<typeof buscarServidores>>) {
    setResultados(novosResultados)
    setTotalPaginas(novoTotalPaginas)
    setTotalResultados(novoTotalResultados)
  }

  async function executarBusca(page: number, values?: SearchFormValues) {
    setEmCarregamento(true)
    setMensagemErro(null)

    try {
      const resposta = await buscarServidores(page, values)
      atualizarResultados(resposta)
    } catch (error) {
      setResultados([])
      setTotalPaginas(0)
      setTotalResultados(0)
      setMensagemErro(
        error instanceof Error
          ? error.message
          : 'Não foi possível concluir a busca.',
      )
    } finally {
      setEmCarregamento(false)
    }
  }

  function handleSearch(values: SearchFormValues) {
    // Filtro novo sempre começa na página 1, não na página da consulta anterior.
    setFiltros(values)
    setPaginaAtual(1)

    if (!values.nome && !values.cargo && !values.uf && !values.orgao) {
      setResultados([])
      setTotalPaginas(0)
      setTotalResultados(0)
      setMensagemErro('Informe ao menos um filtro para realizar a busca.')
      return
    }

    void executarBusca(1, values)
  }

  function handlePageChange(page: number) {
    // Reusa os filtros da busca enviada, mesmo se o formulário estiver sendo editado.
    setPaginaAtual(page)
    void executarBusca(page, filtros)
  }

  return (
    <AppLayout>
      <section
        aria-labelledby="page-title"
        className="rounded-panel border border-border bg-surface p-4 sm:p-8"
      >
        <p className="text-sm font-semibold uppercase tracking-wide text-link">
          Consulta pública
        </p>
        <h1
          id="page-title"
          className="mt-2 text-2xl font-semibold leading-tight sm:text-3xl"
        >
          Dados de pessoal do Executivo Federal
        </h1>
        <p className="mt-4 max-w-3xl text-[15px] leading-6 text-body sm:text-base sm:leading-7">
          Consulte informações de aposentados, carreiras e cargos em uma
          interface simples e organizada.
        </p>
        <SearchForm isLoading={emCarregamento} onSearch={handleSearch} />
      </section>
      <ResultsList
        errorMessage={mensagemErro}
        hasSearched={filtros !== undefined}
        isLoading={emCarregamento}
        resultados={resultados}
        totalResultados={totalResultados}
      />
      {!emCarregamento && !mensagemErro && totalPaginas > 1 && (
        <Pagination
          currentPage={paginaAtual}
          onPageChange={handlePageChange}
          totalPages={totalPaginas}
        />
      )}
    </AppLayout>
  )
}

const root = document.getElementById('root')

if (!root) {
  throw new Error('Elemento raiz nao encontrado')
}

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
