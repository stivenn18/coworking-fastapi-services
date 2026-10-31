import os
import enum
from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL de la base de datos (PostgreSQL RDS o local por defecto)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/coworking_db"
)

# SQLite fallback para desarrollo o tests en caso de no tener PostgreSQL activo
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Configuración del motor con Connection Pooling robusto
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verifica la conexión antes de entregarla del pool (manejo de desconexiones)
    pool_recycle=3600,   # Recicla conexiones cada hora para evitar timeouts en AWS RDS
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"

class OrderModel(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    space_id = Column(Integer, index=True, nullable=False)
    space_name = Column(String(255), nullable=False)
    user_email = Column(String(255), index=True, nullable=False)
    hours = Column(Integer, nullable=False)
    price_per_hour = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.CONFIRMED, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

def get_db():
    """Dependencia para inyección de sesiones en FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
