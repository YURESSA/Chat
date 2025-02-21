import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog

import requests

base_url = "http://localhost:5000"


class ChatClient:
    def __init__(self):
        self.is_group_selected = False
        self.selected_recipient = None
        self.groups = []  # Список групп
        self.users = []  # Список пользователей
        self.message_history = []  # Хранение истории сообщений
        self.history_index = -1
        self.root = tk.Tk()
        self.root.title("Чат-клиент")
        self.root.geometry("330x230")
        self.root.configure(bg="#2c3e50")

        self.server_ip = tk.StringVar()
        self.server_port = tk.StringVar()
        self.nickname = tk.StringVar()
        self.previous_nicknames = []

        self.socket = None
        self.is_connected = False

        self.create_main_menu()
        self.root.mainloop()

    @staticmethod
    def get_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip

    def create_main_menu(self):
        """Создаёт главное меню с вводом IP, порта и ника."""
        frame = tk.Frame(self.root, bg="#34495e", padx=20, pady=20)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        tk.Label(frame, text="IP сервера:", fg="#ecf0f1", bg="#34495e").grid(row=0, column=0, sticky="w", pady=5)
        ip_entry = tk.Entry(frame, textvariable=self.server_ip, font=("Arial", 12), bd=2, relief="solid")
        ip_entry.grid(row=0, column=1, sticky="ew", pady=10)

        tk.Label(frame, text="Порт сервера:", fg="#ecf0f1", bg="#34495e").grid(row=1, column=0, sticky="w", pady=5)
        port_entry = tk.Entry(frame, textvariable=self.server_port, font=("Arial", 12), bd=2, relief="solid")
        port_entry.grid(row=1, column=1, sticky="ew", pady=10)

        connect_button = tk.Button(frame, text="Подключиться", command=self.request_nicknames, font=("Arial", 14),
                                   bg="#1abc9c", fg="#fff", relief="raised", bd=5)
        connect_button.grid(row=2, column=0, columnspan=2, pady=20)

    def request_nicknames(self):
        ip = self.server_ip.get()
        port = self.server_port.get()
        if not ip or not port:
            messagebox.showwarning("Ошибка", "Введите IP и порт!")
            return

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((ip, int(port)))
            response = self.socket.recv(1024).decode()

            if response.startswith("/last_nicknames:"):
                # self.previous_nicknames = response.replace('/last_nicknames: ', '')
                # self.previous_nicknames = self.previous_nicknames.split(', ')
                response = requests.get(f"{base_url}/last_nicknames", params={'ip_address': self.get_ip()})
                if response.status_code == 200:
                    data = response.json()
                    self.previous_nicknames = data.get("last_nicknames", []).split(', ')
            else:
                self.previous_nicknames = []

            self.show_nickname_selection()
        except Exception as e:
            messagebox.showerror("Ошибка подключения", f"Не удалось подключиться к серверу: {e}")

    def show_nickname_selection(self):
        self.root.destroy()
        self.root = tk.Tk()
        self.root.title("Выбор ника")
        self.root.geometry("405x425")
        self.root.configure(bg="#2c3e50")

        # Настройка сетки для адаптивного размещения элементов
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        frame = tk.Frame(self.root, bg="#34495e", padx=20, pady=20)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Адаптивность внутри фрейма
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        tk.Label(frame, text="Выберите ник, который вы использовали, или введите новый:", fg="#ecf0f1",
                 bg="#34495e", wraplength=350, justify="center").grid(row=0, column=0, columnspan=2, pady=5, sticky="n")

        self.nick_listbox = tk.Listbox(frame, font=("Arial", 12), bd=2, relief="solid")
        self.nick_listbox.grid(row=1, column=0, columnspan=2, pady=5, sticky="nsew")

        for nick in self.previous_nicknames:
            self.nick_listbox.insert(tk.END, nick)
        self.nick_listbox.bind("<<ListboxSelect>>", self.on_nickname_selected)

        self.nickname = tk.StringVar()  # Добавляем переменную для хранения ника

        self.nick_entry = tk.Entry(frame, textvariable=self.nickname, font=("Arial", 12), bd=5, relief="solid")
        self.nick_entry.grid(row=2, column=0, columnspan=2, pady=10, sticky="ew")

        select_button = tk.Button(frame, text="Выбрать ник", command=self.select_nickname, font=("Arial", 14),
                                  bg="#1abc9c", fg="#fff", relief="raised", bd=5)
        select_button.grid(row=3, column=0, columnspan=2, pady=20, sticky="ew")

        # Применяем адаптивность к фрейму
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_rowconfigure(2, weight=0)
        frame.grid_rowconfigure(3, weight=0)
        frame.grid_columnconfigure(0, weight=1)

    def on_nickname_selected(self, event):
        """ Обработчик выбора ника из списка """
        selected_index = self.nick_listbox.curselection()
        if selected_index:
            selected_nick = self.nick_listbox.get(selected_index)
            self.nickname.set(selected_nick)

    def select_nickname(self):
        """Отправляет выбранный ник серверу."""
        nickname = self.nick_entry.get()
        if not nickname:
            nickname = self.nickname.get()
        self.nickname = nickname
        if not nickname:
            messagebox.showwarning("Ошибка", "Введите ник!")
            return
        try:
            self.socket.send(nickname.encode())
            self.is_connected = True

            self.root.destroy()
            self.open_chat_window()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось отправить ник: {e}")

    def open_chat_window(self):
        """Создаёт окно чата после успешного подключения."""
        self.chat_window = tk.Tk()
        self.chat_window.title("Чат")
        self.chat_window.geometry("970x510")
        self.chat_window.configure(bg="#2c3e50")

        # Общее окно
        main_frame = tk.Frame(self.chat_window, bg="#34495e")
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Текстовая область для чата
        self.text_area = scrolledtext.ScrolledText(main_frame, state="disabled", wrap="word", font=("Arial", 12),
                                                   bg="#34495e", fg="#ecf0f1", bd=2, relief="solid")
        self.text_area.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Панель для ввода сообщения
        input_frame = tk.Frame(main_frame, bg="#34495e")
        input_frame.grid(row=1, column=0, sticky="ew", pady=5)

        self.recipient_label = tk.Label(input_frame, text="Общий чат", fg="#ecf0f1", bg="#34495e",
                                        font=("Arial", 12))
        self.recipient_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        self.entry_msg = tk.Entry(input_frame, font=("Arial", 12), bd=2, relief="solid")
        self.entry_msg.grid(row=0, column=1, sticky="ew", padx=5)

        send_button = tk.Button(input_frame, text="Отправить", command=self.send_message, font=("Arial", 12),
                                bg="#1abc9c", fg="#fff", relief="raised", bd=5)
        send_button.grid(row=0, column=2, padx=5)

        self.entry_msg.bind("<Return>", self.on_enter_pressed)

        # Правая панель с пользователями и группами
        right_frame = tk.Frame(self.chat_window, bg="#34495e", width=200, height=500)
        right_frame.grid(row=0, column=1, rowspan=2, sticky="nse", padx=10, pady=10)

        # Список групп
        self.group_label = tk.Label(right_frame, text="Группы", fg="#ecf0f1", bg="#34495e", font=("Arial", 12))
        self.group_label.grid(row=0, column=0, sticky="w", pady=5)

        self.group_listbox = tk.Listbox(right_frame, height=6, font=("Arial", 12), bd=2, relief="solid")
        self.group_listbox.grid(row=1, column=0, pady=5, sticky="nsew")
        self.group_listbox.bind("<ButtonRelease-1>", self.on_group_selected)

        # Список пользователей
        self.user_label = tk.Label(right_frame, text="Пользователи", fg="#ecf0f1", bg="#34495e", font=("Arial", 12))
        self.user_label.grid(row=2, column=0, sticky="w", pady=5)

        self.user_listbox = tk.Listbox(right_frame, height=6, font=("Arial", 12), bd=2, relief="solid")
        self.user_listbox.grid(row=3, column=0, pady=5, sticky="nsew")
        self.user_listbox.bind("<ButtonRelease-1>", self.on_user_selected)

        create_group_button = tk.Button(
            right_frame, text="Создать группу", font=("Arial", 12),
            bg="#3498db", fg="#fff", relief="raised", bd=5,
            command=self.create_group
        )
        create_group_button.grid(row=4, column=0, pady=5)
        invite_button = tk.Button(
            right_frame, text="Пригласить в группу", font=("Arial", 12),
            bg="#f39c12", fg="#fff", relief="raised", bd=5,
            command=self.invite_to_group
        )
        invite_button.grid(row=5, column=0, pady=5)

        self.entry_msg.bind("<Up>", self.navigate_history_up)
        self.entry_msg.bind("<Down>", self.navigate_history_down)
        self.chat_window.protocol("WM_DELETE_WINDOW", self.on_closing)
        # Настройка растяжения колонок и строк
        self.chat_window.grid_rowconfigure(0, weight=1)
        self.chat_window.grid_columnconfigure(0, weight=1)
        self.chat_window.grid_columnconfigure(1, weight=0)
        threading.Thread(target=self.listen_for_messages, daemon=True).start()
        self.chat_window.mainloop()

    def on_closing(self):
        """Обработчик закрытия окна."""
        if self.is_connected:
            try:
                self.socket.send("CLOSE".encode())
            except Exception as e:
                print(f"Ошибка при отправке CLOSE: {e}")
            finally:
                self.socket.close()
                self.is_connected = False
        self.chat_window.destroy()

    def navigate_history_up(self, event):
        """Перемещение по истории сообщений вверх (стрелка вверх)."""
        if self.message_history and self.history_index > 0:
            self.history_index -= 1
            self.entry_msg.delete(0, tk.END)
            self.entry_msg.insert(0, self.message_history[self.history_index])

    def navigate_history_down(self, event):
        """Перемещение по истории сообщений вниз (стрелка вниз)."""
        if self.message_history and self.history_index < len(self.message_history) - 1:
            self.history_index += 1
            self.entry_msg.delete(0, tk.END)
            self.entry_msg.insert(0, self.message_history[self.history_index])
        else:
            self.entry_msg.delete(0, tk.END)

    def create_group(self):
        """Создаёт новую группу."""
        group_name = simpledialog.askstring("Создание группы", "Введите название группы:")
        if group_name:
            try:
                self.socket.send(f"/create_group {group_name}".encode())
            except:
                messagebox.showerror("Ошибка", "Не удалось отправить запрос на сервер.")

    def invite_to_group(self):
        """Приглашает пользователя в выбранную группу."""
        if not self.groups:
            messagebox.showwarning("Ошибка", "Список групп пуст.")
            return

        if not self.users:
            messagebox.showwarning("Ошибка", "Список пользователей пуст.")
            return

        # Создание окна для ввода группы и пользователя
        def on_submit():
            group_name = group_entry.get()
            user_name = user_entry.get()

            if not group_name or group_name not in self.groups:
                messagebox.showwarning("Ошибка", "Группа не найдена.")
                return

            if not user_name or user_name not in self.users:
                messagebox.showwarning("Ошибка", "Пользователь не найден.")
                return

            try:
                self.socket.send(f"/invite {group_name} {user_name}".encode())
                messagebox.showinfo("Приглашение", f"{user_name} приглашён в {group_name}.")
                invite_window.destroy()  # Закрываем окно после успешного приглашения
            except:
                messagebox.showerror("Ошибка", "Не удалось отправить приглашение.")
                invite_window.destroy()  # Закрываем окно при ошибке

        invite_window = tk.Toplevel()  # Создаем новое окно
        invite_window.title("Приглашение в группу")

        tk.Label(invite_window, text="Введите название группы:").pack(pady=5)
        group_entry = tk.Entry(invite_window)
        group_entry.pack(pady=5)

        tk.Label(invite_window, text="Введите имя пользователя:").pack(pady=5)
        user_entry = tk.Entry(invite_window)
        user_entry.pack(pady=5)

        submit_button = tk.Button(invite_window, text="Пригласить", command=on_submit)
        submit_button.pack(pady=10)

        invite_window.mainloop()

    def on_group_selected(self, event):
        """Обработчик выбора группы для отправки сообщения."""
        selected_group = self.group_listbox.get(self.group_listbox.curselection())
        if self.selected_recipient == selected_group:
            self.selected_recipient = None
            self.is_group_selected = False
            self.recipient_label.config(text="Общий чат")
        else:
            self.selected_recipient = selected_group
            self.is_group_selected = True
            self.recipient_label.config(text=f"Выбрана группа: {self.selected_recipient}")

    def on_user_selected(self, event):
        """Обработчик выбора пользователя для отправки сообщения."""
        selected_user = self.user_listbox.get(self.user_listbox.curselection())
        if self.selected_recipient == selected_user:
            self.selected_recipient = None
            self.is_group_selected = False
            self.recipient_label.config(text="Общий чат")
        else:
            self.selected_recipient = selected_user
            self.is_group_selected = False
            self.recipient_label.config(text=f"Выбран адресат: {self.selected_recipient}")

    def send_message(self):
        """Отправляет сообщение на сервер и отображает его локально."""
        msg = self.entry_msg.get().strip()
        if msg:
            self.message_history.append(msg)
            self.history_index = len(self.message_history)
            if self.selected_recipient:
                if self.is_group_selected:
                    msg = f"/group_msg {self.selected_recipient} {msg}"
                else:
                    msg = f"/p {self.selected_recipient} {msg}"
            try:
                self.socket.send(msg.encode())
                if self.selected_recipient:
                    parts = msg.split(" ", 2)

                    if self.is_group_selected:

                        msg = f"[Группа {self.selected_recipient} | Вы]: {parts[2]}"
                    else:
                        msg = f"[ЛС для {self.selected_recipient}]: {parts[2]}"
                else:
                    msg = f"Вы: {msg}"
                self.display_message(msg)

                self.entry_msg.delete(0, tk.END)
            except:
                messagebox.showerror("Ошибка", "Соединение с сервером потеряно.")

    def on_enter_pressed(self, event):
        """Обработчик нажатия клавиши Enter."""
        self.send_message()

    def listen_for_messages(self):
        """Слушает входящие сообщения от сервера."""
        while self.is_connected:
            try:
                msg = self.socket.recv(1024).decode()
                if not msg:
                    break

                if msg.startswith("update_groups"):
                    # groups = msg.split(" ", 1)[1].split(",")
                    response = requests.get(f"{base_url}/update_groups", params={'nickname': self.nickname})
                    if response.status_code == 200:
                        data = response.json()
                        groups = data.get("update_groups", [])
                        self.update_group_list(groups)

                elif msg.startswith("update_users"):
                    # users = msg.split(" ", 1)[1].split(",")
                    response = requests.get(f"{base_url}/update_users", params={'nickname': self.nickname})
                    if response.status_code == 200:
                        data = response.json()
                        users = data.get("update_users", [])
                        self.update_user_list(users)

                else:
                    self.display_message(msg)
            except:
                self.is_connected = False
                self.socket.close()
                break

    def display_message(self, msg):
        """Выводит сообщение в чат."""
        self.text_area.config(state="normal")
        self.text_area.insert(tk.END, msg + "\n")
        self.text_area.config(state="disabled")
        self.text_area.yview(tk.END)

    def update_group_list(self, groups):
        """Обновляет список групп на клиенте."""
        self.groups = groups
        self.group_listbox.delete(0, tk.END)
        for group in self.groups:
            self.group_listbox.insert(tk.END, group)

    def update_user_list(self, users):
        """Обновляет список пользователей."""
        self.users = users
        self.user_listbox.delete(0, tk.END)
        for user in self.users:
            self.user_listbox.insert(tk.END, user)

    def start(self):
        """Запуск клиента."""
        self.socket.connect((self.host, self.port))
        print(f"Подключено к серверу {self.host}:{self.port}")

        # Ввод никнейма
        while not self.nickname:
            self.nickname = input("Введите никнейм: ")
            self.socket.send(self.nickname.encode())
            response = self.socket.recv(1024).decode()
            if "занят" in response:
                print(response)
                self.nickname = None
            else:
                print("Вы вошли в чат.")

        receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
        receive_thread.start()

        self.send_message()


if __name__ == "__main__":
    ChatClient()
