# servidor_simples.py
import socket
import threading
import signal
import sys

MSG_BAD = (
    b"HTTP/1.0 400 Bad Request\r\n"
    b"Content-Type: text/plain; charset=utf-8\r\n"
    b"Content-Length: 12\r\n"
    b"\r\n"
    b"Bad Request"
)

def resposta_ok(corpo: str) -> bytes:
    body = corpo.encode("utf-8")
    headers = (
        "HTTP/1.0 200 OK\r\n"
        "Content-Type: text/plain; charset=utf-8\r\n"
        f"Content-Length: {len(body)}\r\n"
        "\r\n"
    ).encode("utf-8")
    return headers + body

stop_event = threading.Event()

def tratar_cliente(conn: socket.socket, addr):
    # Cada cliente roda em uma thread
    with conn:
        conn.settimeout(15)
        f = conn.makefile("rb", buffering=0)
        try:
            # Lê a primeira linha (request-line ou mensagem)
            primeira_linha = f.readline(4096)
            if not primeira_linha or not primeira_linha.strip():
                conn.sendall(MSG_BAD)
                return

            # Se vier algo com jeito de HTTP, consome cabeçalhos até linha vazia
            while True:
                linha = f.readline(4096)
                if not linha or linha in (b"\r\n", b"\n"):
                    break

            texto = primeira_linha.decode("utf-8", errors="ignore").strip()
            corpo = (
                f"Olá {addr[0]}:{addr[1]}!\n"
                f"Você enviou: {texto}\n"
                "ServidorSimples (Python) está funcionando.\n"
            )
            conn.sendall(resposta_ok(corpo))
        except socket.timeout:
            # Se o cliente não envia nada a tempo, responde 400
            try:
                conn.sendall(MSG_BAD)
            except Exception:
                pass

def main(host="0.0.0.0", port=8080, backlog=100):
    # Permite CTRL+C encerrar graciosamente
    def handle_sigint(sig, frame):
        stop_event.set()
        print("\nEncerrando servidor...")
        sys.exit(0)
    signal.signal(signal.SIGINT, handle_sigint)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((host, port))
        srv.listen(backlog)
        print(f"Servidor escutando em {host}:{port} (CTRL+C para sair)")

        while not stop_event.is_set():
            try:
                conn, addr = srv.accept()
            except OSError:
                break
            t = threading.Thread(target=tratar_cliente, args=(conn, addr), daemon=True)
            t.start()

if __name__ == "__main__":
    main()  # porta 8080 por padrão (evita necessidade de privilégio de root)
