"""Emulador MFC con interfaz web Gradio."""

import logging
import queue
import socket
import sys
import threading
import xml.etree.ElementTree as ET

sys.path.insert(0, "libs")

from protocols import aberle
from protocols import durkopp
from protocols import commander

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

logging.info("Arrancamos el emulador con Gradio")

protocolos = {
    "aberle": {
        "interpreta": aberle.interpreta,
        "crea": aberle.crea,
        "kal": aberle.kal,
        "ack": aberle.ack,
    },
    "durkopp": {
        "interpreta": durkopp.interpreta,
        "crea": durkopp.crea,
        "kal": durkopp.kal,
        "ack": durkopp.ack,
    },
    
    "commander": {
        "interpreta": commander.interpreta,
        "crea": commander.crea,
        "kal": commander.kal,
    }
}


def cargar_conexiones():
    tree = ET.parse("config.xml")
    root = tree.getroot()
    conexiones = {}

    for plc in root.findall("plc"):
        for puerto in plc.findall("port"):
            conexion_id = f'{plc.attrib["name"]}.{puerto.attrib["name"]}'
            conexiones[conexion_id] = {
                "id_plc": plc.attrib["name"],
                "id_puerto": puerto.attrib["name"],
                "protocolo": plc.attrib["protocolo"],
                "puerto": int(puerto.attrib["port"]),
                "kal": bool(int(puerto.attrib["kal"])),
                "kal.time": int(puerto.attrib["kal.time"]),
                "sender": plc.attrib["sender"],
                "receiver": plc.attrib["receiver"],
                "cola": queue.Queue(),
                "contador": 0,
                "conectado": False,
                "version": puerto.attrib["version"],
                "isoOnTCP": bool(int(puerto.attrib.get("isoOnTCP", "0"))),
            }

    logging.info("Conexiones cargadas: %s", conexiones)
    return conexiones


conexiones = cargar_conexiones()


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
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind(("0.0.0.0", datos["puerto"]))
        servidor.listen()

        logging.info("Escuchando en 0.0.0.0:%s...", datos["puerto"])

        while True:
            conn, addr = servidor.accept()
            with conn:
                logging.info(
                    "Conexión establecida desde %s en puerto %s.%s",
                    addr,
                    datos["id_plc"],
                    datos["id_puerto"],
                )
                datos["conectado"] = True
                conn.settimeout(0.1)
                buffer_iso_on_tcp = b""
                usa_iso_on_tcp = datos["isoOnTCP"]

                while True:
                    if not datos["cola"].empty():
                        response = datos["cola"].get()
                        if usa_iso_on_tcp:
                            response = empaqueta_iso_on_tcp(response)
                        conn.sendall(response)
                        logging.info(
                            "Enviado: %s en puerto %s.%s",
                            response,
                            datos["id_plc"],
                            datos["id_puerto"],
                        )

                    try:
                        data = conn.recv(1024)
                    except socket.timeout:
                        continue
                    except ConnectionError:
                        break

                    if not data:
                        break

                    if usa_iso_on_tcp:
                        buffer_iso_on_tcp += data
                        mensaje_iso_on_tcp = extrae_mensaje_iso_on_tcp(buffer_iso_on_tcp)

                        if mensaje_iso_on_tcp:
                            payload, buffer_iso_on_tcp = mensaje_iso_on_tcp
                            mensaje = payload.decode("ascii")
                            logging.info(
                                "Datos recibidos en puerto %s.%s: %s",
                                datos["id_plc"],
                                datos["id_puerto"],
                                mensaje,
                            )
                            protocolos[datos["protocolo"]]["interpreta"](
                                datos, mensaje
                            )
                    else:
                        mensaje = data.decode("utf-8")
                        logging.info(
                            "Datos recibidos en puerto %s.%s: %s",
                            datos["id_plc"],
                            datos["id_puerto"],
                            mensaje,
                        )
                        protocolos[datos["protocolo"]]["interpreta"](
                            datos, mensaje
                        )

                datos["conectado"] = False
                logging.info(
                    "Conexión cerrada en puerto %s.%s",
                    datos["id_plc"],
                    datos["id_puerto"],
                )


def crear_mensaje(conexion_id, tipo, origen, destino, matricula, largo, alto, ancho, peso):
    if not conexion_id:
        return "Selecciona una conexión."

    datos = {
        "conexion": conexion_id,
        "tipo": tipo,
        "origen": origen or "",
        "destino": destino or "",
        "matricula": matricula or "",
        "largo": largo or "0",
        "alto": alto or "0",
        "ancho": ancho or "0",
        "peso": peso or "0",
    }

    try:
        conexion = conexiones[conexion_id]
        protocolos[conexion["protocolo"]]["crea"](conexion, datos)
    except (KeyError, TypeError, ValueError) as exc:
        logging.exception("No se pudo crear el mensaje")
        return f"Error: {exc}"

    return f"Mensaje {tipo} encolado para {conexion_id}."


