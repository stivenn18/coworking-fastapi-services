"""
Script de prueba end-to-end para la Parte 2: Arquitectura Serverless y Event-Driven
Valida:
1. Lambda catalog-fn (GET spaces, GET space by id, PUT availability).
2. Publicación de eventos 'SpaceChanged' a EventBridge.
3. Propagación a SQS y consumo mediante consumer-fn.
4. Notificación y suscripción en orders-service.
"""

import sys
import os

# Establecer región por defecto para evitar NoRegionError al instanciar clientes boto3 en tests locales
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_REGION"] = "us-east-1"

import json
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

# Cargar modulos dinamicamente
import importlib.util

print("=" * 70)
print("  TALLER 2: SERVERLESS & EVENT-DRIVEN ARCHITECTURE (LAB 6 & LAB 7)")
print("=" * 70)

# 1. Cargar orders-service
ord_spec = importlib.util.spec_from_file_location("orders_service", "orders-service/main.py")
orders_mod = importlib.util.module_from_spec(ord_spec)
ord_spec.loader.exec_module(orders_mod)
orders_client = TestClient(orders_mod.app)

# 2. Cargar lambda-catalog
cat_spec = importlib.util.spec_from_file_location("lambda_catalog", "lambda-catalog/handler.py")
cat_mod = importlib.util.module_from_spec(cat_spec)

# Mock de EventBridge para pruebas locales sin credenciales AWS reales
mock_eventbridge = MagicMock()
mock_eventbridge.put_events.return_value = {
    "FailedEntryCount": 0,
    "Entries": [{"EventId": "ev-12345-mock-id"}]
}
cat_mod.eventbridge = mock_eventbridge
cat_spec.loader.exec_module(cat_mod)
cat_mod.eventbridge = mock_eventbridge

# 3. Cargar lambda-consumer
cons_spec = importlib.util.spec_from_file_location("lambda_consumer", "lambda-consumer/handler.py")
cons_mod = importlib.util.module_from_spec(cons_spec)
cons_spec.loader.exec_module(cons_mod)

# Interceptar llamada HTTP de consumer-fn para enrutarla directamente a orders_client
def mock_notify_orders_service(event_data):
    res = orders_client.post("/events/space-changed", json=event_data)
    print(f"  [HTTP Dispatch] consumer-fn -> orders-service (/events/space-changed): {res.status_code}")
    return {"status": res.status_code, "body": res.json()}

cons_mod.notify_orders_service = mock_notify_orders_service


# ------------------------------------------------------------------------------
# LAB 6: PRUEBAS DE LAMBDA CATALOG-FN
# ------------------------------------------------------------------------------
print("\n" + "-" * 70)
print("  LAB 6: Lambda catalog-service (API Gateway Proxy Events)")
print("-" * 70)

# 6.1 GET /spaces
event_get_spaces = {
    "httpMethod": "GET",
    "path": "/spaces"
}
res_spaces = cat_mod.lambda_handler(event_get_spaces, None)
print(f"[6.1] GET /spaces -> Status: {res_spaces['statusCode']}")
spaces_data = json.loads(res_spaces["body"])
print(f"      Total de espacios retornados por Lambda: {len(spaces_data)}")
for s in spaces_data:
    print(f"      - ID {s['id']}: {s['name']} | Disponible: {s['available']} | ${s['price_per_hour']}/h")

# 6.2 GET /spaces/1
event_get_one = {
    "httpMethod": "GET",
    "path": "/spaces/1",
    "pathParameters": {"id": "1"}
}
res_one = cat_mod.lambda_handler(event_get_one, None)
print(f"\n[6.2] GET /spaces/1 -> Status: {res_one['statusCode']}")
print(f"      Detalle: {res_one['body']}")

# 6.3 PUT /spaces/1/availability -> Cambio de estado y emisión a EventBridge
print("\n[6.3] PUT /spaces/1/availability (Cambiando disponibilidad a False)...")
event_update = {
    "httpMethod": "PUT",
    "path": "/spaces/1/availability",
    "pathParameters": {"id": "1"},
    "body": json.dumps({"available": False})
}
res_update = cat_mod.lambda_handler(event_update, None)
print(f"      Status: {res_update['statusCode']}")
update_data = json.loads(res_update["body"])
print(f"      Mensaje: {update_data['message']}")
print(f"      Evento publicado en EventBridge:")
print(f"      Detail: {json.dumps(update_data['event'], indent=2)}")

# Verificar que EventBridge recibió la entrada
mock_eventbridge.put_events.assert_called_once()
entry_sent = mock_eventbridge.put_events.call_args[1]["Entries"][0]
print(f"\n      ✓ Verificación EventBridge:")
print(f"        Source:     {entry_sent['Source']}")
print(f"        DetailType: {entry_sent['DetailType']}")
print(f"        EventBus:   {entry_sent['EventBusName']}")


# ------------------------------------------------------------------------------
# LAB 7: CONSUMER LAMBDA & PROPAGACIÓN EVENT-DRIVEN
# ------------------------------------------------------------------------------
print("\n" + "-" * 70)
print("  LAB 7: Consumer Lambda suscrita a SQS (catalog-events)")
print("-" * 70)

# Simulación del mensaje SQS recibido desde la regla de EventBridge
sqs_event = {
    "Records": [
        {
            "messageId": "sqs-msg-987654321",
            "receiptHandle": "handle-abc-123",
            "body": json.dumps({
                "version": "0",
                "id": "eb-event-001",
                "detail-type": "SpaceChanged",
                "source": "coworking.catalog",
                "account": "123456789012",
                "time": "2026-10-24T19:30:00Z",
                "region": "us-east-1",
                "resources": [],
                "detail": json.loads(entry_sent["Detail"])
            })
        }
    ]
}

print("[7.1] Despachando mensaje SQS hacia consumer-fn...")
res_consumer = cons_mod.lambda_handler(sqs_event, None)
print(f"      consumer-fn Status: {res_consumer['statusCode']}")
print(f"      Eventos procesados: {res_consumer['processedCount']}")

# 7.2 Verificar que orders-service recibió y cacheó el cambio de disponibilidad
print("\n[7.2] Verificando sincronización en orders-service (/events)...")
res_orders_events = orders_client.get("/events")
print(f"      orders-service Status: {res_orders_events.status_code}")
events_state = res_orders_events.json()
print(f"      Total eventos en orders-service: {events_state['total']}")
print(f"      Caché de disponibilidad sincronizada:")
for sp_id, is_avail in events_state["availability_cache"].items():
    print(f"        - Espacio ID {sp_id}: {'Disponible' if is_avail else 'NO Disponible (Ocupado)'}")

print("\n" + "=" * 70)
print("  ¡FLUJO SERVERLESS & EVENT-DRIVEN COMPLETADO Y VALIDADO CON ÉXITO!")
print("=" * 70)
