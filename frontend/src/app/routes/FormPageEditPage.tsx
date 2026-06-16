/**
 * FormPageEdit Page - Edição de Página com Campos
 */

import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { formPagesApi } from '@/lib/api/formPages'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'
import FormPageInfo from '../components/FormPage/FormPageInfo'
import FormFieldList from '../components/FormPage/FormFieldList'

export default function FormPageEditPage() {
  const { id, pageId } = useParams<{ id: string; pageId: string }>()
  const navigate = useNavigate()
  const templateId = parseInt(id || '0')
  const pageIdNum = parseInt(pageId || '0')

  const { data: page, isLoading } = useQuery({
    queryKey: ['form-page', templateId, pageIdNum],
    queryFn: () => formPagesApi.get(templateId, pageIdNum),
    enabled: !!templateId && !!pageIdNum,
  })

  if (isLoading) {
    return <div className="flex items-center justify-center h-64"><div className="text-gray-500">Carregando...</div></div>
  }

  if (!page) {
    return <div className="flex items-center justify-center h-64"><div className="text-red-500">Página não encontrada</div></div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate(`/formularios/${templateId}`)}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Página: {page.nome}</h1>
          <p className="text-gray-500 mt-1">Ordem: {page.ordem}</p>
        </div>
      </div>

      <Tabs defaultValue="info">
        <TabsList>
          <TabsTrigger value="info">Informações da Página</TabsTrigger>
          <TabsTrigger value="fields">Campos</TabsTrigger>
        </TabsList>

        <TabsContent value="info" className="mt-6">
          <FormPageInfo page={page} templateId={templateId} />
        </TabsContent>

        <TabsContent value="fields" className="mt-6">
          <FormFieldList pageId={pageIdNum} templateId={templateId} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
