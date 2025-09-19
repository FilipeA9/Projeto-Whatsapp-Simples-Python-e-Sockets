import socket

HOST = "10.179.238.41"  # The server's hostname or IP address
PORT = 8080       # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    while True:
        message = input("Escreva a mensagem (or 'exit' to quit): ")
        if message.lower() == 'exit':
            break
        s.sendall(message.encode())
        data = s.recv(1024)
        print('Received', repr(data))
