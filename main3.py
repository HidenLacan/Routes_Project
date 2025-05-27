# Mapa temporal solo para dibujar un polígono y exportarlo como GeoJSON

import folium
from folium.plugins import Draw
import os
import webbrowser
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from threading import Thread

# Bounding box aproximado para centrar el mapa
bbox = (
    float("19.30"),  # south
    float("19.32"),  # north
    float("-99.07"),  # west
    float("-99.05")   # east
)

# Calcular centro del mapa
center_lat = (bbox[0] + bbox[1]) / 2
center_lon = (bbox[2] + bbox[3]) / 2
m = folium.Map(location=[center_lat, center_lon], zoom_start=15)
# Dibujar bounding box
bbox_coords = [
    (bbox[0], bbox[2]),  # (south, west)
    (bbox[0], bbox[3]),  # (south, east)
    (bbox[1], bbox[3]),  # (north, east)
    (bbox[1], bbox[2]),  # (north, west)
]
folium.Polygon(
    locations=bbox_coords,
    color='orange',
    weight=2,
    fill=True,
    fill_opacity=0.2,
    tooltip='Bounding Box'
).add_to(m)

# Agregar herramienta de dibujo
Draw(export=True, filename='data/drawn_features.geojson').add_to(m)

# Guardar el HTML del mapa
output_file = "mapa_dibujo_temporal.html"
m.save(output_file)

# Abrir servidor local para servir el mapa y abrir navegador
print("🧭 Abriendo mapa temporal para dibujar polígono...")

def lanzar_mapa():
    with TCPServer(("", 8000), SimpleHTTPRequestHandler) as httpd:
        webbrowser.open(f"http://localhost:8000/{output_file}")
        httpd.serve_forever()

thread = Thread(target=lanzar_mapa)
thread.daemon = True
thread.start()

input("🔴 Dibuja un polígono en el navegador y expórtalo como GeoJSON.\nLuego presiona ENTER aquí para cerrar...")
print("✅ Mapa temporal finalizado. Puedes cerrar esta ventana si lo deseas.")
