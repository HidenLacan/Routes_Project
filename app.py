# app.py: Servidor Flask para recibir y guardar un polígono dibujado en el navegador

from flask import Flask, request, jsonify
import os
import json

app = Flask(__name__)

### Ruta para guardar un polígono dibujado en el navegador
### Esta ruta recibe un JSON con los datos del polígono y lo guarda en un archivo
@app.route("/guardar_poligono", methods=["POST"])
def guardar_poligono():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No se recibió JSON"}), 400

    base_nombre = data.get("nombre", "colonia_sin_nombre").strip().lower().replace(" ", "_") or "colonia_sin_nombre"
    output_dir = "data/poligonos"
    os.makedirs(output_dir, exist_ok=True)

    # Generar nombre incremental si ya existe
    nombre_final = base_nombre
    contador = 1
    while os.path.exists(os.path.join(output_dir, f"{nombre_final}.json")):
        contador += 1
        nombre_final = f"{base_nombre}_{contador}"

    output_path = os.path.join(output_dir, f"{nombre_final}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return jsonify({"status": "ok", "message": f"Polígono guardado como {nombre_final}.json"})
### Ruta para obtener los datos de la colonia
@app.route("/datos")
def datos():
    with open(f"cache/{colonia}", "r", encoding="utf-8") as f:
        datos = json.load(f)[0]  # se espera una lista con un dict
        

    nombre = datos.get("name", datos.get("display_name", "Colonia sin nombre")).strip().lower().replace(" ", "_")
    bbox = datos.get("boundingbox", ["19.30", "19.32", "-99.07", "-99.05"])
            
    return jsonify({
        "nombre": nombre,
        "bbox": [float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])]
    })

### Ruta principal que sirve el archivo HTML
@app.route("/")
def index():
    print(datos)
    return app.send_static_file("mapa_dibujo.html")

if __name__ == "__main__":
    colonia = 'san_lorenzo_tezonco_ciudad_de_méxico.json'
    app.run(debug=True, port=5000)
