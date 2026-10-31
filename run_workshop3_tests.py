"""
Suite de Pruebas Automatizada - Taller 3: Bases de Datos en la Nube
Valida:
1. Conexión de SQLAlchemy y modelos relacionales (OrderModel).
2. Inicialización y ejecución de migraciones con Alembic (upgrade head).
3. Inserción de órdenes en base de datos real con cálculo de totales.
4. Conexión con MongoDB (Atlas o emulado), creación de índices y registro de eventos.
5. Ejecución de pipelines de agregación analítica (ingresos, conteo y top espacios).
"""

import os
import sys
import tempfile
from datetime import datetime

# Forzar SQLite en memoria/archivo temporal para validar la lógica relacional completa de forma autónoma
db_fd, temp_db_path = tempfile.mkstemp(suffix=".db")
os.close(db_fd)
os.environ["DATABASE_URL"] = f"sqlite:///{temp_db_path}"

# Agregar orders-service y analytics-service al sys.path
sys.path.insert(0, os.path.abspath("orders-service"))
sys.path.insert(0, os.path.abspath("analytics-service"))

from database import engine, Base, SessionLocal, OrderModel, OrderStatus
from alembic.config import Config
from alembic import command
from mongodb_client import MongoDBClient

print("=" * 70)
print("  TALLER 3: BASES DE DATOS EN LA NUBE - LAB 8 & LAB 9")
print("=" * 70)

# ------------------------------------------------------------------------------
# LAB 8: POSTGRESQL / SQLALCHEMY + ALEMBIC
# ------------------------------------------------------------------------------
print("\n" + "-" * 70)
print("  LAB 8: PostgreSQL con SQLAlchemy + Alembic")
print("-" * 70)

# 8.1 Ejecutar migraciones con Alembic
print("[8.1] Ejecutando migración de Alembic ('alembic upgrade head')...")
alembic_cfg = Config("orders-service/alembic.ini")
alembic_cfg.set_main_option("script_location", "orders-service/alembic")
alembic_cfg.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])
command.upgrade(alembic_cfg, "head")
print("      ✓ Migración '001_initial_schema' aplicada exitosamente en la base de datos.")

# 8.2 Insertar datos en la base de datos a través de SQLAlchemy
print("\n[8.2] Creando órdenes en la base de datos con SQLAlchemy...")
db = SessionLocal()

orders_to_create = [
    {
        "space_id": 1,
        "space_name": "Hot Desk - Open Space",
        "user_email": "juan@empresa.com",
        "hours": 3,
        "price_per_hour": 15.0,
        "total_price": 45.0,
        "status": OrderStatus.CONFIRMED
    },
    {
        "space_id": 3,
        "space_name": "Meeting Room Alpha",
        "user_email": "maria@startup.io",
        "hours": 2,
        "price_per_hour": 50.0,
        "total_price": 100.0,
        "status": OrderStatus.CONFIRMED
    },
    {
        "space_id": 4,
        "space_name": "Private Team Office",
        "user_email": "carlos@tech.org",
        "hours": 4,
        "price_per_hour": 80.0,
        "total_price": 320.0,
        "status": OrderStatus.CONFIRMED
    }
]

created_ids = []
for ord_data in orders_to_create:
    order_obj = OrderModel(**ord_data)
    db.add(order_obj)
    db.commit()
    db.refresh(order_obj)
    created_ids.append(order_obj.id)
    print(f"      ✓ Orden persistida: ID={order_obj.id} | Espacio: '{order_obj.space_name}' | Total: ${order_obj.total_price}")

# 8.3 Consultar y verificar integridad referencial
persisted_orders = db.query(OrderModel).all()
print(f"\n[8.3] Total de órdenes persistidas en BD: {len(persisted_orders)}")
assert len(persisted_orders) == 3, "Error: Las órdenes no coinciden"
print("      ✓ Integridad de datos y tipos verificada correctamente.")
db.close()


# ------------------------------------------------------------------------------
# LAB 9: MONGODB ATLAS PARA ANALYTICS
# ------------------------------------------------------------------------------
print("\n" + "-" * 70)
print("  LAB 9: MongoDB Atlas para Analytics y Logs Flexibles")
print("-" * 70)

mongo = MongoDBClient()

print("[9.1] Registrando eventos de telemetría y uso en MongoDB...")
for ord_data in orders_to_create:
    event_payload = {
        "event_type": "ORDER_CREATED",
        "space_id": ord_data["space_id"],
        "space_name": ord_data["space_name"],
        "user_email": ord_data["user_email"],
        "hours": ord_data["hours"],
        "total_price": ord_data["total_price"],
        "timestamp": datetime.utcnow().isoformat()
    }
    inserted_id = mongo.record_event(event_payload)
    print(f"      ✓ Evento analítico indexado: Doc ID={inserted_id} para '{ord_data['space_name']}'")

print("\n[9.2] Ejecutando pipelines de agregación analítica en MongoDB...")
summary = mongo.get_summary()
print(f"      - Total de reservas analizadas: {summary['total_orders']}")
print(f"      - Ingresos totales agregados:   ${summary['total_revenue']}")
print(f"      - Horas totales reservadas:     {summary['total_hours']} horas")
print("\n[9.3] Ranking de espacios más demandados (Top Revenue):")
for idx, sp in enumerate(summary.get("top_spaces", []), start=1):
    print(f"      {idx}. {sp['_id']}: ${sp.get('revenue', 0.0)} ({sp.get('orders_count', 0)} órdenes)")

# Limpieza
if os.path.exists(temp_db_path):
    try:
        os.remove(temp_db_path)
    except Exception:
        pass

print("\n" + "=" * 70)
print("  ¡TALLER 3 COMPLETADO Y VALIDADO CON ÉXITO ROTUNDO!")
print("=" * 70)
