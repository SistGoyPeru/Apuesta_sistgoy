from flask import Flask, jsonify, render_template_string
import subprocess
import os

app = Flask(__name__)

# Configuración
SCRIPT_NAME = "generar_pronosticos_multi_pdf.py"
CWD = os.path.dirname(os.path.abspath(__file__))

# Plantilla HTML con un diseño amigable para móvil
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>SistGoy Apuestas</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background-color: #121212; color: white; text-align: center; padding: 20px; }
        h1 { color: #bb86fc; }
        .btn {
            background-color: #03dac6; 
            color: black;
            padding: 20px 40px;
            font-size: 20px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            width: 100%;
            max-width: 300px;
            margin-top: 30px;
            font-weight: bold;
        }
        .btn:active { background-color: #018786; }
        .btn:disabled { background-color: #555; cursor: not-allowed; }
        #status { margin-top: 20px; font-size: 1.2em; }
        .spinner {
            display: none;
            width: 40px; height: 40px; margin: 20px auto;
            border: 4px solid rgba(255,255,255,0.3); border-radius: 50%; border-top: 4px solid #bb86fc;
            animation: spin 1s linear infinite;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
    <script>
        function generarReporte() {
            var btn = document.getElementById("genBtn");
            var status = document.getElementById("status");
            var spinner = document.getElementById("spinner");

            btn.disabled = true;
            btn.innerText = "Generando...";
            status.innerText = "Procesando pronósticos y generando PDF...";
            status.style.color = "#ccc";
            spinner.style.display = "block";

            fetch('/ejecutar-reporte')
            .then(response => response.json())
            .then(data => {
                spinner.style.display = "none";
                btn.disabled = false;
                btn.innerText = "Generar PDF Nuevo";
                if(data.status === "success") {
                    status.innerText = "✅ ¡Listo! El PDF se ha actualizado en OneDrive.";
                    status.style.color = "#03dac6";
                } else {
                    status.innerText = "❌ Error: " + data.message;
                    status.style.color = "#cf6679";
                }
            })
            .catch(err => {
                spinner.style.display = "none";
                btn.disabled = false;
                btn.innerText = "Reintentar";
                status.innerText = "❌ Error de conexión.";
                status.style.color = "#cf6679";
            });
        }
    </script>
</head>
<body>
    <h1>SistGoy Apuestas ⚽</h1>
    <p>Presiona para actualizar el reporte PDF en OneDrive.</p>
    
    <button id="genBtn" class="btn" onclick="generarReporte()">GENERAR PDF</button>
    
    <div id="spinner" class="spinner"></div>
    <div id="status"></div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/ejecutar-reporte')
def ejecutar():
    try:
        # Ejecutar el script existente
        # capture_output=True permite ver si hubo errores
        result = subprocess.run(["python", SCRIPT_NAME], cwd=CWD, capture_output=True, text=True)
        
        if result.returncode == 0:
            return jsonify({
                "status": "success", 
                "message": "Reporte actualizado exitosamente."
            })
        else:
            # Si falla, devolvemos el error (últimas 200 líneas para no saturar)
            error_msg = result.stderr[-500:] if result.stderr else "Error desconocido"
            return jsonify({
                "status": "error", 
                "message": error_msg
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    # host='0.0.0.0' hace que el servidor sea visible en tu red local (WiFi)
    print("--- SERVIDOR SISTGOY ACTIVO ---")
    print("Para entrar desde tu celular:")
    print("1. Conecta tu celular al mismo WiFi que esta PC.")
    print("2. Averigua la IP local de esta PC (ej. ipconfig -> 192.168.X.X)")
    print("3. Entra en el navegador del celular a: http://<TU_IP>:5000")
    app.run(host='0.0.0.0', port=5000)
