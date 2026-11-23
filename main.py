"""
main.py - Integración de carga de grafo, factores extra y algoritmo A*.
Incluye validación de entradas (control de errores).
"""

from grafo import cargar_estaciones, cargar_conexiones, construir_grafo
from costes import calcular_coste
from astar import astar, ids_de_estacion


def validar_entrada(estaciones: dict, origen: str, destino: str) -> None:
    """Valida que los campos no estén vacíos, existan y no sean iguales."""
    if not origen or not str(origen).strip():
        raise ValueError("Debes seleccionar o indicar una estación de origen.")
    if not destino or not str(destino).strip():
        raise ValueError("Debes seleccionar o indicar una estación de destino.")

    ids_origen = ids_de_estacion(estaciones, str(origen).strip())
    ids_destino = ids_de_estacion(estaciones, str(destino).strip())

    # Comprueba tanto por texto como por nombre normalizado de estación
    nombres_origen = {estaciones[i]["nombre"].strip().lower() for i in ids_origen}
    nombres_destino = {estaciones[i]["nombre"].strip().lower() for i in ids_destino}

    if str(origen).strip().lower() == str(destino).strip().lower() or nombres_origen == nombres_destino:
        raise ValueError("La estación de origen y la de destino no pueden ser la misma.")


def ejecutar_busqueda(
    origen: str,
    destino: str,
    hora: str = "12:00",
    dia: str = "lunes",
    ruta_accesible: bool = False,
    algoritmo: str = "astar",
):
    """Carga el grafo, valida la entrada y ejecuta la búsqueda con costes extra."""
    estaciones = cargar_estaciones()
    conexiones = cargar_conexiones()
    grafo = construir_grafo(estaciones, conexiones)

    validar_entrada(estaciones, origen, destino)

    contexto = {
        "hora": hora,
        "dia": dia,
        "ruta_accesible": bool(ruta_accesible),
    }

    resultado = astar(
        estaciones=estaciones,
        grafo=grafo,
        origen=str(origen).strip(),
        destino=str(destino).strip(),
        contexto=contexto,
        coste_fn=calcular_coste,
        algoritmo=algoritmo,
    )
    return estaciones, resultado


if __name__ == "__main__":
    # Ejemplo de prueba rápida por consola
    try:
        estaciones, res = ejecutar_busqueda(
            origen="Talleres",
            destino="Hospital Metropolitano",
            hora="08:15",
            dia="lunes",
            ruta_accesible=True,
            algoritmo="astar",
        )
        print(res.resumen(estaciones))
    except ValueError as err:
        print(f"Error de entrada: {err}")
