# ==============================================================================
# Script para ejecutar la prueba de la Parte 2 (Serverless & Event-Driven)
# ==============================================================================

Write-Host "Ejecutando pruebas de la Parte 2 (Serverless & Event-Driven)..." -ForegroundColor Cyan

wsl -e bash -c "cd /mnt/c/Users/stive/Downloads/coworking-fastapi-services && source .venv/bin/activate && python3 test_serverless_event_flow.py"
