# Encerra processos EXCEL.EXE órfãos após falha na exportação COM.
# Executar como administrador se necessário:
#   powershell -ExecutionPolicy Bypass -File backend\scripts\kill_orphan_excel.ps1

$processes = Get-Process -Name EXCEL -ErrorAction SilentlyContinue
if (-not $processes) {
    Write-Host "Nenhum processo EXCEL.EXE em execucao."
    exit 0
}

Write-Host "Encerrando $($processes.Count) processo(s) EXCEL.EXE..."
$processes | Stop-Process -Force
Write-Host "Concluido."
