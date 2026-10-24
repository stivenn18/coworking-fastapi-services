# Coworking Services - De Microservicios a Sistemas Distribuidos Inteligentes

Proyecto completo que abarca la evolución desde una arquitectura de microservicios HTTP tradicionales con Docker y Chaos Engineering hasta una arquitectura híbrida **Serverless & Event-Driven** con AWS SAM, API Gateway, EventBridge, SQS y Lambdas.

---

## 🏗 Arquitectura del Sistema

### Parte 1: Microservicios en Contenedores (Docker Compose)
```
  +-------------------------+              +-------------------------+
  |     catalog-service     | <--- HTTP ---|     orders-service      |
  |        (FastAPI)        |              |        (FastAPI)        |
  |       Puerto 8001       |              |       Puerto 8002       |
  +-------------------------+              +-------------------------+
               |                                        |
               +-------------------+--------------------+
                                   |
                         [ Docker Network ]
                    (coworking_coworking-network)
```

### Parte 2: Migración Serverless & Event-Driven
```
[ API Gateway ]  --> [ Lambda: catalog-fn ] --> [ EventBridge: SpaceChanged ]
  (/catalog)                  |
                              v
                   [ SQS: catalog-events ]
                              |
                              v
                   [ Lambda: consumer-fn ]
                              |
                              v (HTTP Notif / Sync)
                   [ orders-service (FastAPI/ECS) ]
```

---

## 📁 Estructura del Proyecto

```text
coworking-fastapi-services/
├── README.md
├── docker-compose.yml                     # Orquestación Parte 1
├── template.yaml                          # Plantilla AWS SAM (Parte 2: Serverless)
├── architecture-diagram.png
├── chaos-report.md                        # Informe técnico de Chaos Engineering
├── chaos-test.sh / chaos-test.ps1         # Scripts de prueba de caos (Lab 4)
├── coworking.postman_collection.json      # Colección Postman completa
│
├── catalog-service/                       # Parte 1: Microservicio Catálogo original
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── orders-service/                        # Parte 1 & 2: Servicio de Órdenes (FastAPI)
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── lambda-catalog/                        # Parte 2 (Lab 6): Lambda catalog-service
│   ├── handler.py
│   └── requirements.txt
│
├── lambda-consumer/                       # Parte 2 (Lab 7): Lambda consumer de SQS
│   ├── handler.py
│   └── requirements.txt
│
├── test_serverless_event_flow.py          # Suite de validación Parte 2
└── run_workshop_tests.py                  # Suite de validación Parte 1
```

---

## 🚀 Parte 1: Guía de Inicio (Microservicios & Chaos)

### Levantar con Docker Compose
```bash
docker-compose up --build -d
```

### Probar los endpoints:
```bash
# Ver espacios disponibles
curl http://localhost:8001/spaces

# Crear una orden
curl -X POST "http://localhost:8002/orders?space_id=1&user_email=test@example.com&hours=2"

# Ver órdenes creadas
curl http://localhost:8002/orders
```

### Chaos Engineering:
- **En PowerShell:** `.\chaos-test.ps1`
- **En Bash:** `./chaos-test.sh`

---

## ⚡ Parte 2: Arquitectura Serverless & Event-Driven (Labs 6 y 7)

### Objetivo
Migrar el `catalog-service` a **AWS Lambda con API Gateway**, publicar eventos en **EventBridge (`SpaceChanged`)** cuando cambie la disponibilidad de un espacio, enrutarlos a través de una cola **SQS (`catalog-events`)**, y procesarlos mediante una Lambda consumidora (`consumer-fn`) suscrita para sincronizar el estado en `orders-service`.

### 1. Componentes Implementados

1. **`lambda-catalog` (Lab 6):**
   - Manejador de API Gateway para `/catalog/spaces` y `/catalog/spaces/{id}`.
   - Endpoint `PUT /spaces/{id}/availability`: al modificar la disponibilidad de un espacio, publica un evento estructurado en EventBridge:
     - `Source`: `coworking.catalog`
     - `DetailType`: `SpaceChanged`
     - `EventBusName`: `coworking-events`

2. **Infraestructura con AWS SAM (`template.yaml`):**
   - **`CoworkingEventBus`**: Bus personalizado de eventos.
   - **`CatalogEventsQueue`**: Cola SQS con política de acceso para EventBridge.
   - **`SpaceChangedRule`**: Regla de enrutamiento basada en patrones (`Source = coworking.catalog`, `DetailType = SpaceChanged`).
   - **`CatalogFunction`**: Función Lambda asociada a API Gateway con permisos `events:PutEvents`.
   - **`ConsumerFunction`**: Función Lambda activada por disparador de SQS (batch size: 5).

3. **`lambda-consumer` (Lab 7):**
   - Consume en lote los mensajes desde la cola SQS `catalog-events`.
   - Extrae el payload original emitido por EventBridge.
   - Notifica a `orders-service` a través del endpoint `/events/space-changed`.

4. **Suscripción en `orders-service`:**
   - Endpoint `POST /events/space-changed`: recibe la notificación de evento y actualiza en tiempo real la caché de disponibilidad de espacios (`SPACE_AVAILABILITY_CACHE`).
   - Endpoint `GET /events`: permite auditar los eventos procesados.

---

### 2. Prueba Local Automatizada (Sin credenciales de AWS)

Para verificar el ciclo completo de la Parte 2 localmente:

```powershell
wsl -e bash -c "source .venv/bin/activate && python3 test_serverless_event_flow.py"
```

**Resultado:**
- Simula llamadas a `catalog-fn` (`GET`, `PUT`).
- Valida la emisión del evento `SpaceChanged`.
- Enruta el mensaje a `consumer-fn`.
- Comprueba que `orders-service` recibe el evento y actualiza el estado del espacio.

---

### 3. Despliegue en la Nube con AWS SAM CLI

Cuando desees desplegar en tu cuenta de AWS:

```bash
# 1. Instalar SAM CLI (si no lo tienes)
pip install aws-sam-cli

# 2. Compilar la aplicación SAM
sam build

# 3. Desplegar de forma interactiva (primera vez)
sam deploy --guided

# 4. Despliegues posteriores
sam deploy
```
