import socket
import threading


class ChatServer:
    def __init__(self, host='', port=9090):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connections = {}  # {nickname: (address, socket)}
        self.groups = {}  # {group_name: {"owner": "nick", "members": [nick1, nick2, ...]}}

    @staticmethod
    def get_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip

    def update_clients_group_list(self):
        """Отправка обновленных списков групп всем подключенным клиентам."""
        group_names = list(self.groups.keys())
        for nickname, (_, conn) in self.connections.items():
            self.send_message(conn, f"update_groups {','.join(group_names)}")

    def update_clients_user_list(self):
        """Отправка обновленных списков пользователей всем подключенным клиентам."""
        user_names = list(self.connections.keys())
        for nickname, (_, conn) in self.connections.items():
            self.send_message(conn, f"update_users {','.join(user_names)}")

    def send_message(self, conn, message):
        """Универсальная отправка сообщения клиенту с обработкой ошибок."""
        try:
            conn.send(message.encode())
        except Exception as e:
            print(f"Ошибка отправки сообщения: {e}")

    def send_message_to_all(self, message, sender_nickname=None):
        """Отправка сообщения всем пользователям, кроме отправителя."""
        for nickname, (_, conn) in self.connections.items():
            if nickname != sender_nickname:
                self.send_message(conn, message)

    def send_private_message(self, recipient_nickname, msg, sender_nickname):
        """Отправка личного сообщения пользователю."""
        if recipient_nickname in self.connections:
            conn = self.connections[recipient_nickname][1]
            private_msg = f"[ЛС от {sender_nickname}]: {msg}"
            self.send_message(conn, private_msg)
        else:
            error_msg = f"Пользователь {recipient_nickname} не найден."
            self.send_message(self.connections[sender_nickname][1], error_msg)

    def handle_group_command(self, nickname, msg, conn):
        """Обработка команд группового чата."""
        parts = msg.split(" ", 2)
        command = parts[0]

        if command == "/help":
            self.send_message(conn, "Доступные команды:\n/help - Список доступных команд.\n/create_group <group_name> - Создать новую группу.\n/invite <group_name> <user_name> - Пригласить пользователя в группу.\n/leave_group <group_name> - Покинуть группу.\n/group_msg <group_name> <message> - Отправить сообщение в группу.\n/p <user_name> <message> - Отправить личное сообщение.")

        elif command == "/create_group":
            self.create_group(parts, conn, nickname)

        elif command == "/invite":
            self.invite_to_group(parts, conn, nickname)

        elif command == "/leave_group":
            self.leave_group(parts, conn, nickname)

        elif command == "/group_msg":
            self.group_message(parts, conn, nickname)

        elif command == "/users":
            user_list = "\n".join(self.connections.keys())
            self.send_message(conn, f"Подключённые пользователи:\n{user_list}")

    def create_group(self, parts, conn, nickname):
        """Создание новой группы."""
        if len(parts) < 2:
            self.send_message(conn, "Ошибка: укажите название группы.")
            return

        group_name = parts[1]
        if group_name in self.groups:
            self.send_message(conn, "Группа уже существует.")
        else:
            self.groups[group_name] = {"owner": nickname, "members": [nickname]}
            self.send_message(conn, f"Группа {group_name} создана.")
            self.update_clients_group_list()

    def invite_to_group(self, parts, conn, nickname):
        """Приглашение пользователя в группу."""
        if len(parts) < 3:
            self.send_message(conn, "Ошибка: укажите группу и пользователя. Пример: /invite group_name user")
            return

        group_name, new_member = parts[1], parts[2]
        if group_name not in self.groups:
            self.send_message(conn, "Группа не найдена.")
            return

        if self.groups[group_name]["owner"] != nickname:
            self.send_message(conn, "Вы не являетесь владельцем этой группы.")
            return

        if new_member not in self.connections:
            self.send_message(conn, f"Пользователь {new_member} не найден.")
            return

        if new_member in self.groups[group_name]["members"]:
            self.send_message(conn, f"{new_member} уже в группе.")
            return

        self.groups[group_name]["members"].append(new_member)
        self.update_clients_group_list()
        self.send_message(self.connections[new_member][1], f"Вы были приглашены в группу {group_name}.")
        self.send_message_to_all(f"{new_member} присоединился к группе {group_name}!", sender_nickname=new_member)

    def leave_group(self, parts, conn, nickname):
        """Покидание группы."""
        if len(parts) < 2:
            self.send_message(conn, "Ошибка: укажите название группы. Пример: /leave_group group_name")
            return

        group_name = parts[1]
        if group_name not in self.groups:
            self.send_message(conn, "Группа не найдена.")
            return

        if nickname not in self.groups[group_name]["members"]:
            self.send_message(conn, "Вы не состоите в этой группе.")
            return

        self.groups[group_name]["members"].remove(nickname)
        self.send_message_to_all(f"{nickname} покинул группу {group_name}.", sender_nickname=nickname)
        self.send_message(conn, f"Вы покинули группу {group_name}.")

    def group_message(self, parts, conn, nickname):
        """Отправка сообщения в группу."""
        if len(parts) < 3:
            self.send_message(conn, "Ошибка: укажите группу и сообщение. Пример: /group_msg group_name текст")
            return

        group_name, group_msg = parts[1], parts[2]
        if group_name in self.groups and nickname in self.groups[group_name]["members"]:
            for member in self.groups[group_name]["members"]:
                if member != nickname:
                    self.send_message(self.connections[member][1], f"[Группа {group_name} | {nickname}]: {group_msg}")
        else:
            self.send_message(conn, "Вы не состоите в этой группе.")

    def handle_connection(self, conn, addr):
        """Обработка подключения клиента."""
        nickname = None
        try:
            nickname = conn.recv(1024).decode()

            if not nickname or nickname in self.connections:
                self.send_message(conn, 'Никнейм занят или некорректен.')
                conn.close()
                return

            self.connections[nickname] = (addr, conn)
            welcome_msg = f'--- {nickname} присоединился к чату! ---'
            self.update_clients_user_list()
            self.send_message_to_all(message=welcome_msg, sender_nickname=nickname)

            while True:
                msg = conn.recv(1024).decode()
                if msg == 'CLOSE':
                    leave_msg = f'--- {nickname} покинул чат ---'
                    print(f'Соединение приостановлено: {conn}, {addr}')
                    if nickname in self.connections:
                        del self.connections[nickname]
                    self.send_message_to_all(message=leave_msg, sender_nickname=nickname)
                    break

                elif msg.startswith("/p "):
                    parts = msg.split(' ', 2)
                    if len(parts) < 3:
                        self.send_message(conn, 'Формат: /p ник_пользователя сообщение')
                    else:
                        recipient, private_msg = parts[1], parts[2]
                        self.send_private_message(recipient, private_msg, nickname)

                elif msg.startswith("/"):
                    self.handle_group_command(nickname, msg, conn)
                else:
                    result_msg = f'[{nickname}] {msg}'
                    self.send_message_to_all(message=result_msg, sender_nickname=nickname)
        except Exception as e:
            print(f'Ошибка с клиентом {addr}: {e}')
        finally:
            conn.close()
            if nickname and nickname in self.connections:
                del self.connections[nickname]

    def run(self):
        """Запуск сервера."""
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen()
            print(f'Сервер запущен на {self.get_ip()}:{self.port}')
            while True:
                conn, addr = self.socket.accept()
                print(f'Соединение установлено: {conn}, {addr}')
                threading.Thread(target=self.handle_connection, args=(conn, addr)).start()
        except Exception as err:
            print(f'Error: {err}')
        finally:
            self.socket.close()


if __name__ == '__main__':
    server = ChatServer()
    server.run()
