import os
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, Request, status
import httpx
import uvicorn

app = FastAPI(title="Orders Service", version="1.0.0")

CATALOG_SERVICE_URL = os.getenv("CATALOG_SERVICE_URL", "http://catalog-service:8001")

# Mock database of orders
ORDERS: List[dict] = []
order_counter = 1

# Event subscription store (Parte 2: Event-Driven)
RECEIVED_EVENTS: List[dict] = []
SPACE_AVAILABILITY_CACHE: dict = {}

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "orders-service"}

@app.get("/orders")
def get_orders():
    return ORDERS

@app.post("/events/space-changed", status_code=status.HTTP_200_OK)
async def receive_space_event(request: Request):
    """
    Endpoint para recibir eventos propagados por consumer-fn desde SQS/EventBridge.
    """
    event_data = await request.json()
    RECEIVED_EVENTS.append(event_data)
    
    payload = event_data.get("payload", {})
    space_id = payload.get("space_id")
    new_avail = payload.get("new_available")
    if space_id is not None and new_avail is not None:
        SPACE_AVAILABILITY_CACHE[space_id] = new_avail
        
    return {
        "status": "received",
        "total_events": len(RECEIVED_EVENTS),
        "cached_spaces": SPACE_AVAILABILITY_CACHE
    }

@app.get("/events")
def get_received_events():
    return {
        "total": len(RECEIVED_EVENTS),
        "events": RECEIVED_EVENTS,
        "availability_cache": SPACE_AVAILABILITY_CACHE
    }

def get_http_client():
    return httpx.AsyncClient(timeout=4.0)

@app.post("/orders", status_code=status.HTTP_201_CREATED)
async def create_order(
    request: Request,
    space_id: Optional[int] = Query(None),
    user_email: Optional[str] = Query(None),
    hours: Optional[int] = Query(None)
):
    global order_counter

    # Check if parameters were provided via JSON body instead of query params
    if space_id is None or user_email is None or hours is None:
        try:
            body = await request.json()
            if isinstance(body, dict):
                space_id = space_id if space_id is not None else body.get("space_id")
                user_email = user_email if user_email is not None else body.get("user_email")
                hours = hours if hours is not None else body.get("hours")
        except Exception:
            pass

    if space_id is None or user_email is None or hours is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Missing required parameters: space_id, user_email, and hours"
        )

    if hours <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hours must be greater than 0"
        )

    # Call catalog-service to retrieve space details
    catalog_url = f"{CATALOG_SERVICE_URL}/spaces/{space_id}"
    try:
        async with get_http_client() as client:
            response = await client.get(catalog_url)
    except (httpx.RequestError, httpx.TimeoutException):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Catalog service unavailable"
        )

    if response.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Space with id {space_id} not found in catalog"
        )
    elif response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Catalog service unavailable"
        )

    space_data = response.json()

    # The order calculation depends directly on the catalog contract: space["price_per_hour"]
    # If the contract changes (e.g. to hourly_rate), this will raise a KeyError
    price_per_hour = space_data["price_per_hour"]
    total_price = price_per_hour * hours

    order = {
        "id": order_counter,
        "space_id": space_id,
        "space_name": space_data.get("name", "Unknown"),
        "user_email": user_email,
        "hours": hours,
        "price_per_hour": price_per_hour,
        "total_price": total_price,
        "created_at": datetime.utcnow().isoformat()
    }
    ORDERS.append(order)
    order_counter += 1

    return order

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
