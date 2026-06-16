/**
 * Dispara download de Blob no navegador.
 */
export function triggerBlobDownload(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

/**
 * Download de arquivo Excel a partir de data URL base64 (upload local ainda não salvo).
 */
export function downloadExcelFromDataUrl(dataUrl: string, filename: string): void {
  const base64 = dataUrl.includes(',') ? dataUrl.split(',')[1] : dataUrl
  const byteChars = atob(base64)
  const bytes = new Uint8Array(byteChars.length)
  for (let i = 0; i < byteChars.length; i++) {
    bytes[i] = byteChars.charCodeAt(i)
  }
  const mime = dataUrl.toLowerCase().includes('application/vnd.ms-excel')
    ? 'application/vnd.ms-excel'
    : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  triggerBlobDownload(new Blob([bytes], { type: mime }), filename)
}

export function mesclagemExcelFilename(formularioNome: string, formularioId: number, dataUrl?: string): string {
  const slug = formularioNome.replace(/[^a-zA-Z0-9]+/g, '-').replace(/^-|-$/g, '').toLowerCase() || 'formulario'
  const ext = dataUrl?.toLowerCase().includes('application/vnd.ms-excel') ? '.xls' : '.xlsx'
  return `template-mesclagem-${slug}-${formularioId}${ext}`
}
