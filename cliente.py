"""
Ejercicios — Clase 2: APIs (y el concepto de MQTT)
Parte C — Consumir la API desde un cliente con requests (C1 a C8) y Cierre F1 / F3
"""

import requests

BASE_URL = "http://127.0.0.1:8000"
TIMEOUT_SEGUNDOS = 5


def interpretar_respuesta(respuesta: requests.Response) -> str:
    """
    🔴 C4 — Reacciona según el código de estado HTTP devuelto por la API:
    - 200 / 201 / 204 -> "ok"
    - 422             -> "dato inválido"
    - 404             -> "no existe"
    """
    codigo = respuesta.status_code
    if codigo in (200, 201, 204):
        estado = "ok"
    elif codigo == 422:
        estado = "dato inválido"
    elif codigo == 404:
        estado = "no existe"
    else:
        estado = f"otro estado ({codigo})"

    print(f"  [HTTP {codigo}] -> {estado}")
    return estado


def listar_libros(
    session: requests.Session,
    base_url: str = BASE_URL,
    paginas_min: int | None = None,
) -> list | None:
    """🟡 C1 / 🔴 C6 / 🔴 C7 / 🔴 C8 — Hace GET /libros reutilizando Session y timeout."""
    params = {"paginas_min": paginas_min} if paginas_min is not None else None
    try:
        resp = session.get(
            f"{base_url}/libros",
            params=params,
            timeout=TIMEOUT_SEGUNDOS,
        )
        interpretar_respuesta(resp)
        return resp.json() if resp.ok else None
    except requests.exceptions.Timeout:
        print("  [ERROR] Tiempo de espera agotado (requests.exceptions.Timeout).")
        return None
    except requests.exceptions.ConnectionError:
        print(
            "  [ERROR] No se pudo conectar a la API "
            "(requests.exceptions.ConnectionError: verificá que uvicorn esté corriendo)."
        )
        return None


def crear_libro(
    session: requests.Session,
    datos_libro: dict,
    base_url: str = BASE_URL,
) -> dict | None:
    """
    🟡 C2 / 🔴 C3 — Hace POST /libros enviando el diccionario en `json=datos_libro`.
    Nota C3 ("En /docs andaba y acá no"):
    Si en requests usamos `data=datos_libro` en vez de `json=datos_libro`, requests lo envía
    como formulario (`application/x-www-form-urlencoded`) sin el header
    `Content-Type: application/json`, y FastAPI devuelve 422. Usar `json=...` serializa
    el dict a JSON y agrega el header automáticamente.
    """
    try:
        resp = session.post(
            f"{base_url}/libros",
            json=datos_libro,
            timeout=TIMEOUT_SEGUNDOS,
        )
        interpretar_respuesta(resp)
        return resp.json()
    except requests.exceptions.Timeout:
        print("  [ERROR] Tiempo de espera agotado (requests.exceptions.Timeout).")
        return None
    except requests.exceptions.ConnectionError:
        print("  [ERROR] No se pudo conectar a la API (requests.exceptions.ConnectionError).")
        return None


def obtener_libro(
    session: requests.Session,
    titulo: str,
    base_url: str = BASE_URL,
) -> dict | None:
    """Busca un libro puntual por título con GET /libros/{titulo}."""
    try:
        resp = session.get(
            f"{base_url}/libros/{titulo}",
            timeout=TIMEOUT_SEGUNDOS,
        )
        interpretar_respuesta(resp)
        return resp.json()
    except requests.exceptions.Timeout:
        print("  [ERROR] Tiempo de espera agotado (requests.exceptions.Timeout).")
        return None
    except requests.exceptions.ConnectionError:
        print("  [ERROR] No se pudo conectar a la API (requests.exceptions.ConnectionError).")
        return None


def reemplazar_libro(
    session: requests.Session,
    titulo: str,
    datos_libro: dict,
    base_url: str = BASE_URL,
) -> dict | None:
    """🟡 C5 — Hace PUT /libros/{titulo} para reemplazar un libro completo."""
    try:
        resp = session.put(
            f"{base_url}/libros/{titulo}",
            json=datos_libro,
            timeout=TIMEOUT_SEGUNDOS,
        )
        interpretar_respuesta(resp)
        return resp.json()
    except requests.exceptions.Timeout:
        print("  [ERROR] Tiempo de espera agotado (requests.exceptions.Timeout).")
        return None
    except requests.exceptions.ConnectionError:
        print("  [ERROR] No se pudo conectar a la API (requests.exceptions.ConnectionError).")
        return None


