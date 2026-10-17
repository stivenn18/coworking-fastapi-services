#!/bin/bash

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}        EJECUTANDO TALLER COMPLETO DE FASTAPI & CHAOS          ${NC}"
echo -e "${CYAN}================================================================${NC}"

# Matar procesos previos en caso de que existan
pkill -f "python.*catalog-service" || true
pkill -f "python.*orders-service" || true
sleep 1

source .venv/bin/activate

# -------------------------------------------------------------
# LAB 1: CATALOG-SERVICE CON FASTAPI
# -------------------------------------------------------------
echo -e "\n${YELLOW}>>> [LAB 1] Levantando catalog-service en puerto 8001...${NC}"
python catalog-service/main.py > /tmp/catalog.log 2>&1 &
CATALOG_PID=$!
sleep 2

echo -e "\n${GREEN}1. Probando /health:${NC}"
curl -s http://127.0.0.1:8001/health | python3 -m json.tool

echo -e "\n${GREEN}2. Probando /spaces (todos los espacios disponibles):${NC}"
curl -s http://127.0.0.1:8001/spaces | python3 -m json.tool

echo -e "\n${GREEN}3. Probando /spaces/1 (detalle de espacio id 1):${NC}"
curl -s http://127.0.0.1:8001/spaces/1 | python3 -m json.tool

# -------------------------------------------------------------
# LAB 2 & 3: ORDERS-SERVICE Y CONSULTA VÍA HTTP
# -------------------------------------------------------------
echo -e "\n${YELLOW}>>> [LAB 2 & 3] Levantando orders-service en puerto 8002...${NC}"
export CATALOG_SERVICE_URL="http://127.0.0.1:8001"
python orders-service/main.py > /tmp/orders.log 2>&1 &
ORDERS_PID=$!
sleep 2

echo -e "\n${GREEN}1. Probando /health de orders-service:${NC}"
curl -s http://127.0.0.1:8002/health | python3 -m json.tool

echo -e "\n${GREEN}2. Creando orden (orders-service consulta internamente al catalogo):${NC}"
echo "curl -X POST \"http://localhost:8002/orders?space_id=1&user_email=test@example.com&hours=2\""
curl -s -X POST "http://127.0.0.1:8002/orders?space_id=1&user_email=test@example.com&hours=2" | python3 -m json.tool

echo -e "\n${GREEN}3. Ver todas las órdenes creadas (/orders):${NC}"
curl -s http://127.0.0.1:8002/orders | python3 -m json.tool

# -------------------------------------------------------------
# LAB 4: CHAOS ENGINEERING - APAGAR EL CATÁLOGO
# -------------------------------------------------------------
echo -e "\n${CYAN}================================================================${NC}"
echo -e "${YELLOW}>>> [LAB 4] Chaos Engineering: Simular caida del catalogo...${NC}"
echo -e "${CYAN}================================================================${NC}"

echo -e "\n1. Apagando catalog-service (Chaos Injection)..."
kill -9 $CATALOG_PID
sleep 1

echo -e "\n2. Peticion con catalogo caido (Esperado: 503 Catalog service unavailable):"
STATUS_CODE=$(curl -s -o /tmp/chaos_resp.txt -w "%{http_code}" -X POST "http://127.0.0.1:8002/orders?space_id=1&user_email=test@example.com&hours=2")
echo -e "HTTP Status recibido: ${RED}$STATUS_CODE${NC}"
cat /tmp/chaos_resp.txt | python3 -m json.tool
echo ""

echo -e "\n3. Recuperando catalog-service..."
python catalog-service/main.py > /tmp/catalog.log 2>&1 &
CATALOG_PID=$!
sleep 2

echo -e "\n4. Peticion tras recuperacion del catalogo (Esperado: 201 Created):"
curl -s -X POST "http://127.0.0.1:8002/orders?space_id=1&user_email=test@example.com&hours=2" | python3 -m json.tool

# -------------------------------------------------------------
# LAB 5: CHAOS ENGINEERING - CAMBIAR EL CONTRATO SIN AVISAR
# -------------------------------------------------------------
echo -e "\n${CYAN}================================================================${NC}"
echo -e "${YELLOW}>>> [LAB 5] Chaos Engineering: Romper contrato (price_per_hour -> hourly_rate)...${NC}"
echo -e "${CYAN}================================================================${NC}"

echo -e "\n1. Modificando catalog-service (renombrando price_per_hour por hourly_rate)..."
sed -i 's/"price_per_hour"/"hourly_rate"/g' catalog-service/main.py

kill -9 $CATALOG_PID
sleep 1
python catalog-service/main.py > /tmp/catalog.log 2>&1 &
CATALOG_PID=$!
sleep 2

echo -e "\n2. Intentando crear orden con contrato roto:"
echo "curl -X POST \"http://localhost:8002/orders?space_id=1&user_email=contract@test.com&hours=2\""
CONTRACT_STATUS=$(curl -s -o /tmp/contract_resp.txt -w "%{http_code}" -X POST "http://127.0.0.1:8002/orders?space_id=1&user_email=contract@test.com&hours=2")
echo -e "HTTP Status recibido: ${RED}$CONTRACT_STATUS${NC}"
cat /tmp/contract_resp.txt
echo ""

echo -e "\n3. Detalle del fallo en logs de orders-service:"
tail -n 8 /tmp/orders.log

# Limpieza y restauración
echo -e "\n${GREEN}Restaurando contrato original en catalog-service...${NC}"
sed -i 's/"hourly_rate"/"price_per_hour"/g' catalog-service/main.py
kill -9 $CATALOG_PID || true
kill -9 $ORDERS_PID || true

echo -e "\n${CYAN}================================================================${NC}"
echo -e "${CYAN}  ¡TODOS LOS LABORATORIOS FUERON EJECUTADOS CON ÉXITO ROTUNDO!  ${NC}"
echo -e "${CYAN}================================================================${NC}"
