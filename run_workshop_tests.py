"""
Script interactivo y ejecutable que realiza todos los laboratorios del taller
Coworking Microservices Workshop (FastAPI & Chaos Engineering).
"""

import os
import sys
import importlib.util
import httpx
from fastapi.testclient import TestClient

print("=" * 70)
print("     INICIANDO EJECUCIÓN COMPLETA DEL TALLER (LABS 1 AL 5)")
print("=" * 70)

# Cargar catalog-service dinámicamente
cat_spec = importlib.util.spec_from_file_location("catalog_service", "catalog-service/main.py")
catalog_module = importlib.util.module_from_spec(cat_spec)
cat_spec.loader.exec_module(catalog_module)
catalog_app = catalog_module.app
SPACES = catalog_module.SPACES

# Cargar orders-service dinámicamente
ord_spec = importlib.util.spec_from_file_location("orders_service", "orders-service/main.py")
orders_module = importlib.util.module_from_spec(ord_spec)
ord_spec.loader.exec_module(orders_module)
orders_app = orders_module.app
ORDERS = orders_module.ORDERS

catalog_client = TestClient(catalog_app)

print("\n" + "=" * 70)
print("  LAB 1: catalog-service con FastAPI")
print("=" * 70)

print("\n[1.1] GET http://localhost:8001/health")
res_health = catalog_client.get("/health")
print(f"Status: {res_health.status_code}")
print(f"Body:   {res_health.json()}")

print("\n[1.2] GET http://localhost:8001/spaces (Listar todos los espacios)")
res_spaces = catalog_client.get("/spaces")
print(f"Status: {res_spaces.status_code}")
print(f"Total espacios: {len(res_spaces.json())}")
for s in res_spaces.json():
    print(f"  - ID {s['id']}: {s['name']} | Capacidad: {s['capacity']} | ${s['price_per_hour']}/h")

print("\n[1.3] GET http://localhost:8001/spaces/1 (Detalle de un espacio)")
res_space1 = catalog_client.get("/spaces/1")
print(f"Status: {res_space1.status_code}")
print(f"Body:   {res_space1.json()}")


print("\n" + "=" * 70)
print("  LAB 2 & 3: orders-service y orquestación con red compartida")
print("=" * 70)

# Usamos un transporte que simula la red HTTP interna hacia catalog-service
class MockInternalNetworkTransport(httpx.AsyncBaseTransport):
    def __init__(self, is_catalog_up=True, catalog_app_ref=catalog_app):
        self.is_catalog_up = is_catalog_up
        self.catalog_app_ref = catalog_app_ref

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        if not self.is_catalog_up:
            raise httpx.ConnectError("Connection refused: catalog-service unreachable")
        
        # Petición interna simulada hacia catalog-service
        async with httpx.AsyncClient(app=self.catalog_app_ref, base_url="http://catalog-service:8001") as client:
            return await client.send(request)

mock_network = MockInternalNetworkTransport(is_catalog_up=True)

# TestClient para orders-service inyectando el transporte de red interna
orders_client = TestClient(orders_app, raise_server_exceptions=False)
orders_module.get_http_client = lambda: httpx.AsyncClient(transport=mock_network)

print("\n[2.1] GET http://localhost:8002/health")
res_orders_health = orders_client.get("/health")
print(f"Status: {res_orders_health.status_code}")
print(f"Body:   {res_orders_health.json()}")

print("\n[2.2] POST http://localhost:8002/orders?space_id=1&user_email=test@example.com&hours=2")
res_create_order = orders_client.post("/orders?space_id=1&user_email=test@example.com&hours=2")
print(f"Status: {res_create_order.status_code}")
order_data = res_create_order.json()
print(f"Orden creada exitosamente:")
print(f"  - ID:           {order_data.get('id')}")
print(f"  - Espacio:      {order_data.get('space_name')} (ID {order_data.get('space_id')})")
print(f"  - Usuario:      {order_data.get('user_email')}")
print(f"  - Precio/hora:  ${order_data.get('price_per_hour')}")
print(f"  - Horas:        {order_data.get('hours')}")
print(f"  - Total:        ${order_data.get('total_price')}")

print("\n[2.3] GET http://localhost:8002/orders (Consultar órdenes existentes)")
res_list_orders = orders_client.get("/orders")
print(f"Status: {res_list_orders.status_code}")
print(f"Total órdenes registradas: {len(res_list_orders.json())}")
for o in res_list_orders.json():
    print(f"  - Orden #{o['id']}: {o['user_email']} reservó '{o['space_name']}' por {o['hours']}h (${o['total_price']})")


print("\n" + "=" * 70)
print("  LAB 4: Chaos Engineering - Apagar el catálogo")
print("=" * 70)

print("\n[4.1] Simulando caída del catalog-service (Chaos Injection)...")
mock_network.is_catalog_up = False

print("\n[4.2] Intentando crear orden con catálogo caído:")
print("      curl -X POST 'http://localhost:8002/orders?space_id=1&user_email=test@example.com&hours=2'")
res_chaos_fail = orders_client.post("/orders?space_id=1&user_email=test@example.com&hours=2")
print(f"Status recibido: {res_chaos_fail.status_code} (Esperado: 503 Service Unavailable)")
print(f"Respuesta JSON:  {res_chaos_fail.json()}")

print("\n[4.3] Recuperando catalog-service...")
mock_network.is_catalog_up = True

print("\n[4.4] Reintentando crear orden tras recuperación del catálogo:")
res_chaos_recover = orders_client.post("/orders?space_id=1&user_email=test@example.com&hours=2")
print(f"Status recibido: {res_chaos_recover.status_code} (Esperado: 201 Created)")
recovered_order = res_chaos_recover.json()
print(f"Orden creada exitosamente: ID #{recovered_order.get('id')} | Total: ${recovered_order.get('total_price')}")


print("\n" + "=" * 70)
print("  LAB 5: Chaos Engineering - Cambiar el contrato sin avisar")
print("=" * 70)

print("\n[5.1] Modificando catálogo para romper el contrato:")
print("      Renombrando campo 'price_per_hour' -> 'hourly_rate'...")
for s in SPACES:
    if "price_per_hour" in s:
        s["hourly_rate"] = s.pop("price_per_hour")

print("\n[5.2] Intentando crear orden con contrato roto:")
print("      curl -X POST 'http://localhost:8002/orders?space_id=1&user_email=contract@test.com&hours=2'")
res_contract_fail = orders_client.post("/orders?space_id=1&user_email=contract@test.com&hours=2")
print(f"Status recibido: {res_contract_fail.status_code} (Esperado: 500 Internal Server Error)")
print("Observación: orders-service falló porque esperaba space['price_per_hour'] pero recibió 'hourly_rate'.")

print("\n[5.3] Restaurando contrato en el catálogo...")
for s in SPACES:
    if "hourly_rate" in s:
        s["price_per_hour"] = s.pop("hourly_rate")

print("\n" + "=" * 70)
print("     ¡TODOS LOS LABORATORIOS (1 AL 5) FUERON EJECUTADOS CON ÉXITO!")
print("=" * 70)