def borrar_libro(
    session: requests.Session,
    titulo: str,
    base_url: str = BASE_URL,
) -> int | None:
    """🟡 C5 — Hace DELETE /libros/{titulo} para eliminar un libro."""
    try:
        resp = session.delete(
            f"{base_url}/libros/{titulo}",
            timeout=TIMEOUT_SEGUNDOS,
        )
        interpretar_respuesta(resp)
        return resp.status_code
    except requests.exceptions.Timeout:
        print("  [ERROR] Tiempo de espera agotado (requests.exceptions.Timeout).")
        return None
    except requests.exceptions.ConnectionError:
        print("  [ERROR] No se pudo conectar a la API (requests.exceptions.ConnectionError).")
        return None


def provocar_timeout_real() -> str:
    """
    🔴 C7 — Apunta a una IP no enrutable (10.255.255.1) con timeout=1 segundo
    para provocar de forma confiable requests.exceptions.Timeout.
    """
    try:
        requests.get("http://10.255.255.1/", timeout=1)
        return "conectado"
    except requests.exceptions.Timeout as exc:
        mensaje = f"Timeout capturado exitosamente ({type(exc).__name__}): {exc}"
        print(f"  {mensaje}")
        return mensaje
    except requests.exceptions.RequestException as exc:
        mensaje = f"Excepción de red capturada ({type(exc).__name__}): {exc}"
        print(f"  {mensaje}")
        return mensaje


def main() -> None:
    print("=" * 65)
    print("PARTE C — Cliente HTTP con requests.Session() (C1 a C8 + F3)")
    print("=" * 65)

    # 🔴 C8 — Usamos una única requests.Session() para reutilizar la conexión TCP (keep-alive)
    with requests.Session() as session:
        # C1: Listar libros iniciales
        print("\n1) C1 — GET /libros (lista inicial):")
        libros = listar_libros(session)
        if libros is not None:
            for l in libros:
                print(f"   - {l['titulo']} ({l['paginas']} págs.) - Editorial: {l['editorial']['nombre']}")

            # C2: Crear un libro nuevo con POST
            print("\n2) C2 — POST /libros (crear 'El Aleph'):")
            nuevo = {
                "titulo": "El Aleph",
                "autor": "Jorge Luis Borges",
                "paginas": 196,
                "disponible": True,
                "editorial": {"nombre": "Emecé", "pais": "Argentina"},
            }
            creado = crear_libro(session, nuevo)
            print(f"   Respuesta POST: {creado}")

            # Confirmar con GET que se agregó
            print("\n3) C2 — GET /libros?paginas_min=300 (filtro B11):")
            filtrados = listar_libros(session, paginas_min=300)
            print(f"   Libros con >= 300 páginas: {[l['titulo'] for l in (filtrados or [])]}")

            # C5: Reemplazar con PUT
            print("\n4) C5 — PUT /libros/El Aleph (actualizar páginas a 210):")
            actualizado = reemplazar_libro(
                session,
                "El Aleph",
                {
                    "titulo": "El Aleph",
                    "autor": "Jorge Luis Borges",
                    "paginas": 210,
                    "disponible": False,
                    "editorial": {"nombre": "Debolsillo", "pais": "Argentina"},
                },
            )
            print(f"   Respuesta PUT: {actualizado}")

            # C5: Borrar con DELETE
            print("\n5) C5 — DELETE /libros/El Aleph:")
            borrar_libro(session, "El Aleph")

            # F3 / C4: Provocar 404 (pedir un libro que no existe)
            print("\n6) C4 / F3 — GET /libros/El Aleph (ya borrado -> 404 'no existe'):")
            detalle_404 = obtener_libro(session, "El Aleph")
            print(f"   Cuerpo 404: {detalle_404}")

            # F3 / C4: Provocar 422 (mandar un POST sin el campo obligatorio 'paginas')
            print("\n7) C4 / F3 — POST /libros inválido sin 'paginas' (-> 422 'dato inválido'):")
            detalle_422 = crear_libro(session, {"titulo": "Libro Incompleto"})
            print(f"   Cuerpo 422: {detalle_422}")

        # C6 / F3: Demostrar qué pasa cuando la API está apagada (puerto cerrado 8999)
        print("\n8) C6 / F3 — Pedido contra API apagada (http://127.0.0.1:8999):")
        listar_libros(session, base_url="http://127.0.0.1:8999")

        # C7: Provocar timeout real contra IP no enrutable 10.255.255.1
        print("\n9) C7 — Provocar Timeout real contra http://10.255.255.1/ (timeout=1s):")
        provocar_timeout_real()


if __name__ == "__main__":
    main()
