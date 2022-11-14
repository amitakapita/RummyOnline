import hashlib
import library_protocol
import socket
import threading
import tkinter as tk
import traceback
from library_protocol import client_commands, server_commands

class Client(object):
    def __init__(self, ip1, port1):
        self.ip = ip1
        self.port = port1
        self.login_try_counts = 0
        self.current_lobby = "login"

        self.root = tk.Tk()
        self.root.title("RummyOnline")
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="#2596be")

        self.lbl_welcome = tk.Label(self.root, text="Welcome to RummyOnline", font="Arial 17", bg="#2596be")
        self.enter_name = tk.Label(self.root, text="Please enter your Username:", font="Arial 14", bg="#2596be")
        self.entry_username = tk.Entry(self.root, font="Arial 13", bg="DeepSkyBlue2")
        self.enter_password = tk.Label(self.root, text="Please enter your Password:", font="Arial 14", bg="#2596be")
        self.entry_password = tk.Entry(self.root, font="Arial 13", bg="DeepSkyBlue2", show="*")
        self.login_btn = tk.Button(self.root, text="login", relief="solid", activebackground="DeepSkyBlue3",
                                   bg="DeepSkyBlue2", font="Arial 14")
        self.lbl1_message = tk.Label(self.root, bg="#2596be", font="Arial 14")

        self.username = ""
        self.password = ""

    def start(self):
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.ip, self.port))

            receive_connection_thread = threading.Thread(target=self.receive_messages, args=(client_socket,))
            receive_connection_thread.daemon = True
            receive_connection_thread.start()

            self.login_btn["command"] = lambda: self.check_in(client_socket)

            self.login_lobby()
            self.root.mainloop()
        except socket.error as e:
            print(e)

    def receive_messages(self, conn):
        try:
            while True:
                data = conn.recv(1024).decode()
                self.handle_received_connection(conn, data)
        except ConnectionError:
            print(traceback.format_exc())  #
            print("you have disconnected from the main server.")

    def send_messages(self, conn, data, msg=""):
        message = library_protocol.build_message(data, msg)
        print(f"[Client] {message}\n--------------------------------\n")
        conn.sendall(message.encode())

    def handle_received_connection(self, conn, data):
        print(f"[Server] {data}")
        cmd, msg = library_protocol.disassemble_message(data)
        if cmd == server_commands["login_ok_cmd"]:
            pass
        elif cmd == server_commands["login_failed_cmd"]:
            self.lbl1_message["text"] = "login has failed."

    def login_lobby(self):
        self.lbl_welcome.pack(pady=50)
        self.enter_name.pack(pady=20)
        self.entry_username.pack()
        self.enter_password.pack(pady=5)
        self.entry_password.pack(pady=2)
        self.lbl1_message.pack(pady=1)
        self.login_btn.pack(pady=3)

    def check_in(self, conn):
        self.username, self.password = (self.entry_username.get(), self.entry_password.get())
        print(self.password)
        if self.username == "":
            self.lbl1_message["text"] = "the username isn't empty"
            print("the username isn't empty")
        elif self.password == "":
            self.lbl1_message["text"] = "the password isn't empty"
            print("the password isn't empty")
        elif not library_protocol.check_username_validation(self.username):
            self.lbl1_message["text"] = "the syntax of the username is not valid"
            print("the syntax of the username is not valid")
        else:
            data, msg = library_protocol.client_commands["login_cmd"], "%s#%s" % (
                self.username, hashlib.sha256(self.password.encode()).hexdigest())
            self.send_messages(conn, data, msg)


if __name__ == "__main__":
    ip = "127.0.0.1"
    port = 34254
    client = Client(ip, port)
    client.start()
