"""
Ejercicios — Clase 2: APIs (y el concepto de MQTT)
Parte B — API de Libros y Autores con FastAPI (B1 a B12) y Cierre F1
"""

from fastapi import FastAPI, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

app = FastAPI(
    title="API de Libros y Autores — IC2 Clase 2",
    description="API REST construida con FastAPI para los ejercicios de la Clase 2 (UNRaf).",
    version="1.0.0",
)


# ------------------------------------------------------------------
# Modelos Pydantic (B3, B8, B9, B10, B12)
# ------------------------------------------------------------------
class Editorial(BaseModel):
    """Modelo anidado que representa la editorial de un libro (B10)."""

    nombre: str = Field(..., min_length=1, examples=["Sudamericana"])
    pais: str = Field(..., min_length=1, examples=["Argentina"])


class LibroIn(BaseModel):
    """
    Modelo de entrada para crear o reemplazar un libro (POST / PUT).
    - B8: paginas debe ser estrictamente mayor a 0 (gt=0).
    - B10: incluye el objeto anidado Editorial.
    - B12: disponible tiene valor por defecto True; precio_costo es un campo interno
      que no se expone en las respuestas gracias a response_model=LibroOut.
    """

    titulo: str = Field(..., min_length=1, examples=["Ficciones"])
    autor: str = Field(default="Autor Desconocido", examples=["Jorge Luis Borges"])
    paginas: int = Field(
        ...,
        gt=0,
        description="La cantidad de páginas debe ser mayor a 0 (B8).",
        examples=[224],
    )
    disponible: bool = Field(default=True, examples=[True])
    editorial: Editorial = Field(
        default_factory=lambda: Editorial(nombre="Sudamericana", pais="Argentina")
    )
    precio_costo: float | None = Field(
        default=None,
        description="Campo interno de costo que response_model filtra en la salida (B12).",
    )


class LibroOut(BaseModel):
    """
    Modelo de salida (response_model, B12): expone los datos públicos del libro
    y filtra automáticamente campos internos como 'precio_costo'.
    """

    titulo: str
    autor: str
    paginas: int
    disponible: bool = True
    editorial: Editorial


class Autor(BaseModel):
    """Segundo recurso independiente para la API (B9)."""

    nombre: str = Field(..., min_length=1, examples=["Jorge Luis Borges"])
    nacionalidad: str = Field(default="Argentina", examples=["Argentina"])


# ------------------------------------------------------------------
# Estado en memoria (al menos 3 libros precargados, B2)
# ------------------------------------------------------------------
LIBROS_INICIALES: list[dict] = [
    {
        "titulo": "Ficciones",
        "autor": "Jorge Luis Borges",
        "paginas": 224,
        "disponible": True,
        "editorial": {"nombre": "Sur", "pais": "Argentina"},
        "precio_costo": 8500.0,
    },
    {
        "titulo": "Rayuela",
        "autor": "Julio Cortázar",
        "paginas": 600,
        "disponible": True,
        "editorial": {"nombre": "Sudamericana", "pais": "Argentina"},
        "precio_costo": 12000.0,
    },
    {
        "titulo": "El Eternauta",
        "autor": "Héctor Germán Oesterheld",
        "paginas": 352,
        "disponible": False,
        "editorial": {"nombre": "Planeta", "pais": "Argentina"},
        "precio_costo": 14500.0,
    },
]

AUTORES_INICIALES: list[dict] = [
    {"nombre": "Jorge Luis Borges", "nacionalidad": "Argentina"},
    {"nombre": "Julio Cortázar", "nacionalidad": "Argentina"},
    {"nombre": "Héctor Germán Oesterheld", "nacionalidad": "Argentina"},
]

libros_db: list[dict] = [ dict(libro, editorial=dict(libro["editorial"])) for libro in LIBROS_INICIALES ]
autores_db: list[dict] = [ dict(autor) for autor in AUTORES_INICIALES ]


