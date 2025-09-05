# cliente_simples.py
import argparse
import socket

def main():
    parser = argparse.ArgumentParser(description="Cliente TCP simples")
    parser.add_argument("host", help="Nome ou IP do servidor")
    parser.add_argument("mensagem", help="Mensagem a enviar")
    parser.add_argument("porta", nargs="?", type=int, default=80, help="Porta TCP (padrão: 80)")
    args = parser.parse_args()

    # Cria e conecta o socket (IPv4/TCP)
    with socket.create_connection((args.host, args.porta), timeout=10) as sock:
        sock.settimeout(10)

        # Envio da mensagem (terminada por CRLF CRLF para agradar servidores HTTP/1.0)
        payload = (args.mensagem + "\r\n\r\n").encode("utf-8", errors="ignore")
        sock.sendall(payload)

        # Recepção da resposta até EOF
        resposta_chunks = []
        while True:
            bloco = sock.recv(4096)
            if not bloco:
                break
            resposta_chunks.append(bloco)

        resposta = b"".join(resposta_chunks).decode("utf-8", errors="ignore")
        print("\nResposta do Host:\n")
        print(resposta)

if __name__ == "__main__":
    main()