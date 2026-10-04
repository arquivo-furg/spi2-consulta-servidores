interface PaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
}

const buttonClassName =
  'min-h-11 min-w-11 rounded-pill border border-primary px-4 text-sm font-semibold text-primary transition-colors hover:bg-primary hover:text-white focus:outline-none focus:ring-2 focus:ring-link focus:ring-offset-2 disabled:cursor-not-allowed disabled:border-border disabled:bg-surface disabled:text-disabled'

export function Pagination({
  currentPage,
  totalPages,
  onPageChange,
}: PaginationProps) {
  // Mostra até cinco páginas, deslocando a faixa quando chega perto do fim.
  const firstPage = Math.max(1, Math.min(currentPage - 2, totalPages - 4))
  const visiblePages = Math.min(5, totalPages)
  const pages = Array.from(
    { length: visiblePages },
    (_, index) => firstPage + index,
  )

  return (
    <nav
      aria-label="Paginação dos resultados"
      className="mt-5 grid grid-cols-2 gap-2 sm:flex sm:flex-wrap sm:items-center sm:justify-center"
    >
      <button
        className={`${buttonClassName} w-full sm:w-auto`}
        disabled={currentPage === 1}
        onClick={() => onPageChange(currentPage - 1)}
        type="button"
      >
        Anterior
      </button>

      <div className="col-span-2 row-start-2 flex flex-wrap justify-center gap-2 sm:contents">
        {pages.map((page) => (
          <button
            aria-current={page === currentPage ? 'page' : undefined}
            aria-label={`Página ${page}`}
            className={`size-11 rounded-pill border text-sm font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-link focus:ring-offset-2 ${
              page === currentPage
                ? 'border-primary bg-primary text-white'
                : 'border-primary bg-surface text-primary hover:bg-primary-hover hover:text-white'
            }`}
            key={page}
            onClick={() => onPageChange(page)}
            type="button"
          >
            {page}
          </button>
        ))}
      </div>

      <button
        className={`${buttonClassName} col-start-2 row-start-1 w-full sm:w-auto`}
        disabled={currentPage === totalPages}
        onClick={() => onPageChange(currentPage + 1)}
        type="button"
      >
        Próxima
      </button>
    </nav>
  )
}
