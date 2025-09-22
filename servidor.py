import socket
import threading
import json
import models_app

# Configurações do servidor
HOST = "localhost"  # Endereço IP do servidor
PORT = 8080        # Porta que o servidor vai escutar

# Lista global para armazenar os endereços dos clientes conectados
clientes_cadastrados = []
grupos_cadastrados = []


def handle_client(conn, addr):
    """
    Recebe um JSON que representa um Comando:
      { "tipo": <int>, "objeto": <objeto_json> }

    - extrai apenas o campo 'tipo'
    - despacha para a função responsável pelo comando, passando (conn, addr, objeto)
    - se a função retornar algo, envia como resposta (serializado JSON quando aplicável)
    """
    print("inicio do handle_client", addr)
    try:
        with conn:
            raw = conn.recv(8192)
            if not raw:
                return

            try:
                comando = json.loads(raw.decode())
            except Exception:
                resp = {'status': 'error', 'error': 'invalid_json'}
                conn.sendall(json.dumps(resp).encode())
                return

            tipo = comando.get('tipo')
            objeto = comando.get('objeto')

            if tipo is None:
                resp = {'status': 'error', 'error': 'missing_tipo'}
                conn.sendall(json.dumps(resp).encode())
                return

            # procura handler em mapa global COMMAND_HANDLERS ou por convenção de nome
            handler = COMMAND_HANDLERS.get(tipo) if 'COMMAND_HANDLERS' in globals() else None
            if handler is None:
                handler_name = f'comando_{tipo}'
                handler = globals().get(handler_name)

            if handler is None:
                resp = {'status': 'error', 'error': 'no_handler', 'tipo': tipo}
                conn.sendall(json.dumps(resp).encode())
                return

            # chama o handler. espera-se que o handler:
            # - envie resposta diretamente via conn OU
            # - retorne um objeto (dict/list/str) que será enviado aqui
            try:
                result = handler(conn, addr, objeto)
                if result is None:
                    # assume handler já enviou resposta quando necessário
                    return
                # envia resultado retornado pelo handler
                if isinstance(result, (dict, list)):
                    conn.sendall(json.dumps(result).encode())
                else:
                    # str/int/etc
                    conn.sendall(str(result).encode())
            except Exception as e:
                resp = {'status': 'error', 'error': 'handler_exception', 'detail': str(e)}
                conn.sendall(json.dumps(resp).encode())
    except Exception as e:
        print(f"Erro no handle_client {addr}: {e}")


def cadastrar_cliente(conn, addr, dados_cliente):
    """
    Handler para comando tipo 1: cadastrar cliente
    dados_cliente é um dict com os dados do cliente
    """
    try:
        # Converte o dict recebido em um objeto Usuario
        usuario = models_app.Usuario(
            nome=dados_cliente.get('nome'),
            login=dados_cliente.get('login'),
            senha=dados_cliente.get('senha'),
            ip=dados_cliente.get('ip'),
            porta=dados_cliente.get('porta'),
            conversas=[models_app.Conversa(**c) for c in dados_cliente.get('conversas', [])],
            contatos=dados_cliente.get('contatos', []),
            status='offline'
        )

        # Verifica se o login já existe
        for cliente in clientes_cadastrados:
            if cliente.login == usuario.login:
                return {'status': 'error', 'error': 'login_exists'}

        # Adiciona o novo cliente à lista global
        clientes_cadastrados.append(usuario)
        print(f"Cliente cadastrado: {usuario.login} ({usuario.ip}:{usuario.porta})")
        return {'status': 'success', 'message': 'Cliente cadastrado com sucesso'}
    except Exception as e:
        return {'status': 'error', 'error': 'exception', 'detail': str(e)}
    
def login_cliente(conn, addr, dados_login):
    """
    Handler para comando tipo 2: login cliente
    dados_login é um dict com 'login' e 'senha'
    """
    try:
        login = dados_login.get('login')
        senha = dados_login.get('senha')
        ip_cliente = dados_login.get('ip')
        porta_cliente = dados_login.get('porta')

        for cliente in clientes_cadastrados:
            if cliente.login == login and cliente.senha == senha:
                cliente.status = 'online'
                cliente.ip = ip_cliente
                cliente.porta = porta_cliente
                print(f"Cliente logado: {cliente.login}")
                return {'status': 'success', 'message': 'Login efetuado com sucesso'}

        return {'status': 'error', 'error': 'invalid_credentials'}
    except Exception as e:
        return {'status': 'error', 'error': 'exception', 'detail': str(e)}
    
def logout_cliente(conn, addr, dados_logout):
    """
    Handler para comando tipo 7: logout cliente
    dados_logout é um dict com 'login'
    """
    try:
        login = dados_logout.get('login')

        for cliente in clientes_cadastrados:
            if cliente.login == login:
                cliente.status = 'offline'
                print(f"Cliente deslogado: {cliente.login}")
                return {'status': 'success', 'message': 'Logout efetuado com sucesso'}

        return {'status': 'error', 'error': 'user_not_found'}
    except Exception as e:
        return {'status': 'error', 'error': 'exception', 'detail': str(e)}
    
