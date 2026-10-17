# Informe de Chaos Engineering

## Test 1: Caída de servicio dependiente

- **Escenario**: 
  Se detiene intencionalmente el contenedor `catalog-service` (`docker-compose stop catalog-service`) mientras `orders-service` permanece en ejecución y continúa recibiendo solicitudes para la creación de órdenes de reserva vía `POST /orders`.

- **Impacto**: 
  - `orders-service` no puede comunicarse con su dependencia crítica para verificar la existencia del espacio ni su costo por hora.
  - Al implementar manejo de excepciones en HTTPX con timeout delimitado (4s), `orders-service` no colapsa ni retiene conexiones infinitamente; en su lugar, degrada de forma controlada respondiendo con `HTTP 503 Service Unavailable` y el mensaje `{"detail": "Catalog service unavailable"}`.
  - Los usuarios son notificados de inmediato del fallo en lugar de experimentar un cuelgue indefinido (Gateway Timeout / 504).

- **Tiempo de detección**: 
  Inmediato a nivel de aplicación (determinado por el timeout de conexión de 4.0 segundos en la llamada HTTP asíncrona hacia `catalog-service`).

- **Recuperación**: 
  - Se reactiva el contenedor `catalog-service` con `docker-compose start catalog-service`.
  - La recuperación es inmediata (aproximadamente 2 a 5 segundos mientras Uvicorn levanta el worker y enlaza el socket). Las solicitudes subsiguientes a `orders-service` vuelven a retornar exitosamente `HTTP 201 Created` sin requerir reinicio de `orders-service`.

---

## Test 2: Cambio de contrato sin versionar

- **Escenario**: 
  El equipo de `catalog-service` renombra unilateralmente el campo de precios en su esquema de respuesta: cambia `price_per_hour` por `hourly_rate` sin cambiar la versión de la API ni notificar al equipo consumidor (`orders-service`).

- **Impacto**: 
  - Aunque `catalog-service` responde `HTTP 200 OK`, el servicio dependiente `orders-service` sufre una excepción en tiempo de ejecución (`KeyError: 'price_per_hour'`) al calcular el monto total (`space["price_per_hour"] * hours`).
  - La transacción de creación de órdenes falla catastróficamente con `HTTP 500 Internal Server Error`.
  - Se quiebra la disponibilidad del flujo principal de negocio a pesar de que ambos servicios están "vivos" y la red funciona correctamente.

- **Causa raíz**: 
  - Falta de versionamiento semántico en la API (ejemplo: `/v1/spaces` vs `/v2/spaces`).
  - Acoplamiento directo y débil validación de contrato entre microservicios sin una capa de traducción o esquema formal de Pydantic para deserializar respuestas de dependencias externas.
  - Ausencia de pruebas de contrato en el pipeline de CI/CD (Consumer-Driven Contract Testing).

- **Solución propuesta**: 
  1. **Versionamiento de API**: Implementar rutas versionadas (e.g., `/api/v1/spaces` y `/api/v2/spaces`) y mantener retrocompatibilidad durante un periodo de deprecación acordado.
  2. **Validación de esquema con Pydantic**: En `orders-service`, deserializar la respuesta del catálogo utilizando un esquema Pydantic con aliases y valores predeterminados (e.g., `Field(validation_alias=AliasChoices('price_per_hour', 'hourly_rate'))`).
  3. **Consumer-Driven Contract Testing**: Implementar herramientas de pruebas de contrato como **Pact** en los flujos de CI/CD para validar que ningún cambio en el proveedor rompa las expectativas del consumidor antes de desplegar a producción.
  4. **Patrón Circuit Breaker y Fallback**: Implementar librerías de Circuit Breaker (como pybreaker o tenacidade) y posibles cachés locales de catálogo para mitigar impactos inmediatos.
