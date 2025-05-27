# import osmnx as ox

# place = "Kamppi, Helsinki, Finland"
# aoi = ox.geocoder.geocode_to_gdf(place)
# aoi.explore()


### -- obtengo las coordenadas
import osmnx as ox
# Opcional: mostrar mapa de la red
import matplotlib.pyplot as plt
# Definir el área de interés
place_name = "Privadas Diamante,General Escobedo, N.L., México "

# Descargar la red vial para vehículos (drive)
G = ox.graph_from_place(place_name, network_type='drive')

# Número de calles = número de aristas en el grafo
num_calles = G.number_of_edges()

print(f"Número estimado de calles en {place_name}: {num_calles}")



fig, ax = ox.plot_graph(G, figsize=(10,10), node_size=10, edge_color='blue', edge_linewidth=1)
plt.show()



import osmnx as ox
from shapely.geometry import Polygon

# Define el polígono con las coordenadas (lat, lon)
coords = [
    (19.30, -99.08),
    (19.30, -99.06),
    (19.32, -99.06),
    (19.32, -99.08),
]

# Crear objeto Polygon (nota que shapely usa (lon, lat))
polygon = Polygon([(lon, lat) for lat, lon in coords])

# Descargar la red vial dentro del polígono
G = ox.graph_from_polygon(polygon, network_type='drive')

# Contar número de calles (aristas)
num_calles = G.number_of_edges()
print(f"Número estimado de calles en el área definida: {num_calles}")

# Opcional: visualizar la red vial
fig, ax = ox.plot_graph(G, figsize=(10,10), node_size=10, edge_color='blue', edge_linewidth=1)
