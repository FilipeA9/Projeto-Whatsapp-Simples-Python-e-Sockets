from xml.dom import minidom

import xml.etree.ElementTree as ET

def prettify(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

class Usuario:
    def __init__(self, nome, id, nome_usuario, senha):
        self.nome = nome
        self.id = id
        self.nome_usuario = nome_usuario
        self.senha = senha

    def to_xml(self):
        usuario_el = ET.Element("usuario")
        ET.SubElement(usuario_el, "nome").text = self.nome
        ET.SubElement(usuario_el, "id").text = str(self.id)
        ET.SubElement(usuario_el, "nome_usuario").text = self.nome_usuario
        ET.SubElement(usuario_el, "senha").text = self.senha
        return usuario_el

    @staticmethod
    def from_xml(elem):
        nome = elem.find("nome").text
        id = elem.find("id").text
        nome_usuario = elem.find("nome_usuario").text
        senha = elem.find("senha").text
        return Usuario(nome, id, nome_usuario, senha)

    @staticmethod
    def salvar_em_arquivo(usuario, arquivo):
        root = usuario.to_xml()
        xml_str = prettify(root)
        with open(arquivo, "w", encoding="utf-8") as f:
            f.write(xml_str)

    @staticmethod
    def ler_de_arquivo(arquivo):
        tree = ET.parse(arquivo)
        root = tree.getroot()
        return Usuario.from_xml(root)

class Grupo:
    def __init__(self, id, nome, participantes=None):
        self.id = id
        self.nome = nome
        # participantes should be a list of Usuario objects
        self.participantes = participantes if participantes else []

    def to_xml(self):
        grupo_el = ET.Element("grupo")
        ET.SubElement(grupo_el, "id").text = str(self.id)
        ET.SubElement(grupo_el, "nome").text = self.nome
        participantes_el = ET.SubElement(grupo_el, "participantes")
        for usuario in self.participantes:
            participantes_el.append(usuario.to_xml())
        return grupo_el

    @staticmethod
    def from_xml(elem):
        id = elem.find("id").text
        nome = elem.find("nome").text
        participantes_el = elem.find("participantes")
        participantes = []
        if participantes_el is not None:
            for usuario_el in participantes_el.findall("usuario"):
                participantes.append(Usuario.from_xml(usuario_el))
        return Grupo(id, nome, participantes)

    @staticmethod
    def salvar_em_arquivo(grupo, arquivo):
        root = grupo.to_xml()
        xml_str = prettify(root)
        with open(arquivo, "w", encoding="utf-8") as f:
            f.write(xml_str)

    @staticmethod
    def ler_de_arquivo(arquivo):
        tree = ET.parse(arquivo)
        root = tree.getroot()
        return Grupo.from_xml(root)

class Mensagem:
    def __init__(self, texto, date_time, id):
        self.texto = texto
        self.date_time = date_time
        self.id = id

    def to_xml(self):
        mensagem_el = ET.Element("mensagem")
        ET.SubElement(mensagem_el, "texto").text = self.texto
        ET.SubElement(mensagem_el, "date_time").text = self.date_time
        ET.SubElement(mensagem_el, "id").text = str(self.id)
        return mensagem_el

    @staticmethod
    def from_xml(elem):
        texto = elem.find("texto").text
        date_time = elem.find("date_time").text
        id = elem.find("id").text
        return Mensagem(texto, date_time, id)

    @staticmethod
    def salvar_em_arquivo(mensagem, arquivo):
        root = mensagem.to_xml()
        xml_str = prettify(root)
        with open(arquivo, "w", encoding="utf-8") as f:
            f.write(xml_str)

    @staticmethod
    def ler_de_arquivo(arquivo):
        tree = ET.parse(arquivo)
        root = tree.getroot()
        return Mensagem.from_xml(root)

# Example usage:
if __name__ == '__main__':
    # Usuario example
    user = Usuario("Alice", 1, "alice123", "senhaSecreta")
    Usuario.salvar_em_arquivo(user, "usuario.xml")
    user_loaded = Usuario.ler_de_arquivo("usuario.xml")
    print(user_loaded.__dict__)

    # Grupo example
    grupo = Grupo(1, "Grupo1", participantes=[user])
    Grupo.salvar_em_arquivo(grupo, "grupo.xml")
    grupo_loaded = Grupo.ler_de_arquivo("grupo.xml")
    print(grupo_loaded.nome, [u.__dict__ for u in grupo_loaded.participantes])

    # Mensagem example
    mensagem = Mensagem("Olá Mundo!", "2023-10-10T10:00:00", 100)
    Mensagem.salvar_em_arquivo(mensagem, "mensagem.xml")
    mensagem_loaded = Mensagem.ler_de_arquivo("mensagem.xml")
    print(mensagem_loaded.__dict__)
