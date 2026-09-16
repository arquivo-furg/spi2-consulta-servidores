import type { PropsWithChildren } from 'react'

const contentWidth = 'mx-auto w-full max-w-6xl px-4 sm:px-6 lg:px-8'

export function Header() {
  return (
    <header className="border-b border-primary-hover bg-primary text-white">
      <div className={`${contentWidth} flex min-h-20 items-center py-4`}>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-highlight-strong">
            Dados abertos
          </p>
          <p className="mt-1 text-lg font-semibold text-white sm:text-xl">
            Gestão de pessoas do Executivo Federal
          </p>
        </div>
      </div>
    </header>
  )
}

export function MainContainer({ children }: PropsWithChildren) {
  return (
    <main className={`${contentWidth} flex-1 py-8 sm:py-12`}>{children}</main>
  )
}

export function Footer() {
  return (
    <footer className="border-t border-border bg-surface">
      <div
        className={`${contentWidth} flex min-h-20 items-center py-4 text-sm text-muted`}
      >
        Dados provenientes do Portal Brasileiro de Dados Abertos.
      </div>
    </footer>
  )
}

export function AppLayout({ children }: PropsWithChildren) {
  return (
    <div className="flex min-h-screen flex-col bg-canvas">
      <Header />
      <MainContainer>{children}</MainContainer>
      <Footer />
    </div>
  )
}
