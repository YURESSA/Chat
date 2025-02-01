import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox


class ChatClient:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Чат-клиент")
        self.root.geometry("350x320")
        self.root.configure(bg="#2c3e50")

        self.server_ip = tk.StringVar()
        self.server_port = tk.StringVar()
        self.nickname = tk.StringVar()

        self.socket = None
        self.is_connected = False

        self.create_main_menu()
        self.root.mainloop()

    def create_main_menu(self):
        """Создаёт главное меню с вводом IP, порта и ника."""
        frame = tk.Frame(self.root, padx=20, pady=20, bg="#34495e")
        frame.pack(expand=True, fill="both")

        tk.Label(frame, text="IP сервера:", fg="#ecf0f1", bg="#34495e").pack(anchor="w")
        ip_entry = tk.Entry(frame, textvariable=self.server_ip, font=("Arial", 12), bd=2, relief="solid")
        ip_entry.pack(fill="x", pady=10)
        self.enable_paste(ip_entry)

        tk.Label(frame, text="Порт сервера:", fg="#ecf0f1", bg="#34495e").pack(anchor="w")
        port_entry = tk.Entry(frame, textvariable=self.server_port, font=("Arial", 12), bd=2, relief="solid")
        port_entry.pack(fill="x", pady=10)
        self.enable_paste(port_entry)

        tk.Label(frame, text="Ваш ник:", fg="#ecf0f1", bg="#34495e").pack(anchor="w")
        nick_entry = tk.Entry(frame, textvariable=self.nickname, font=("Arial", 12), bd=2, relief="solid")
        nick_entry.pack(fill="x", pady=10)
        self.enable_paste(nick_entry)

        connect_button = tk.Button(frame, text="Подключиться", command=self.connect_to_server, font=("Arial", 14),
                                   bg="#1abc9c", fg="#fff", relief="raised", bd=5)
        connect_button.pack(pady=20, fill="x", ipadx=10)

    def enable_paste(self, entry):
        entry.bind("<Control-v>", self.paste)
        entry.bind("<Command-v>", self.paste)

    def paste(self, event):
        """Функция вставки из буфера обмена."""
        widget = event.widget
        try:
            widget.insert(tk.INSERT, widget.clipboard_get())
        except tk.TclError:
            pass
        return "break"

    def connect_to_server(self):
        """Подключается к серверу."""
        ip = self.server_ip.get()
        port = self.server_port.get()
        nickname = self.nickname.get()

        if not ip or not port or not nickname:
            messagebox.showwarning("Ошибка", "Все поля должны быть заполнены!")
            return

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((ip, int(port)))
            self.socket.send(nickname.encode())
            self.is_connected = True

            self.root.destroy()
            self.open_chat_window()

        except Exception as e:
            messagebox.showerror("Ошибка подключения", f"Не удалось подключиться к серверу: {e}")

    def open_chat_window(self):
        """Создаёт окно чата после успешного подключения."""
        self.chat_window = tk.Tk()
        self.chat_window.title("Чат")
        self.chat_window.geometry("500x550")
        self.chat_window.configure(bg="#2c3e50")

        self.text_area = scrolledtext.ScrolledText(self.chat_window, state="disabled", wrap="word", font=("Arial", 12),
                                                   bg="#34495e", fg="#ecf0f1", bd=2, relief="solid")
        self.text_area.pack(padx=10, pady=10, fill="both", expand=True)

        frame = tk.Frame(self.chat_window, bg="#34495e")
        frame.pack(fill="x", padx=10, pady=5)

        self.entry_msg = tk.Entry(frame, font=("Arial", 12), bd=2, relief="solid")
        self.entry_msg.pack(side="left", fill="x", expand=True, padx=5)

        send_button = tk.Button(frame, text="Отправить", command=self.send_message, font=("Arial", 12), bg="#1abc9c",
                                fg="#fff", relief="raised", bd=5)
        send_button.pack(side="right")
        self.entry_msg.bind("<Return>", self.on_enter_pressed)

        threading.Thread(target=self.listen_for_messages, daemon=True).start()

        self.chat_window.mainloop()

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
                self.display_message(msg)
            except:
                self.is_connected = False
                self.socket.close()
                break

    def send_message(self):
        """Отправляет сообщение на сервер и отображает его локально."""
        msg = self.entry_msg.get().strip()
        if msg:
            try:
                self.socket.send(msg.encode())
                self.display_message(f"Вы: {msg}")
                self.entry_msg.delete(0, tk.END)
            except:
                messagebox.showerror("Ошибка", "Соединение с сервером потеряно.")

    def display_message(self, msg):
        """Выводит сообщение в чат."""
        self.text_area.config(state="normal")
        self.text_area.insert(tk.END, msg + "\n")
        self.text_area.config(state="disabled")
        self.text_area.yview(tk.END)


if __name__ == "__main__":
    ChatClient()
