"""
Ejercicios — Clase 2: APIs (y el concepto de MQTT)
Parte E — Testear la API con pytest y TestClient (E1 a E4 + B1-B12 + F1)
"""

import pytest
from fastapi.testclient import TestClient
from main import app, resetear_datos
from parte_a_json import validar_jsons

client = TestClient(app)


@pytest.fixture(autouse=True)
def limpiar_base_en_memoria():
    """Restaura los datos iniciales antes de cada test para que sean independientes."""
    resetear_datos()


# ------------------------------------------------------------------
# 🟢 E1 — Tu primer test de API (GET /libros -> 200)
# ------------------------------------------------------------------
def test_listar_libros_status_200():
    """Verifica que GET /libros responde 200 OK y devuelve al menos 3 libros (E1 / B2)."""
    respuesta = client.get("/libros")
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert isinstance(datos, list)
    assert len(datos) >= 3


# ------------------------------------------------------------------
# 🟡 E2 — Automatizá el 422 de B4
# ------------------------------------------------------------------
def test_post_libro_sin_paginas_devuelve_422():
    """Verifica que enviar un libro sin el campo obligatorio 'paginas' devuelve 422 (E2 / B4)."""
    respuesta = client.post("/libros", json={"titulo": "Libro Sin Páginas"})
    assert respuesta.status_code == 422
    detalle = respuesta.json()["detail"]
    assert any(err["loc"][-1] == "paginas" for err in detalle)


def test_post_libro_paginas_tipo_texto_devuelve_422():
    """Verifica que enviar 'paginas': 'muchas' (texto en vez de int) devuelve 422 (E2 / B4)."""
    respuesta = client.post(
        "/libros",
        json={"titulo": "Libro Texto", "paginas": "muchas"},
    )
    assert respuesta.status_code == 422


def test_post_libro_paginas_menores_o_iguales_a_cero_devuelve_422():
    """Verifica la validación propia de B8: paginas <= 0 es rechazado con 422."""
    respuesta = client.post(
        "/libros",
        json={"titulo": "Libro Cero Páginas", "paginas": 0},
    )
    assert respuesta.status_code == 422


def test_post_libro_con_campo_extra_lo_ignora():
    """Verifica qué hace FastAPI/Pydantic por defecto ante un campo extra no esperado (B4)."""
    respuesta = client.post(
        "/libros",
        json={"titulo": "Libro Extra", "paginas": 150, "campo_inexistente": "valor"},
    )
    assert respuesta.status_code == 201
    assert "campo_inexistente" not in respuesta.json()


# ------------------------------------------------------------------
# 🟡 E3 — Camino feliz y camino con error para POST /libros
# ------------------------------------------------------------------
def test_post_libro_camino_feliz_201():
    """Camino feliz (E3): un libro válido con editorial anidada devuelve 201 Created."""
    nuevo_libro = {
        "titulo": "El Aleph",
        "autor": "Jorge Luis Borges",
        "paginas": 196,
        "editorial": {"nombre": "Emecé", "pais": "Argentina"},
        "precio_costo": 9000.0,
    }
    respuesta = client.post("/libros", json=nuevo_libro)
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["titulo"] == "El Aleph"
    assert cuerpo["paginas"] == 196
    assert cuerpo["disponible"] is True  # Valor por defecto (B12)
    assert cuerpo["editorial"] == {"nombre": "Emecé", "pais": "Argentina"}  # Modelo anidado (B10)
    assert "precio_costo" not in cuerpo  # Filtrado por response_model=LibroOut (B12)


# ------------------------------------------------------------------
# 🔴 E4 — Testear la secuencia POST -> GET
# ------------------------------------------------------------------
def test_secuencia_post_luego_get_confirma_insercion():
    """
    Encadena POST /libros y luego GET /libros para verificar que el libro creado
    aparece efectivamente en la lista devuelta por la API (E4).
    """
    libro_nuevo = {
        "titulo": "Sobre héroes y tumbas",
        "autor": "Ernesto Sabato",
        "paginas": 512,
        "editorial": {"nombre": "Seix Barral", "pais": "Argentina"},
    }
    resp_post = client.post("/libros", json=libro_nuevo)
    assert resp_post.status_code == 201

    resp_get = client.get("/libros")
    assert resp_get.status_code == 200
    titulos = [libro["titulo"] for libro in resp_get.json()]
    assert "Sobre héroes y tumbas" in titulos


# ------------------------------------------------------------------
# Tests adicionales de cobertura completa (B1, B5, B6, B7, B9, B11, A4)
# ------------------------------------------------------------------
def test_endpoint_saludo_raiz():
    """Verifica GET / -> {'mensaje': 'hola'} (B1)."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"mensaje": "hola"}


def test_buscar_libro_por_titulo_existente_y_404():
    """Verifica GET /libros/{titulo} cuando existe (200) y cuando no existe (404) (B5)."""
    resp_ok = client.get("/libros/Rayuela")
    assert resp_ok.status_code == 200
    assert resp_ok.json()["titulo"] == "Rayuela"

    resp_404 = client.get("/libros/Inexistente")
    assert resp_404.status_code == 404


def test_actualizar_libro_put_existente_y_404():
    """Verifica PUT /libros/{titulo} cuando existe (200) y cuando no existe (404) (B6)."""
    reemplazo = {
        "titulo": "Rayuela Edición Especial",
        "autor": "Julio Cortázar",
        "paginas": 720,
        "disponible": False,
        "editorial": {"nombre": "Alfaguara", "pais": "España"},
    }
    resp_put = client.put("/libros/Rayuela", json=reemplazo)
    assert resp_put.status_code == 200
    assert resp_put.json()["paginas"] == 720

    resp_404 = client.put("/libros/NoExiste", json=reemplazo)
    assert resp_404.status_code == 404


def test_borrar_libro_delete_204_y_luego_404():
    """Verifica DELETE /libros/{titulo} devuelve 204 sin body y luego GET da 404 (B7)."""
    resp_del = client.delete("/libros/Ficciones")
    assert resp_del.status_code == 204
    assert resp_del.content == b""

    resp_get = client.get("/libros/Ficciones")
    assert resp_get.status_code == 404


def test_filtrar_libros_por_paginas_min():
    """Verifica GET /libros?paginas_min=300 (B11)."""
    resp = client.get("/libros", params={"paginas_min": 300})
    assert resp.status_code == 200
    libros_filtrados = resp.json()
    assert len(libros_filtrados) == 2
    assert all(l["paginas"] >= 300 for l in libros_filtrados)


def test_recurso_autores_get_y_post():
    """Verifica el segundo recurso GET/POST /autores (B9)."""
    resp_post = client.post(
        "/autores",
        json={"nombre": "Mariana Enriquez", "nacionalidad": "Argentina"},
    )
    assert resp_post.status_code == 201

    resp_get = client.get("/autores")
    assert resp_get.status_code == 200
    nombres = [a["nombre"] for a in resp_get.json()]
    assert "Mariana Enriquez" in nombres


def test_json_a_mano_parte_a4():
    """Verifica que los 3 JSON de A4 sean válidos."""
    datos = validar_jsons()
    assert datos["libro_simple"]["titulo"] == "Ficciones"
    assert len(datos["lista_libros"]) == 2
    assert datos["libro_anidado"]["editorial"]["pais"] == "Argentina"
