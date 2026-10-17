# Coworking Microservices Workshop - FastAPI & Chaos Engineering

Proyecto de microservicios con **FastAPI** y **Docker Compose** enfocado en integración HTTP y experimentación de resiliencia mediante **Chaos Engineering**.

---

## 🏗 Arquitectura del Sistema

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

---

## 📁 Estructura del Proyecto

```text
coworking-workshop/
├── README.md
├── docker-compose.yml
├── chaos-test.sh
├── chaos-test.ps1
├── chaos-report.md
├── architecture-diagram.png
├── coworking.postman_collection.json
├── catalog-service/
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
└── orders-service/
    ├── main.py
    ├── requirements.txt
    └── Dockerfile
```

---

## 🚀 Guía de Inicio Rápido

### Prerrequisitos
- [Docker](https://www.docker.com/) y Docker Compose instalados.
- Python 3.11+ (opcional para ejecución directa local).

---

### LAB 1: Ejecución Local de `catalog-service`
1. Entrar a la carpeta del catálogo e instalar dependencias:
   ```bash
   cd catalog-service
   pip install -r requirements.txt
   python main.py
   ```
2. En otra terminal, probar los endpoints:
   ```bash
   curl http://localhost:8001/health
   curl http://localhost:8001/spaces
   curl http://localhost:8001/spaces/1
   ```

---

### LAB 2 & 3: Orquestación con Docker Compose
1. En la raíz del proyecto, construir y levantar ambos servicios:
   ```bash
   docker-compose up --build
   ```
2. Probar el flujo completo:
   - **Ver espacios disponibles:**
     ```bash
     curl http://localhost:8001/spaces
     ```
   - **Crear una orden (orders-service consulta internamente a catalog-service):**
     ```bash
     curl -X POST "http://localhost:8002/orders?space_id=1&user_email=test@example.com&hours=2"
     ```
   - **Ver órdenes registradas:**
     ```bash
     curl http://localhost:8002/orders
     ```

---

### LAB 4: Chaos Engineering - Caída del Catálogo
Para simular y verificar la respuesta ante la caída del servicio dependiente:

**En Linux / Mac / Git Bash:**
```bash
chmod +x chaos-test.sh
./chaos-test.sh
```

**En Windows (PowerShell):**
```powershell
.\chaos-test.ps1
```

**Comportamiento observado:**
1. Primera petición: `201 Created` / `200 OK` (catálogo arriba).
2. Con catálogo detenido (`docker-compose stop catalog-service`): `503 Service Unavailable` con mensaje `"Catalog service unavailable"`.
3. Tras reactivar (`docker-compose start catalog-service`): `201 Created` / `200 OK`.

---

### LAB 5: Chaos Engineering - Cambio de Contrato
Para experimentar la ruptura de contrato:
1. En `catalog-service/main.py`, modificar el campo `price_per_hour` por `hourly_rate`:
   ```python
   # Antes:
   "price_per_hour": 15.0
   # Después:
   "hourly_rate": 15.0
   ```
2. Reconstruir el servicio:
   ```bash
   docker-compose up --build -d
   ```
3. Intentar crear una orden:
   ```bash
   curl -X POST "http://localhost:8002/orders?space_id=1&user_email=contract@test.com&hours=2"
   ```
4. **Resultado esperado:** Error `500 Internal Server Error` debido a que `orders-service` esperaba `space["price_per_hour"]`.
5. Ver informe completo en [chaos-report.md](file:///c:/Users/stive/Downloads/coworking-fastapi-services/chaos-report.md).

---

## 🛠 Comandos de Debugging Útiles

```bash
# Ver logs en tiempo real
docker-compose logs -f

# Ver estado de los contenedores
docker-compose ps

# Entrar al contenedor de orders-service
docker-compose exec orders-service bash

# Inspeccionar redes Docker
docker network ls
docker network inspect coworking_coworking-network

# Probar conectividad interna entre contenedores
docker-compose exec orders-service ping catalog-service

# Reconstruir imágenes sin caché
docker-compose build --no-cache
```
