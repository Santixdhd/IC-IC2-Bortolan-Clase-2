# Parte A — Entender HTTP antes de escribir nada (A1 a A7)

---

## 🟢 A1 — Verbo correcto

| Acción | Verbo HTTP | Justificación |
| :--- | :---: | :--- |
| **(a) Ver la lista de libros** | `GET` | Consulta información existente en el servidor sin modificar ningún dato (operación de solo lectura). |
| **(b) Agregar un libro nuevo** | `POST` | Envía una entidad nueva al servidor para que cree un recurso dentro de la colección `/libros`. |
| **(c) Borrar un libro** | `DELETE` | Elimina un recurso específico identificado por su URL (ej. `/libros/{titulo}`). |
| **(d) Cambiarle el precio a un libro** | `PATCH` | Modifica parcialmente un recurso existente (solo el campo `precio`), dejando el resto intacto. |
| **(e) Reemplazar un libro entero por otro** | `PUT` | Sustituye la representación completa del recurso en esa URL por el nuevo objeto enviado. |
| **(f) Cambiarle solo la disponibilidad a un libro** | `PATCH` | Actualiza únicamente el campo `disponible` sin necesidad de reenviar todos los demás atributos del libro. |

**Diferencia entre (e) `PUT` y (f) `PATCH`:**
- **`PUT`** exige mandar el **recurso completo** y pisa todos los campos anteriores con la nueva versión (si un campo opcional no se manda, vuelve a su valor por defecto).
- **`PATCH`** aplica un **cambio parcial** solo sobre los campos enviados en el body, conservando intactos todos los demás campos del libro.

---

## 🟢 A2 — Leer códigos de estado (dominio de libros)

| Código | Nombre | Significado y ejemplo concreto en la API de libros |
| :---: | :--- | :--- |
| **`200`** | `OK` | El pedido salió bien y devuelve contenido. Ej.: `GET /libros` devuelve la lista de libros o `PUT /libros/Rayuela` devuelve el libro actualizado. |
| **`201`** | `Created` | Se creó un recurso nuevo con éxito. Ej.: `POST /libros` agrega `"El Aleph"` a la colección y devuelve el libro creado. |
| **`204`** | `No Content` | La operación tuvo éxito pero no devuelve cuerpo (`body`) en la respuesta. Ej.: `DELETE /libros/Rayuela` borra el libro y confirma que ya no está. |
| **`400`** | `Bad Request` | El pedido está mal formado a nivel sintáctico o de protocolo. Ej.: el cliente envía un JSON truncado con llaves sin cerrar `{"titulo": "Ficciones"`. |
| **`404`** | `Not Found` | El recurso pedido no existe. Ej.: `GET /libros/LibroInexistente` cuando ese título no está en la lista. |
| **`405`** | `Method Not Allowed` | La URL existe, pero no acepta ese verbo HTTP. Ej.: hacer `DELETE /libros` sobre la colección entera cuando solo está definido `GET` y `POST` en `/libros`. |
| **`422`** | `Unprocessable Entity` | El JSON es sintácticamente válido, pero viola las reglas de validación o tipos del modelo. Ej.: `POST /libros` con `{"titulo": "Dune", "paginas": "muchas"}` o `paginas: 0`. |
| **`500`** | `Internal Server Error` | Falló algo inesperado dentro del servidor (un bug no manejado en el código o caída de base de datos). Ej.: división por cero o excepción no capturada al procesar el libro. |

---

## 🟢 A3 — Familias de códigos

- **`2xx` (Éxito):** El servidor recibió, entendió y procesó el pedido correctamente (`200`, `201`, `204`).
- **`3xx` (Redirección):** El cliente debe realizar una acción adicional o ir a otra URL para completar el pedido (ej. `301 Moved Permanently` indica que el endpoint se mudó definitivamente a otra ruta).
- **`4xx` (Error del cliente):** El pedido tiene algún problema originado por quien llama a la API: falta autenticación, no tiene permisos (`403 Forbidden`), la ruta no existe (`404`) o los datos enviados son inválidos (`422`).
- **`5xx` (Error del servidor):** El pedido del cliente era válido, pero el servidor falló internamente al intentar responderlo (`500`, `502 Bad Gateway`, `503 Service Unavailable`).

---

## 🟡 A4 — JSON a mano

### 1. Un libro simple
```json
{
  "titulo": "Ficciones",
  "autor": "Jorge Luis Borges",
  "paginas": 224,
  "disponible": true
}
```

### 2. Una lista de 2 libros
```json
[
  {
    "titulo": "Ficciones",
    "autor": "Jorge Luis Borges",
    "paginas": 224,
    "disponible": true
  },
  {
    "titulo": "Rayuela",
    "autor": "Julio Cortázar",
    "paginas": 600,
    "disponible": false
  }
]
```

### 3. Un libro con campo anidado (`editorial`)
```json
{
  "titulo": "El Eternauta",
  "autor": "Héctor Germán Oesterheld",
  "paginas": 352,
  "disponible": true,
  "editorial": {
    "nombre": "Planeta",
    "pais": "Argentina"
  }
}
```
> Nota: En JSON los booleanos van en minúscula (`true` / `false`) y las claves siempre llevan comillas dobles `""`. Al parsearlo en Python con `json.loads()`, un objeto JSON `{...}` se convierte directamente en un `dict`, una lista `[...]` en un `list`, y el objeto anidado `"editorial"` pasa a ser un `dict` dentro de otro `dict`.

---

## 🟢 A5 — Idempotencia

- **¿Cuáles son idempotentes?**
  - **`GET`** es idempotente: consultar un libro 1 o 100 veces devuelve el mismo recurso sin alterar el estado del servidor.
  - **`PUT`** es idempotente: reemplazar `/libros/Rayuela` con los mismos datos 1 vez o 100 veces deja exactamente el mismo libro guardado.
  - **`DELETE`** es idempotente en cuanto al estado del servidor: borrar `/libros/Rayuela` una vez lo elimina; si se repite el pedido, el libro sigue sin existir en la colección (aunque la primera vez devuelva `204` y las siguientes `404`, el estado final del sistema es idéntico).
- **¿Cuál NO es idempotente?**
  - **`POST`** **NO es idempotente**: si el cliente manda un `POST /libros` para crear un libro y por un corte de red lo reenvía dos veces, el servidor procesa dos creaciones independientes (duplicando el registro o generando dos IDs distintos).

---

## 🟢 A6 — Headers, lo mínimo (`Content-Type: application/json`)

El header `Content-Type: application/json` le avisa al servidor en qué formato viajan los bytes del `body` para que sepa con qué parser leerlos.
Si un cliente manda el texto `{"titulo": "Dune", "paginas": 500}` pero omite ese header (o manda `text/plain`), el servidor no lo interpreta como un objeto JSON estructurado y FastAPI rechaza el pedido con `422 Unprocessable Entity` indicando que falta el cuerpo JSON esperado.

---

## 🟡 A7 — Diseñar URLs (REST básico)

En REST las URLs nombran **sustantivos en plural (recursos)** y la acción la define el **verbo HTTP**:

| Operación | Verbo HTTP | URL REST |
| :--- | :---: | :--- |
| Listar todos los libros | `GET` | `/libros` |
| Ver un libro puntual | `GET` | `/libros/{titulo}` (o `/libros/{id}`) |
| Listar los libros de un autor puntual | `GET` | `/autores/{id}/libros` (o `/libros?autor={nombre}`) |
| Crear un autor | `POST` | `/autores` |
