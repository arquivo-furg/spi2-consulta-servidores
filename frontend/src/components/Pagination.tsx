interface PaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
}

const buttonClassName =
  'min-h-10 rounded-pill border border-primary px-4 text-sm font-semibold text-primary transition-colors hover:bg-primary hover:text-white disabled:cursor-not-allowed disabled:border-border disabled:bg-surface disabled:text-disabled'

export function Pagination({
  currentPage,
  totalPages,
  onPageChange,
}: PaginationProps) {
  const pages = Array.from({ length: totalPages }, (_, index) => index + 1)

  return (
    <nav
      aria-label="Paginação dos resultados"
      className="mt-5 flex flex-wrap items-center justify-center gap-2"
    >
      <button
        className={buttonClassName}
        disabled={currentPage === 1}
        onClick={() => onPageChange(currentPage - 1)}
        type="button"
      >
        Anterior
      </button>

      {pages.map((page) => (
        <button
          aria-current={page === currentPage ? 'page' : undefined}
          aria-label={`Página ${page}`}
          className={`size-10 rounded-pill border text-sm font-semibold transition-colors ${
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

      <button
        className={buttonClassName}
        disabled={currentPage === totalPages}
        onClick={() => onPageChange(currentPage + 1)}
        type="button"
      >
        Próxima
      </button>
    </nav>
  )
}
