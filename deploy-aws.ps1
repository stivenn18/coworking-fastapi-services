# ==============================================================================
# Script para Desplegar la Arquitectura Serverless a AWS Cloud
# ==============================================================================

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " INICIANDO DESPLIEGUE A AWS CON AWS SAM" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Asegurar que el PATH contenga sam.exe
$env:Path += ";C:\Users\stive\AppData\Local\Python\pythoncore-3.14-64\Scripts"

# Ejecutar el despliegue automático
& 'C:\Users\stive\AppData\Local\Python\pythoncore-3.14-64\Scripts\sam.exe' deploy `
    --stack-name "coworking-serverless" `
    --resolve-s3 `
    --capabilities CAPABILITY_IAM `
    --region "us-east-1"

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host " DESPLIEGUE FINALIZADO" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
