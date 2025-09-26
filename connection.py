import socket
import threading

class Connection:
    def __init__(self, host: str, port: int, timeout: int = 10):
        """
        Classe para gerenciar uma conexão cliente-servidor.
        - host: endereço IP ou hostname
        - port: porta do servidor
        - timeout: tempo em segundos para encerrar a conexão automaticamente (default 5 minutos)
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock = None
        self._timer = None
        self._closed_by_timeout = False

    def __enter__(self):
        """Abre a conexão com o servidor"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))

        # inicia um timer para encerrar a conexão após timeout
        self._timer = threading.Timer(self.timeout, self._timeout_close)
        self._timer.daemon = True
        self._timer.start()

        print(f"Conexão estabelecida com {self.host}:{self.port}")
        return self.sock

    def __exit__(self, exc_type, exc_value, traceback):
        """Garante que a conexão seja fechada ao sair do with"""
        self.close()

    def _timeout_close(self):
        """Função chamada apenas pelo timer"""
        self._closed_by_timeout = True
        self.close()

    def close(self):
        """Fecha a conexão manualmente"""
        if self._timer:
            self._timer.cancel()
            self._timer = None
        if self.sock:
            try:
                self.sock.close()
                if self._closed_by_timeout:
                    print("⚠️ Conexão encerrada automaticamente (timeout).")
                else:
                    print("✅ Conexão encerrada normalmente.")
            except Exception:
                pass
            self.sock = None
