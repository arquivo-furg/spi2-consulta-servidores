export interface Servidor {
  id: number
  nome: string
  cargo: string
  uf: string | null
  orgao: string
}

interface ResultsListProps {
  resultados: Servidor[]
}

function EmptyResults() {
  return (
    <section
      aria-labelledby="results-feedback-title"
      className="mt-8 rounded-panel border border-border bg-surface p-4 text-center sm:p-6"
      role="status"
    >
      <h2
        className="text-xl font-semibold text-primary sm:text-[23px]"
        id="results-feedback-title"
      >
        Nenhum resultado encontrado
      </h2>
      <p className="mt-2 text-[15px] leading-6 text-body">
        Não há registros para os filtros informados.
      </p>
    </section>
  )
}

export function ResultsList({ resultados }: ResultsListProps) {
  if (resultados.length === 0) {
    return <EmptyResults />
  }

  return (
    <section aria-labelledby="results-title" className="mt-8">
      <h2
        id="results-title"
        className="text-xl font-semibold text-primary sm:text-[23px]"
      >
        Resultados
      </h2>
      <p className="mt-2 text-[15px] text-body">
        {resultados.length}{' '}
        {resultados.length === 1
          ? 'registro encontrado.'
          : 'registros encontrados.'}
      </p>
      <ul className="mt-5 grid gap-4">
        {resultados.map((resultado) => (
          <li
            key={resultado.id}
            className="rounded-panel border border-border bg-surface p-4 sm:p-6"
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
    </section>
  )
}
