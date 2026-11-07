# Coworking Services - De Microservicios a Sistemas Distribuidos Inteligentes

Proyecto integral que abarca la evolución arquitectónica completa a través de 4 talleres:
1. **Taller 1:** Microservicios con FastAPI, Docker Compose y Chaos Engineering.
2. **Taller 2:** Migración Serverless y Event-Driven con AWS SAM, API Gateway, EventBridge, SQS y Lambdas.
3. **Taller 3:** Bases de Datos en la Nube con PostgreSQL en AWS RDS (SQLAlchemy + Alembic) y MongoDB Atlas para Analytics.
4. **Taller 4:** Backend Avanzado FastAPI - Autenticación JWT, Hashes bcrypt, Jerarquía RBAC y Protección de Rutas (LAB 10).

---

## 🏗 Arquitectura Global del Sistema

```
                        [ Clientes / API ]
                                │
               ┌────────────────┴────────────────┐
               │                                 │
               ▼                                 ▼
       [ catalog-service ]               [ orders-service ]
     (FastAPI / AWS Lambda)                (FastAPI / ECS)
               │                                 │
               │ (EventBridge / SQS)             ├──────────────────────────┐
               ▼                                 ▼                          ▼
       [ consumer-fn ]                ┌─────────────────────┐    ┌────────────────────┐
               │                      │   PostgreSQL RDS    │    │   analytics-svc    │
               └─► [ Webhook Sync ]──►│  (órdenes, usuarios)│    │     (FastAPI)      │
                                      └─────────────────────┘    └──────────┬─────────┘
                                                                            │
                                                                            ▼
                                                                 ┌────────────────────┐
                                                                 │   MongoDB Atlas    │
                                                                 │  (métricas y logs) │
                                                                 └────────────────────┘
```

---

## 📁 Estructura del Proyecto

```text
coworking-fastapi-services/
├── README.md
├── docker-compose.yml                     # Orquestación de servicios y BDs locales
├── template.yaml                          # AWS SAM (Serverless: Lambdas + EventBridge + SQS)
├── architecture-diagram.png
├── chaos-report.md                        # Informe técnico de Chaos Engineering
├── chaos-test.sh / chaos-test.ps1         # Scripts de prueba de caos (Lab 4)
├── coworking.postman_collection.json      # Colección Postman de los 3 talleres
│
├── catalog-service/                       # Taller 1: Catálogo de espacios original
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── orders-service/                        # Talleres 1, 2 y 3: Servicio de Órdenes
│   ├── main.py                            # Endpoints + persistencia en PostgreSQL
│   ├── database.py                        # Modelos SQLAlchemy + Connection Pooling
│   ├── alembic.ini                        # Configuración de migraciones
│   ├── alembic/                           # Entorno y versiones de migraciones
│   ├── requirements.txt                   # Incluye sqlalchemy, alembic, psycopg2
│   └── Dockerfile
│
├── analytics-service/                     # Taller 3 (Lab 9): Servicio de Analytics
│   ├── main.py                            # Endpoints de eventos y agregación
│   ├── mongodb_client.py                  # Conexión MongoDB Atlas + Índices + Pipelines
│   ├── requirements.txt                   # Incluye pymongo, fastapi
│   └── Dockerfile
│
├── lambda-catalog/                        # Taller 2 (Lab 6): Lambda catalog-service
│   ├── handler.py
│   └── requirements.txt
│
├── lambda-consumer/                       # Taller 2 (Lab 7): Lambda consumer de SQS
│   ├── handler.py
│   └── requirements.txt
│
├── run_workshop3_tests.py                 # Suite de validación Taller 3 (BDs)
├── test_serverless_event_flow.py          # Suite de validación Taller 2 (Serverless)
└── run_workshop_tests.py                  # Suite de validación Taller 1 (Chaos)
```

---

## 💾 Taller 3: Bases de Datos en la Nube (Labs 8 y 9)

### Objetivo
Reemplazar el almacenamiento volátil en memoria por bases de datos de producción:
* **PostgreSQL (AWS RDS)**: Para datos relacionales estructurados y transaccionales (órdenes, usuarios) usando **SQLAlchemy ORM** y control de esquema con **Alembic**.
* **MongoDB Atlas**: Para datos no estructurados y de alta ingesta (eventos de uso, analítica de ocupación, métricas y agregaciones).

---

### 1. LAB 8: PostgreSQL con SQLAlchemy + Alembic

#### Componentes:
* **`orders-service/database.py`**:
  * Motor `create_engine` con Connection Pooling configurado (`pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`, `pool_recycle=3600`).
  * Modelo declarativo `OrderModel` con tabla `orders`, índices en `space_id` y `user_email`, y enum de estado (`OrderStatus: PENDING, CONFIRMED, CANCELLED`).
  * Dependencia `get_db()` para inyección limpia de sesión por petición.
* **Migraciones con Alembic**:
  * `alembic.ini` y `alembic/env.py` configurados para autogeneración basada en `Base.metadata`.
  * Migración inicial: `001_initial_schema.py`.

