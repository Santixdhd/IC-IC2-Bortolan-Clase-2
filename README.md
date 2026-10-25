# Ingeniería en Computación 2 — Clase 2: APIs (FastAPI) y Conceptos de MQTT

Repositorio con la resolución completa de los ejercicios de la **Clase 2 (HTTP, FastAPI, cliente `requests`, MQTT conceptual y tests con `TestClient`)** y el cierre integrador (**F1 a F4**).

---

## Estructura del proyecto

| Archivo | Descripción |
| :--- | :--- |
| `docs/parte-a-http.md` | **Parte A** (A1–A7): Verbos HTTP, códigos de estado, familias `2xx–5xx`, JSON a mano, idempotencia, headers y diseño de URLs REST. |
| `parte_a_json.py` | **Parte A4**: Script que valida con `json.loads()` los 3 documentos JSON escritos a mano. |
| `main.py` | **Parte B + Cierre F1** (B1–B12): API en FastAPI con endpoints `GET /`, `GET /libros` (con filtro `paginas_min`), `POST /libros`, `GET /libros/{titulo}`, `PUT /libros/{titulo}`, `DELETE /libros/{titulo}`, recurso `/autores`, modelo anidado `Editorial` y `response_model`. |
| `cliente.py` | **Parte C + Cierre F1/F3** (C1–C8): Cliente HTTP con `requests.Session()`, `timeout`, manejo de `ConnectionError` y `Timeout`, lectura de códigos de estado (`200/201/204/404/422`) y pruebas de `GET`, `POST`, `PUT`, `DELETE`. |
| `docs/mqtt-notas.md` | **Parte D + Cierre F2** (D1–D8): Defensa conceptual de MQTT (Pub/Sub, broker, topics, wildcards `+` y `#`, QoS 0/1/2, `retained` y comparativa numérica vs Polling HTTP). |
| `test_main.py` | **Parte E + Cierre F1** (E1–E4): Suite de tests automáticos con `pytest` y `TestClient` de FastAPI. |
| `requirements.txt` | Dependencias del proyecto (`fastapi`, `uvicorn`, `requests`, `httpx`, `pytest`). |

---

## Cómo levantar la API, correr el cliente y ejecutar los tests (F1)

1. **Crear y activar el entorno virtual (`venv`):**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
   *(En Linux / macOS / Raspberry Pi: `source venv/bin/activate`)*

2. **Instalar las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Levantar el servidor de la API con `uvicorn`:**
   ```bash
   uvicorn main:app --reload
   ```
   - La API queda disponible en: `http://127.0.0.1:8000`
   - Documentación interactiva (**Swagger UI**): `http://127.0.0.1:8000/docs`

4. **Correr el script cliente (`cliente.py`) en otra terminal:**
   ```bash
   python cliente.py
   ```

5. **Correr los tests automáticos con `pytest` (no requiere tener `uvicorn` levantado):**
   ```bash
   pytest -v
   ```

---

## Cierre F3 — Errores de contrato documentados de punta a punta

### 1. Error `422 Unprocessable Entity` en la API (falta el campo obligatorio `paginas`)
- **Cómo se provocó:** enviando `POST /libros` con el body `{"titulo": "Libro Incompleto"}`.
- **Mensaje de error real devuelto por FastAPI:**
  ```json
  {
    "detail": [
      {
        "type": "missing",
        "loc": ["body", "paginas"],
        "msg": "Field required",
        "input": {"titulo": "Libro Incompleto"}
      }
    ]
  }
  ```
- **Cómo lo identificamos:** el código HTTP `422` y la lista `detail` donde `loc: ["body", "paginas"]` y `type: "missing"` indican exactamente qué campo del modelo Pydantic faltó en el JSON enviado.

### 2. Error `404 Not Found` en el cliente (se pide un título que no existe)
- **Cómo se provocó:** consultando `GET /libros/El%20Aleph` luego de haberlo eliminado con `DELETE`.
- **Mensaje de error real recibido:**
  ```json
  {
    "detail": "El libro 'El Aleph' no existe."
  }
  ```
- **Cómo lo identificamos:** en `cliente.py`, `respuesta.status_code == 404` activa la rama `"no existe"` de `interpretar_respuesta()`, mostrando el `detail` devuelto por `HTTPException(status_code=404, ...)`.

### 3. Excepción de conexión en el cliente (con la API apagada)
- **Cómo se provocó:** ejecutando `session.get("http://127.0.0.1:8999/libros")` hacia un puerto donde no hay ningún servidor escuchando.
- **Excepción real de `requests`:**
  ```text
  requests.exceptions.ConnectionError: HTTPConnectionPool(host='127.0.0.1', port=8999): Max retries exceeded with url: /libros (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object>: Failed to establish a new connection: [WinError 10061] No se puede establecer una conexión ya que el equipo de destino denegó expresamente dicha conexión'))
  ```
- **Cómo lo identificamos y manejamos:** atrapando `requests.exceptions.ConnectionError` en un bloque `try/except` dentro de `cliente.py` para imprimir un aviso claro en lugar de abortar el programa con un traceback.

---

## Cierre F4 — Comparación entre `/docs` (Swagger UI) y herramientas externas (`curl` / Postman)

Se probaron los mismos 3 pedidos (`GET /libros`, `POST /libros` válido y `POST /libros` inválido sin `paginas`) tanto desde `http://127.0.0.1:8000/docs` como desde la terminal con `curl`:

```bash
# 1. GET /libros
curl -i http://127.0.0.1:8000/libros

# 2. POST /libros válido (201 Created)
curl -i -X POST http://127.0.0.1:8000/libros \
  -H "Content-Type: application/json" \
  -d '{"titulo": "El Aleph", "autor": "Jorge Luis Borges", "paginas": 196}'

# 3. POST /libros inválido sin 'paginas' (422 Unprocessable Entity)
curl -i -X POST http://127.0.0.1:8000/libros \
  -H "Content-Type: application/json" \
  -d '{"titulo": "Libro Incompleto"}'
```

- **Similitud:** Ambos caminos envían exactamente el mismo pedido HTTP al servidor (mismo verbo, misma URL, mismo header `Content-Type: application/json` y mismo body JSON) y reciben idéntico código de estado (`200`, `201`, `422`) y cuerpo de respuesta. Underneath, `/docs` incluso muestra el comando `curl` equivalente que acaba de ejecutar.
- **Diferencia:** `/docs` se genera automáticamente a partir de los modelos Pydantic de FastAPI y ya trae el esquema JSON pre-armado en el navegador, mientras que en Postman / Insomnia / `curl` uno debe construir manualmente la URL, los headers y el body, pero puede guardar colecciones, variables de entorno y automatizar secuencias de prueba.
- **Cuándo preferir cada uno:**
  - **`/docs` (Swagger UI):** ideal durante el desarrollo para explorar rápidamente los endpoints, ver qué campos y tipos espera cada modelo y hacer pruebas manuales inmediatas sin salir del navegador.
  - **Postman / `curl` / scripts cliente:** ideal para compartir una colección reproducible con el equipo, probar flujos encadenados con variables o depurar cabeceras crudas desde una terminal (por ejemplo, dentro de una Raspberry Pi por SSH donde no hay navegador).
