import sys
import os
from pathlib import Path

# Asegurar que el directorio de orders-service esté en sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, Request, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import httpx
import uvicorn

from database import engine, Base, get_db, OrderModel, OrderStatus, UserModel
from auth import (
    Token,
    UserCreate,
    UserResponse,
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    require_role,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# Crear tablas si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Orders Service - Advanced Backend",
    version="3.0.0",
    description="Microservicio de órdenes con autenticación JWT, RBAC y persistencia en PostgreSQL"
)

CATALOG_SERVICE_URL = os.getenv("CATALOG_SERVICE_URL", "http://catalog-service:8001")
ANALYTICS_SERVICE_URL = os.getenv("ANALYTICS_SERVICE_URL", "http://analytics-service:8003")

# Event subscription store (Parte 2: Event-Driven)
RECEIVED_EVENTS: List[dict] = []
SPACE_AVAILABILITY_CACHE: dict = {}

# ==============================================================================
# ENDPOINTS DE AUTENTICACIÓN Y USUARIOS (LAB 10)
# ==============================================================================
@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """Registra un nuevo usuario con contraseña cifrada (bcrypt)."""
    existing_user = db.query(UserModel).filter(UserModel.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    role = user_in.role if user_in.role in ["user", "admin", "superadmin"] else "user"

    new_user = UserModel(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        role=role,
        created_at=datetime.utcnow()
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/auth/login", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Inicio de sesión compatible con OAuth2PasswordRequestForm.
    Verifica las credenciales y genera el token de acceso JWT.
    """
    user = db.query(UserModel).filter(UserModel.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserResponse)
def read_current_user_profile(current_user: UserModel = Depends(get_current_user)):
    """Retorna la información del usuario actualmente autenticado."""
    return current_user

@app.get("/admin")
def panel_admin(current_user: UserModel = Depends(require_role("admin"))):
    """
    Ruta protegida por RBAC exacta según guía Taller 4 (LAB 10).
    Solo accesible por roles 'admin' y 'superadmin'.
    """
    return {"mensaje": "Acceso autorizado"}

@app.get("/admin/panel")
def get_admin_panel(current_user: UserModel = Depends(require_role("admin"))):
    """
    Ruta protegida por RBAC: Solo accesible por roles 'admin' y 'superadmin'.
    Devuelve 403 Forbidden a usuarios con rol 'user'.
    """
    return {
        "mensaje": "Acceso autorizado",
        "panel": "Panel de Administración del Coworking",
        "solicitante": current_user.email,
        "rol": current_user.role
    }

# ==============================================================================
# ENDPOINTS TRANSACCIONALES DE ÓRDENES
# ==============================================================================
@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(Base.metadata.tables["orders"].select().limit(1))
        db_status = "connected"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        
    return {
        "status": "ok",
        "service": "orders-service",
        "database": db_status
    }

@app.get("/orders")
def get_orders(
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user)
):
    """
    Lista órdenes:
      - Si es admin/superadmin: puede ver todas las órdenes.
      - Si es usuario básico: solo sus propias órdenes.
    """
    if current_user.role in ["admin", "superadmin"]:
        orders = db.query(OrderModel).order_by(OrderModel.id.desc()).all()
    else:
        orders = db.query(OrderModel).filter(OrderModel.user_email == current_user.email).order_by(OrderModel.id.desc()).all()

    return [
        {
            "id": o.id,
            "space_id": o.space_id,
            "space_name": o.space_name,
            "user_email": o.user_email,
            "hours": o.hours,
            "price_per_hour": o.price_per_hour,
            "total_price": o.total_price,
            "status": o.status.value if hasattr(o.status, "value") else str(o.status),
            "created_at": o.created_at.isoformat() if isinstance(o.created_at, datetime) else str(o.created_at)
        }
        for o in orders
    ]

def get_http_client():
    return httpx.AsyncClient(timeout=4.0)

@app.post("/orders", status_code=status.HTTP_201_CREATED)
async def create_order(
    request: Request,
    space_id: Optional[int] = Query(None),
    user_email: Optional[str] = Query(None),
    hours: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user)
):
    """
    Crea una orden protegida por autenticación.
    Toma automáticamente el email del usuario autenticado si no se envía explícito.
    """
    if space_id is None or hours is None:
        try:
            body = await request.json()
            if isinstance(body, dict):
                space_id = space_id if space_id is not None else body.get("space_id")
                user_email = user_email if user_email is not None else body.get("user_email")
                hours = hours if hours is not None else body.get("hours")
        except Exception:
            pass

    # Usar email del token autenticado por defecto
    effective_email = user_email if user_email else (current_user.email if current_user else None)

    if space_id is None or effective_email is None or hours is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Missing required parameters: space_id and hours"
        )

    if hours <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hours must be greater than 0"
        )

    # Consulta al catálogo
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
    price_per_hour = space_data["price_per_hour"]
    total_price = price_per_hour * hours

    new_order = OrderModel(
        space_id=space_id,
        space_name=space_data.get("name", "Unknown"),
        user_email=effective_email,
        hours=hours,
        price_per_hour=price_per_hour,
        total_price=total_price,
        status=OrderStatus.CONFIRMED,
        created_at=datetime.utcnow()
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    # Notificar asíncronamente a analytics-service (MongoDB)
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.post(
                f"{ANALYTICS_SERVICE_URL}/analytics/events",
                json={
                    "event_type": "ORDER_CREATED",
                    "order_id": new_order.id,
                    "space_id": space_id,
                    "space_name": new_order.space_name,
                    "user_email": effective_email,
                    "hours": hours,
                    "total_price": total_price,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    except Exception as e:
        print(f"Warning: could not push event to analytics-service: {e}")

    return {
        "id": new_order.id,
        "space_id": new_order.space_id,
        "space_name": new_order.space_name,
        "user_email": new_order.user_email,
        "hours": new_order.hours,
        "price_per_hour": new_order.price_per_hour,
        "total_price": new_order.total_price,
        "status": new_order.status.value,
        "created_at": new_order.created_at.isoformat()
    }

# ==============================================================================
# EVENT-DRIVEN SUBSCRIPTION (PARTE 2)
# ==============================================================================
@app.post("/events/space-changed", status_code=status.HTTP_200_OK)
async def receive_space_event(request: Request):
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