def resetear_datos() -> None:
    """Restaura las listas en memoria a su estado inicial (útil para tests)."""
    libros_db.clear()
    for libro in LIBROS_INICIALES:
        libros_db.append(dict(libro, editorial=dict(libro["editorial"])))
    autores_db.clear()
    for autor in AUTORES_INICIALES:
        autores_db.append(dict(autor))


# ------------------------------------------------------------------
# Endpoints de la API
# ------------------------------------------------------------------
@app.get("/", tags=["Saludo"])
def raiz() -> dict[str, str]:
    """🟢 B1 — Endpoint que saluda."""
    return {"mensaje": "hola"}


@app.get("/libros", response_model=list[LibroOut], tags=["Libros"])
def listar_libros(
    paginas_min: int | None = Query(
        default=None,
        description="Filtra y devuelve solo los libros con al menos esta cantidad de páginas (B11).",
    ),
) -> list[dict]:
    """
    🟡 B2 / 🔴 B11 / 🔴 B12 — Lista todos los libros o filtra por `paginas_min` si se envía.
    Usa `response_model=list[LibroOut]` para no exponer `precio_costo`.
    """
    if paginas_min is not None:
        return [libro for libro in libros_db if libro["paginas"] >= paginas_min]
    return libros_db


@app.post(
    "/libros",
    response_model=LibroOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Libros"],
)
def crear_libro(libro: LibroIn) -> dict:
    """
    🟡 B3 / 🟡 B4 / 🔴 B8 / 🔴 B10 / 🔴 B12 — Agrega un libro nuevo a la colección.
    Devuelve 201 Created con el libro creado (filtrado por LibroOut).
    """
    nuevo_libro = libro.model_dump()
    libros_db.append(nuevo_libro)
    return nuevo_libro


@app.get("/libros/{titulo}", response_model=LibroOut, tags=["Libros"])
def obtener_libro(titulo: str) -> dict:
    """
    🟡 B5 — Busca un libro por su título exacto (ignorando mayúsculas/minúsculas).
    Si no existe, devuelve 404 Not Found.
    """
    for libro in libros_db:
        if libro["titulo"].lower() == titulo.lower():
            return libro
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"El libro '{titulo}' no existe.",
    )


@app.put("/libros/{titulo}", response_model=LibroOut, tags=["Libros"])
def reemplazar_libro(titulo: str, libro_nuevo: LibroIn) -> dict:
    """
    🟡 B6 — Reemplaza un libro existente entero por uno nuevo (PUT).
    Si el título no existe, devuelve 404 Not Found en lugar de crearlo silenciosamente.
    """
    for indice, libro in enumerate(libros_db):
        if libro["titulo"].lower() == titulo.lower():
            datos_actualizados = libro_nuevo.model_dump()
            libros_db[indice] = datos_actualizados
            return datos_actualizados

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No se puede actualizar: el libro '{titulo}' no existe.",
    )


@app.delete(
    "/libros/{titulo}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Libros"],
)
def borrar_libro(titulo: str) -> Response:
    """
    🟡 B7 — Elimina un libro por su título.
    Devuelve 204 No Content (sin cuerpo porque el recurso eliminado ya no existe)
    o 404 Not Found si no estaba en la lista.
    """
    for indice, libro in enumerate(libros_db):
        if libro["titulo"].lower() == titulo.lower():
            libros_db.pop(indice)
            return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No se puede borrar: el libro '{titulo}' no existe.",
    )


# ------------------------------------------------------------------
# 🔴 B9 — Segundo recurso: /autores
# ------------------------------------------------------------------
@app.get("/autores", response_model=list[Autor], tags=["Autores"])
def listar_autores() -> list[dict]:
    """🔴 B9 — Lista todos los autores registrados."""
    return autores_db


@app.post(
    "/autores",
    response_model=Autor,
    status_code=status.HTTP_201_CREATED,
    tags=["Autores"],
)
def crear_autor(autor: Autor) -> dict:
    """🔴 B9 — Registra un nuevo autor."""
    nuevo_autor = autor.model_dump()
    autores_db.append(nuevo_autor)
    return nuevo_autor
