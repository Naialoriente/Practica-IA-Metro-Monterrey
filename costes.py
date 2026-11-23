"""
costes.py - Cálculo de recargos por factores extra para el trayecto.
Regla importante: los factores extra solo suman coste (nunca restan)
para no romper la admisibilidad de la heurística h(n) en A*.
"""

RECARGO_HORA_PUNTA_TRAMO = 0.25       # +25% en tramos normales en hora punta
RECARGO_HORA_PUNTA_TRANSBORDO = 1.5  # +1.5 min en transbordos en hora punta
PENALIZACION_SIN_ASCENSOR = 15.0     # +15.0 min si se pide ruta accesible y no hay ascensor

FRANJAS_PUNTA = [
    (7, 0, 9, 30),    # Mañana: 07:00 - 09:30
    (17, 30, 20, 30), # Tarde: 17:30 - 20:30
]

DIAS_LABORABLES = {"lunes", "martes", "miercoles", "miércoles", "jueves", "viernes"}


def _tiene_ascensor(info_estacion: dict) -> bool:
    """Devuelve True si la estación tiene ascensor ('Si'), False en caso contrario."""
    valor = str(info_estacion.get("ascensor", "")).strip().lower()
    return valor in {"si", "sí", "true", "1"}


def _parsear_minutos_dia(hora_valor) -> int | None:
    """Convierte 'HH:MM' o un entero de hora (0-23) a minutos desde las 00:00."""
    if hora_valor is None or hora_valor == "":
        return None
    if isinstance(hora_valor, int):
        if 0 <= hora_valor <= 23:
            return hora_valor * 60
        return None
    texto = str(hora_valor).strip()
    if ":" in texto:
        partes = texto.split(":")
        if len(partes) >= 2:
            h = int(partes[0])
            m = int(partes[1])
            return h * 60 + m
    if texto.isdigit():
        h = int(texto)
        if 0 <= h <= 23:
            return h * 60
    return None


def es_hora_punta(contexto: dict) -> bool:
    """Comprueba si el día y la hora del contexto corresponden a hora punta."""
    if not contexto:
        return False

    # Si la interfaz envía directamente un booleano o etiqueta de franja, también lo soporta
    if contexto.get("hora_punta") is True:
        return True

    dia = str(contexto.get("dia", "lunes")).strip().lower()
    if dia and dia not in DIAS_LABORABLES:
        return False

    minutos_actuales = _parsear_minutos_dia(contexto.get("hora"))
    if minutos_actuales is None:
        return False

    for h_ini, m_ini, h_fin, m_fin in FRANJAS_PUNTA:
        inicio = h_ini * 60 + m_ini
        fin = h_fin * 60 + m_fin
        if inicio <= minutos_actuales <= fin:
            return True

    return False


def calcular_recargo_hora_punta(arista, contexto: dict) -> float:
    """Devuelve los minutos extra por hora punta (>= 0.0)."""
    if not es_hora_punta(contexto):
        return 0.0

    coste_base = float(arista.minutos)
    if arista.tipo == "transbordo":
        return max(0.0, RECARGO_HORA_PUNTA_TRANSBORDO)
    return max(0.0, coste_base * RECARGO_HORA_PUNTA_TRAMO)


def calcular_recargo_accesibilidad(arista, contexto: dict) -> float:
    """
    Si el usuario pide ruta accesible y origen o destino no tienen ascensor
    (teniendo que usar escaleras), suma una penalización en minutos.
    """
    if not contexto or not contexto.get("ruta_accesible", False):
        return 0.0

    origen_ok = _tiene_ascensor(arista.origen_info)
    destino_ok = _tiene_ascensor(arista.destino_info)

    if not origen_ok or not destino_ok:
        return max(0.0, PENALIZACION_SIN_ASCENSOR)

    return 0.0


def calcular_coste(arista, contexto: dict | None = None) -> float:
    """
    Función principal pasada a astar(..., coste_fn=calcular_coste).
    Devuelve el coste base más los recargos aplicables (siempre >= arista.minutos).
    """
    ctx = contexto or {}
    base = float(arista.minutos)
    extra_punta = calcular_recargo_hora_punta(arista, ctx)
    extra_acceso = calcular_recargo_accesibilidad(arista, ctx)

    total = base + extra_punta + extra_acceso
    if total < base:
        return base
    return total
