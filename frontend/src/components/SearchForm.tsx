const fieldClassName =
  'mt-2 min-h-12 min-w-0 w-full rounded-lg border border-border bg-surface px-4 py-3 text-[15px] font-normal text-body outline-none transition-colors placeholder:text-muted hover:border-disabled focus:border-link focus:ring-2 focus:ring-link/20'

const labelClassName = 'block min-w-0 text-[15px] font-semibold text-primary'

const estados = [
  'AC',
  'AL',
  'AP',
  'AM',
  'BA',
  'CE',
  'DF',
  'ES',
  'GO',
  'MA',
  'MT',
  'MS',
  'MG',
  'PA',
  'PB',
  'PR',
  'PE',
  'PI',
  'RJ',
  'RN',
  'RS',
  'RO',
  'RR',
  'SC',
  'SP',
  'SE',
  'TO',
]

export function SearchForm() {
  return (
    <form
      aria-label="Filtros de busca"
      className="mt-8 grid min-w-0 gap-5 rounded-panel border border-border bg-canvas p-5 md:grid-cols-2 md:p-6"
    >
      <label className={labelClassName}>
        Nome
        <input
          className={fieldClassName}
          name="nome"
          placeholder="Digite o nome"
          type="text"
        />
      </label>

      <label className={labelClassName}>
        Cargo
        <input
          className={fieldClassName}
          name="cargo"
          placeholder="Digite o cargo"
          type="text"
        />
      </label>

      <label className={labelClassName}>
        UF
        <select
          className={`${fieldClassName} cursor-pointer`}
          defaultValue=""
          name="uf"
        >
          <option value="">Selecione a UF</option>
          {estados.map((estado) => (
            <option key={estado} value={estado}>
              {estado}
            </option>
          ))}
        </select>
      </label>

      <label className={labelClassName}>
        Órgão
        <input
          className={fieldClassName}
          name="orgao"
          placeholder="Digite o órgão"
          type="text"
        />
      </label>
    </form>
  )
}
