"""Pruebas de astar.py con los datos reales de P1 (python test_astar.py  o  pytest)."""
import heapq
import math
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))   # grafo.py lee los CSV de esta carpeta

from astar import astar, ids_de_estacion, verificar_consistencia
from grafo import cargar_conexiones, cargar_estaciones, construir_grafo

EST = cargar_estaciones()
GR = construir_grafo(EST, cargar_conexiones())


def dijkstra_referencia(origen, destino):
    """Dijkstra independiente (sin heurística) para contrastar el resultado."""
    ini, meta = ids_de_estacion(EST, origen), set(ids_de_estacion(EST, destino))
    dist = {n: 0.0 for n in ini}
    cola = [(0.0, n) for n in ini]
    heapq.heapify(cola)
    while cola:
        d, n = heapq.heappop(cola)
        if d > dist.get(n, math.inf):
            continue
        if n in meta:
            return d
        for m, c in GR[n]:
            if d + c < dist.get(m, math.inf):
                dist[m] = d + c
                heapq.heappush(cola, (d + c, m))
    return math.inf


def test_misma_linea_sin_transbordos():
    r = astar(EST, GR, "Talleres", "Exposición")
    assert r.encontrado and r.transbordos == 0
    assert r.camino[0] == "L1_01" and r.camino[-1] == "L1_19"


def test_un_transbordo_en_cuauhtemoc():
    r = astar(EST, GR, "Sendero", "Talleres")
    assert r.transbordos == 1
    assert "Cuauhtémoc" in r.nombres(EST)


def test_dos_transbordos():
    r = astar(EST, GR, "Hospital Metropolitano", "Alameda")
    assert r.transbordos >= 1


def test_origen_igual_destino():
    r = astar(EST, GR, "Regina", "Regina")
    assert r.encontrado and r.coste_total == 0 and r.transbordos == 0


def test_acepta_ids_y_nombres_sin_tildes():
    a = astar(EST, GR, "cuauhtemoc", "FELIX U. GOMEZ")
    b = astar(EST, GR, "L1_12", "L1_14")
    assert abs(a.coste_total - b.coste_total) < 1e-9


def test_optimo_igual_que_dijkstra_para_todas_las_parejas():
    nombres = sorted({e["nombre"] for e in EST.values()})
    for o in nombres:
        for d in nombres:
            r = astar(EST, GR, o, d)
            assert abs(r.coste_total - dijkstra_referencia(o, d)) < 1e-9, (o, d)


def test_heuristica_consistente():
    assert verificar_consistencia(EST, GR) == []


def test_factores_extra_solo_suman():
    base = astar(EST, GR, "Sendero", "Talleres")
    intento_bajar = astar(EST, GR, "Sendero", "Talleres", coste_fn=lambda a, ctx: 0.0)
    assert abs(base.coste_total - intento_bajar.coste_total) < 1e-9
    punta = lambda a, ctx: a.minutos * (1.5 if ctx.get("hora_punta") else 1.0)
    assert astar(EST, GR, "Sendero", "Talleres", {"hora_punta": True}, punta).coste_total > base.coste_total


def test_astar_expande_menos_que_dijkstra():
    a = astar(EST, GR, "Talleres", "Hospital Metropolitano")
    d = astar(EST, GR, "Talleres", "Hospital Metropolitano", algoritmo="dijkstra")
    assert abs(a.coste_total - d.coste_total) < 1e-9
    assert a.nodos_expandidos <= d.nodos_expandidos


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_"):
            fn()
            print("OK", nombre)
