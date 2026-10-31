import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Cadena de conexión para MongoDB Atlas (o local)
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://zukabarcenas_db_user:miCePLAc8643pLYh@cluster0.bcov6bc.mongodb.net/coworking_analytics?retryWrites=true&w=majority"
)
DATABASE_NAME = os.getenv("MONGODB_DATABASE", "coworking_analytics")

class MongoDBClient:
    def __init__(self, uri: str = MONGODB_URI):
        self.uri = uri
        self.client: Optional[MongoClient] = None
        self.db = None
        self._in_memory_events: List[Dict[str, Any]] = []  # Fallback si no hay mongo vivo
        self.connect()

    def connect(self):
        """Conecta a MongoDB con pool de conexiones y configuración de reintentos."""
        try:
            self.client = MongoClient(
                self.uri,
                maxPoolSize=50,             # Connection Pool
                minPoolSize=10,
                maxIdleTimeMS=45000,
                serverSelectionTimeoutMS=2500, # Timeout rápido de conexión
                retryReads=True,
                retryWrites=True
            )
            # Verificar conexión
            self.client.admin.command('ping')
            self.db = self.client[DATABASE_NAME]
            self._ensure_indexes()
            print("Conectado exitosamente a MongoDB")
        except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as e:
            print(f"Aviso MongoDB: No se pudo conectar a {self.uri} ({e}). Usando modo memoria simulada.")
            self.db = None

    def _ensure_indexes(self):
        """Crea índices para optimizar las consultas de analítica."""
        if self.db is not None:
            events_col = self.db["events"]
            events_col.create_index([("event_type", ASCENDING)])
            events_col.create_index([("space_id", ASCENDING)])
            events_col.create_index([("user_email", ASCENDING)])
            events_col.create_index([("timestamp", DESCENDING)])

    def record_event(self, event_data: Dict[str, Any]) -> str:
        """Registra un evento analítico en la base de datos."""
        event_doc = dict(event_data)
        if "timestamp" not in event_doc:
            event_doc["timestamp"] = datetime.utcnow().isoformat()

        if self.db is not None:
            try:
                res = self.db["events"].insert_one(event_doc)
                return str(res.inserted_id)
            except Exception as e:
                print(f"Error insertando en MongoDB: {e}")

        # Fallback local
        event_doc["_id"] = f"mem-{len(self._in_memory_events)+1}"
        self._in_memory_events.append(event_doc)
        return str(event_doc["_id"])

    def get_summary(self) -> Dict[str, Any]:
        """Calcula agregaciones de uso, ingresos y espacios más populares."""
        if self.db is not None:
            try:
                events_col = self.db["events"]

                # Total reservas y monto total
                pipeline_totals = [
                    {"$match": {"event_type": "ORDER_CREATED"}},
                    {"$group": {
                        "_id": None,
                        "total_orders": {"$sum": 1},
                        "total_revenue": {"$sum": "$total_price"},
                        "total_hours": {"$sum": "$hours"}
                    }}
                ]
                totals = list(events_col.aggregate(pipeline_totals))
                totals_data = totals[0] if totals else {"total_orders": 0, "total_revenue": 0.0, "total_hours": 0}

                # Top espacios por ingresos
                pipeline_spaces = [
                    {"$match": {"event_type": "ORDER_CREATED"}},
                    {"$group": {
                        "_id": "$space_name",
                        "orders_count": {"$sum": 1},
                        "revenue": {"$sum": "$total_price"}
                    }},
                    {"$sort": {"revenue": -1}},
                    {"$limit": 5}
                ]
                top_spaces = list(events_col.aggregate(pipeline_spaces))

                return {
                    "source": "mongodb",
                    "total_orders": totals_data.get("total_orders", 0),
                    "total_revenue": totals_data.get("total_revenue", 0.0),
                    "total_hours": totals_data.get("total_hours", 0),
                    "top_spaces": top_spaces
                }
            except Exception as e:
                print(f"Error agregando en MongoDB: {e}")

        # Fallback cálculo en memoria
        orders = [e for e in self._in_memory_events if e.get("event_type") == "ORDER_CREATED"]
        total_rev = sum(o.get("total_price", 0.0) for o in orders)
        total_h = sum(o.get("hours", 0) for o in orders)

        return {
            "source": "fallback_memory",
            "total_orders": len(orders),
            "total_revenue": total_rev,
            "total_hours": total_h,
            "top_spaces": [{"_id": "All Spaces", "orders_count": len(orders), "revenue": total_rev}]
        }

mongo_client = MongoDBClient()
