import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { AppLayout } from './components/AppLayout'
import { ResultsList } from './components/ResultsList'
import { SearchForm } from './components/SearchForm'
import './index.css'

const root = document.getElementById('root')

if (!root) {
  throw new Error('Elemento raiz nao encontrado')
}

createRoot(root).render(
  <StrictMode>
    <AppLayout>
      <section
        aria-labelledby="page-title"
        className="rounded-panel border border-border bg-surface p-6 sm:p-8"
      >
        <p className="text-sm font-semibold uppercase tracking-wide text-link">
          Consulta pública
        </p>
        <h1 id="page-title" className="mt-2 text-3xl font-semibold">
          Dados de pessoal do Executivo Federal
        </h1>
        <p className="mt-4 max-w-3xl text-base leading-7 text-body">
          Consulte informações de aposentados, carreiras e cargos em uma
          interface simples e organizada.
        </p>
        <SearchForm />
      </section>
      <ResultsList />
    </AppLayout>
  </StrictMode>,
)
