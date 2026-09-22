import { useState } from 'react'
import { Pagination } from './Pagination'

const resultadosMockados = [
  {
    id: 1,
    nome: 'Pessoa Exemplo 1',
    cargo: 'Analista administrativo',
    uf: 'DF',
    orgao: 'Órgão Exemplo A',
  },
  {
    id: 2,
    nome: 'Pessoa Exemplo 2',
    cargo: 'Técnico em assuntos educacionais',
    uf: 'SP',
    orgao: 'Órgão Exemplo B',
  },
  {
    id: 3,
    nome: 'Pessoa Exemplo 3',
    cargo: 'Assistente em administração',
    uf: 'RJ',
    orgao: 'Órgão Exemplo C',
  },
]

const itensPorPagina = 2

type ResultsView = 'results' | 'empty' | 'error'

const viewOptions: { label: string; value: ResultsView }[] = [
  { label: 'Resultados', value: 'results' },
  { label: 'Nenhum resultado', value: 'empty' },
  { label: 'Erro na busca', value: 'error' },
]

function ResultsFeedback({ view }: { view: Exclude<ResultsView, 'results'> }) {
  const isError = view === 'error'

  return (
    <section
      aria-labelledby="results-feedback-title"
      className="mt-8 rounded-panel border border-border bg-surface p-6 text-center"
      role={isError ? 'alert' : 'status'}
    >
      <h2
        className="text-[23px] font-semibold text-primary"
        id="results-feedback-title"
      >
        {isError ? 'Erro na busca' : 'Nenhum resultado encontrado'}
      </h2>
      <p className="mt-2 text-[15px] leading-6 text-body">
        {isError
          ? 'Não foi possível concluir a busca simulada. Tente novamente.'
          : 'Não há registros fictícios para os filtros informados.'}
      </p>
    </section>
  )
}

export function ResultsList() {
  const [currentPage, setCurrentPage] = useState(1)
  const [view, setView] = useState<ResultsView>('results')
  const totalPages = Math.ceil(resultadosMockados.length / itensPorPagina)
  const firstItem = (currentPage - 1) * itensPorPagina
  const resultadosDaPagina = resultadosMockados.slice(
    firstItem,
    firstItem + itensPorPagina,
  )

  const resultsContent = (
    <section aria-labelledby="results-title" className="mt-8">
      <h2 id="results-title" className="text-[23px] font-semibold text-primary">
        Resultados de exemplo
      </h2>
      <p className="mt-2 text-[15px] text-body">
        Os registros abaixo são fictícios.
      </p>
      <ul className="mt-5 grid gap-4">
        {resultadosDaPagina.map((resultado) => (
          <li
            key={resultado.id}
            className="rounded-panel border border-border bg-surface p-5 sm:p-6"
          >
            <h3 className="break-words text-lg font-semibold text-primary">
              {resultado.nome}
            </h3>
            <dl className="mt-4 grid gap-4 border-t border-border pt-4 sm:grid-cols-3">
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-body">
                  Cargo
                </dt>
                <dd className="mt-1 break-words text-[15px] text-body">
                  {resultado.cargo}
                </dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-body">
                  UF
                </dt>
                <dd className="mt-1 text-[15px] text-body">{resultado.uf}</dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-body">
                  Órgão
                </dt>
                <dd className="mt-1 break-words text-[15px] text-body">
                  {resultado.orgao}
                </dd>
              </div>
            </dl>
          </li>
        ))}
      </ul>
      <Pagination
        currentPage={currentPage}
        onPageChange={setCurrentPage}
        totalPages={totalPages}
      />
    </section>
  )

  return (
    <>
      <div className="mt-8 rounded-panel border border-border bg-surface p-4">
        <p className="text-sm font-semibold text-primary">
          Simulação da listagem
        </p>
        <div
          aria-label="Selecionar estado simulado dos resultados"
          className="mt-3 flex flex-wrap gap-2"
          role="group"
        >
          {viewOptions.map((option) => (
            <button
              aria-pressed={view === option.value}
              className={`min-h-10 rounded-pill border px-4 text-sm font-semibold transition-colors ${
                view === option.value
                  ? 'border-primary bg-primary text-white'
                  : 'border-primary bg-surface text-primary hover:bg-primary-hover hover:text-white'
              }`}
              key={option.value}
              onClick={() => setView(option.value)}
              type="button"
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {view === 'results' ? resultsContent : <ResultsFeedback view={view} />}
    </>
  )
}
