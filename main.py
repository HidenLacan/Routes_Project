# Proyecto: División de rutas para vendedores en una colonia

import osmnx as ox
import networkx as nx
from networkx.algorithms.community import kernighan_lin_bisection
import folium
from shapely.geometry import shape, Polygon
import osmnx as ox
import json
import os
import re
import geopandas as gpd
import requests

import matplotlib.pyplot as plt
import networkx as nx

def sanitize_filename(name: str) -> str:
    return re.sub(r'\W+', '_', name.lower())

def download_graph(place_name: str):
    print(f"Descargando grafo de {place_name}...")

    # Ruta para guardar la caché con nombre limpio
    cache_file = f"cache/{sanitize_filename(place_name)}.json"
    os.makedirs("cache", exist_ok=True)
    
    # ------------------------------------------------------
    # Si ya existe el archivo, cargarlo
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        # Consulta a Nominatim directamente
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": place_name,
            "format": "json",
            "limit": 1,
            "polygon_geojson": 1
        }
        headers = {"User-Agent": "mi-aplicacion-ceneval"}
        response = requests.get(url, params=params, headers=headers)
        if response.status_code != 200:
            raise RuntimeError(f"Error en la petición: {response.status_code}")
        data = response.json()
        if not data:
            raise RuntimeError(f"No se encontró '{place_name}' en Nominatim.")
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Guardado en {cache_file}")

    entry = data[0]
    geojson = entry.get("geojson", {})
    geometry_type = geojson.get("type", "")

    # Extraer bounding box siempre -----------------------------------------------------------
    try:
        bbox = entry["boundingbox"]
        south = float(bbox[0])
        north = float(bbox[1])
        west = float(bbox[2])
        east = float(bbox[3])
    except (KeyError, ValueError, IndexError):
        raise RuntimeError("No se pudo extraer bounding box del JSON")

    # Caso 1: Usamos geojson si hay polígono válido
    if geometry_type in ["Polygon", "MultiPolygon"] and "coordinates" in geojson:
        print("Generando grafo desde geojson (polígono)...")
        geometry = shape(geojson)
        G = ox.graph_from_polygon(geometry, network_type='walk')
        G = nx.Graph(G)
    # Caso 2: Creamos un polígono rectangular a partir del bounding box ------ tenemos que manejar siempre a logica del bbox dado a que se usara mas adelante
    else:
        print("Generando grafo desde bounding box (como polígono)...")
        polygon_coords = [
            (west, south),
            (east, south),
            (east, north),
            (west, north),
        ]
        polygon = Polygon(polygon_coords)
        gdf = gpd.GeoDataFrame(index=[0], geometry=[polygon], crs="EPSG:4326")
        G = ox.graph_from_polygon(gdf.geometry[0], network_type='drive')
        G = nx.Graph(G)
    return G

#### --------------------------------------------Division de grafo

def split_graph(G):
    print("Dividiendo grafo en dos zonas...")
    part1, part2 = kernighan_lin_bisection(G)
    return part1, part2


def draw_partitioned_graph(G, part1, part2):
    print("Dibujando el grafo con zonas en rojo y azul...")
    color_map = ['red' if node in part1 else 'blue' for node in G.nodes()]
    nx.draw(G, node_color=color_map, node_size=10, edge_color='gray', with_labels=False)
    plt.show()

def calcular_longitud_por_zona(G, part1, part2):
    total_part1 = 0
    total_part2 = 0

    for u, v, data in G.edges(data=True):
        length = data.get("length", 0)

        if u in part1 and v in part1:
            total_part1 += length
        elif u in part2 and v in part2:
            total_part2 += length

    return total_part1, total_part2

import geopandas as gpd
from shapely.geometry import Point

def calcular_area_por_zona(G, part1, part2):
    def area_de_particion(nodos):
        puntos = [Point((G.nodes[n]['x'], G.nodes[n]['y'])) for n in nodos]
        gdf = gpd.GeoDataFrame(geometry=puntos, crs="EPSG:4326")
        gdf = gdf.to_crs(epsg=32614)  # UTM zona 14N

        # Usamos union_all en lugar de unary_union (más moderno)
        union_geom = gdf.geometry.union_all()
        hull = union_geom.convex_hull

        if hull.area == 0:
            return 0
        return hull.area /   1_000_000  # en m²

    area1 = area_de_particion(part1)
    area2 = area_de_particion(part2)
    return area1, area2

import folium

#### --------------------------------------------Mapa interactivo con Folium

def draw_graph_folium(G, part1, part2, place_name="colonia", output_html=None):
    print("Generando mapa interactivo con folium...")

    if output_html is None:
        nombre_archivo = f"mapa_{sanitize_filename(place_name)}.html"
    else:
        nombre_archivo = output_html

    # Centro del mapa
    centro = list(G.nodes(data=True))[0][1]
    m = folium.Map(location=[centro['y'], centro['x']], zoom_start=16)

    for u, v, data in G.edges(data=True):
        if 'geometry' in data:
            coords = [(pt[1], pt[0]) for pt in data['geometry'].coords]
        else:
            coords = [(G.nodes[u]['y'], G.nodes[u]['x']), (G.nodes[v]['y'], G.nodes[v]['x'])]

        if u in part1 and v in part1:
            color = 'red'
        elif u in part2 and v in part2:
            color = 'blue'
        else:
            color = 'gray'

        folium.PolyLine(coords, color=color, weight=3, opacity=0.7).add_to(m)

    m.save(nombre_archivo)
    print(f"🗺️ Mapa guardado en: {nombre_archivo}")

## Entradas---------------------------------
####
if __name__ == '__main__':
    colonia = "San Lorenzo Tezonco, Ciudad de México"
    G = download_graph(colonia)
    part1, part2 = split_graph(G)
    
       # Estadísticas de nodos
    print(f"📊 Total de nodos: {len(G.nodes)}")
    print(f"🔴 Zona 1 (vendedor A): {len(part1)} nodos")
    print(f"🔵 Zona 2 (vendedor B): {len(part2)} nodos")

    # Estadísticas de longitud
    long1, long2 = calcular_longitud_por_zona(G, part1, part2)
    print(f"🛣️ Longitud total zona 1 (rojo): {long1:.2f} m")
    print(f"🛣️ Longitud total zona 2 (azul): {long2:.2f} m")
    
    
    area1, area2 = calcular_area_por_zona(G, part1, part2)
    print(f"📐 Área zona 1 (rojo): {area1:.2f} m²")
    print(f"📐 Área zona 2 (azul): {area2:.2f} m²")
    
    # Densidades
    dens_nodos1 = len(part1) / area1
    dens_nodos2 = len(part2) / area2
    dens_calles1 = long1 / area1
    dens_calles2 = long2 / area2
    print(f"🔗 Densidad de nodos zona 1: {dens_nodos1:.2f} nodos/km²")
    print(f"🔗 Densidad de nodos zona 2: {dens_nodos2:.2f} nodos/km²")
    print(f"🚏 Densidad de calles zona 1: {dens_calles1:.2f} m/km²")
    print(f"🚏 Densidad de calles zona 2: {dens_calles2:.2f} m/km²")
    draw_partitioned_graph(G, part1, part2)
    draw_graph_folium(G, part1, part2,place_name=colonia)

    