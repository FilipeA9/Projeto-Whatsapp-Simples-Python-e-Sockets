import socket
import threading
import json
import mimetypes, os, hashlib
import re
from pathlib import Path
from base64 import b64decode, b64encode
import models_app

historico_msgs = []  # lista de objetos Conversa

# Função auxiliar para ler um arquivo e retornar um dicionário com os dados necessários
# ajuda na hora de enviar arquivos
def _file_to_payload(path: str) -> dict:
        with open(path, 'rb') as f:
            raw = f.read()
        b64 = b64encode(raw).decode('ascii')
        mime, _ = mimetypes.guess_type(path)
        sha256 = hashlib.sha256(raw).hexdigest()
        print(f"Arquivo lido: {path}, tamanho: {len(raw)} bytes, sha256: {sha256}")
        return {
            "filename": os.path.basename(path),
            "mimetype": mime or "application/octet-stream",
            "size": len(raw),
            "sha256": sha256,
            "data_base64": b64,
        }

def _send_with_len(sock, data_bytes: bytes):
    size = len(data_bytes).to_bytes(8, 'big')
    sock.sendall(size)
    sock.sendall(data_bytes)

def _recv_exact(conn, n):
    buf = bytearray()
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("socket fechado antes de receber tudo")
        buf.extend(chunk)
    return bytes(buf)

def _recv_msg(conn):
    # 8 bytes com o tamanho
    header = _recv_exact(conn, 8)
    total = int.from_bytes(header, 'big')
    # agora lê exatamente total bytes
    return _recv_exact(conn, total)

def salvar_arquivo_recebido(self, mensagem: models_app.Mensagem):
        if mensagem.tipo == "arquivo" and isinstance(mensagem.conteudo, dict):
            info = mensagem.conteudo

            # 1) Nome da pasta: "<login_remetente>_arquivos" em C:\
            pasta_base = Path(r"C:\{}".format(f"{mensagem.remetente}_arquivos"))
            pasta_base.mkdir(parents=True, exist_ok=True)

            # 2) Sanitizar nome do arquivo (Windows não aceita \ / : * ? " < > |)
            filename = info.get("filename", "arquivo.bin")
            filename = re.sub(r'[\\/:*?"<>|]', "_", filename)

            # 3) Caminho final
            destino = pasta_base / filename

            # (Opcional) Evitar sobrescrever: cria "nome (1).ext", "nome (2).ext", ...
            i, original = 1, destino
            while destino.exists():
                destino = original.with_name(f"{original.stem} ({i}){original.suffix}")
                i += 1

            # 4) Salvar
            data = b64decode(info["data_base64"])
            with open(destino, "wb") as f:
                f.write(data)

            tamanho = info.get("size") or len(data)
            mimetype = info.get("mimetype", "application/octet-stream")
            print(f"Arquivo recebido e salvo: {destino} ({mimetype}, {tamanho} bytes)")


# Cliente que se conecta ao servidor e envia comandos
class Cliente:

    # inicializa o cliente, conecta ao servidor e inicia a thread de escuta
    def __init__(self, server='localhost', port=8080):
       
       self.socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
       self.socket_cliente.bind(('localhost', 0)) # vincula a uma porta livre
       self.socket_cliente.listen()

       self.listen_port = self.socket_cliente.getsockname()[1]
       self.listen_ip = self.socket_cliente.getsockname()[0]

       self.server = server
       self.port = port

       # thread que aceita conexões de entrada e cria handlers
       t = threading.Thread(target=self._accept_loop, daemon=True)
       t.start()
    
    # thread que aceita conexões de entrada e cria handlers
    def _accept_loop(self):
        while True:
            conn, addr = self.socket_cliente.accept()
            threading.Thread(target=self._handle_incoming, args=(conn, addr), daemon=True).start()

    # thread que lida com uma conexão de entrada
    # recebe a mensagem, decodifica e adiciona ao histórico
    def _handle_incoming(self, conn, addr):
        with conn:
            data = _recv_msg(conn)
            if data:
                
                data = json.loads(data.decode())

                mensagem = models_app.Mensagem(
                    remetente=data.get('remetente'),
                    destino=data.get('destino'),
                    tipo=data.get('tipo'), 
                    datetime_envio=data.get('datetime'),
                    conteudo=data.get('conteudo') )

                print(f"Mensagem recebida de {addr}: {mensagem}")

                # dentro de Cliente._handle_incoming (após criar 'mensagem')
                salvar_arquivo_recebido(mensagem)

                if mensagem.remetente not in [conversa.id for conversa in historico_msgs]:
                    nova_conversa = models_app.Conversa(id_conversa=mensagem.remetente, mensagens=[mensagem], participantes=[mensagem.remetente, mensagem.destino])
                    historico_msgs.append(nova_conversa)
                else:
                    for conversa in historico_msgs:
                        if conversa.id == mensagem.remetente:
                            conversa.mensagens.append(mensagem)
                            break
                
