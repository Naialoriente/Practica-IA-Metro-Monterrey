
import csv

def cargar_estaciones():
    # Cada estación y línea se identifica con un id único, que representa un nodo.
    estaciones = {}

    archivo = open("estaciones.csv", encoding="utf-8-sig")
    lineas = archivo.readlines()
    archivo.close()

    # DictReader usa la cabecera del csv para dar nombre a cada campo.
    lector = csv.DictReader(lineas)

    for fila in lector:
        estaciones[fila["id"]] = fila
    return estaciones


def cargar_conexiones():
    # Cada fila representa un arco dirigido con un coste en minutos.
    conexiones = []

    archivo = open("conexiones.csv", encoding="utf-8-sig")
    lineas = archivo.readlines()
    archivo.close()

    lector = csv.DictReader(lineas)

    for fila in lector:
        conexion = {
            "origen": fila["origen"],
            "destino": fila["destino"],
            "linea": fila["linea"],
            # Pasamos el coste a número para poder sumarlo en A*.
            "minutos": float(fila["minutos"])
        }

        conexiones.append(conexion)

    return conexiones


def construir_grafo(estaciones, conexiones):
    # La lista de adyacencia guarda los sucesores de cada nodo.
    grafo = {}

    for id_estacion in estaciones:
        grafo[id_estacion] = []

    for conexion in conexiones:
        origen = conexion["origen"]
        destino = conexion["destino"]
        minutos = conexion["minutos"]

        # Añadimos el nodo destino y el coste de llegar a él desde el origen.
        grafo[origen].append((destino, minutos))

    return grafo


def comprobar_conectividad(grafo):
    # Recorremos el grafo en profundidad desde Talleres.
    # Las pendientes forman una pila. Las visitadas evitan repetir nodos en ciclos.
    visitadas = set()
    pendientes = ["L1_01"]

    while pendientes:
        actual = pendientes.pop()

        if actual not in visitadas:
            visitadas.add(actual)

            for destino, minutos in grafo[actual]:
                if destino not in visitadas:
                    pendientes.append(destino)

    return len(visitadas) == len(grafo)




if __name__ == "__main__":
    estaciones = cargar_estaciones()
    conexiones = cargar_conexiones()
    grafo = construir_grafo(estaciones, conexiones)

    print("Número de estaciones:", len(estaciones))
    print("Número de conexiones:", len(conexiones))
    print("Número de nodos:", len(grafo))
    print("Conexiones desde Cuauhtémoc:", grafo["L1_12"])
    print("¿Todas las estaciones son accesibles?", comprobar_conectividad(grafo))


