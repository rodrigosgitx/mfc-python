import sys
sys.path.insert(0, "libs")
import http.server
import socketserver
import queue
import socket
import threading
import xml.etree.ElementTree as ET
#from dns.rdatatype import AAAA

from protocols import aberle
from protocols import durkopp
from protocols import commander

# Creamos el logger

import logging
logging.basicConfig(
    level=logging.INFO,
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("logs/info.log", mode="a", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

logging.info("Arrancamos el emulador")

#Definimos los protocolos

protocolos = {
    "aberle" :
        {"interpreta" : aberle.interpreta,
         "crea" : aberle.crea,
         "kal" : aberle.kal,
         "ack" : aberle.ack
         },
    "durkopp" :
        {"interpreta" : durkopp.interpreta,
         "crea" : durkopp.crea,
         "kal" : durkopp.kal,
         "ack" : durkopp.ack
         },
    "commander" :
        {"interpreta" : commander.interpreta,
         "crea" : commander.crea,
         "kal" : commander.kal
         }
    }

# Definimos los Sockets, leyendo config.xml

tree = ET.parse('config.xml')
root = tree.getroot()
conexiones = {}
# creamos el diccionario con los datos
for child in root:
    if (child.tag in ['plc'] ):
        logging.info (child.tag, child.attrib)
        for conx in child:
            conexiones[f'{child.attrib["name"]}.{conx.attrib["name"]}'] = {
                "id_plc" : child.attrib["name"],
                "id_puerto" : conx.attrib["name"],
                "protocolo" : child.attrib["protocolo"],
                "puerto" : int(conx.attrib["port"]),
                "kal" : bool(int(conx.attrib["kal"])),
                "kal.time" : int(conx.attrib["kal.time"]),
                "sender" : child.attrib["sender"],
                "receiver" : child.attrib ["receiver"],
                "cola" : queue.Queue(),
                "contador" : 0,
                "conectado" : False,
                "version" : conx.attrib ["version"],
                "isoOnTCP" : bool(int(conx.attrib.get("isoOnTCP", "0")))

                }

logging.info(conexiones)



def extrae_mensaje_iso_on_tcp(buffer):
  '''Extrae un payload TPKT/COTP completo del buffer si está disponible.'''
  if len(buffer) < 4 or buffer[:2] != b"\x03\x00":
    return None

  longitud = int.from_bytes(buffer[2:4], byteorder="big")
  if longitud < 7:
    raise ValueError(f"Longitud TPKT inválida: {longitud}")
  if len(buffer) < longitud:
    return None
  if buffer[4:7] != b"\x02\xf0\x80":
    raise ValueError("Cabecera COTP no soportada")

  return buffer[7:longitud], buffer[longitud:]


def empaqueta_iso_on_tcp(mensaje):
  '''Encapsula el payload en una trama TPKT/COTP de datos.'''
  longitud = len(mensaje) + 7
  return b"\x03\x00" + longitud.to_bytes(2, byteorder="big") + b"\x02\xf0\x80" + mensaje


def conexion_puerto(datos):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', datos["puerto"]))
        s.listen()

        logging.info(f'Escuchando en 0.0.0.0:{datos["puerto"]}...')

        while True:
            conn, addr = s.accept()
            with conn:
                logging.info(f'Conexión establecida desde {addr} en puerto {datos["id_plc"]}.{datos["id_puerto"]}\n')
                datos['conectado'] = True
                buffer_iso_on_tcp = b""
                usa_iso_on_tcp = datos["isoOnTCP"]

                # Si la cola no está vacía, recogemos y enviamos
                while True:
                    if not datos["cola"].empty():
                        response = datos["cola"].get()
                        if usa_iso_on_tcp:
                          response = empaqueta_iso_on_tcp(response)
                        conn.sendall(response)  # Enviar respuesta al cliente
                        logging.info(f'Enviado:{response} en puerto {datos["id_plc"]}.{datos["id_puerto"]}\n')

                    # Comprobamos si hay mensajes en el socket
                    s.settimeout(0.1)
                    conn.settimeout(0.1)
                    try:
                        data = conn.recv(1024)
                    except socket.timeout:
                        data = b""
                    if data:
                      if usa_iso_on_tcp:
                        buffer_iso_on_tcp += data
                        mensaje_iso_on_tcp = extrae_mensaje_iso_on_tcp(buffer_iso_on_tcp)

                        if mensaje_iso_on_tcp:
                          payload, buffer_iso_on_tcp = mensaje_iso_on_tcp
                          logging.info(
                            f'Datos recibidos en puerto {datos["id_plc"]}.{datos["id_puerto"]}: '
                            f'{payload.decode("ascii")}'
                          )
                          protocolos[datos["protocolo"]]["interpreta"](datos, payload.decode("ascii"))
                      else:
                        logging.info(
                          f'Datos recibidos en puerto {datos["id_plc"]}.{datos["id_puerto"]}: '
                          f'{data.decode("utf-8")}'
                        )
                        protocolos[datos["protocolo"]]["interpreta"](datos, data.decode("utf-8"))

# Frontend web

from flask import Flask, render_template, request, redirect, url_for, render_template_string

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])

