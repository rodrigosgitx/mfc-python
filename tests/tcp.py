import socket

# Definir el host y el puerto donde se va a escuchar
HOST = '0.0.0.0'  # Escuchar en todas las interfaces
PORT = 5000      # Puerto de escucha

# Crear el socket TCP
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))  # Vincular el socket al host y puerto definidos
    s.listen()            # Activar escucha en el puerto
    print(f'Escuchando en {HOST}:{PORT}...')

    conn, addr = s.accept()  # Aceptar conexión entrante
    with conn:
        print(f'Conexión establecida desde {addr}')
        while True:
            data = conn.recv(1024)  # Recibir datos en bloques de 1024 bytes
            if not data:
                break
            print(f'Datos recibidos: {data.decode("utf-8")}')  # Printar en pantalla los datos recibidos