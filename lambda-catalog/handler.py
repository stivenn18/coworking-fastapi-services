import json
import os
from datetime import datetime
import boto3

# Región por defecto para compatibilidad local y Lambda
AWS_REGION = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
EVENT_BUS_NAME = os.getenv("EVENT_BUS_NAME", "coworking-events")

# Cliente de EventBridge con región configurada
eventbridge = boto3.client("events", region_name=AWS_REGION)

# Datos en memoria de los espacios de coworking
SPACES = {
    1: {
        "id": 1,
        "name": "Hot Desk - Open Space",
        "capacity": 1,
        "price_per_hour": 15.0,
        "available": True,
        "description": "Flexible desk in a vibrant open shared workspace."
    },
    2: {
        "id": 2,
        "name": "Dedicated Desk - Quiet Zone",
        "capacity": 1,
        "price_per_hour": 25.0,
        "available": True,
        "description": "Personal desk in a quiet work area with ergonomic chair."
    },
    3: {
        "id": 3,
        "name": "Meeting Room Alpha",
        "capacity": 8,
        "price_per_hour": 50.0,
        "available": False,
        "description": "Equipped with video conferencing TV, whiteboard, and high-speed Wi-Fi."
    },
    4: {
        "id": 4,
        "name": "Private Team Office",
        "capacity": 4,
        "price_per_hour": 80.0,
        "available": True,
        "description": "Private lockable office for small teams."
    }
}

def build_response(status_code: int, body: any):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,PUT,OPTIONS"
        },
        "body": json.dumps(body)
    }

def lambda_handler(event, context):
    """
    Handler para catalog-fn detrás de API Gateway.
    Soporta:
      - GET /spaces
      - GET /spaces/{id}
      - PUT o POST /spaces/{id}/availability (publica evento SpaceChanged en EventBridge)
    """
    http_method = event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method", "GET")
    path = event.get("path") or event.get("rawPath", "/spaces")
    path_parameters = event.get("pathParameters") or {}

    print(f"Petición recibida: {http_method} {path}")

    # 1. GET /health
    if path.endswith("/health"):
        return build_response(200, {"status": "ok", "service": "lambda-catalog"})

    # 2. GET /spaces
    if http_method == "GET" and (path.endswith("/spaces") or path.endswith("/catalog")):
        return build_response(200, list(SPACES.values()))

    # 3. GET /spaces/{id}
    space_id_str = path_parameters.get("id") or path_parameters.get("space_id")
    if not space_id_str and "/spaces/" in path:
        parts = path.rstrip("/").split("/")
        if parts[-1].isdigit():
            space_id_str = parts[-1]

    if http_method == "GET" and space_id_str:
        space_id = int(space_id_str)
        space = SPACES.get(space_id)
        if not space:
            return build_response(404, {"detail": f"Space with id {space_id} not found"})
        return build_response(200, space)

    # 4. PUT / POST /spaces/{id}/availability -> Actualiza disponibilidad y publica en EventBridge
    if http_method in ["PUT", "POST"] and "availability" in path:
        if not space_id_str:
            parts = path.rstrip("/").split("/")
            for i, p in enumerate(parts):
                if p == "spaces" and i + 1 < len(parts) and parts[i + 1].isdigit():
                    space_id_str = parts[i + 1]
                    break

        if not space_id_str:
            return build_response(400, {"detail": "space_id missing in path"})

        space_id = int(space_id_str)
        space = SPACES.get(space_id)
        if not space:
            return build_response(404, {"detail": f"Space with id {space_id} not found"})

        # Leer cuerpo del request
        body_raw = event.get("body") or "{}"
        if isinstance(body_raw, str):
            body = json.loads(body_raw)
        else:
            body = body_raw

        new_status = body.get("available")
        if new_status is None:
            return build_response(400, {"detail": "Missing 'available' boolean field"})

        # Actualizar estado
        old_status = space["available"]
        space["available"] = bool(new_status)
        timestamp = datetime.utcnow().isoformat()

        # Publicar evento en EventBridge
        event_payload = {
            "space_id": space["id"],
            "name": space["name"],
            "old_available": old_status,
            "new_available": space["available"],
            "price_per_hour": space["price_per_hour"],
            "updated_at": timestamp
        }

        try:
            eb_response = eventbridge.put_events(
                Entries=[
                    {
                        "Source": "coworking.catalog",
                        "DetailType": "SpaceChanged",
                        "Detail": json.dumps(event_payload),
                        "EventBusName": EVENT_BUS_NAME
                    }
                ]
            )
            print(f"Evento SpaceChanged publicado exitosamente en EventBridge: {eb_response}")
        except Exception as e:
            print(f"Error publicando evento en EventBridge: {e}")
            event_payload["eventbridge_warning"] = str(e)

        return build_response(200, {
            "message": "Availability updated and SpaceChanged event published",
            "space": space,
            "event": event_payload
        })

    return build_response(404, {"detail": f"Route not found: {http_method} {path}"})