def formulario():

    if request.method == 'POST':
        datos = request.form.to_dict()
        logging.info("Datos recibidos del formulario:", datos)

        # Obtener la conexión seleccionada
        conexion_id = datos["conexion"]
        conexion_obj = conexiones[conexion_id]

        # Crear mensaje usando el protocolo de esa conexión
        protocolos[conexion_obj["protocolo"]]["crea"](conexion_obj, datos)

        return redirect(url_for('formulario'))

    # FORMULARIO DINÁMICO
    html = """
    <!doctype html>
    <html lang="es">
     <head>
       <meta charset="UTF-8">
       <title>Formulario</title>
     </head>
     <body>
       <h2>Crear Mensaje</h2>
       <form method="POST" action="/">

         <label for="conexion">Conexión:</label>
         <select name="conexion" id="conexion" required>
            {% for nombre in conexiones %}
                <option value="{{nombre}}">{{nombre}}</option>
            {% endfor %}
         </select>
         <br><br>

         <label for="tipo">Tipo:</label>
         <select name="tipo" id="tipo" required>
           <option value="DR">DR</option>
           <option value="DR-P">DR-P</option>
           <option value="TR">TR</option>
           <option value="KAL">KAL</option>
         </select><br><br>

         <div id="campo-origen">
          <label for="origen">Origen:</label>
          <input type="text" id="origen" name="origen">
        </div>
        <br>

        <div id="campo-destino">
          <label for="destino">Destino:</label>
          <input type="text" id="destino" name="destino">
        </div>
        <br>

        <div id="campo-matricula">
          <label for="matricula">Matricula:</label>
          <input type="text" id="matricula" name="matricula">
        </div>
        <br>
        
        <div id="campo-largo">
          <label for="largo">Largo:</label>
          <input type="text" id="largo" name="largo" placeholder="0">mm
        </div>
        <br>
        
        <div id="campo-alto">
          <label for="alto">Alto:</label>
          <input type="text" id="alto" name="alto" placeholder="0">mm
        </div>
        <br>
        
        <div id="campo-ancho">
          <label for="ancho">Ancho:</label>
          <input type="text" id="ancho" name="ancho" placeholder="0">mm
        </div>
        <br>
        
        <div id="campo-peso">
          <label for="peso">Peso:</label>
          <input type="text" id="peso" name="peso" placeholder="0">gr
        </div>
        <br>

         <button type="submit">Enviar</button>
       </form>

       <script>
      const tipoSelect = document.getElementById("tipo");

      const origen = document.getElementById("campo-origen");
      const destino = document.getElementById("campo-destino");
      const matricula = document.getElementById("campo-matricula");
      const largo = document.getElementById("campo-largo");
      const ancho = document.getElementById("campo-ancho");
      const alto = document.getElementById("campo-alto");
      const peso = document.getElementById("campo-peso");
      

      const inpOrigen = document.getElementById("origen");
      const inpDestino = document.getElementById("destino");
      const inpMatricula = document.getElementById("matricula");
      const inpLargo = document.getElementById("largo");
      const inpAncho = document.getElementById("ancho");
      const inpAlto = document.getElementById("alto");
      const inpPeso = document.getElementById("peso");
      
      function actualizarCampos() {
        const tipo = tipoSelect.value;

        // Ocultar todos por defecto
        origen.style.display = "none";
        destino.style.display = "none";
        matricula.style.display = "none";
        alto.style.display = "none";
        ancho.style.display = "none";
        largo.style.display = "none";
        peso.style.display = "none";
        
        // Quitar requeridos
        inpOrigen.required = false;
        inpDestino.required = false;
        inpMatricula.required = false;
        inpLargo.required = false;
        inpAncho.required = false;
        inpAlto.required = false;
        inpPeso.required = false;
        

        if (tipo === "DR") {
          origen.style.display = "block";
          matricula.style.display = "block";

          inpOrigen.required = true;
          inpMatricula.required = true;
        }

        if (tipo === "TR") {
          origen.style.display = "block";
          destino.style.display = "block";
          matricula.style.display = "block";

          inpOrigen.required = true;
          inpDestino.required = true;
          inpMatricula.required = true;
        }
        
        if (tipo === "DR-P") {
          origen.style.display = "block";
          matricula.style.display = "block";
          alto.style.display = "block";
          ancho.style.display = "block";
          largo.style.display = "block";
          peso.style.display = "block";
          
          inpOrigen.required = true;
          inpMatricula.required = true;
          inpAlto.required = true;
          inpAncho.required = true;
          inpLargo.required = true;
          inpPeso.required = true;
        }
          

        // Si es KAL, no se muestra ninguno y no se requiere nada
      }

      tipoSelect.addEventListener("change", actualizarCampos);

      // Ejecutar al cargar para ocultar campos inicialmente
      actualizarCampos();
    </script>

        <hr><br>

       <h2>Enviar Mensaje Manual</h2>
       <form method="POST" action="/">

         <label for="conexion">Conexión:</label>
         <select name="conexion" id="conexion" required>
            {% for nombre in conexiones %}
                <option value="{{nombre}}">{{nombre}}</option>
            {% endfor %}
         </select>
         <br><br>

         <label for="tipomensaje">Tipo mensaje:</label><br>
         <input type="text" id="tipomensaje" name="tipomensaje" required>
         <br><br>

         <label for="mensaje">Mensaje:</label><br>
         <textarea id="telegrama" name="telegrama" rows="4" cols="40" required></textarea>
         <br><br>

         <small>
            <i>Introduce el mensaje sin cabecera, sólo a partir del tipo de mensaje</i>
         </small>
         <br><br>

         <input type="hidden" name="tipo" value="MANUAL">

         <button type="submit">Enviar mensaje manual</button>
       </form>
     </body>
    </html>
    """

    return render_template_string(html, conexiones=conexiones)


if __name__ == "__main__":
    threads = []


    for port in conexiones:
        logging.info(f"conexion:{port} {conexiones[port]['puerto']} - creando thread")
        thread = threading.Thread(target=conexion_puerto, args=(conexiones[port],))
        threads.append(thread)
        thread.start()
        if conexiones[port]['kal'] == True:
            thread = threading.Thread (target= protocolos[conexiones[port]["protocolo"]]["kal"], args=(conexiones[port],))
            threads.append(thread)
            thread.start()


    app.run(host= "0.0.0.0", port=50001,debug=False, use_reloader=False, threaded=False)  # Ejecuta la aplicación Flask

    for thread in threads:
        thread.join()