def enviar_mensagem_handler(conn, addr, dados_msg):
    """
    Handler para comando tipo 3: enviar mensagem
    dados_msg é um dict com os dados da mensagem
    """
    try:
        mensagem = models_app.Mensagem(
            remetente=dados_msg.get('remetente'),
            destino=dados_msg.get('destino'),
            tipo=dados_msg.get('tipo'),
            conteudo=dados_msg.get('conteudo')
        )
        
        print(f"Mensagem recebida de {mensagem.remetente} para {mensagem.destino}")
        
        # Encontra o cliente destinatário
        destinatario = None
        for cliente in clientes_cadastrados:
            if cliente.login == mensagem.destino:
                destinatario = cliente
                break   
        if destinatario is None or destinatario.status != 'online':
            return {'status': 'error', 'error': 'user_offline_or_not_found'}
         
        conexao_destino = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conexao_destino.connect((destinatario.ip, destinatario.porta))
        conexao_destino.sendall(mensagem.to_json().encode())
        conexao_destino.close()

        # Aqui você pode implementar a lógica para encaminhar a mensagem ao destinatário
        # Por simplicidade, apenas confirmamos o recebimento
        return {'status': 'success', 'message': 'Mensagem recebida'}
    except Exception as e:
        return {'status': 'error', 'error': 'exception', 'detail': str(e)}
    
def enviar_mensagem_grupo(conn, addr, dados_msg):
    """
    Handler para comando tipo 9: enviar mensagem para grupo
    dados_msg é um dict com os dados da mensagem
    """
    try:
        mensagem = models_app.Mensagem(
            remetente=dados_msg.get('remetente'),
            destino=dados_msg.get('destino'),  # aqui destino é o id do grupo
            tipo=dados_msg.get('tipo'),
            conteudo=dados_msg.get('conteudo'),
            grupo=True
        )
        
        print(f"Mensagem de grupo recebida de {mensagem.remetente} para o grupo {mensagem.destino}")
        
        # Encontra o grupo destinatário
        grupo_destino = None
        for grupo in grupos_cadastrados:
            if grupo.id == mensagem.destino:
                grupo_destino = grupo
                break   
        if grupo_destino is None:
            return {'status': 'error', 'error': 'group_not_found'}
        
        # Envia a mensagem para todos os participantes do grupo que estão online
        for participante_login in grupo_destino.participantes:
            for cliente in clientes_cadastrados:
                if cliente.login == participante_login and cliente.status == 'online' and cliente.login != mensagem.remetente:
                    conexao_destino = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    conexao_destino.connect((cliente.ip, cliente.porta))
                    conexao_destino.sendall(mensagem.to_json().encode())
                    conexao_destino.close()

        return {'status': 'success', 'message': 'Mensagem de grupo enviada'}
    except Exception as e:
        return {'status': 'error', 'error': 'exception', 'detail': str(e)}
    
def adicionar_contato(conn, addr, contato_dados):
    """
    Handler para comando tipo 4: adicionar contato
    contato_dados é um dict com os dados do contato a ser adicionado
    """
    try:
        contato = models_app.Contato(
            nome=contato_dados.get('nome'),
            id_usuario=contato_dados.get('id'),
            contato_dono=contato_dados.get('contato_dono')
        )
        for cliente in clientes_cadastrados:
            if cliente.login == contato.contato_dono:
                cliente.contatos.append(contato)
                break
        # Aqui você pode implementar a lógica para adicionar o contato ao usuário
        # Por simplicidade, apenas confirmamos o recebimento
        print(f"Contato a ser adicionado: {contato.nome} ({contato.id}) para cliente {cliente.login}")
        return {'status': 'success', 'message': 'Contato adicionado'}
    except Exception as e:
        return {'status': 'error', 'error': 'exception', 'detail': str(e)}

def listar_contatos(conn, addr, login):
    """
    Handler para comando tipo 4: listar contatos
    login é o login do usuário que solicita a lista de contatos
    """
    try:
        for cliente in clientes_cadastrados:
            if cliente.login == login.get('login'): # assume login é um dict com 'login'
                contatos_info = [contato.to_dict() for contato in cliente.contatos]
                return {'status': 'success', 'contatos': contatos_info}

        return {'status': 'error', 'error': 'user_not_found'}
    except Exception as e:
        return {'status': 'error', 'error': 'exception', 'detail': str(e)}
    
def listar_todos_usuarios(conn, addr, _):
    """
    Handler para comando tipo 6: listar todos os usuários
    """
    try:
        usuarios_info = [ {'login': cliente.login, 'nome': cliente.nome, 'status': cliente.status} for cliente in clientes_cadastrados ]
        return {'status': 'success', 'usuarios': usuarios_info}
    except Exception as e:
        return {'status': 'error', 'error': 'exception', 'detail': str(e)}
    
def criar_grupo(conn, addr, dados_grupo):
    """
    Handler para comando tipo 8: criar grupo
    dados_grupo é um dict com os dados do grupo a ser criado
    """
    id_ = grupos_cadastrados[-1].id + 1 if grupos_cadastrados else 1  # simples auto-incremento

    try:
        grupo = models_app.Grupo(
            id_grupo= id_,
            nome=dados_grupo.get('nome'),
            participantes=dados_grupo.get('participantes', []),
            conversa_id=dados_grupo.get('conversa')
        )
        grupos_cadastrados.append(grupo)
        print(f"Grupo criado: {grupo.nome} ({grupo.id})")
        return {'status': 'success', 'message': 'Grupo criado'}
    except Exception as e:
        return {'status': 'error', 'error': 'exception', 'detail': str(e)}
    
# mapa de exemplo: associe tipos de comando aos handlers implementados
# Ex: 1 -> cadastrar_cliente
COMMAND_HANDLERS = {
    1: cadastrar_cliente,
    2: login_cliente,         # defina e adicione outros handlers aqui
    3: enviar_mensagem_handler,
    4: adicionar_contato,
    5: listar_contatos,
    6: listar_todos_usuarios,
    7: logout_cliente,
}

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
        client_thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        client_thread.start()


