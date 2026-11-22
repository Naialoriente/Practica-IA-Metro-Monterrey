
"""
astar.py - Algoritmo A* para el metro de Monterrey (Metrorrey)
Calcula el trayecto óptimo entre dos estaciones de las líneas 1, 2 y 3.
Cada nodo representa una pareja estación-línea.
Los transbordos se representan mediante arcos entre nodos
de una misma estación pertenecientes a líneas diferentes.
FUNCIONES DE EVALUACIÓN
    g(n) = coste real acumulado desde el origen hasta n.
    h(n) = distancia en línea recta hasta el destino / velocidad máxima.
    f(n) = g(n) + h(n).
ALGORITMOS DISPONIBLES
    A*:       f(n) = g(n) + h(n)
    Voraz:    f(n) = h(n)
    Dijkstra: f(n) = g(n)
La heurística de A* es minorante y consistente, por lo que
el algoritmo encuentra una solución óptima si existe.
"""
from __future__ import annotations
import heapq
import itertools
import math
import unicodedata
from dataclasses import dataclass, field
from typing import Callable, Optional
R_TIERRA_KM = 6371.0088
ALGORITMOS = ("astar", "voraz", "dijkstra")

@dataclass
class Arista:
    origen: str
    destino: str
    linea_origen: str
    linea_destino: str
    minutos: float
    tipo: str
    origen_info: dict = field(default_factory=dict)
    destino_info: dict = field(default_factory=dict)


@dataclass
class Paso:
    arista: Arista
    coste: float


@dataclass
class Resultado:
    encontrado: bool
    camino: list = field(default_factory=list)
    pasos: list = field(default_factory=list)
    coste_total: float = math.inf
    transbordos: int = 0
    nodos_expandidos: int = 0
    algoritmo: str = "astar"
    v_max_km_min: float = 0.0

    def nombres(self, estaciones) -> list:
        nombres = []
        for nodo in self.camino:
            nombre = estaciones[nodo]["nombre"]
            if not nombres or nombres[-1] != nombre:
                nombres.append(nombre)
        return nombres

    def resumen(self, estaciones) -> str:
        """Genera un resumen legible del recorrido."""
        if not self.encontrado:
            return "No existe ruta entre las estaciones indicadas."
        filas = []
        for paso in self.pasos:
            arista = paso.arista
            origen = estaciones[arista.origen]["nombre"]
            destino = estaciones[arista.destino]["nombre"]
            if arista.tipo == "tramo":
                filas.append(
                    f"  [L{arista.linea_destino}] "
                    f"{origen} -> {destino} "
                    f"({paso.coste:.2f} min)"
                )
            else:
                filas.append(
                    f"  TRANSBORDO en {origen}: "
                    f"L{arista.linea_origen} -> "
                    f"L{arista.linea_destino} "
                    f"({paso.coste:.2f} min)"
                )
        cabecera = (
            f"{self.algoritmo.upper()}: "
            f"{self.coste_total:.2f} min, "
            f"{self.transbordos} transbordo(s), "
            f"{self.nodos_expandidos} nodos expandidos"
        )
        return cabecera + "\n" + "\n".join(filas)


def _norm(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto.strip().lower())
    return "".join(
        c for c in texto
        if unicodedata.category(c) != "Mn"
    )

def ids_de_estacion(estaciones: dict, estacion: str) -> list:
    """Si una estación tiene varias líneas, devuelve todos sus nodos."""

    if estacion in estaciones:
        return [estacion]
    buscado = _norm(estacion)
    ids = [
        identificador
        for identificador, datos in estaciones.items()
        if _norm(datos["nombre"]) == buscado
    ]

    if not ids:
        raise ValueError(f"Estación desconocida: {estacion}")
    return ids



