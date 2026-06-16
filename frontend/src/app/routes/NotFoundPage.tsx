/**
 * Not Found Page - 404
 */

import { Link } from 'react-router-dom'
import { Home, ArrowLeft } from 'lucide-react'

export default function NotFoundPage() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4">
      <div className="text-center">
        <h1 className="text-9xl font-bold text-primary">404</h1>
        <h2 className="text-3xl font-bold text-gray-900 mt-4 mb-2">
          Página não encontrada
        </h2>
        <p className="text-gray-600 mb-8 max-w-md mx-auto">
          Desculpe, a página que você está procurando não existe ou foi movida.
        </p>

        <div className="flex items-center justify-center space-x-4">
          <Link
            to="/"
            className="btn-primary flex items-center"
          >
            <Home size={20} className="mr-2" />
            Ir para o Dashboard
          </Link>
          <button
            onClick={() => window.history.back()}
            className="btn-secondary flex items-center"
          >
            <ArrowLeft size={20} className="mr-2" />
            Voltar
          </button>
        </div>
      </div>
    </div>
  )
}
