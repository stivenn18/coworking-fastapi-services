import json
import os
import boto3
import urllib.request
import urllib.error
from datetime import datetime

ORDERS_SERVICE_URL = os.getenv("ORDERS_SERVICE_URL", "http://orders-service:8002")

def notify_orders_service(event_data: dict) -> dict:
    """
    Envía el evento de cambio de disponibilidad a orders-service.
    """
    target_url = f"{ORDERS_SERVICE_URL}/events/space-changed"
    payload = json.dumps(event_data).encode("utf-8")
    req = urllib.request.Request(
        target_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            res_body = response.read().decode("utf-8")
            print(f"Notificación exitosa a orders-service: status {response.status}, body: {res_body}")
            return {"status": response.status, "body": res_body}
    except urllib.error.URLError as e:
        print(f"Aviso: No se pudo contactar a orders-service en {target_url} ({e}). Registrando localmente.")
        return {"error": str(e)}

def lambda_handler(event, context):
    """
    Handler para consumer-fn suscrito a la cola SQS 'catalog-events'.
    Procesa mensajes originados en EventBridge (SpaceChanged) y
    notifica a orders-service.
    """
    print(f"[{datetime.utcnow().isoformat()}] Consumer Lambda invocado. Procesando {len(event.get('Records', []))} registros...")

    processed_events = []

    for record in event.get("Records", []):
        message_id = record.get("messageId")
        raw_body = record.get("body", "{}")

        try:
            body = json.loads(raw_body)
        except json.JSONDecodeError:
            body = {"raw": raw_body}

        # Cuando EventBridge enruta hacia SQS, el evento se encapsula dentro del campo 'detail'
        detail_type = body.get("detail-type") or body.get("DetailType", "SpaceChanged")
        detail = body.get("detail") or body.get("Detail", body)

        print(f"Procesando mensaje SQS ID: {message_id} | Tipo: {detail_type}")
        print(f"Detalle del evento: {json.dumps(detail)}")

        # Notificar a orders-service
        notification_result = notify_orders_service({
            "source_event": detail_type,
            "message_id": message_id,
            "payload": detail,
            "received_at": datetime.utcnow().isoformat()
        })

        processed_events.append({
            "messageId": message_id,
            "status": "PROCESSED",
            "detail": detail,
            "notification": notification_result
        })

    return {
        "statusCode": 200,
        "batchItemFailures": [],
        "processedCount": len(processed_events),
        "results": processed_events
    }
