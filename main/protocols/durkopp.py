'''librería de mensajería dft Duerkopp'''

import xml.etree.ElementTree as ET
import logging
from datetime import datetime

# Terminador para mensajes 
hex_string = "0D0A"
terminator = bytes.fromhex(hex_string).decode('utf-8')

contorno = {
    "01" : 1200,
    "02" : 1600,
    "99" : 9999,
    }


def cabecera (conexion, mensaje):
    ''' Añade cabecera y caracteres de cola a un mensaje y lo devuelve listo para envío''' 
       
    now = datetime.now()
    date_string = now.strftime('%Y%m%d%H%M%S') + "{:02d}".format(now.microsecond // 10000)
    
    mida = str(79 + len(mensaje['cuerpo'])+2)
    mida2 = str(len(mensaje['cuerpo']))
    serie = str(conexion ['contador'])
    sender = conexion ['sender']
    receiver = conexion ['receiver']
    cab=f'$$+TI{mensaje["tipo"]}+TS{date_string}+TX{sender}+RX{receiver}+VE{conexion["version"]}+TC{serie.zfill(8)}+TL{mida.zfill(4)}+BQ0001+BL{mida2.zfill(4)}{mensaje["cuerpo"]}{terminator}'
    return(cab)

def ctsdr(datos,root):
    ''' crea un mensaje CTS_DR a partir de una posición y una matrícula longitud (+SD) fija a 10'''
    
    longitudes ={}
    for child in root:
        if (child.tag == 'message' and child.attrib['type'] =='CTS_DR'):
          
            for net in child:
                if net.attrib["name"] == "position":
                    longitudes["origen"] = [net.attrib["length"],net.attrib["type"]]
                if net.attrib["name"] == "scanData":
                    longitudes["matricula"] = [net.attrib["length"],net.attrib["type"]]
    
    origen = datos["origen"].zfill(int(longitudes["origen"][0]))
    matricula = datos["matricula"].ljust(int(longitudes["matricula"][0]))
    mensaje=f"+MS{origen}+UI00000+RV****+TDBIT+SD{matricula}+SR1+CA0000000000+SC10+QU0000+SQ0000+IN********************"
    return(mensaje)

def ctsdrp(datos,root):
    ''' Crea un mensaje CTS_DR con medidas'''
    
    longitudes ={}
    for child in root:
        if (child.tag == 'message' and child.attrib['type'] =='CTS_DR'):
          
            for net in child:
                if net.attrib["name"] == "position":
                    longitudes["origen"] = [net.attrib["length"],net.attrib["type"]]
                if net.attrib["name"] == "scanData":
                    longitudes["matricula"] = [net.attrib["length"],net.attrib["type"]]
    
    origen = datos["origen"].zfill(int(longitudes["origen"][0]))
    matricula = datos["matricula"].ljust(int(longitudes["matricula"][0]))
    longitud = str(int(datos['largo'])//10)
    for a in contorno:
        if int(datos['alto']) <= contorno[a]:
            altura = a
            break
        
    mensaje=f"+MS{origen}+UI00000+RV****+TDBIT+SD{matricula}+SR1+CA0000000000+SC{longitud}+QU0000+SQ0000+INW01H{altura}              "
    return(mensaje)
    
def ctstr(datos,root):
    '''crea un mensaje CTS_TR a partir de origen, destino y matrícula, longitud (+SC) fija a 10'''
    
    longitudes ={}
    for child in root:
        if (child.tag == 'message' and child.attrib['type'] =='CTS_DR'):
          
            for net in child:
                if net.attrib["name"] == "position":
                    longitudes["origen"] = [net.attrib["length"],net.attrib["type"]]
                if net.attrib["name"] == "unitId":
                    longitudes["destino"] = [net.attrib["length"],net.attrib["type"]]
                if net.attrib["name"] == "scanData":
                    longitudes["matricula"] = [net.attrib["length"],net.attrib["type"]]
    
    origen = datos["origen"].zfill(int(longitudes["origen"][0]))
    destino = datos["destino"].zfill(int(longitudes["destino"][0]))
    matricula = datos["matricula"].ljust(int(longitudes["matricula"][0]))
    mensaje=f"+MS{origen}+UI{destino}+RVDONE+TDBIT+SD{matricula}+SR0+CA0000000000+SC10+QU0000+SQ0000+IN********************"
    return(mensaje)

def interpreta(conexion, mensaje):
    ''' Recibe un mensaje y un socket y decide qué hacer con el mensaje'''
    
    # Que tipo de mensaje ha llegado
    tipo = mensaje[5:11]
    logging.info (f"recibido tipo: {tipo} en socket {conexion['id_plc']}.{conexion['id_puerto']}")
    
    #Si no es un ack, enviamos ack
    if tipo != 'BCM_AC':
        serie = mensaje[2:79]
        ack(conexion,serie)    
    
    
def crea(conexion, datos):
    ''' Recibe un socket y datos para crear un mensaje a enviar, se añade el mensaje a la cola correspondiente para su envío'''
        
    # Parsear metainfo
    tree = ET.parse('protocols/dft-metainfo.xml')
    root = tree.getroot()
    mensaje ={}
  
    
    if datos["tipo"] == "KAL":
        mensaje['tipo'] = 'BCM_AL' 
        mensaje['cuerpo'] = f"+IV{str(conexion['kal.time']).zfill(3)}+PS1"
    if datos["tipo"] == "DR":
        mensaje["cuerpo"] = ctsdr(datos,root)
        mensaje["tipo"] = "CTS_DR"
    if datos["tipo"] == "DR-P":
        mensaje["cuerpo"] = ctsdrp(datos,root)
        mensaje["tipo"] = "CTS_DR"
    if datos["tipo"] == "TR":
        mensaje["cuerpo"] = ctstr(datos,root)
        mensaje["tipo"] = "CTS_TR"
    if datos["tipo"] == "MANUAL":
        mensaje = datos['telegrama']
    if datos["tipo"] == "ACK":
        mensaje['tipo'] = 'BCS_AC'
        mensaje['cuerpo'] = datos['telegrama']
        
    mensaje = cabecera (conexion,mensaje)
    
    conexion['contador']+= 1
    if conexion['contador'] == 100000000: conexion['contador'] =1
    
    conexion["cola"].put(mensaje.encode("utf-8"), block=True)    
    logging.info(f'Encolado mensaje:{mensaje} en socket {conexion["id_plc"]}.{conexion["id_puerto"]}')
    

def ack(conexion, serie):
    ''' Recibe un socket y una cabecera de mensaje y envía a crea un ack para que lo encole con el número de mensaje (+TC) correspondiente'''
    mensaje ={}
    mensaje['telegrama'] = f'+SC0000{serie}'
    mensaje['tipo'] = 'ACK'
    # Enviamos a crea para que encole el mensaje
    crea(conexion,mensaje)
        
    
def kal (conexion):
    ''' Controla el tiempo entre KALs e indica a la función crea cuando enviar uno '''
    import time
    a = {"tipo" : "KAL"}
    while True:
        if conexion['conectado'] == True:
            crea (conexion, a)
        time.sleep (int(conexion["kal.time"]))