import { StrictMode, useEffect, useState } from 'react'
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

  const response = await fetch(`/api/servidores?${searchParams}`)
  const payload = (await response.json()) as ApiResponse

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

  function atualizarResultados({
    resultados: novosResultados,
    totalPaginas: novoTotalPaginas,
    totalResultados: novoTotalResultados,
  }: Awaited<ReturnType<typeof buscarServidores>>) {
    setResultados(novosResultados)
    setTotalPaginas(novoTotalPaginas)
    setTotalResultados(novoTotalResultados)
  }

  useEffect(() => {
    void buscarServidores(1).then(atualizarResultados)
  }, [])

  function handleSearch(values: SearchFormValues) {
    // Filtro novo sempre começa na página 1, não na página da consulta anterior.
    setFiltros(values)
    setPaginaAtual(1)
    void buscarServidores(1, values).then(atualizarResultados)
  }

  function handlePageChange(page: number) {
    // Reusa os filtros da busca enviada, mesmo se o formulário estiver sendo editado.
    setPaginaAtual(page)
    void buscarServidores(page, filtros).then(atualizarResultados)
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
        <SearchForm onSearch={handleSearch} />
      </section>
      <ResultsList
        resultados={resultados}
        totalResultados={totalResultados}
      />
      {totalPaginas > 1 && (
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
