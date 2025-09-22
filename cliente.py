import socket
import threading
import json
import base64, mimetypes, os, hashlib
import models_app

historico_msgs = []  # lista de objetos Conversa


def _file_to_payload(path: str) -> dict:
        with open(path, 'rb') as f:
            raw = f.read()
        b64 = base64.b64encode(raw).decode('ascii')
        mime, _ = mimetypes.guess_type(path)
        sha256 = hashlib.sha256(raw).hexdigest()
        return {
            "filename": os.path.basename(path),
            "mimetype": mime or "application/octet-stream",
            "size": len(raw),
            "sha256": sha256,
            "data_base64": b64,
        }


class Cliente:

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
    
    def _accept_loop(self):
        while True:
            conn, addr = self.socket_cliente.accept()
            threading.Thread(target=self._handle_incoming, args=(conn, addr), daemon=True).start()

    def _handle_incoming(self, conn, addr):
        with conn:
            data = conn.recv(4096)
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
                if mensagem.tipo == "arquivo" and isinstance(mensagem.conteudo, dict):
                    from base64 import b64decode
                    info = mensagem.conteudo
                    data = b64decode(info["data_base64"])
                    with open(info["filename"], "wb") as f:
                        f.write(data)
                    print(f"Arquivo recebido e salvo: {info['filename']} ({info.get('mimetype')}, {info.get('size')} bytes)")


                if mensagem.remetente not in [conversa.id for conversa in historico_msgs]:
                    nova_conversa = models_app.Conversa(id_conversa=mensagem.remetente, mensagens=[mensagem], participantes=[mensagem.remetente, mensagem.destino])
                    historico_msgs.append(nova_conversa)
                else:
                    for conversa in historico_msgs:
                        if conversa.id == mensagem.remetente:
                            conversa.mensagens.append(mensagem)
                            break
                

    def login(self,login, senha,):
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((self.server, self.port))

        usuario = models_app.Usuario( nome=None, login=login, senha=senha, ip=self.listen_ip, porta=self.listen_port)
        comando = models_app.Comando(tipo=2, objeto = usuario) # tipo 2 para login
          
        cliente.sendall(comando.to_json().encode())
        
        resposta = cliente.recv(4096).decode()
        print('Resposta do servidor:', resposta)

        cliente.close()
        return resposta
    
    def logout(self, login):
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((self.server, self.port))

        usuario = models_app.Usuario( nome=None, login=login, senha=None, ip=None, porta=None)
        comando = models_app.Comando(tipo=7, objeto = usuario) # tipo 7 para logout
          
        cliente.sendall(comando.to_json().encode())
        
        resposta = cliente.recv(4096).decode()
        print('Resposta do servidor:', resposta)

        cliente.close()
        return resposta
    

    def registrar(self, nome, login, senha):
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((self.server, self.port))

        usuario = models_app.Usuario(nome=nome, login=login, senha=senha, ip=self.listen_ip, porta=self.listen_port)
        comando = models_app.Comando(tipo=1, objeto = usuario) # tipo 1 para registro

        cliente.sendall(comando.to_json().encode())

        resposta = cliente.recv(4096).decode()
        print('Resposta do servidor:', resposta)

        cliente.close()
        return resposta

    def enviar_mensagem(self, remetente, destino, conteudo, tipo='texto'):
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((self.server, self.port))

        mensagem = models_app.Mensagem(remetente = remetente, destino=destino, tipo=tipo, conteudo=conteudo)
        comando = models_app.Comando(tipo=3, objeto=mensagem)  # tipo 3 para enviar mensagem

        cliente.sendall(comando.to_json().encode())

        resposta = cliente.recv(4096).decode()
        print('Resposta do servidor:', resposta)

        cliente.close()
        return resposta
    
    def enviar_mensagem_grupo(self, remetente, grupo_id, conteudo, tipo='texto'):
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((self.server, self.port))

        mensagem = models_app.Mensagem(remetente = remetente, destino=grupo_id, tipo=tipo, conteudo=conteudo, grupo=True)
        comando = models_app.Comando(tipo=10, objeto=mensagem)  # tipo 10 para enviar mensagem para grupo

        cliente.sendall(comando.to_json().encode())

        resposta = cliente.recv(4096).decode()
        print('Resposta do servidor:', resposta)

        cliente.close()
        return resposta
    
    def adicionar_contato(self, contato_login, contato_nome, contato_dono):
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((self.server, self.port))

        contato = models_app.Contato(nome=contato_nome, id_usuario=contato_login, contato_dono=contato_dono)
        comando = models_app.Comando(tipo=4, objeto=contato)  # tipo 4 para adicionar contato

        cliente.sendall(comando.to_json().encode())

        resposta = cliente.recv(4096).decode()
        print('Resposta do servidor:', resposta)

        cliente.close()
        return resposta

    def listar_contatos(self, login):
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((self.server, self.port))

        usuario = models_app.Usuario(nome=None, login=login, senha=None, ip=None, porta=None)
        comando = models_app.Comando(tipo=5, objeto=usuario)  # tipo 5 para listar contatos

        cliente.sendall(comando.to_json().encode())

        resposta = cliente.recv(4096).decode()
        print('Resposta do servidor:', resposta)

        cliente.close()
        return resposta
    
    def listar_todos_usuarios(self):
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((self.server, self.port))

        comando = models_app.Comando(tipo=6, objeto=None)  # tipo 6 para listar todos os usuários

        cliente.sendall(comando.to_json().encode())

        resposta = cliente.recv(4096).decode()
        print('Resposta do servidor:', resposta)

        cliente.close()
        return resposta
    
    '''def listar_mensagens(self, conversa_id):
        for conversa in historico_msgs:
            if conversa.id == conversa_id:
                return conversa.mensagens
        return []'''
    
    def _human_size(self, n: int) -> str:
        # opcional: deixa o tamanho mais amigável (KB/MB)
        for unit in ("B", "KB", "MB", "GB"):
            if n < 1024:
                return f"{n:.0f} {unit}" if unit == "B" else f"{n:.2f} {unit}"
            n /= 1024
        return f"{n:.2f} TB"
    

    def listar_mensagens(self, conversa_id):
        for conversa in historico_msgs:
            if conversa.id == conversa_id:
                mensagens = conversa.mensagens
                if not mensagens:
                    print("— sem mensagens —")
                    return []

                for m in mensagens:
                    # tenta usar datetime se existir (ajuste se seu atributo tiver outro nome)
                    ts = getattr(m, "datetime", "") or getattr(m, "datetime_envio", "")
                    cab = f"[{ts}] {m.remetente} -> {m.destino}: "

                    if m.tipo == "arquivo" and isinstance(m.conteudo, dict):
                        filename = m.conteudo.get("filename", "arquivo")
                        size = m.conteudo.get("size")
                        # mostre em KB/MB se quiser, senão use f"{size} bytes"
                        size_str = self._human_size(size) if isinstance(size, int) else "tamanho desconhecido"
                        print(cab + f"{filename} {size_str}")
                    else:
                        print(cab + str(m.conteudo))

                return mensagens

        print("— conversa não encontrada —")
        return []



    
    def criar_grupo(self, nome_grupo, participantes):
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((self.server, self.port))

        grupo = models_app.Grupo(id_grupo=None, nome=nome_grupo, participantes=participantes)
        comando = models_app.Comando(tipo=8, objeto=grupo)  # tipo 8 para criar grupo

        cliente.sendall(comando.to_json().encode())

        resposta = cliente.recv(4096).decode()
        print('Resposta do servidor:', resposta)

        cliente.close()
        return resposta
    
    def listar_grupos(self, login):
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((self.server, self.port))

        usuario = models_app.Usuario(nome=None, login=login, senha=None, ip=None, porta=None)
        comando = models_app.Comando(tipo=9, objeto=usuario)  # tipo 9 para listar grupos

        cliente.sendall(comando.to_json().encode())

        resposta = cliente.recv(4096).decode()
        print('Resposta do servidor:', resposta)

        cliente.close()
        return resposta


    def enviar_arquivo(self, remetente: str, destino: str, caminho_arquivo: str):
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((self.server, self.port))

        payload = _file_to_payload(caminho_arquivo)
        msg = models_app.Mensagem(remetente=remetente, destino=destino, tipo="arquivo", conteudo=payload)
        cmd = models_app.Comando(tipo=3, objeto=msg)   # 3 = enviar mensagem (reutilizamos)
        cliente.sendall(cmd.to_json().encode())

        resposta = cliente.recv(65536).decode()
        print("Resposta do servidor:", resposta)
        cliente.close()
        return resposta
