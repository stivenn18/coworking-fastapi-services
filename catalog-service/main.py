from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Catalog Service", version="1.0.0")

class Space(BaseModel):
    id: int
    name: str
    capacity: int
    price_per_hour: float
    description: Optional[str] = None

# Mock database of coworking spaces
SPACES: List[dict] = [
    {
        "id": 1,
        "name": "Hot Desk - Open Space",
        "capacity": 1,
        "price_per_hour": 15.0,
        "description": "Flexible desk in a vibrant open shared workspace."
    },
    {
        "id": 2,
        "name": "Dedicated Desk - Quiet Zone",
        "capacity": 1,
        "price_per_hour": 25.0,
        "description": "Personal desk in a quiet work area with ergonomic chair."
    },
    {
        "id": 3,
        "name": "Meeting Room Alpha",
        "capacity": 8,
        "price_per_hour": 50.0,
        "description": "Equipped with video conferencing TV, whiteboard, and high-speed Wi-Fi."
    },
    {
        "id": 4,
        "name": "Private Team Office",
        "capacity": 4,
        "price_per_hour": 80.0,
        "description": "Private lockable office for small teams."
    }
]

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "catalog-service"}

@app.get("/spaces")
def get_spaces():
    return SPACES

@app.get("/spaces/{space_id}")
def get_space(space_id: int):
    for space in SPACES:
        if space["id"] == space_id:
            return space
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Space with id {space_id} not found"
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
