"""Interface gráfica Tkinter para o cliente de chat."""

import json
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Any, Dict, List, Optional, Tuple

from cliente import Cliente, historico_msgs


class ChatGUI:
    """Interface gráfica principal da aplicação de chat."""

    def __init__(self, master: tk.Tk) -> None:
        self.master = master
        self.master.title("Cliente de Chat")
        self.master.geometry("960x640")

        # estado da aplicação
        self.cliente: Optional[Cliente] = None
        self.client_params: Optional[Tuple[str, int]] = None
        self.username: Optional[str] = None
        self.mode: str = "login"
        self.contacts_data: List[Dict[str, Any]] = []
        self.groups_data: List[Dict[str, Any]] = []
        self.list_items: List[Dict[str, Any]] = []
        self._list_signature: Optional[List[Tuple[str, str, str]]] = None
        self.current_item: Optional[Dict[str, Any]] = None
        self.conversation_cache: Dict[str, int] = {}

        # variáveis dos campos
        self.server_var = tk.StringVar(value="localhost")
        self.port_var = tk.StringVar(value="8080")
        self.login_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.message_var = tk.StringVar()

        # área de status compartilhada entre telas
        self.status_var = tk.StringVar(value="Informe os dados de conexão.")
        self.status_label = tk.Label(
            master, textvariable=self.status_var, anchor="w", bd=1, relief="sunken"
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

        # construção das telas
        self._build_login_frame()
        self._build_chat_frame()

        self._show_login_frame()
        self.master.after(1000, self._poll_messages)
        self.master.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # Construção das telas
    # ------------------------------------------------------------------
    def _build_login_frame(self) -> None:
        self.login_frame = tk.Frame(self.master, padx=20, pady=20)
        self.login_frame.columnconfigure(1, weight=1)

        tk.Label(self.login_frame, text="Servidor:").grid(row=0, column=0, sticky="w")
        tk.Entry(self.login_frame, textvariable=self.server_var).grid(
            row=0, column=1, sticky="ew", pady=2
        )

        tk.Label(self.login_frame, text="Porta:").grid(row=1, column=0, sticky="w")
        tk.Entry(self.login_frame, textvariable=self.port_var).grid(
            row=1, column=1, sticky="ew", pady=2
        )

        tk.Label(self.login_frame, text="Login:").grid(row=2, column=0, sticky="w")
        tk.Entry(self.login_frame, textvariable=self.login_var).grid(
            row=2, column=1, sticky="ew", pady=2
        )

        tk.Label(self.login_frame, text="Senha:").grid(row=3, column=0, sticky="w")
        tk.Entry(self.login_frame, textvariable=self.password_var, show="*").grid(
            row=3, column=1, sticky="ew", pady=2
        )

        self.name_label = tk.Label(self.login_frame, text="Nome:")
        self.name_entry = tk.Entry(self.login_frame, textvariable=self.name_var)

        # botões
        self.login_button = tk.Button(
            self.login_frame, text="Login", command=self._perform_login
        )
        self.register_button = tk.Button(
            self.login_frame, text="Registrar", command=self._perform_register
        )

        self.login_button.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(10, 2))

        self.toggle_button = tk.Button(
            self.login_frame,
            text="Criar uma conta",
            command=self._toggle_mode,
            relief="flat",
            fg="#1a73e8",
            cursor="hand2",
        )
        self.toggle_button.grid(row=6, column=0, columnspan=2, pady=(6, 0))

    def _build_chat_frame(self) -> None:
        self.chat_frame = tk.Frame(self.master, padx=10, pady=10)
        for col, weight in enumerate((1, 2, 0)):
            self.chat_frame.columnconfigure(col, weight=weight)
        self.chat_frame.rowconfigure(0, weight=1)

        # coluna esquerda - contatos e grupos
        left = tk.Frame(self.chat_frame)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left.rowconfigure(1, weight=1)

        tk.Label(left, text="Contatos e Grupos").grid(row=0, column=0, sticky="w")
        list_frame = tk.Frame(left)
        list_frame.grid(row=1, column=0, sticky="nsew", pady=(4, 6))
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        self.contacts_listbox = tk.Listbox(list_frame, exportselection=False)
        self.contacts_listbox.grid(row=0, column=0, sticky="nsew")
        scrollbar = tk.Scrollbar(list_frame, command=self.contacts_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.contacts_listbox.config(yscrollcommand=scrollbar.set)
        self.contacts_listbox.bind("<<ListboxSelect>>", self._on_chat_selected)

        tk.Button(
            left,
            text="Atualizar Contatos/Grupos",
            command=self._refresh_contacts_and_groups,
        ).grid(row=2, column=0, sticky="ew")

        # coluna central - área de chat
        center = tk.Frame(self.chat_frame)
        center.grid(row=0, column=1, sticky="nsew")
        center.rowconfigure(1, weight=1)

        self.chat_title_var = tk.StringVar(value="Nenhuma conversa selecionada")
        tk.Label(center, textvariable=self.chat_title_var, font=("Arial", 12, "bold")).grid(
            row=0, column=0, sticky="w"
        )

        chat_text_frame = tk.Frame(center)
        chat_text_frame.grid(row=1, column=0, sticky="nsew", pady=(6, 6))
        chat_text_frame.rowconfigure(0, weight=1)
        chat_text_frame.columnconfigure(0, weight=1)

        self.chat_text = tk.Text(chat_text_frame, state="disabled", wrap="word")
        self.chat_text.grid(row=0, column=0, sticky="nsew")
        chat_scroll = tk.Scrollbar(chat_text_frame, command=self.chat_text.yview)
        chat_scroll.grid(row=0, column=1, sticky="ns")
        self.chat_text.configure(yscrollcommand=chat_scroll.set)

        message_frame = tk.Frame(center)
        message_frame.grid(row=2, column=0, sticky="ew")
        message_frame.columnconfigure(0, weight=1)

        self.message_entry = tk.Entry(
            message_frame, textvariable=self.message_var, state="disabled"
        )
        self.message_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.send_button = tk.Button(
            message_frame, text="Enviar", command=self._send_message, state="disabled"
        )
        self.send_button.grid(row=0, column=1)

        self.send_file_button = tk.Button(
            center,
            text="Enviar Arquivo",
            command=self._send_file,
            state="disabled",
        )
        self.send_file_button.grid(row=3, column=0, sticky="ew")

        # coluna direita - ações adicionais
        right = tk.Frame(self.chat_frame)
        right.grid(row=0, column=2, sticky="ns")

        tk.Button(right, text="Adicionar Contato", command=self._open_add_contact_window).pack(
            fill="x", pady=4
        )
        tk.Button(right, text="Criar Grupo", command=self._open_create_group_window).pack(
            fill="x", pady=4
        )
        tk.Button(
            right, text="Listar Todos os Usuários", command=self._open_all_users_window
        ).pack(fill="x", pady=4)
        tk.Button(right, text="Logout", command=self._handle_logout).pack(
            fill="x", pady=4
        )

    # ------------------------------------------------------------------
    # Auxiliares gerais
    # ------------------------------------------------------------------
    def _set_status(self, message: str) -> None:
        self.status_var.set(message)

    def _show_login_frame(self) -> None:
        self.chat_frame.pack_forget()
        self.login_frame.pack(fill="both", expand=True)
        self.mode = "login"
        self._update_mode_widgets()
        self._set_status("Informe os dados de conexão e faça login.")

    def _show_chat_frame(self) -> None:
        self.login_frame.pack_forget()
        self.chat_frame.pack(fill="both", expand=True)
        self.message_var.set("")
        self.message_entry.configure(state="disabled")
        self.send_button.configure(state="disabled")
        self.send_file_button.configure(state="disabled")
        self.chat_title_var.set("Nenhuma conversa selecionada")
        self.current_item = None
        self.conversation_cache.clear()
        self._update_conversation_list()

    def _toggle_mode(self) -> None:
        self.mode = "register" if self.mode == "login" else "login"
        self._update_mode_widgets()

    def _update_mode_widgets(self) -> None:
        if self.mode == "register":
            self.name_label.grid(row=4, column=0, sticky="w")
            self.name_entry.grid(row=4, column=1, sticky="ew", pady=2)
            self.register_button.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(10, 2))
            self.login_button.grid_forget()
            self.toggle_button.configure(text="Já tenho uma conta")
        else:
            self.name_label.grid_forget()
            self.name_entry.grid_forget()
            self.login_button.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(10, 2))
            self.register_button.grid_forget()
            self.toggle_button.configure(text="Criar uma conta")

    def _ensure_client(self) -> Optional[Cliente]:
        server = self.server_var.get().strip() or "localhost"
        port_str = self.port_var.get().strip() or "8080"
        try:
            port = int(port_str)
        except ValueError:
            self._set_status("Porta inválida. Informe um número inteiro.")
            return None

        if self.cliente is None or self.client_params != (server, port):
            try:
                self.cliente = Cliente(server=server, port=port)
                self.client_params = (server, port)
                self._set_status("Conexão inicializada com sucesso.")
            except Exception as exc:
                self.cliente = None
                self.client_params = None
                self._set_status(f"Falha ao criar cliente: {exc}")
                return None
        return self.cliente

    @staticmethod
    def _parse_response(response: Optional[str]):
        try:
            if response is None:
                return None
            return json.loads(response)
        except (json.JSONDecodeError, TypeError):
            return response

    @staticmethod
    def _describe_response(data: Any) -> str:
        if isinstance(data, dict):
            status = data.get("status")
            if status == "success":
                return data.get("message") or "Operação realizada com sucesso."
            if status == "error":
                detail = data.get("detail")
                if detail:
                    return f"Erro: {data.get('error', 'desconhecido')} - {detail}"
                return f"Erro: {data.get('error', 'desconhecido')}"
            return json.dumps(data, ensure_ascii=False)
        if data is None:
            return "Sem resposta do servidor."
        return str(data)

    # ------------------------------------------------------------------
    # Login / Registro
    # ------------------------------------------------------------------
    def _perform_login(self) -> None:
        client = self._ensure_client()
        if client is None:
            return

        login = self.login_var.get().strip()
        senha = self.password_var.get().strip()
        if not login or not senha:
            self._set_status("Informe login e senha para continuar.")
            return

        resposta = client.login(login, senha)
        data = self._parse_response(resposta)
        self._set_status(self._describe_response(data))

        if isinstance(data, dict) and data.get("status") == "success":
            self.username = login
            self._show_chat_frame()
            self._refresh_contacts_and_groups()

    def _perform_register(self) -> None:
        client = self._ensure_client()
        if client is None:
            return

        nome = self.name_var.get().strip()
        login = self.login_var.get().strip()
        senha = self.password_var.get().strip()

        if not nome or not login or not senha:
            self._set_status("Informe nome, login e senha para registrar.")
            return

        resposta = client.registrar(nome, login, senha)
        data = self._parse_response(resposta)
        self._set_status(self._describe_response(data))
        if isinstance(data, dict) and data.get("status") == "success":
            self.mode = "login"
            self._update_mode_widgets()

    # ------------------------------------------------------------------
    # Contatos, grupos e conversas
    # ------------------------------------------------------------------
    def _refresh_contacts_and_groups(self) -> None:
        if not self.username or not self.cliente:
            return

        contatos_resp = self.cliente.listar_contatos(self.username)
        contatos_data = self._parse_response(contatos_resp)
        if isinstance(contatos_data, dict) and contatos_data.get("status") == "success":
            self.contacts_data = contatos_data.get("contatos", []) or []
            self._set_status(self._describe_response(contatos_data))
        else:
            self.contacts_data = []
            self._set_status(self._describe_response(contatos_data))

        grupos_resp = None
        try:
            grupos_resp = self.cliente.listar_grupos(self.username)
        except AttributeError:
            grupos_resp = None
        grupos_data = self._parse_response(grupos_resp)
        if isinstance(grupos_data, dict) and grupos_data.get("status") == "success":
            self.groups_data = grupos_data.get("grupos", []) or []
        else:
            self.groups_data = []

        self._update_conversation_list()

    def _update_conversation_list(self) -> None:
        selected_key = None
        if self.current_item:
            selected_key = self.current_item.get("history_key")

        items: List[Dict[str, Any]] = []

        for contato in self.contacts_data:
            login = contato.get("login") or contato.get("id")
            if not login:
                continue
            nome = contato.get("nome") or login
            key = str(login)
            items.append(
                {
                    "type": "contact",
                    "label": f"Contato: {nome} ({login})",
                    "target": login,
                    "history_key": key,
                }
            )

        for grupo in self.groups_data:
            gid = grupo.get("id") or grupo.get("id_grupo") or grupo.get("grupo_id")
            if gid is None:
                continue
            nome = grupo.get("nome") or f"Grupo {gid}"
            key = str(gid)
            items.append(
                {
                    "type": "group",
                    "label": f"Grupo: {nome} (ID {gid})",
                    "target": gid,
                    "history_key": key,
                }
            )

        existing_keys = {item["history_key"] for item in items}
        for conversa in list(historico_msgs):
            key = str(conversa.id)
            if key not in existing_keys:
                items.append(
                    {
                        "type": "historico",
                        "label": f"Conversa: {key}",
                        "target": conversa.id,
                        "history_key": key,
                    }
                )
                existing_keys.add(key)

        signature = [(item["type"], item["history_key"], item["label"]) for item in items]
        self.list_items = items
        if signature == self._list_signature:
            return
        self._list_signature = signature

        self.contacts_listbox.delete(0, tk.END)
        for item in items:
            self.contacts_listbox.insert(tk.END, item["label"])

        if selected_key:
            for index, item in enumerate(items):
                if item["history_key"] == selected_key:
                    self.contacts_listbox.selection_set(index)
                    self.contacts_listbox.see(index)
                    break

    def _on_chat_selected(self, _event=None) -> None:
        selection = self.contacts_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        if index >= len(self.list_items):
            return

        item = self.list_items[index]
        self.current_item = item
        self.chat_title_var.set(item["label"])
        self.message_entry.configure(state="normal")
        self.send_button.configure(state="normal")
        state_file = tk.NORMAL if item["type"] != "group" else tk.DISABLED
        self.send_file_button.configure(state=state_file)
        self._refresh_current_chat(force=True)

    def _get_messages_for_item(self, item: Dict[str, Any]) -> List[Any]:
        if not self.cliente:
            return []
        conv_id = item.get("target")
        mensagens = self.cliente.listar_mensagens(conv_id)
        if mensagens:
            return list(mensagens)
        key = str(conv_id)
        for conversa in list(historico_msgs):
            if str(conversa.id) == key:
                return list(conversa.mensagens)
        return []

    def _refresh_current_chat(self, force: bool = False) -> None:
        if not self.current_item:
            return
        key = self.current_item.get("history_key")
        messages = self._get_messages_for_item(self.current_item)
        count = len(messages)
        if not force and self.conversation_cache.get(key) == count:
            return
        self.conversation_cache[key] = count

        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.delete("1.0", tk.END)

        if not messages:
            self.chat_text.insert(tk.END, "Nenhuma mensagem nesta conversa.\n")
        else:
            for msg in messages:
                timestamp = getattr(msg, "datetime", "") or getattr(
                    msg, "datetime_envio", ""
                )
                sender = getattr(msg, "remetente", "?")
                sender_display = "Você" if sender == self.username else sender
                if getattr(msg, "tipo", "texto") == "arquivo" and isinstance(
                    getattr(msg, "conteudo", None), dict
                ):
                    info = msg.conteudo
                    filename = info.get("filename", "arquivo")
                    size = info.get("size")
                    size_info = f" ({size} bytes)" if size is not None else ""
                    content = f"[Arquivo] {filename}{size_info}"
                else:
                    content = getattr(msg, "conteudo", "")
                line = f"[{timestamp}] {sender_display}: {content}"
                self.chat_text.insert(tk.END, line + "\n")

        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)

    # ------------------------------------------------------------------
    # Envio de mensagens e arquivos
    # ------------------------------------------------------------------
    def _send_message(self) -> None:
        if not self.username or not self.current_item or not self.cliente:
            self._set_status("Selecione uma conversa para enviar mensagens.")
            return

        conteudo = self.message_var.get().strip()
        if not conteudo:
            self._set_status("Digite uma mensagem antes de enviar.")
            return

        target = self.current_item.get("target")
        try:
            if self.current_item.get("type") == "group":
                resposta = self.cliente.enviar_mensagem_grupo(
                    self.username, target, conteudo
                )
            else:
                resposta = self.cliente.enviar_mensagem(self.username, target, conteudo)
        except Exception as exc:
            self._set_status(f"Erro ao enviar mensagem: {exc}")
            return

        data = self._parse_response(resposta)
        self._set_status(self._describe_response(data))
        if isinstance(data, dict) and data.get("status") == "success":
            self.message_var.set("")
            self._refresh_current_chat(force=True)

    def _send_file(self) -> None:
        if not self.username or not self.current_item or not self.cliente:
            self._set_status("Selecione uma conversa para enviar arquivos.")
            return

        if self.current_item.get("type") == "group":
            self._set_status("Envio de arquivos para grupos não é suportado.")
            return

        caminho = filedialog.askopenfilename()
        if not caminho:
            return

        target = self.current_item.get("target")
        try:
            resposta = self.cliente.enviar_arquivo(self.username, target, caminho)
        except Exception as exc:
            self._set_status(f"Erro ao enviar arquivo: {exc}")
            return

        data = self._parse_response(resposta)
        self._set_status(self._describe_response(data))
        if isinstance(data, dict) and data.get("status") == "success":
            self._refresh_current_chat(force=True)

    # ------------------------------------------------------------------
    # Janelas auxiliares
    # ------------------------------------------------------------------
    def _open_add_contact_window(self) -> None:
        if not self.username or not self.cliente:
            self._set_status("Realize login para adicionar contatos.")
            return

        top = tk.Toplevel(self.master)
        top.title("Adicionar Contato")
        top.grab_set()

        login_var = tk.StringVar()
        nome_var = tk.StringVar()

        tk.Label(top, text="Login do contato:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        tk.Entry(top, textvariable=login_var).grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        tk.Label(top, text="Nome do contato:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        tk.Entry(top, textvariable=nome_var).grid(row=1, column=1, sticky="ew", padx=10, pady=5)

        tk.Button(
            top,
            text="Adicionar",
            command=lambda: self._submit_add_contact(top, login_var, nome_var),
        ).grid(row=2, column=0, columnspan=2, pady=10)

        top.columnconfigure(1, weight=1)

    def _submit_add_contact(
        self, window: tk.Toplevel, login_var: tk.StringVar, nome_var: tk.StringVar
    ) -> None:
        login = login_var.get().strip()
        nome = nome_var.get().strip()
        if not login or not nome:
            messagebox.showwarning("Adicionar contato", "Informe login e nome do contato.")
            return

        try:
            resposta = self.cliente.adicionar_contato(login, nome, self.username)
        except Exception as exc:
            self._set_status(f"Erro ao adicionar contato: {exc}")
            return

        data = self._parse_response(resposta)
        self._set_status(self._describe_response(data))
        if isinstance(data, dict) and data.get("status") == "success":
            window.destroy()
            self._refresh_contacts_and_groups()

    def _open_create_group_window(self) -> None:
        if not self.username or not self.cliente:
            self._set_status("Realize login para criar grupos.")
            return

        top = tk.Toplevel(self.master)
        top.title("Criar Grupo")
        top.grab_set()

        nome_var = tk.StringVar()
        participantes_var = tk.StringVar()

        tk.Label(top, text="Nome do grupo:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        tk.Entry(top, textvariable=nome_var).grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        tk.Label(
            top, text="Participantes (logins separados por vírgula):"
        ).grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        tk.Entry(top, textvariable=participantes_var).grid(
            row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=5
        )

        tk.Button(
            top,
            text="Criar",
            command=lambda: self._submit_create_group(top, nome_var, participantes_var),
        ).grid(row=3, column=0, columnspan=2, pady=10)

        top.columnconfigure(0, weight=1)
        top.columnconfigure(1, weight=1)

    def _submit_create_group(
        self, window: tk.Toplevel, nome_var: tk.StringVar, participantes_var: tk.StringVar
    ) -> None:
        nome = nome_var.get().strip()
        participantes_texto = participantes_var.get().strip()
        if not nome:
            messagebox.showwarning("Criar grupo", "Informe o nome do grupo.")
            return

        participantes = [p.strip() for p in participantes_texto.split(",") if p.strip()]
        if self.username not in participantes:
            participantes.append(self.username)

        try:
            resposta = self.cliente.criar_grupo(nome, participantes)
        except Exception as exc:
            self._set_status(f"Erro ao criar grupo: {exc}")
            return

        data = self._parse_response(resposta)
        self._set_status(self._describe_response(data))
        if isinstance(data, dict) and data.get("status") == "success":
            window.destroy()
            self._refresh_contacts_and_groups()

    def _open_all_users_window(self) -> None:
        if not self.cliente:
            self._set_status("Conecte-se ao servidor para listar usuários.")
            return

        try:
            resposta = self.cliente.listar_todos_usuarios()
        except Exception as exc:
            self._set_status(f"Erro ao listar usuários: {exc}")
            return

        data = self._parse_response(resposta)
        self._set_status(self._describe_response(data))

        top = tk.Toplevel(self.master)
        top.title("Usuários cadastrados")
        top.geometry("360x420")

        listbox = tk.Listbox(top)
        listbox.pack(fill="both", expand=True, padx=10, pady=10)

        if isinstance(data, dict) and data.get("status") == "success":
            usuarios = data.get("usuarios", [])
            if not usuarios:
                listbox.insert(tk.END, "Nenhum usuário encontrado.")
            else:
                for usuario in usuarios:
                    login = usuario.get("login", "")
                    nome = usuario.get("nome") or login or "Usuário"
                    status = usuario.get("status", "")
                    listbox.insert(tk.END, f"{nome} ({login}) - {status}")
        else:
            listbox.insert(tk.END, str(data))

    # ------------------------------------------------------------------
    # Logout e ciclo de atualização
    # ------------------------------------------------------------------
    def _handle_logout(self) -> None:
        if self.username and self.cliente:
            try:
                resposta = self.cliente.logout(self.username)
                data = self._parse_response(resposta)
                self._set_status(self._describe_response(data))
            except Exception as exc:
                self._set_status(f"Erro ao realizar logout: {exc}")

        self.username = None
        self.current_item = None
        self.contacts_data = []
        self.groups_data = []
        self.list_items = []
        self._list_signature = None
        self.conversation_cache.clear()
        self.message_var.set("")

        self.contacts_listbox.delete(0, tk.END)
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.delete("1.0", tk.END)
        self.chat_text.config(state=tk.DISABLED)

        self._show_login_frame()

    def _poll_messages(self) -> None:
        if self.username:
            self._update_conversation_list()
            self._refresh_current_chat()
        self.master.after(1000, self._poll_messages)

    def _on_close(self) -> None:
        if self.username and self.cliente:
            try:
                self.cliente.logout(self.username)
            except Exception:
                pass
        self.master.destroy()


def main() -> None:
    root = tk.Tk()
    ChatGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
