import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'

const root = document.getElementById('root')

if (!root) {
  throw new Error('Elemento raiz nao encontrado')
}

createRoot(root).render(
  <StrictMode>
    <main className="grid min-h-screen place-items-center">
      <h1 className="text-2xl font-semibold">Frontend configurado</h1>
    </main>
  </StrictMode>,
)