def _validar_grafo(estaciones: dict, grafo: dict):
    """Comprueba que el grafo y sus costes sean válidos."""
    if not estaciones:
        raise ValueError("No hay estaciones cargadas.")
    if not grafo:
        raise ValueError("El grafo está vacío.")
    for nodo, sucesores in grafo.items():
        if nodo not in estaciones:
            raise ValueError(f"Nodo desconocido: {nodo}")
        for destino, minutos in sucesores:
            if destino not in estaciones:
                raise ValueError(
                    f"La conexión {nodo} -> {destino} "
                    "apunta a una estación inexistente."
                )

            if not math.isfinite(float(minutos)) or minutos <= 0:
                raise ValueError(
                    f"Coste inválido en la conexión "
                    f"{nodo} -> {destino}: {minutos}"
                )



def haversine_km(lat1: float, lon1: float,
                 lat2: float, lon2: float) -> float:
    """Calcula la distancia en línea recta entre dos coordenadas."""
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = (
        math.sin(dp / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    )
    return 2 * R_TIERRA_KM * math.asin(math.sqrt(a))

def _dist_nodos(estaciones: dict, a: str, b: str) -> float:
    """Calcula la distancia geográfica entre dos nodos."""
    ea = estaciones[a]
    eb = estaciones[b]
    return haversine_km(
        float(ea["latitud"]),
        float(ea["longitud"]),
        float(eb["latitud"]),
        float(eb["longitud"])
    )


def velocidad_maxima(estaciones: dict, grafo: dict) -> float:
    """
    Calcula la velocidad máxima observada en los arcos.
    Esta velocidad permite construir una heurística minorante.
    """
    v_max = 0.0
    for origen, sucesores in grafo.items():
        for destino, minutos in sucesores:
            distancia = _dist_nodos(
                estaciones, origen, destino
            )
            velocidad = distancia / minutos
            v_max = max(v_max, velocidad)

    if v_max <= 0 or not math.isfinite(v_max):
        raise ValueError(
            "No se puede calcular la velocidad máxima."
        )
    return v_max


def heuristica(estaciones: dict, nodo: str,
               meta: str, v_max: float) -> float:
    """ h(n) = distancia en línea recta hasta la meta / v_max. """
    distancia = _dist_nodos(estaciones, nodo, meta)
    return distancia / v_max


def _sucesores(estaciones: dict, grafo: dict, nodo: str):
    """Genera las aristas que salen de un nodo."""
    for destino, minutos in grafo[nodo]:
        linea_origen = estaciones[nodo]["linea"]
        linea_destino = estaciones[destino]["linea"]
        tipo = (
            "tramo"
            if linea_origen == linea_destino
            else "transbordo"
        )
        yield Arista(
            nodo,
            destino,
            linea_origen,
            linea_destino,
            minutos,
            tipo,
            estaciones[nodo],
            estaciones[destino]
        )


def _coste_aplicado(arista: Arista, contexto: dict,
                    coste_fn: Optional[Callable]) -> float:
    """
    Calcula el coste real de una arista.
    """
    if coste_fn is None:
        return arista.minutos
    ajustado = float(coste_fn(arista, contexto))
    if not math.isfinite(ajustado):
        raise ValueError("La función de costes ha devuelto un valor inválido.")
    return max(arista.minutos, ajustado)


def astar(estaciones: dict, grafo: dict,
          origen: str, destino: str,
          contexto: Optional[dict] = None,
          coste_fn: Optional[Callable] = None,
          algoritmo: str = "astar") -> Resultado:
    """
    Busca el camino de menor coste entre dos estaciones.
    """
    if algoritmo not in ALGORITMOS:
        raise ValueError(
            f"Algoritmo no válido. Opciones: {ALGORITMOS}"
        )
    _validar_grafo(estaciones, grafo)
    contexto = contexto or {}
    ids_origen = ids_de_estacion(estaciones, origen)
    ids_meta = set(ids_de_estacion(estaciones, destino))
    meta_ref = next(iter(ids_meta))
    v_max = velocidad_maxima(estaciones, grafo)
    cache_h = {}

    def h(nodo):
        if algoritmo == "dijkstra":
            return 0.0
        if nodo not in cache_h:
            cache_h[nodo] = heuristica(
                estaciones, nodo, meta_ref, v_max
            )
        return cache_h[nodo]

    def f(g, nodo):
        if algoritmo == "voraz":
            return h(nodo)
        return g + h(nodo)


    contador = itertools.count()
    abierta = []
    g_mejor = {}
    padre = {}

    cerrada = set()
    expandidos = 0

    for nodo_inicial in ids_origen:
        g_mejor[nodo_inicial] = 0.0
        padre[nodo_inicial] = None
        heapq.heappush(
            abierta,
            (
                f(0.0, nodo_inicial),
                h(nodo_inicial),
                next(contador),
                0.0,
                nodo_inicial
            )
        )


    while abierta:
        _, _, _, g, nodo = heapq.heappop(abierta)

        if g != g_mejor.get(nodo):
            continue
        if nodo in cerrada:
            continue
        if nodo in ids_meta:

            return _reconstruir(
                nodo,
                padre,
                g,
                expandidos,
                algoritmo,
                v_max
            )

        cerrada.add(nodo)
        expandidos += 1

        for arista in _sucesores(estaciones, grafo, nodo):
            sucesor = arista.destino
            if sucesor in cerrada:
                continue
            coste = _coste_aplicado(
                arista,
                contexto,
                coste_fn
            )

            g_nuevo = g + coste
            if g_nuevo < g_mejor.get(sucesor, math.inf):
                g_mejor[sucesor] = g_nuevo
                padre[sucesor] = (
                    nodo,
                    Paso(arista, coste)
                )
                heapq.heappush(
                    abierta,
                    (
                        f(g_nuevo, sucesor),
                        h(sucesor),
                        next(contador),
                        g_nuevo,
                        sucesor
                    )
                )

    return Resultado(
        encontrado=False,
        nodos_expandidos=expandidos,
        algoritmo=algoritmo,
        v_max_km_min=v_max
    )



def _reconstruir(nodo, padre, g,
                 expandidos, algoritmo, v_max) -> Resultado:
    """Reconstruye el camino siguiendo los nodos padre."""
    pasos = []
    camino = [nodo]
    while padre[nodo] is not None:
        nodo, paso = padre[nodo]
        pasos.append(paso)
        camino.append(nodo)

    pasos.reverse()
    camino.reverse()

    transbordos = sum(
        1 for paso in pasos
        if paso.arista.tipo == "transbordo"
    )

    return Resultado(
        encontrado=True,
        camino=camino,
        pasos=pasos,
        coste_total=g,
        transbordos=transbordos,
        nodos_expandidos=expandidos,
        algoritmo=algoritmo,
        v_max_km_min=v_max
    )



def verificar_consistencia(estaciones: dict,
                           grafo: dict,
                           eps: float = 1e-9) -> list:
    """
    Comprueba la condición:
        h(n) <= c(n,m) + h(m)
    Para todos los arcos y destinos posibles.
    Devuelve una lista de violaciones.
    Si está vacía, la heurística es consistente.
    """
    _validar_grafo(estaciones, grafo)
    v_max = velocidad_maxima(estaciones, grafo)
    malos = []
    for meta in estaciones:
        for nodo, sucesores in grafo.items():
            for destino, minutos in sucesores:
                h_n = heuristica(
                    estaciones, nodo, meta, v_max
                )
                h_m = heuristica(
                    estaciones, destino, meta, v_max
                )
                if h_n > minutos + h_m + eps:
                    malos.append(
                        (nodo, destino, meta)
                    )
    return malos


if __name__ == "__main__":
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    from grafo import (
        cargar_estaciones,
        cargar_conexiones,
        construir_grafo
    )
    estaciones = cargar_estaciones()
    conexiones = cargar_conexiones()
    grafo = construir_grafo(
        estaciones,
        conexiones
    )
    for algoritmo in ALGORITMOS:
        resultado = astar(
            estaciones,
            grafo,
            "Talleres",
            "Hospital Metropolitano",
            algoritmo=algoritmo
        )
        print(resultado.resumen(estaciones))
        print()
    print(
        "Velocidad máxima:",
        round(velocidad_maxima(estaciones, grafo) * 60, 2),
        "km/h"
    )
    print(
        "Violaciones de consistencia:",
        verificar_consistencia(estaciones, grafo)
    )
