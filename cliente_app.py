import json
import sys
from cliente import Cliente

def main():
    server = input("Servidor (enter para localhost): ").strip() or 'localhost'
    port_str = input("Porta (enter para 8080): ").strip()
    port = int(port_str) if port_str else 8080

    cliente = Cliente(server=server, port=port)

    logged = False
    username = None

    try:
        while True:
            if not logged:
                print("\n--- MENU ---")
                print("1) Login")
                print("2) Cadastrar")
                print("3) Sair")
                escolha = input("Escolha: ").strip()

                if escolha == '1':
                    login = input("Login: ").strip()
                    senha = input("Senha: ").strip()
                    resposta = cliente.login(login, senha)
                    # tenta interpretar como JSON com campo 'status'
                    try:
                        obj = json.loads(resposta)
                        if obj.get('status') == 'success':
                            logged = True
                            username = login
                
                            print("Login efetuado com sucesso.")
                        else:
                            print("Resposta do servidor:", obj)
                    except Exception:
                        print("Resposta do servidor:", resposta)

                elif escolha == '2':
                    nome = input("Nome: ").strip()
                    login = input("Login: ").strip()
                    senha = input("Senha: ").strip()
                    resposta = cliente.registrar(nome, login, senha)
                    try:
                        obj = json.loads(resposta)
                        print("Resposta do servidor:", obj)
                    except Exception:
                        print("Resposta do servidor:", resposta)

                elif escolha == '3':
                    print("Encerrando aplicação.")
                    break

                else:
                    print("Opção inválida.")

            else:
                print(f"\n--- {username} — Opções ---")
                print("1) Listar contatos")
                print("2) Adicionar contato")
                print("3) Ver mensagens de um contato/grupo")
                print("4) Enviar mensagem")
                print("5) Listar grupos")
                print("6) Criar grupo")
                print("7) Enviar mensagem para grupo")
                print("8) Listar todos os usuários cadastrados no servidor")
                print("9) Logout")
                print("10) Sair")
                escolha = input("Escolha: ").strip()

                if escolha == '1':
                    resposta = cliente.listar_contatos(login=username)
                    if isinstance(resposta, str):
                        try:
                            obj = json.loads(resposta)
                            if isinstance(obj, list):
                                print("\n--- Contatos ---")
                                for contato in obj:
                                    print(f"Nome: {contato.get('nome')}, Login: {contato.get('login')}")
                            else:
                                print("Resposta do servidor:", obj)
                        except Exception:
                            print("Resposta do servidor:", resposta)
                    else:
                        print("Resposta do servidor:", resposta)


                elif escolha == '2':
                    contato_login = input("Login do contato a adicionar: ").strip()
                    contato_nome = input("Nome do contato: ").strip()
                    resposta = cliente.adicionar_contato(contato_login, contato_nome, username)
                    print("Resposta do servidor:", resposta)

                elif escolha == '3':
                    conversa_id = input("Login do contato ou ID do grupo: ").strip()
                    mensagens = cliente.listar_mensagens(conversa_id=conversa_id)
                    if mensagens:
                        print(f"\n--- Mensagens com {conversa_id} ---")
                        for msg in mensagens:
                            if msg.tipo == 'arquivo':
                                print(f"[{msg.datetime}] {msg.remetente} -> {msg.destino}: [Arquivo]")
                            else:
                                print(f"[{msg.datetime}] {msg.remetente} -> {msg.destino}: {msg.conteudo}")
                    else:
                        print(f"Nenhuma mensagem encontrada com {conversa_id}.")

                elif escolha == '4':
                    tipo_mensagem = input("Deseja enviar um texto ou arquivo? Digite 1 para texto e 2 para arquivo: ").strip()
                    if tipo_mensagem not in ['1', '2']:
                        print("Opção inválida.")
                        continue
                    destino = input("Destino (login do usuário): ").strip()
                    if tipo_mensagem == '2':
                        caminho_arquivo = input("Caminho do arquivo: ").strip()
                        resposta = cliente.enviar_arquivo(username, destino, caminho_arquivo)
                        print("Resposta do servidor:", resposta)
                        continue
                    else:
                        conteudo = input("Mensagem: ")
                        resposta = cliente.enviar_mensagem(username,destino, conteudo)
                        print("Resposta do servidor:", resposta)

                elif escolha == '5':
                    resposta = cliente.listar_grupos(username)
                    print("Resposta do servidor:", resposta)

                elif escolha == '6':
                    nome_grupo = input("Nome do grupo: ").strip()
                    participantes = input("Participantes (logins separados por vírgula): ").strip().split(',')
                    participantes = [p.strip() for p in participantes if p.strip()]
                    if username not in participantes:
                        participantes.append(username)  # adiciona o criador do grupo
                    resposta = cliente.criar_grupo(nome_grupo, participantes)
                    print("Resposta do servidor:", resposta)

                elif escolha == '7':
                    grupo_id = input("ID do grupo: ").strip()
                    conteudo = input("Mensagem para o grupo: ")
                    resposta = cliente.enviar_mensagem_grupo(username, grupo_id, conteudo)
                    print("Resposta do servidor:", resposta)

                elif escolha == '8':
                    resposta = cliente.listar_todos_usuarios()
                    print("Resposta do servidor:", resposta)

                elif escolha == '9':
                    cliente.logout(username)
                    logged = False
                    username = None
                    print("Desconectado.")

                elif escolha == '10':
                    print("Encerrando aplicação.")
                    break

                else:
                    print("Opção inválida.")
    except KeyboardInterrupt:
        print("keyboard interrupt")
        cliente.logout(username)
        print("\nInterrompido pelo usuário. Encerrando.")
    finally:
        print("Encerrando aplicação. Finally")
        cliente.logout(username)
        sys.exit(0)

if __name__ == "__main__":
    main()