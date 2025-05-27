# editor_launcher.py
import os
import json
import time
import webbrowser
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from threading import Thread


def shutdown_server():
    """Apaga el servidor HTTP si está en ejecución."""
    global httpd_reference
    if httpd_reference:
        print("🛑 Cerrando servidor (por función externa)...")
        Thread(target=httpd_reference.shutdown).start()

def launch_polygon_editor(colonia_nombre: str, cache_path: str, timeout: int = 300) -> str:
    """
    Lanza un servidor local con un mapa interactivo centrado en el bounding box
    de la colonia proporcionada. Espera a que el usuario dibuje un polígono y
    lo guarde como GeoJSON. Devuelve la ruta al archivo generado.
    """
    output_path = f"data/poligonos/{colonia_nombre}"
    os.makedirs("data/poligonos", exist_ok=True)

    with open(cache_path, "r", encoding="utf-8") as f:
        data = json.load(f)[0]
    bbox = [float(x) for x in data["boundingbox"]]  # south, north, west, east

    center_lat = (bbox[0] + bbox[1]) / 2
    center_lon = (bbox[2] + bbox[3]) / 2
    nombre = data.get("name", data.get("display_name", "colonia_sin_nombre")).strip().lower().replace(" ", "_")

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset='utf-8'/>
        <title>Dibujar Polígono</title>
        <link rel='stylesheet' href='https://unpkg.com/leaflet@1.9.3/dist/leaflet.css'/>
        <link rel='stylesheet' href='https://cdn.jsdelivr.net/npm/leaflet-draw@1.0.4/dist/leaflet.draw.css'/>
        <style> html, body, #map {{ height: 100%; margin: 0; }} </style>
    </head>
    <body>
    <div id='map'></div>
    <script src='https://unpkg.com/leaflet@1.9.3/dist/leaflet.js'></script>
    <script src='https://cdn.jsdelivr.net/npm/leaflet-draw@1.0.4/dist/leaflet.draw.js'></script>
    <script>
        const map = L.map('map').setView([{center_lat}, {center_lon}], 16);
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png').addTo(map);

        const bounds = [
            [{bbox[0]}, {bbox[2]}],
            [{bbox[1]}, {bbox[3]}]
        ];
        L.rectangle(bounds, {{color: 'orange', weight: 2, fillOpacity: 0.2}}).addTo(map);

        const drawnItems = new L.FeatureGroup().addTo(map);
        new L.Control.Draw({{
            draw: {{ polygon: true, polyline: false, marker: false, circle: false, rectangle: false, circlemarker: false }},
            edit: {{ featureGroup: drawnItems }}
        }}).addTo(map);

        map.on('draw:created', function(e) {{
            const layer = e.layer;
            drawnItems.addLayer(layer);
            const geojson = layer.toGeoJSON();
            geojson.nombre = "{nombre}";

            fetch('/guardar', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify(geojson)
            }}).then(() => {{
                alert('✅ Polígono enviado. Puedes cerrar esta ventana.');
            }});
        }});
    </script>
    </body>
    </html>
    """

    html_file = f"mapa_{nombre}.html"
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_code)

    class Handler(SimpleHTTPRequestHandler):
        def do_POST(self):
            global httpd_reference
            if self.path == "/guardar":
                content_len = int(self.headers.get('Content-Length'))
                body = self.rfile.read(content_len)
                with open(output_path, "wb") as f:
                    f.write(body)
                self.send_response(200)
                self.end_headers()

                print("🛑 Cerrando servidor (internamente)...")
                
                if httpd_reference:
                    Thread(target=httpd_reference.shutdown).start()

    def run_server():
        global httpd_reference
        with TCPServer(("", 8000), Handler) as httpd:
            httpd_reference = httpd
            webbrowser.open(f"http://localhost:8000/{html_file}")
            httpd.serve_forever()

    thread = Thread(target=run_server)
    thread.start()
    thread.join()

    if os.path.exists(output_path):
        print(f"✅ Polígono guardado en {output_path}")
        return output_path
    else:
        raise TimeoutError("⏱️ No se recibió polígono en el tiempo esperado.")
