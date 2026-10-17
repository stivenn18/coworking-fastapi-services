#!/bin/bash
# ==============================================================================
# Script de Chaos Engineering: Lab 4 - Caída de servicio dependiente
# ==============================================================================

echo "=========================================================="
echo " INICIANDO CHAOS TEST: Resiliencia ante caída del Catálogo"
echo "=========================================================="

# 1. Primera petición con todo funcionando
echo -e "\n[PASO 1] Primera petición con catálogo activo (Esperado: 200 OK / 201 Created):"
RESPONSE_1=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "http://localhost:8002/orders?space_id=1&user_email=test@example.com&hours=2")
echo "$RESPONSE_1"

# 2. Simular fallo apagando catalog-service
echo -e "\n[PASO 2] Apagando catalog-service (Chaos Injection)..."
docker-compose stop catalog-service

echo -e "\n[PASO 3] Petición con catálogo apagado (Esperado: 503 Service Unavailable):"
RESPONSE_2=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "http://localhost:8002/orders?space_id=1&user_email=test@example.com&hours=2")
echo "$RESPONSE_2"

# 3. Recuperar catalog-service
echo -e "\n[PASO 4] Recuperando catalog-service..."
docker-compose start catalog-service

echo "Esperando 5 segundos a que catalog-service esté listo..."
sleep 5

# 4. Petición tras recuperación
echo -e "\n[PASO 5] Petición tras recuperación del catálogo (Esperado: 200 OK / 201 Created):"
RESPONSE_3=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "http://localhost:8002/orders?space_id=1&user_email=test@example.com&hours=2")
echo "$RESPONSE_3"

echo -e "\n=========================================================="
echo " CHAOS TEST COMPLETADO"
echo "=========================================================="
