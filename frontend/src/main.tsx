import { StrictMode, useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { AppLayout } from './components/AppLayout'
import { ResultsList, type Servidor } from './components/ResultsList'
import {
  SearchForm,
  type SearchFormValues,
} from './components/SearchForm'
import './index.css'

async function buscarServidores(values?: SearchFormValues) {
  const searchParams = new URLSearchParams()

  if (values?.nome) {
    if (values.modoNome === 'similar') {
      searchParams.set('similar', values.nome)

      if (values.limite) {
        searchParams.set('limit', values.limite)
      }
    } else {
      searchParams.set('nome', values.nome)
    }
  }

  const search = searchParams.size > 0 ? `?${searchParams}` : ''
  const response = await fetch(`/api/servidores${search}`)

  return response.json() as Promise<Servidor[]>
}

function App() {
  const [resultados, setResultados] = useState<Servidor[]>([])

  useEffect(() => {
    void buscarServidores().then(setResultados)
  }, [])

  function handleSearch(values: SearchFormValues) {
    void buscarServidores(values).then(setResultados)
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
      <ResultsList resultados={resultados} />
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
