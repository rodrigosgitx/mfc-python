'''''Librería de mensajería TGW Aberle'''
import xml.etree.ElementTree as ET
import logging

# Terminador para mensajes 
hex_string = "0D0A"
terminator = bytes.fromhex(hex_string).decode('utf-8')

#valores del contorno, sacados de configurationMFC.properties

contorno = {
    "200" : "01",
    "300" : "02",
    "400" : "03",
    "500" : "04"
    }



#parsear campos

def parsear (texto, longitud):
    devuelve = texto
    largo = int(longitud) - len(texto)
    for i in range(largo):
        devuelve = devuelve + '*'
    return devuelve.upper()

#funcion cabecera

def cabecera (conexion, mensaje):
    serie = conexion ['contador']
    sender = conexion ['sender']
    receiver = conexion ['receiver']
    mida = len(sender) + len(receiver) + 4 + 2 + len(mensaje["tipo"]) + len(mensaje["cuerpo"]) + len(terminator)
    cab = f'{sender}{receiver}{str(mida).zfill(4)}{str(serie).zfill(2)}{mensaje["tipo"]}{mensaje["cuerpo"]}{terminator}'
    return (cab)    


# Funciones para mensajes específicos

def ee61(datos, root):
    mensaje = ''
    #longitudes de los campos
    longitudes ={}
    for child in root:
        if (child.tag == 'message' and child.attrib['type'] =='01'):
            
            for net in child:
                if net.attrib["name"] == "source":
                    longitudes["origen"] = net.attrib["length"]
                if net.attrib["name"] == "destination":
                    longitudes["destino"] = net.attrib["length"]
                if net.attrib["name"] == "tunumber":
                    longitudes["matricula"] = net.attrib["length"]
                               
    # Parseamos los datos de los campos
    origen = parsear (datos["origen"],longitudes["origen"])
    matricula = parsear (datos["matricula"], longitudes["matricula"])
    
    for child in root:
        if (child.tag == 'message' and child.attrib['type'] == '61'):
            for net in child:
                if (net.attrib['name'] == 'source' and origen):
                    mensaje = mensaje + origen
                elif (net.attrib['name'] == 'tunumber' and matricula):
                    mensaje = mensaje + matricula
                else:
                    n=int(net.attrib["length"])
                    for a in range(n): mensaje = mensaje + '*'
    
    return (mensaje)

def ee61p(datos, root):
    # Calculamos el contour
    cnt = str((int(datos["alto"]) //100) *100)
    contour = contorno[cnt]
    
    mensaje = ''
    #longitudes de los campos
    longitudes ={}
    for child in root:
        if (child.tag == 'message' and child.attrib['type'] =='01'):
            
            for net in child:
                if net.attrib["name"] == "source":
                    longitudes["origen"] = net.attrib["length"]
                if net.attrib["name"] == "destination":
                    longitudes["destino"] = net.attrib["length"]
                if net.attrib["name"] == "tunumber":
                    longitudes["matricula"] = net.attrib["length"]
                               
    # Parseamos los datos de los campos
    origen = parsear (datos["origen"],longitudes["origen"])
    matricula = parsear (datos["matricula"], longitudes["matricula"])
    
    for child in root:
        if (child.tag == 'message' and child.attrib['type'] == '61'):
            for net in child:
                if (net.attrib['name'] == 'source' and origen):
                    mensaje = mensaje + origen
                elif (net.attrib['name'] == 'tunumber' and matricula):
                    mensaje = mensaje + matricula
                elif (net.attrib['name'] == 'realheight'):
                    mensaje = mensaje + datos['alto'].zfill(4)
                elif (net.attrib['name'] == 'length'):
                    mensaje = mensaje + datos['largo'].zfill(4)
                elif (net.attrib['name'] == 'width'):
                    mensaje = mensaje + datos['ancho'].zfill(4)
                elif (net.attrib['name'] == 'weight'):
                    mensaje = mensaje + datos['peso'].zfill(8)
                elif (net.attrib['name'] == 'height'):
                    mensaje = mensaje + contour
                
                else:
                    n=int(net.attrib["length"])
                    for a in range(n): mensaje = mensaje + '*'
                    
    return (mensaje)

def ee81(datos,root):
    mensaje = ''
    #longitudes de los campos
    longitudes ={}
    for child in root:
        if (child.tag == 'message' and child.attrib['type'] =='01'):
            
            for net in child:
                if net.attrib["name"] == "source":
                    longitudes["origen"] = net.attrib["length"]
                if net.attrib["name"] == "destination":
                    longitudes["destino"] = net.attrib["length"]
                if net.attrib["name"] == "tunumber":
                    longitudes["matricula"] = net.attrib["length"]
                               
    # Parseamos los datos de los campos
    origen = parsear (datos["origen"],longitudes["origen"])
    destino = parsear (datos["destino"],longitudes["destino"])
    matricula = parsear (datos["matricula"], longitudes["matricula"])
    
    for child in root:
        if (child.tag == 'message' and child.attrib['type'] == '61'):
            for net in child:
                if (net.attrib['name'] == 'source' and origen):
                    mensaje = mensaje + origen
                elif (net.attrib['name'] == 'destination' and destino):
                    mensaje = mensaje + destino
                elif (net.attrib['name'] == 'tunumber' and matricula):
                    mensaje = mensaje + matricula
                else:
                    n=int(net.attrib["length"])
                    for a in range(n): mensaje = mensaje + '*'
    
    return (mensaje)
    

    



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
    tree = ET.parse('protocols/aberle-metainfo.xml')
    root = tree.getroot()
    mensaje={}
  
    
    if datos["tipo"] == "KAL":
        mensaje['cuerpo'] = "************************************************************************************************"
        mensaje['tipo'] = 'EE99'
    if datos["tipo"] == "DR":
        mensaje['cuerpo'] = ee61(datos,root)
        mensaje['tipo'] = 'EE61'
    if datos["tipo"] == "DR-P":
        mensaje = ee61p(datos,root)
        mensaje['tipo'] = 'EE61'
    if datos["tipo"] == "TR":
        mensaje['cuerpo'] = ee81(datos,root)
        mensaje['tipo'] = 'EE81'
    if datos["tipo"] == "MANUAL":
        mensaje["cuerpo"] = datos['telegrama']
        mensaje['tipo'] = datos['tipomensaje']
        
    telegrama = cabecera (conexion,mensaje)
    
    conexion['contador']+= 1
    if conexion['contador'] == 100: conexion['contador'] =1
    
    conexion["cola"].put(telegrama.encode("utf-8"), block=True)    
    logging.info(f'Encolado mensaje:{telegrama} en socket {conexion["id_plc"]}.{conexion["id_puerto"]}')
    

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
    
    