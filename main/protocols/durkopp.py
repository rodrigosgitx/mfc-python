'''librería de mensajería dft Duerkopp'''
import xml.etree.ElementTree as ET
import logging

# Terminador para mensajes 
hex_string = "0D0A"
terminator = bytes.fromhex(hex_string).decode('utf-8')

def cabecera (conexion, mensaje):
    return(0)

def ctsdr(datos,root):
    return(0)

def ctsdrp(datos,root):
    return(0)
    
def ctstr(datos,root):
    return(0)

def interpreta(conexion, mensaje):
    ''' Recibe un mensaje y un socket y decide qué hacer con el mensaje'''
    
    # Que tipo de mensaje ha llegado
    tipo = mensaje[16:18]
    logging.info (f"recibido tipo: {tipo} en socket {conexion['id_plc']}.{conexion['id_puerto']}")
    
    #Si no es un ack, enviamos ack
    if tipo != 'QQ':
        serie = mensaje[12:14]
        ack(conexion,serie)    
    
    
def crea(conexion, datos):
    ''' Recibe un socket y datos para crear un mensaje a enviar, se añade el mensaje a la cola correspondiente para su envío'''
        
    # Parsear metainfo
    tree = ET.parse('protocols/dft-metainfo.xml')
    root = tree.getroot()

  
    
    if datos["tipo"] == "KAL":
        mensaje = f"+IV{conexion['kal.time'].zfill(3)}+PS1"
    if datos["tipo"] == "DR":
        mensaje = ctsdr(datos,root)
    if datos["tipo"] == "DR-P":
        mensaje = ctsdrp(datos)
    if datos["tipo"] == "TR":
        mensaje = ctstr(datos,root)
    if datos["tipo"] == "MANUAL":
        mensaje = datos['telegrama']
        
    mensaje = cabecera (conexion,mensaje)
    
    conexion['contador']+= 1
    if conexion['contador'] == 100: conexion['contador'] =1
    
    conexion["cola"].put(mensaje.encode("utf-8"), block=True)    
    logging.info(f'Encolado mensaje:{mensaje} en socket {conexion["id_plc"]}.{conexion["id_puerto"]}')
    

def ack(conexion, serie):
    ''' Recibe un socket y un número de secuencia y añade un ack con el número de secuencia a la cola correspondiente'''
    
    sender = conexion ['sender']
    receiver = conexion ['receiver']
    response = f'{sender}{receiver}0028{serie}EEQQ0000ACKN{terminator}'
    # Encolamos la respuesta para si envío
    conexion["cola"].put(response.encode('utf-8'), block=True)  # Enviar respuesta al cliente
    logging.info(f'Encolado ACK:{response} en socket {conexion["id_plc"]}.{conexion["id_puerto"]}')
    
    
def kal (conexion):
    ''' Controla el tiempo entre KALs e indica a la función crea cuando enviar uno '''
    import time
    a = {"tipo" : "KAL"}
    while True:
        if conexion['conectado'] == True:
            crea (conexion, a)
        time.sleep (int(conexion["kal.time"]))