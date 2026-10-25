"""
Ejercicios — Clase 2: APIs (y el concepto de MQTT)
Parte A4 — Verificación en Python de los JSON escritos a mano
"""

import json

JSON_LIBRO_SIMPLE = """
{
  "titulo": "Ficciones",
  "autor": "Jorge Luis Borges",
  "paginas": 224,
  "disponible": true
}
"""

JSON_LISTA_DOS_LIBROS = """
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
"""

JSON_LIBRO_CON_EDITORIAL = """
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
"""


def validar_jsons() -> dict:
    """Parsea los tres textos JSON de A4 y devuelve las estructuras de Python."""
    libro_simple = json.loads(JSON_LIBRO_SIMPLE)
    lista_libros = json.loads(JSON_LISTA_DOS_LIBROS)
    libro_anidado = json.loads(JSON_LIBRO_CON_EDITORIAL)
    return {
        "libro_simple": libro_simple,
        "lista_libros": lista_libros,
        "libro_anidado": libro_anidado,
    }


def main() -> None:
    datos = validar_jsons()
    print("=== Validación de JSON (A4) ===")
    print("1) Libro simple (dict):", datos["libro_simple"])
    print("2) Lista de 2 libros (list[dict]):", datos["lista_libros"])
    print("3) Libro con editorial anidada (dict con dict interno):", datos["libro_anidado"])
    print(
        "   País de la editorial:",
        datos["libro_anidado"]["editorial"]["pais"],
    )


if __name__ == "__main__":
    main()
