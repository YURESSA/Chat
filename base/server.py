import socket
import threading


class ChatServer:
    def __init__(self, host='', port=9091):
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

    def send_message_to_all(self, message, sender_nickname=None):
        """Отправка сообщения всем пользователям, кроме отправителя."""
        for nickname, (_, conn) in self.connections.items():
            if nickname != sender_nickname:
                try:
                    conn.send(message.encode())
                except Exception as e:
                    print(f"Ошибка отправки сообщения {nickname}: {e}")

    def send_private_message(self, recipient_nickname, msg, sender_nickname):
        """Отправка личного сообщения пользователю."""
        if recipient_nickname in self.connections:
            conn = self.connections[recipient_nickname][1]
            private_msg = f"[ЛС от {sender_nickname}]: {msg}"
            conn.send(private_msg.encode())
        else:
            error_msg = f"Пользователь {recipient_nickname} не найден."
            self.connections[sender_nickname][1].send(error_msg.encode())

    def handle_group_command(self, nickname, msg, conn):
        """Обработка команд группового чата."""
        parts = msg.split(" ", 2)
        command = parts[0]

        if command == "/help":
            help_message = (
                "Доступные команды:\n"
                "/help - Список доступных команд.\n"
                "/create_group <group_name> - Создать новую группу.\n"
                "/invite <group_name> <user_name> - Пригласить пользователя в группу.\n"
                "/leave_group <group_name> - Покинуть группу.\n"
                "/group_msg <group_name> <message> - Отправить сообщение в группу.\n"
                "/p <user_name> <message> - Отправить личное сообщение.\n"
            )
            conn.send(help_message.encode())

        elif command == "/create_group":
            self.create_group(parts, conn, nickname)

        elif command == "/invite":
            self.invite_to_group(parts, conn, nickname)

        elif command == "/leave_group":
            self.leave_group(parts, conn, nickname)

        elif command == "/group_msg":
            self.group_message(parts, conn, nickname)

    def create_group(self, parts, conn, nickname):
        """Создание новой группы."""
        if len(parts) < 2:
            conn.send("Ошибка: укажите название группы.".encode())
            return

        group_name = parts[1]
        if group_name in self.groups:
            conn.send("Группа уже существует.".encode())
        else:
            self.groups[group_name] = {"owner": nickname, "members": [nickname]}
            conn.send(f"Группа {group_name} создана.".encode())

    def invite_to_group(self, parts, conn, nickname):
        """Приглашение пользователя в группу."""
        if len(parts) < 3:
            conn.send("Ошибка: укажите группу и пользователя. Пример: /invite group_name user".encode())
            return

        group_name, new_member = parts[1], parts[2]
        if group_name not in self.groups:
            conn.send("Группа не найдена.".encode())
            return

        if self.groups[group_name]["owner"] != nickname:
            conn.send("Вы не являетесь владельцем этой группы.".encode())
            return

        if new_member not in self.connections:
            conn.send(f"Пользователь {new_member} не найден.".encode())
            return

        if new_member in self.groups[group_name]["members"]:
            conn.send(f"{new_member} уже в группе.".encode())
            return

        self.groups[group_name]["members"].append(new_member)
        self.connections[new_member][1].send(f"Вы были приглашены в группу {group_name}.".encode())

        join_msg = f"{new_member} присоединился к группе {group_name}!"
        for member in self.groups[group_name]["members"]:
            if member in self.connections:
                self.connections[member][1].send(join_msg.encode())

    def leave_group(self, parts, conn, nickname):
        """Покидание группы."""
        if len(parts) < 2:
            conn.send("Ошибка: укажите название группы. Пример: /leave_group group_name".encode())
            return

        group_name = parts[1]

        if group_name not in self.groups:
            conn.send("Группа не найдена.".encode())
            return

        if nickname not in self.groups[group_name]["members"]:
            conn.send("Вы не состоите в этой группе.".encode())
            return

        self.groups[group_name]["members"].remove(nickname)
        leave_msg = f"{nickname} покинул группу {group_name}."
        for member in self.groups[group_name]["members"]:
            if member in self.connections:
                self.connections[member][1].send(leave_msg.encode())

        conn.send(f"Вы покинули группу {group_name}.".encode())

    def group_message(self, parts, conn, nickname):
        """Отправка сообщения в группу."""
        if len(parts) < 3:
            conn.send("Ошибка: укажите группу и сообщение. Пример: /group_msg group_name текст".encode())
            return

        group_name, group_msg = parts[1], parts[2]
        if group_name in self.groups and nickname in self.groups[group_name]["members"]:
            for member in self.groups[group_name]["members"]:
                if member != nickname:
                    self.connections[member][1].send(f"[Группа {group_name} | {nickname}]: {group_msg}".encode())
        else:
            conn.send("Вы не состоите в этой группе.".encode())

    def handle_connection(self, conn, addr):
        """Обработка подключения клиента."""
        try:
            nickname = conn.recv(1024).decode()

            if not nickname or nickname in self.connections:
                conn.send('Никнейм занят или некорректен.'.encode())
                conn.close()
                return

            self.connections[nickname] = (addr, conn)
            welcome_msg = f'--- {nickname} присоединился к чату! ---'
            self.send_message_to_all(message=welcome_msg, sender_nickname=nickname)

            while True:
                msg = conn.recv(1024).decode()
                if msg == 'CLOSE':
                    leave_msg = f'--- {nickname} покинул чат ---'
                    print(f'Соединение приостановлено: {conn}, {addr}')
                    self.send_message_to_all(message=leave_msg, sender_nickname=nickname)
                    break

                elif msg.startswith("/p "):
                    parts = msg.split(' ', 2)
                    if len(parts) < 3:
                        conn.send('Формат: /p ник_пользователя сообщение'.encode())
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
            if nickname in self.connections:
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
