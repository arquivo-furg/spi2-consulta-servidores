export interface Servidor {
  id: number
  nome: string
  cargo: string
  uf: string | null
  orgao: string
}

interface ResultsListProps {
  errorMessage: string | null
  hasSearched: boolean
  isLoading: boolean
  resultados: Servidor[]
  totalResultados: number
}

interface ServidorDetailsProps {
  servidor: Servidor
}

// UF nula é ausência na fonte, não um campo para completar com outra informação.
function ServidorDetails({ servidor }: ServidorDetailsProps) {
  return (
    <dl className="mt-4 grid gap-4 border-t border-border pt-4 sm:grid-cols-3">
      <div>
        <dt className="text-xs font-semibold uppercase tracking-wide text-body">
          Cargo
        </dt>
        <dd className="mt-1 break-words text-[15px] text-body">
          {servidor.cargo}
        </dd>
      </div>
      <div>
        <dt className="text-xs font-semibold uppercase tracking-wide text-body">
          UF
        </dt>
        <dd className="mt-1 text-[15px] text-body">
          {servidor.uf ?? 'Não informada'}
        </dd>
      </div>
      <div>
        <dt className="text-xs font-semibold uppercase tracking-wide text-body">
          Órgão
        </dt>
        <dd className="mt-1 break-words text-[15px] text-body">
          {servidor.orgao}
        </dd>
      </div>
    </dl>
  )
}

// Antes da primeira busca, orientar o preenchimento em vez de anunciar resultado vazio.
function EmptyResults({ hasSearched }: { hasSearched: boolean }) {
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
        {hasSearched ? 'Nenhum resultado encontrado' : 'Inicie uma busca'}
      </h2>
      <p className="mt-2 text-[15px] leading-6 text-body">
        {hasSearched
          ? 'Não há registros para os filtros informados.'
          : 'Preencha ao menos um dos filtros acima e clique em Buscar.'}
      </p>
    </section>
  )
}

function LoadingResults() {
  return (
    <section
      aria-busy="true"
      aria-live="polite"
      className="mt-8 flex min-h-32 items-center justify-center gap-3 rounded-panel border border-border bg-surface p-6 text-primary"
      role="status"
    >
      <span
        aria-hidden="true"
        className="size-5 animate-spin rounded-full border-2 border-border border-t-primary motion-reduce:animate-none"
      />
      <span className="text-[15px] font-semibold">Buscando resultados...</span>
    </section>
  )
}

function ErrorResults({ message }: { message: string }) {
  return (
    <section
      aria-labelledby="results-error-title"
      className="mt-8 rounded-panel border border-border bg-surface p-4 sm:p-6"
      role="alert"
    >
      <h2
        className="text-xl font-semibold text-primary sm:text-[23px]"
        id="results-error-title"
      >
        Não foi possível concluir a busca
      </h2>
      <p className="mt-2 break-words text-[15px] leading-6 text-body">
        {message}
      </p>
      <p className="mt-2 text-[15px] leading-6 text-body">
        Ajuste os filtros, se necessário, e tente novamente.
      </p>
    </section>
  )
}

function SingleResult({ servidor }: ServidorDetailsProps) {
  return (
    <section aria-labelledby="single-result-title" className="mt-8">
      <h2
        className="text-xl font-semibold text-primary sm:text-[23px]"
        id="single-result-title"
      >
        Resultado encontrado
      </h2>
      <article className="mt-5 rounded-panel border border-border bg-surface p-4 sm:p-6">
        <h3 className="break-words text-lg font-semibold text-primary">
          {servidor.nome}
        </h3>
        <ServidorDetails servidor={servidor} />
      </article>
    </section>
  )
}

export function ResultsList({
  errorMessage,
  hasSearched,
  isLoading,
  resultados,
  totalResultados,
}: ResultsListProps) {
  if (isLoading) {
    return <LoadingResults />
  }

  if (errorMessage) {
    return <ErrorResults message={errorMessage} />
  }

  if (resultados.length === 0) {
    return <EmptyResults hasSearched={hasSearched} />
  }

  // Uma última página com uma linha não significa que só existe um resultado no total.
  if (totalResultados === 1 && resultados.length === 1) {
    return <SingleResult servidor={resultados[0]} />
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
        {totalResultados}{' '}
        {totalResultados === 1
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
            <ServidorDetails servidor={resultado} />
          </li>
        ))}
      </ul>
    </section>
  )
}
