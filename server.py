import socket
import threading

# Configurações do servidor
HOST = "10.179.238.41"  # Endereço IP do servidor
PORT = 8080        # Porta que o servidor vai escutar

# Lista global para armazenar os endereços dos clientes conectados
clientes_conectados = []
clientes_lock = threading.Lock()  # Lock para evitar condições de corrida

def handle_client(conn, addr):
    global clientes_conectados
    print(f"Conectado por {addr} \n")
    # Envia uma mensagem de boas-vindas ao cliente
    conn.sendall(b'Conexao estabelecida com o servidor. \n')
    
    # Adiciona o cliente à lista de conectados
    with clientes_lock:
        clientes_conectados.append(addr[0])
    
    try:
        with conn:
               
            while True:
                # Recebe dados do cliente
                data = conn.recv(1024)
                if not data:
                    break
                
                # Mostra os IPs dos outros clientes conectados
                with clientes_lock:
                    outros_clientes = [ip for ip in clientes_conectados]
                
                if outros_clientes:
                    mensagem = f"Outros clientes conectados: {', '.join(outros_clientes)}"
                else:
                    mensagem = "Voce e o unico cliente conectado no momento."
                
                # Envia a mensagem de volta ao cliente
                conn.sendall(mensagem.encode())

    finally:
        # Remove o cliente da lista ao desconectar
        with clientes_lock:
            clientes_conectados.remove(addr[0])
        print(f"Conexão encerrada com {addr}")


# Cria um socket TCP/IP
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    # Vincula o socket ao endereço e porta
    s.bind((HOST, PORT))
    # Começa a escutar por conexões
    s.listen()
    print(f"Servidor escutando em {HOST}:{PORT}")
    
    while True:
        # Aceita conexões
        conn, addr = s.accept()
        print(f"Nova conexão de {addr}")
        # Cria uma nova thread para lidar com o cliente
        client_thread = threading.Thread(target=handle_client, args=(conn, addr))
        client_thread.start()