#### Comandos de Migración:
```bash
cd orders-service
# Aplicar migraciones pendientes
alembic upgrade head

# Revertir última migración si es necesario
alembic downgrade -1
```

---

### 2. LAB 9: MongoDB Atlas para Analytics

#### Componentes:
* **`analytics-service/mongodb_client.py`**:
  * Cliente `MongoClient` configurado con Connection Pool (`maxPoolSize=50`, `minPoolSize=10`) y reintentos automáticos (`retryWrites=True`, `retryReads=True`).
  * Creación declarativa de índices compuestos (`event_type`, `space_id`, `timestamp`).
  * Pipelines de agregación (`$match`, `$group`, `$sort`) para calcular métricas de negocio:
    * Total de reservas confirmadas.
    * Ingresos totales generados.
    * Total de horas de coworking contratadas.
    * Ranking de espacios más rentables / demandados.
* **`analytics-service/main.py`**:
  * `POST /analytics/events`: Ingesta de eventos en tiempo real.
  * `GET /analytics/summary`: Retorna el reporte agregado de analítica.
  * `GET /health`: Estado del servicio y ping a MongoDB.

---

### 3. Ejecución Completa con Docker Compose

Para levantar toda la arquitectura con PostgreSQL, MongoDB y los 3 microservicios:

```bash
docker-compose up --build -d
```

#### Pruebas de Endpoints:
```bash
# 1. Crear una orden (se persiste en PostgreSQL y envía evento a Analytics)
curl -X POST "http://localhost:8002/orders?space_id=1&user_email=juan@test.com&hours=3"

# 2. Consultar órdenes persistidas en PostgreSQL
curl http://localhost:8002/orders

# 3. Consultar métricas y analíticas agregadas desde MongoDB
curl http://localhost:8003/analytics/summary
```

---

### 4. Conexión a AWS RDS y MongoDB Atlas en la Nube

Para conectar los servicios a tus instancias reales en la nube:
1. **PostgreSQL en AWS RDS**:
   Configura la variable `DATABASE_URL`:
   ```bash
   DATABASE_URL=postgresql://<usuario>:<password>@<endpoint-rds.amazonaws.com>:5432/<nombre_bd>
   ```
2. **MongoDB Atlas**:
   Configura la variable `MONGODB_URI`:
   ```bash
   MONGODB_URI=mongodb+srv://<usuario>:<password>@<cluster.mongodb.net>/coworking_analytics?retryWrites=true&w=majority
   ```

---

## 🔐 Taller 4: Backend Avanzado FastAPI (LAB 10: Autenticación JWT + RBAC)

Implementación integral de seguridad empresarial en `orders-service`:

### 1. Componentes Clave (`orders-service/auth.py` y `database.py`)
* **Cifrado de contraseñas:** Algoritmo `bcrypt` con `passlib.context.CryptContext`.
* **Firma de Tokens:** JSON Web Tokens (JWT) usando `python-jose`, algoritmo `HS256`, clave secreta configurable y tiempo de expiración unificado a **60 minutos**.
* **Jerarquía de Roles (RBAC):**
  * `user` (Nivel 1): Usuario regular. Puede ver y crear únicamente sus propias órdenes y perfil.
  * `admin` (Nivel 2): Administrador. Puede gestionar órdenes y acceder a `/admin` o `/admin/panel`.
  * `superadmin` (Nivel 3): Administrador con permisos totales sobre el sistema.
* **Manejo de Errores Estándar:**
  * `401 Unauthorized`: Token inválido, expirado o credenciales incorrectas.
  * `403 Forbidden`: Nivel de rol insuficiente para la ruta solicitada.
  * `400 Bad Request`: Email duplicado en el registro.

### 2. Endpoints de Autenticación
| Método | Endpoint | Acceso | Descripción |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/register` | Público | Registra usuario con password hasheada en PostgreSQL |
| `POST` | `/auth/login` | Público (OAuth2) | Valida credenciales y emite Token JWT (`access_token`) |
| `GET` | `/users/me` | Autenticado | Retorna el perfil del usuario autenticado vía `Bearer Token` |
| `GET` | `/admin` | `admin` / `superadmin` | Ruta protegida RBAC (Retorna 403 para rol `user`) |
| `GET` | `/admin/panel` | `admin` / `superadmin` | Panel de control administrativo detallado |
| `GET` | `/orders` | Autenticado | Filtro por usuario (usuarios ven solo las suyas; admin ve todas) |
| `POST` | `/orders` | Autenticado | Crea orden vinculada automáticamente al email del JWT |

### 3. Suite Automatizada de Pruebas
Para ejecutar las pruebas completas del Taller 4 en cualquier momento:
```bash
python test_taller4_auth.py
```
Valida de extremo a extremo:
1. Creación de usuarios con roles jerárquicos.
2. Login y obtención del JWT (60 minutos de expiración UTC).
3. Rechazo de credenciales incorrectas (401).
4. Consulta del perfil autenticado (`/users/me`).
5. Restricción 403 Forbidden a usuarios normales en `/admin` y `/admin/panel`.
6. Autorización 200 OK a usuarios administradores.
7. Rechazo de tokens manipulados/falsos (401).
