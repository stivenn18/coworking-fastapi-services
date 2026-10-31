from typing import Dict, Any
from fastapi import FastAPI, status
import uvicorn
from mongodb_client import mongo_client

app = FastAPI(title="Analytics Service", version="1.0.0")

@app.get("/health")
def health_check():
    is_connected = mongo_client.db is not None
    return {
        "status": "ok",
        "service": "analytics-service",
        "mongodb_connected": is_connected
    }

@app.post("/analytics/events", status_code=status.HTTP_201_CREATED)
def record_event(event: Dict[str, Any]):
    event_id = mongo_client.record_event(event)
    return {
        "status": "recorded",
        "event_id": event_id
    }

@app.get("/analytics/summary")
def get_analytics_summary():
    return mongo_client.get_summary()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
