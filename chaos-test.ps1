# ==============================================================================
# Script de Chaos Engineering para PowerShell (Windows)
# ==============================================================================

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " INICIANDO CHAOS TEST: Resiliencia ante caida del Catalogo" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Primera petición
Write-Host "`n[PASO 1] Primera peticion con catalogo activo (Esperado: 200/201):" -ForegroundColor Yellow
try {
    $res1 = Invoke-RestMethod -Uri "http://localhost:8002/orders?space_id=1&user_email=test@example.com&hours=2" -Method Post
    Write-Host "Respuesta exitosa:" ($res1 | ConvertTo-Json -Compress) -ForegroundColor Green
} catch {
    Write-Host "Error inesperado en paso 1: $_" -ForegroundColor Red
}

# 2. Apagar catalog-service
Write-Host "`n[PASO 2] Apagando catalog-service (Chaos Injection)..." -ForegroundColor Magenta
docker-compose stop catalog-service

# 3. Petición con catálogo apagado
Write-Host "`n[PASO 3] Peticion con catalogo apagado (Esperado: 503 Catalog service unavailable):" -ForegroundColor Yellow
try {
    $res2 = Invoke-RestMethod -Uri "http://localhost:8002/orders?space_id=1&user_email=test@example.com&hours=2" -Method Post
    Write-Host "Inesperado: $res2" -ForegroundColor Red
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-Host "HTTP Status:" $statusCode -ForegroundColor Yellow
    Write-Host "Detalle del error:" $_.ErrorDetails.Message -ForegroundColor Green
}

# 4. Recuperar catálogo
Write-Host "`n[PASO 4] Recuperando catalog-service..." -ForegroundColor Magenta
docker-compose start catalog-service
Write-Host "Esperando 5 segundos a que catalog-service inicialice..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# 5. Petición tras recuperación
Write-Host "`n[PASO 5] Peticion tras recuperacion del catalogo (Esperado: 200/201):" -ForegroundColor Yellow
try {
    $res3 = Invoke-RestMethod -Uri "http://localhost:8002/orders?space_id=1&user_email=test@example.com&hours=2" -Method Post
    Write-Host "Respuesta exitosa:" ($res3 | ConvertTo-Json -Compress) -ForegroundColor Green
} catch {
    Write-Host "Error en paso 5: $_" -ForegroundColor Red
}

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host " CHAOS TEST COMPLETADO" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