def enviar_manual(conexion_id, tipomensaje, telegrama):
    if not conexion_id:
        return "Selecciona una conexión."
    if not tipomensaje:
        return "Introduce el tipo de mensaje."
    if not telegrama:
        return "Introduce un mensaje."

    try:
        conexion = conexiones[conexion_id]
        protocolos[conexion["protocolo"]]["crea"](
            conexion,
            {
                "tipo": "MANUAL",
                "tipomensaje": tipomensaje,
                "telegrama": telegrama,
            },
        )
    except (KeyError, TypeError, ValueError) as exc:
        logging.exception("No se pudo encolar el mensaje manual")
        return f"Error: {exc}"

    return f"Mensaje manual encolado para {conexion_id}."


def actualizar_campos(tipo):
    visibles = {
        "DR": (True, False, True, False, False, False, False),
        "DR-P": (True, False, True, True, True, True, True),
        "TR": (True, True, True, False, False, False, False),
        "KAL": (False, False, False, False, False, False, False),
    }
    try:
        import gradio as gr
    except ImportError as exc:
        raise RuntimeError("Gradio es necesario para actualizar los campos") from exc

    return tuple(
        gr.update(visible=visible)
        for visible in visibles.get(tipo, visibles["DR"])
    )


def construir_interfaz():
    try:
        import gradio as gr
    except ImportError as exc:
        raise SystemExit(
            "No se encontró Gradio. Instálalo con: pip install gradio"
        ) from exc

    conexiones_disponibles = list(conexiones)

    with gr.Blocks(title="Emulador MFC") as demo:
        gr.Markdown("## Crear Mensaje")
        conexion = gr.Dropdown(
            choices=conexiones_disponibles,
            value=conexiones_disponibles[0] if conexiones_disponibles else None,
            label="Conexión",
            allow_custom_value=False,
        )
        tipo = gr.Dropdown(
            choices=["DR", "DR-P", "TR", "KAL"],
            value="DR",
            label="Tipo",
        )

        with gr.Row():
            origen = gr.Textbox(label="Origen", visible=True)
            destino = gr.Textbox(label="Destino", visible=False)
            matricula = gr.Textbox(label="Matrícula", visible=True)

        with gr.Row():
            largo = gr.Textbox(label="Largo (mm)", value="0", visible=False)
            alto = gr.Textbox(label="Alto (mm)", value="0", visible=False)
            ancho = gr.Textbox(label="Ancho (mm)", value="0", visible=False)
            peso = gr.Textbox(label="Peso (gr)", value="0", visible=False)

        enviar = gr.Button("Enviar", variant="primary")
        resultado = gr.Textbox(label="Resultado", interactive=False)

        tipo.change(
            actualizar_campos,
            inputs=tipo,
            outputs=[origen, destino, matricula, largo, alto, ancho, peso],
        )
        enviar.click(
            crear_mensaje,
            inputs=[
                conexion,
                tipo,
                origen,
                destino,
                matricula,
                largo,
                alto,
                ancho,
                peso,
            ],
            outputs=resultado,
        )

        gr.Markdown("---")
        gr.Markdown("## Enviar Mensaje Manual")
        conexion_manual = gr.Dropdown(
            choices=conexiones_disponibles,
            value=conexiones_disponibles[0] if conexiones_disponibles else None,
            label="Conexión",
            allow_custom_value=False,
        )
        tipomensaje = gr.Textbox(label="Tipo mensaje")
        telegrama = gr.Textbox(
            label="Mensaje sin cabecera",
            lines=8,
            placeholder="Introduce el mensaje sin cabecera, sólo a partir del tipo de mensaje",
        )
        enviar_manual_button = gr.Button("Enviar mensaje manual", variant="primary")
        resultado_manual = gr.Textbox(label="Resultado", interactive=False)
        enviar_manual_button.click(
            enviar_manual,
            inputs=[conexion_manual, tipomensaje, telegrama],
            outputs=resultado_manual,
        )

    return demo


if __name__ == "__main__":
    threads = []

    for conexion_id, conexion in conexiones.items():
        logging.info(
            "conexion:%s %s - creando thread",
            conexion_id,
            conexion["puerto"],
        )
        thread = threading.Thread(target=conexion_puerto, args=(conexion,), daemon=True)
        threads.append(thread)
        thread.start()

        if conexion["kal"]:
            thread = threading.Thread(
                target=protocolos[conexion["protocolo"]]["kal"],
                args=(conexion,),
                daemon=True,
            )
            threads.append(thread)
            thread.start()

    construir_interfaz().launch(
        server_name="0.0.0.0",
        server_port=50001,
        show_error=True,
    )
