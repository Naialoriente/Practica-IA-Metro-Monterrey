"""
main.py - Integración de carga de grafo, factores extra y algoritmo A*.
Incluye validación de entradas (control de errores).
"""
import sys
from grafo import cargar_estaciones, cargar_conexiones, construir_grafo
from astar import ids_por_nombre, velocidad_maxima, a_star, mostrar_ruta
from costes import aplicar_recargos_grafo


def validar_peticion(estaciones, nombre_origen, nombre_destino):
    if not nombre_origen or not str(nombre_origen).strip():
        raise ValueError("Debes indicar una estación de origen.")
    if not nombre_destino or not str(nombre_destino).strip():
        raise ValueError("Debes indicar una estación de destino.")
    if str(nombre_origen).strip().lower() == str(nombre_destino).strip().lower():
        raise ValueError("El origen y el destino no pueden ser la misma estación.")

    origenes = ids_por_nombre(estaciones, nombre_origen)
    destinos = ids_por_nombre(estaciones, nombre_destino)

    if not origenes:
        raise ValueError(f"No se ha encontrado el origen: {nombre_origen}")
    if not destinos:
        raise ValueError(f"No se ha encontrado el destino: {nombre_destino}")

    return origenes, destinos


def calcular_ruta_metrorrey(
    nombre_origen,
    nombre_destino,
    dia_semana="lunes",
    hora="12:00",
    ruta_accesible=False,
):
    estaciones = cargar_estaciones()
    conexiones = cargar_conexiones()
    grafo_base = construir_grafo(estaciones, conexiones)

    origenes, destinos = validar_peticion(estaciones, nombre_origen, nombre_destino)

    grafo_con_recargos = aplicar_recargos_grafo(
        grafo=grafo_base,
        estaciones=estaciones,
        dia_semana=dia_semana,
        hora=hora,
        ruta_accesible=ruta_accesible,
    )

    v_max = velocidad_maxima(estaciones, conexiones)
    camino, minutos = a_star(
        estaciones,
        grafo_con_recargos,
        origenes,
        destinos,
        v_max,
    )
    return estaciones, camino, minutos


if __name__ == "__main__":
    origen = sys.argv[1] if len(sys.argv) > 1 else "Talleres"
    destino = sys.argv[2] if len(sys.argv) > 2 else "Hospital Metropolitano"
    dia = sys.argv[3] if len(sys.argv) > 3 else "lunes"
    hora = sys.argv[4] if len(sys.argv) > 4 else "08:15"
    accesible = (sys.argv[5].lower() in {"1", "si", "true"}) if len(sys.argv) > 5 else True

    try:
        estaciones, camino, minutos = calcular_ruta_metrorrey(
            nombre_origen=origen,
            nombre_destino=destino,
            dia_semana=dia,
            hora=hora,
            ruta_accesible=accesible,
        )
        mostrar_ruta(estaciones, camino, minutos)
    except ValueError as e:
        print("Error:", e)
