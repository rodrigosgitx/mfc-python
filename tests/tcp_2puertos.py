import socket
import threading

hex_string = "0D0A"
terminator = bytes.fromhex(hex_string).decode('utf-8')

def listen_on_port(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', port))
        s.listen()
        print(f'Escuchando en 0.0.0.0:{port}...')

        while True:
            conn, addr = s.accept()
            with conn:
                print(f'Conexión establecida desde {addr} en puerto {port}')
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    print(f'Datos recibidos en puerto {port}: {data.decode("utf-8")}')
                    serie = data.decode("utf-8")[12:14]
                    print(serie)
                    response = f'TSC2MFCS0028{serie}EEQQ0000ACKN{terminator}'
                    conn.sendall(response.encode('utf-8'))  # Enviar respuesta al cliente
                    print(f'Enviado:{response}')
                    
                    

def main():
    ports = [5000, 5001]  # Lista de puertos a escuchar
    threads = []

    for port in ports:
        thread = threading.Thread(target=listen_on_port, args=(port,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()