# métodos para enviar comandos ao servidor 
# cada método cria o comando, conecta ao servidor, envia o comando e espera a resposta
# depois fecha a conexão e retorna a resposta

    # método de login, recebe login e senha e envia ao servidor
    # envia o IP e porta do cliente para que o servidor possa se conectar
    # assim o cliente pode receber mensagens indenpendente do ip/porta do servidor                      
    def login(self,login, senha,):
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((self.server, self.port))

        usuario = models_app.Usuario( nome=None, login=login, senha=senha, ip=self.listen_ip, porta=self.listen_port)
        comando = models_app.Comando(tipo=2, objeto = usuario) # tipo 2 para login
          
        #cliente.sendall(comando.to_json().encode())
        _send_with_len(cliente, comando.to_json().encode())
        
        resposta = cliente.recv(4096).decode()
        print('Resposta do servidor:', resposta)

        cliente.close()
        return resposta
    
    # método de logout, recebe o login do usuário e envia ao servidor
    # o servidor coloca o status do usuário como offline
    def logout(self, login):
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((self.server, self.port))

        usuario = models_app.Usuario( nome=None, login=login, senha=None, ip=None, porta=None)
        comando = models_app.Comando(tipo=7, objeto = usuario) # tipo 7 para logout
          
        #cliente.sendall(comando.to_json().encode())
        _send_with_len(cliente, comando.to_json().encode())
        
        resposta = cliente.recv(4096).decode()
        print('Resposta do servidor:', resposta)

        cliente.close()
        return resposta
    
