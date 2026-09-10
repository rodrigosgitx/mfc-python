'''''Librería de mensajería TGW Commander'''
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



#funcion cabecera

def cabecera (conexion, mensaje):
    serie = conexion ['contador']
    sender = conexion ['sender']
    receiver = conexion ['receiver']
    if mensaje["tipo"] != "PONG":
        cab = f'{sender};{receiver};{str(serie)};{mensaje["tipo"]};{mensaje["cuerpo"]}{terminator}'
    else:
        cab = f'{sender};{receiver};{str(serie)};{mensaje["tipo"]}{terminator}'
    return (cab)    


# Funciones para mensajes específicos

def lrepNdir(datos):
    
    mensaje = f'1;"{datos["matricula"]}";;{datos["origen"]};NDIR;[]'
    return (mensaje)


def lrepNdirp(datos):
    
    mensaje = f'1;"{datos["matricula"]}";;{datos["origen"]};;[(LENG:{datos["largo"]}),(WIDT:{datos["ancho"]}),(HEIG:{datos["alto"]}),(WEIG:{datos["peso"]})]'
    return (mensaje)


def lrep(datos):
    mensaje = f'1;"{datos["matricula"]}";;{datos["destino"]};;[]'
    return (mensaje)


def interpreta(conexion, mensaje):
    ''' Recibe un mensaje y un socket y decide qué hacer con el mensaje'''
    tipo = mensaje.strip().split(";")[3]
    logging.info (f"recibido mensaje: {mensaje} en socket {conexion['id_plc']}.{conexion['id_puerto']}")
    if tipo == 'PING':
        a = {"tipo" : "KAL"}
        crea (conexion, a)
        
    
def crea(conexion, datos):
    ''' Recibe un socket y datos para crear un mensaje a enviar, se añade el mensaje a la cola correspondiente para su envío'''
    mensaje={}    
        
    if datos["tipo"] == "KAL":
        mensaje['tipo'] = 'PONG'
    if datos["tipo"] == "DR":
        mensaje['cuerpo'] = lrepNdir(datos)
        mensaje['tipo'] = 'LREP'
    if datos["tipo"] == "DR-P":
        mensaje["cuerpo"] = lrepNdirp(datos)
        mensaje['tipo'] = 'LREP'
    if datos["tipo"] == "TR":
        mensaje['cuerpo'] = lrep(datos)
        mensaje['tipo'] = 'LREP'
    if datos["tipo"] == "MANUAL":
        mensaje = datos['telegrama']
        
    telegrama = cabecera (conexion,mensaje)
    
    conexion['contador']+= 1
    if conexion['contador'] == 9999: conexion['contador'] =1
    
    conexion["cola"].put(telegrama.encode("utf-8"), block=True)    
    logging.info(f'Encolado mensaje:{telegrama} en socket {conexion["id_plc"]}.{conexion["id_puerto"]}')
    

def kal (conexion):
    ''' Controla el tiempo entre KALs e indica a la función crea cuando enviar uno '''
    import time
    a = {"tipo" : "KAL"}
    while True:
        if conexion['conectado'] == True:
            crea (conexion, a)
        time.sleep (int(conexion["kal.time"]))
    
    