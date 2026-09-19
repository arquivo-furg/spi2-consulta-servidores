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

export function ResultsList() {
  return (
    <section aria-labelledby="results-title" className="mt-8">
      <h2 id="results-title" className="text-[23px] font-semibold text-primary">
        Resultados de exemplo
      </h2>
      <p className="mt-2 text-[15px] text-body">
        Os registros abaixo são fictícios.
      </p>
      <ul className="mt-5 grid gap-4">
        {resultadosMockados.map((resultado) => (
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
    </section>
  )
}