# método de registro, recebe nome, login e senha e envia ao servidor
# o servidor cria o usuário e retorna uma mensagem de sucesso ou erro
    def registrar(self, nome, login, senha):
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((self.server, self.port))

        usuario = models_app.Usuario(nome=nome, login=login, senha=senha, ip=self.listen_ip, porta=self.listen_port)
        comando = models_app.Comando(tipo=1, objeto = usuario) # tipo 1 para registro

        #cliente.sendall(comando.to_json().encode())
        _send_with_len(cliente, comando.to_json().encode())

        resposta = cliente.recv(4096).decode()
        print('Resposta do servidor:', resposta)

        cliente.close()
        return resposta

    # método para enviar mensagem, recebe remetente, destino, conteudo e tipo (texto ou arquivo)
    def enviar_mensagem(self, remetente, destino, conteudo, tipo='texto'):
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((self.server, self.port))

        mensagem = models_app.Mensagem(remetente = remetente, destino=destino, tipo=tipo, conteudo=conteudo)
        comando = models_app.Comando(tipo=3, objeto=mensagem)  # tipo 3 para enviar mensagem

        #cliente.sendall(comando.to_json().encode())
        _send_with_len(cliente, comando.to_json().encode())

        resposta = cliente.recv(4096).decode()
        print('Resposta do servidor:', resposta)

        status_ok = False
        try:
            resp = json.loads(resposta)
            status_ok = (resp.get('status') == 'success')
        except Exception:
            # não era JSON, deixa como string mesmo
            print("Resposta do servidor não é JSON:", resposta)

        if status_ok:
            # adiciona a mensagem ao histórico local se o envio foi bem-sucedido
            if destino not in [conversa.id for conversa in historico_msgs]:
                nova_conversa = models_app.Conversa(id_conversa=destino, mensagens=[mensagem], participantes=[remetente, destino])
                historico_msgs.append(nova_conversa)
                print("Nova conversa criada no histórico.")
            else:
                for conversa in historico_msgs:
                    if conversa.id == destino:
                        conversa.mensagens.append(mensagem)
                        print("Mensagem adicionada ao histórico existente.")
                        break

        cliente.close()
        return resposta
    
    # método para enviar mensagem para um grupo, recebe remetente, id do grupo, conteudo e tipo (texto ou arquivo)
    def enviar_mensagem_grupo(self, remetente, grupo_id, conteudo, tipo='texto'):
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((self.server, self.port))

        mensagem = models_app.Mensagem(remetente = remetente, destino=grupo_id, tipo=tipo, conteudo=conteudo, grupo=True)
        comando = models_app.Comando(tipo=10, objeto=mensagem)  # tipo 10 para enviar mensagem para grupo

        #cliente.sendall(comando.to_json().encode())
        _send_with_len(cliente, comando.to_json().encode())

        resposta = cliente.recv(4096).decode()
        print('Resposta do servidor:', resposta)

        cliente.close()
        return resposta
    
    # método para adicionar contato, recebe o login do usuário, nome do contato e login do dono do contato
    def adicionar_contato(self, contato_login, contato_nome, contato_dono):
        if contato_login == contato_dono:
            return "Erro: Não é possível adicionar você mesmo como contato."
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((self.server, self.port))

        contato = models_app.Contato(nome=contato_nome, id_usuario=contato_login, contato_dono=contato_dono)
        comando = models_app.Comando(tipo=4, objeto=contato)  # tipo 4 para adicionar contato

        #cliente.sendall(comando.to_json().encode())
        _send_with_len(cliente, comando.to_json().encode())

        resposta = cliente.recv(4096).decode()
        print('Resposta do servidor:', resposta)

        cliente.close()
        return resposta

    # método para listar contatos, recebe o login do usuário e envia ao servidor
    # o servidor retorna a lista de contatos do usuário
    def listar_contatos(self, login):
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((self.server, self.port))

        usuario = models_app.Usuario(nome=None, login=login, senha=None, ip=None, porta=None)
        comando = models_app.Comando(tipo=5, objeto=usuario)  # tipo 5 para listar contatos

        #cliente.sendall(comando.to_json().encode())
        _send_with_len(cliente, comando.to_json().encode())

        resposta = cliente.recv(4096).decode()
        print('Resposta do servidor:', resposta)

        cliente.close()
        return resposta
    
    # método para listar todos os usuários, envia ao servidor
    # o servidor retorna a lista de todos os usuários cadastrados
    def listar_todos_usuarios(self):
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((self.server, self.port))

        comando = models_app.Comando(tipo=6, objeto=None)  # tipo 6 para listar todos os usuários

        #cliente.sendall(comando.to_json().encode())
        _send_with_len(cliente, comando.to_json().encode())

        resposta = cliente.recv(4096).decode()
        print('Resposta do servidor:', resposta)

        cliente.close()
        return resposta
    
    def listar_mensagens(self, conversa_id):
        for conversa in historico_msgs:
            if conversa.id == conversa_id:
                return conversa.mensagens
        return []



    # método para criar grupo, recebe nome do grupo e lista de participantes (logins)
    def criar_grupo(self, nome_grupo, participantes):
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((self.server, self.port))

        grupo = models_app.Grupo(id_grupo=None, nome=nome_grupo, participantes=participantes)
        comando = models_app.Comando(tipo=8, objeto=grupo)  # tipo 8 para criar grupo

        #cliente.sendall(comando.to_json().encode())
        _send_with_len(cliente, comando.to_json().encode())

        resposta = cliente.recv(4096).decode()
        print('Resposta do servidor:', resposta)

        cliente.close()
        return resposta
    
    # método para listar grupos, recebe o login do usuário e envia ao servidor
    # o servidor retorna a lista de grupos do usuário
    def listar_grupos(self, login):
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((self.server, self.port))

        usuario = models_app.Usuario(nome=None, login=login, senha=None, ip=None, porta=None)
        comando = models_app.Comando(tipo=9, objeto=usuario)  # tipo 9 para listar grupos

        #cliente.sendall(comando.to_json().encode())
        _send_with_len(cliente, comando.to_json().encode())

        resposta = cliente.recv(4096).decode()
        print('Resposta do servidor:', resposta)

        cliente.close()
        return resposta

    # método para enviar arquivo, recebe remetente, destino e caminho do arquivo
    def enviar_arquivo(self, remetente: str, destino: str, caminho_arquivo: str):
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((self.server, self.port))

        payload = _file_to_payload(caminho_arquivo)
        msg = models_app.Mensagem(remetente=remetente, destino=destino, tipo="arquivo", conteudo=payload)
        cmd = models_app.Comando(tipo=3, objeto=msg)   # 3 = enviar mensagem (reutilizamos)
        #cliente.sendall(cmd.to_json().encode())
        _send_with_len(cliente, cmd.to_json().encode())

        resposta = cliente.recv(65536).decode()
        print("Resposta do servidor:", resposta)
        cliente.close()
        return resposta


                 