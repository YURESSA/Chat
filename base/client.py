import socket as sk
import _thread as th


class ChatClient:
    def __init__(self):
        self.socket = sk.socket()
        self.nickname = None

    @staticmethod
    def get_ip():
        s = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip

    def connect_to_server(self, ip, port):
        self.socket.connect((ip, port))
        print(f'Подключено к серверу {ip}:{port}')
        self.socket.send(self.nickname.encode())

    def listen_messages(self):
        try:
            while True:
                msg = self.socket.recv(1024).decode()
                if not msg:
                    break
                print(msg)
        except Exception as err:
            print(f'Ошибка получения сообщения: {err}')
        finally:
            self.socket.close()

    def send_messages(self):
        try:
            while True:
                msg = input('Введите сообщение: ')
                if msg == 'CLOSE':
                    self.socket.send('CLOSE'.encode())
                    break
                self.socket.send(msg.encode())
        except Exception as err:
            print(f'Ошибка отправки сообщения: {err}')
        finally:
            self.socket.close()

    def run(self):
        try:
            self.nickname = input('Введите ваш ник: ')
            ip = input('Введите ip сервера: ')
            port = int(input('Введите port сервера: '))
            print('Подключение...')
            self.connect_to_server(ip, port)
            th.start_new_thread(self.listen_messages, ())
            self.send_messages()
        except Exception as err:
            print(f'Ошибка клиента: {err}')
        finally:
            self.socket.close()


if __name__ == '__main__':
    client = ChatClient()
    client.run()
