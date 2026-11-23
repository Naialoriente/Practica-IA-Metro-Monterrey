"""
astar.py - Algoritmo A* para el metro de Monterrey (Metrorrey)
"""
import heapq
import sys
import unicodedata
from math import radians, sin, cos, asin, sqrt
from grafo import cargar_estaciones, cargar_conexiones, construir_grafo

def normalizar(texto):
    """Convierte el texto a minúsculas y elimina las tildes."""
    texto = unicodedata.normalize("NFD", str(texto).strip().lower())
    return "".join(letra for letra in texto
                   if unicodedata.category(letra) != "Mn" )


def ids_por_nombre(estaciones, nombre):
    ids = []
    for id_estacion, fila in estaciones.items():
        if normalizar(fila["nombre"]) == normalizar(nombre):
            ids.append(id_estacion)
    return ids

def distancia_km(estaciones, a, b):
    """Calcula la distancia geográfica."""
    lat1 = radians(float(estaciones[a]["latitud"]))
    lon1 = radians(float(estaciones[a]["longitud"]))
    lat2 = radians(float(estaciones[b]["latitud"]))
    lon2 = radians(float(estaciones[b]["longitud"]))
    h = ( sin((lat2 - lat1) / 2) ** 2
        + cos(lat1) * cos(lat2)
        * sin((lon2 - lon1) / 2) ** 2)
    h = max(0.0, min(1.0, h))
    return 2 * 6371 * asin(sqrt(h))


def velocidad_maxima(estaciones, conexiones):
    maxima = 0.0
    for conexion in conexiones:
        if normalizar(conexion["linea"]) != "transbordo":
            origen = conexion["origen"]
            destino = conexion["destino"]
            minutos = float(conexion["minutos"])
            if minutos <= 0:
                raise ValueError(
                    "Los tiempos de las conexiones deben ser positivos."
                )
            velocidad = (distancia_km(estaciones, origen, destino) / minutos)
            maxima = max(maxima, velocidad)
    return maxima

def a_star(estaciones, grafo, origenes, destinos, v_max):

    if not origenes or not destinos:
        return None, float("inf")
    destinos = set(destinos)
    def h(nodo):
        """Estima el tiempo restante hasta el destino más cercano."""
        if v_max <= 0:
            return 0.0
        distancia = min(
            distancia_km(estaciones, nodo, destino)
            for destino in destinos)
        return distancia / v_max
    abiertos = []
    g = {}
    padre = {}

    for origen in origenes:
        g[origen] = 0.0
        heapq.heappush(
            abiertos,
            (h(origen), 0.0, origen)
        )

    while abiertos:
        f_actual, g_actual, actual = heapq.heappop(abiertos)
        if g_actual > g.get(actual, float("inf")):
            continue
        if actual in destinos:
            camino = [actual]
            while camino[-1] in padre:
                camino.append(padre[camino[-1]])
            camino.reverse()
            return camino, g_actual

        for vecino, minutos in grafo.get(actual, []):
            minutos = float(minutos)
            if minutos < 0:
                raise ValueError("A* necesita costes no negativos.")

            g_nuevo = g_actual + minutos
            if g_nuevo < g.get(vecino, float("inf")):
                g[vecino] = g_nuevo
                padre[vecino] = actual
                f_nuevo = g_nuevo + h(vecino)
                heapq.heappush(
                    abiertos,
                    (f_nuevo, g_nuevo, vecino)
                )
    return None, float("inf")


def mostrar_ruta(estaciones, camino, minutos):
    """Muestra recorrido y transbordos."""
    if camino is None:
        print("No existe una ruta entre las estaciones seleccionadas.")
        return
    transbordos = 0
    print("\n RUTA ÓPTIMA : \n")
    for i, id_estacion in enumerate(camino):
        actual = estaciones[id_estacion]
        print("Línea", actual["linea"],":", actual["nombre"])
        if i + 1 < len(camino):
            siguiente = estaciones[camino[i + 1]]
            if normalizar(siguiente["nombre"]) == normalizar(actual["nombre"]):
                transbordos += 1
                print(  " Transbordo:",actual["linea"], "->",siguiente["linea"])

    print("Tiempo total: %.2f minutos" % minutos)
    print("Número de transbordos:", transbordos)


if __name__ == "__main__":
    estaciones = cargar_estaciones()
    conexiones = cargar_conexiones()
    grafo = construir_grafo(estaciones, conexiones)

    v_max = velocidad_maxima(estaciones, conexiones)


    nombre_origen = (
        sys.argv[1] if len(sys.argv) > 1 else "Talleres"
    )
    nombre_destino = (
        sys.argv[2] if len(sys.argv) > 2
        else "Hospital Metropolitano")

    origenes = ids_por_nombre(estaciones, nombre_origen)
    destinos = ids_por_nombre(estaciones, nombre_destino)

    if not origenes:
        print("No se ha encontrado el origen:", nombre_origen)

    elif not destinos:
        print("No se ha encontrado el destino:", nombre_destino)

    else:
        camino, minutos = a_star(
            estaciones,
            grafo,
            origenes,
            destinos,
            v_max
        )
        mostrar_ruta(estaciones, camino, minutos)
