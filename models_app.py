import json
from datetime import datetime

class Contato:
    def __init__(self, nome, id_usuario, contato_dono):
        self.nome = nome
        self.id = id_usuario
        self.contato_dono = contato_dono

    def to_dict(self):
        return {
            'nome': self.nome,
            'id': self.id,
            'contato_dono': self.contato_dono
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class Usuario:
    def __init__(self, nome, login, senha, ip, porta, conversas=None, contatos=None, status='offline'):
        self.nome = nome
        self.login = login
        self.senha = senha
        self.ip = ip
        self.porta = porta
        self.conversas = conversas if conversas is not None else []
        self.contatos = contatos if contatos is not None else []
        self.status = status  # pode ser 'online' ou 'offline'

    def to_dict(self):
        return {
            'nome': self.nome,
            'login': self.login,
            'senha': self.senha,
            'ip': self.ip,
            'porta': self.porta,
            'conversas': self.conversas,
            'contatos': [contato.to_dict() for contato in self.contatos]
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class Grupo:
    def __init__(self, id_grupo, nome, participantes=None, conversa_id=None):
        self.id = id_grupo
        self.nome = nome
        self.participantes = participantes if participantes is not None else []
        self.conversa = conversa_id  # referência ao id do objeto conversas

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'participantes': self.participantes,
            'conversa': self.conversa
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class Mensagem:
    def __init__(self, remetente, destino, tipo, conteudo, datetime_envio=None, grupo=False):
        self.remetente = remetente  # login do usuário
        self.destino = destino      # login do usuário
        self.tipo = tipo            # TEXTO ou ARQUIVO
        self.grupo = grupo          # True se for mensagem de grupo
        self.conteudo = conteudo    # conteúdo da mensagem
        self.datetime = datetime_envio if datetime_envio is not None else datetime.now().isoformat()

    def to_dict(self):
        return {
            'remetente': self.remetente,
            'destino': self.destino,
            'tipo': self.tipo,
            'grupo': self.grupo,
            'conteudo': self.conteudo,
            'datetime': self.datetime
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class Conversa:
    def __init__(self, id_conversa, mensagens=None, participantes=None):
        self.id = id_conversa # login do usuario ou id do grupo
        self.mensagens = mensagens if mensagens is not None else []  # lista de objetos Mensagem
        self.participantes = participantes if participantes is not None else []  # pode conter logins de usuários ou  IDS de grupos

    def to_dict(self):
        return {
            'id': self.id,
            'mensagens': [mensagem.to_dict() for mensagem in self.mensagens],
            'participantes': self.participantes
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class Comando:
    def __init__(self, tipo, objeto):
        self.tipo = tipo  # int
        self.objeto = objeto     # pode ser uma lista de usuários, um usuário, uma mensagem etc.

    def to_dict(self):
        # Se o objeto tiver método to_dict usa-o, se for lista, tenta converter cada item
        def serialize_item(item):
            if hasattr(item, 'to_dict'):
                return item.to_dict()
            return item

        if isinstance(self.objeto, list):
            objeto_serializado = [serialize_item(item) for item in self.objeto]
        else:
            objeto_serializado = serialize_item(self.objeto)

        return {
            'tipo': self.tipo,
            'objeto': objeto_serializado
        }

    def to_json(self):
        return json.dumps(self.to_dict())