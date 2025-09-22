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
                print("3) Enviar mensagem")
                print("4) Listar grupos")
                print("5) Criar grupo")
                print("6) Enviar mensagem para grupo")
                print("7) Logout")
                print("8) Sair")
                escolha = input("Escolha: ").strip()

                if escolha == '1':
                    resposta = cliente.listar_contatos(login=username)
                    print("Resposta do servidor:", resposta)

                    print("\n--- Opções ---")
                    print("1) Ver mensagens de um contato")
                    print("2) Voltar")

                    sub_escolha = input("Escolha: ").strip()
                    if sub_escolha == '1':
                        contato_login = input("Login do contato: ").strip()
                        mensagens = cliente.listar_mensagens(conversa_id=contato_login)
                        if mensagens:
                            print(f"\n--- Mensagens com {contato_login} ---")
                            for msg in mensagens:
                                print(f"[{msg.datetime}] {msg.remetente} -> {msg.destino}: {msg.conteudo}")
                        else:
                            print(f"Nenhuma mensagem encontrada com {contato_login}.")
                    elif sub_escolha == '2':
                        continue


                elif escolha == '2':
                    contato_login = input("Login do contato a adicionar: ").strip()
                    contato_nome = input("Nome do contato: ").strip()
                    resposta = cliente.adicionar_contato(contato_login, contato_nome, username)
                    print("Resposta do servidor:", resposta)

                elif escolha == '3':
                    destino = input("Destino (login do usuário): ").strip()
                    conteudo = input("Mensagem: ")
                    resposta = cliente.enviar_mensagem(username,destino, conteudo)
                    print("Resposta do servidor:", resposta)

                elif escolha == '4':
                    resposta = cliente.listar_grupos(username)
                    print("Resposta do servidor:", resposta)

                    print("\n--- Opções ---")
                    print("1) Ver mensagens de um grupo")
                    print("2) Voltar")

                    sub_escolha = input("Escolha: ").strip()
                    if sub_escolha == '1':
                        id_grupo = input("ID DO GRUPO: ").strip()
                        mensagens = cliente.listar_mensagens(conversa_id=id_grupo)
                        if mensagens:
                            print(f"\n--- Mensagens com {id_grupo} ---")
                            for msg in mensagens:
                                print(f"[{msg.datetime}] {msg.remetente} -> {msg.destino}: {msg.conteudo}")
                        else:
                            print(f"Nenhuma mensagem encontrada com {id_grupo}.")
                    elif sub_escolha == '2':
                        continue

                elif escolha == '5':
                    nome_grupo = input("Nome do grupo: ").strip()
                    participantes = input("Participantes (logins separados por vírgula): ").strip().split(',')
                    participantes = [p.strip() for p in participantes if p.strip()]
                    if username not in participantes:
                        participantes.append(username)  # adiciona o criador do grupo
                    resposta = cliente.criar_grupo(nome_grupo, participantes)
                    print("Resposta do servidor:", resposta)

                elif escolha == '6':
                    grupo_id = input("ID do grupo: ").strip()
                    conteudo = input("Mensagem para o grupo: ")
                    resposta = cliente.enviar_mensagem_grupo(username, grupo_id, conteudo)
                    print("Resposta do servidor:", resposta)

                elif escolha == '7':
                    cliente.logout(username)
                    logged = False
                    username = None
                    print("Desconectado.")

                elif escolha == '8':
                    print("Encerrando aplicação.")
                    break

                else:
                    print("Opção inválida.")
    except KeyboardInterrupt:
        cliente.logout(username)
        print("\nInterrompido pelo usuário. Encerrando.")
    finally:
        cliente.logout(username)
        sys.exit(0)

if __name__ == "__main__":
    main()