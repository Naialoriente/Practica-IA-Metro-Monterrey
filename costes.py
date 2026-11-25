"""
costes.py - Cálculo de recargos por factores extra para el trayecto.
Regla importante: los factores extra solo suman coste (nunca restan)
para no romper la admisibilidad de la heurística h(n) en A*.
"""

import unicodedata


RECARGO_HORA_PUNTA_TRAMO = 0.25
RECARGO_HORA_PUNTA_TRANSBORDO = 1.5
PENALIZACION_SIN_ASCENSOR = 15.0

FRANJAS_PUNTA = [
    (7 * 60, 9 * 60 + 30),
    (17 * 60 + 30, 20 * 60 + 30),
]

DIAS_LABORABLES = {"lunes", "martes", "miercoles", "jueves", "viernes"}


def _quitar_tildes(texto):
    texto = unicodedata.normalize("NFD", str(texto).strip().lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def _tiene_ascensor(info_estacion):
    valor = str(info_estacion.get("ascensor", "")).strip().lower()
    valor = _quitar_tildes(valor)
    return valor in {"si", "true", "1"}


def _a_minutos_dia(hora):
    if hora is None:
        return None
    if isinstance(hora, int):
        if 0 <= hora <= 23:
            return hora * 60
        return None
    texto = str(hora).strip()
    if ":" in texto:
        partes = texto.split(":")
        if len(partes) >= 2 and partes[0].strip().isdigit() and partes[1].strip().isdigit():
            h = int(partes[0].strip())
            m = int(partes[1].strip())
            if 0 <= h <= 23 and 0 <= m <= 59:
                return h * 60 + m
        return None
    if texto.isdigit():
        h = int(texto)
        if 0 <= h <= 23:
            return h * 60
    return None


def es_hora_punta(dia_semana, hora):
    if not dia_semana:
        return False
    dia = _quitar_tildes(dia_semana)
    if dia not in DIAS_LABORABLES:
        return False
    mins = _a_minutos_dia(hora)
    if mins is None:
        return False
    for inicio, fin in FRANJAS_PUNTA:
        if inicio <= mins <= fin:
            return True
    return False


def calcular_coste_arista(
    minutos_base,
    info_origen,
    info_destino,
    es_transbordo=False,
    dia_semana=None,
    hora=None,
    ruta_accesible=False,
):
    coste = float(minutos_base)
    if coste < 0:
        raise ValueError("El coste base no puede ser negativo.")

    en_punta = es_hora_punta(dia_semana, hora)
    if en_punta:
        if es_transbordo:
            coste += RECARGO_HORA_PUNTA_TRANSBORDO
        else:
            coste += coste * RECARGO_HORA_PUNTA_TRAMO

    if ruta_accesible:
        if not _tiene_ascensor(info_origen) or not _tiene_ascensor(info_destino):
            coste += PENALIZACION_SIN_ASCENSOR

    return coste


def aplicar_recargos_grafo(
    grafo,
    estaciones,
    dia_semana=None,
    hora=None,
    ruta_accesible=False,
):
    grafo_ajustado = {}
    for origen, vecinos in grafo.items():
        info_origen = estaciones.get(origen, {})
        nueva_lista = []
        for destino, minutos_base in vecinos:
            info_destino = estaciones.get(destino, {})
            mismo_nombre = _quitar_tildes(info_origen.get("nombre", "")) == _quitar_tildes(
                info_destino.get("nombre", "")
            )
            es_transbordo = mismo_nombre and (
                str(info_origen.get("linea", "")) != str(info_destino.get("linea", ""))
            )
            coste_final = calcular_coste_arista(
                minutos_base=minutos_base,
                info_origen=info_origen,
                info_destino=info_destino,
                es_transbordo=es_transbordo,
                dia_semana=dia_semana,
                hora=hora,
                ruta_accesible=ruta_accesible,
            )
            nueva_lista.append((destino, coste_final))
        grafo_ajustado[origen] = nueva_lista
    return grafo_ajustado
