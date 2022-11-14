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
        self.create_account = tk.Label(self.root, bg="#2596be", font="Arial 14",
                                       text="Don't have an account? Sign up if you want:")
        self.create_account_btn = tk.Button(self.root, text="SignUp", relief="solid", activebackground="DeepSkyBlue3",
                                            bg="DeepSkyBlue2", font="Arial 14")

        self.username = ""
        self.password = ""
        self.confirmed_password = ""

        # register menu
        self.title = tk.Label(self.root, text="Register an account", font="Arial 15", bg="#2596be")
        self.register_account_btn = tk.Button(self.root, text="Register", relief="solid",
                                              activebackground="DeepSkyBlue3", bg="DeepSkyBlue2", font="Arial 14")
        self.enter_name1 = tk.Label(self.root, text="New Username: ", font="Arial 14", bg="#2596be")
        self.enter_name_input = tk.Entry(self.root, font="Arial 13", bg="DeepSkyBlue2")
        self.enter_password1 = tk.Label(self.root, text="Password: ", font="Arial 14", bg="#2596be")
        self.enter_password_input = tk.Entry(self.root, font="Arial 13", show="*", bg="DeepSkyBlue2")
        self.confirm_password_enter = tk.Label(self.root, text="Password confirm: ", font="Arial 13", bg="#2596be")
        self.confirm_password_input_enter = tk.Entry(self.root, font="Arial 13", show="*", bg="DeepSkyBlue2")
        self.lbl2_message = tk.Label(self.root, bg="#2596be")
        self.back_btn = tk.Button(self.root, text="Back", relief="solid", font="Arial 15", background="#c76969")

    def start(self):
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.ip, self.port))

            receive_connection_thread = threading.Thread(target=self.receive_messages, args=(client_socket,))
            receive_connection_thread.daemon = True
            receive_connection_thread.start()

            self.login_btn["command"] = lambda: self.check_in(client_socket)
            self.create_account_btn["command"] = lambda: self.sign_up_lobby()
            self.register_account_btn["command"] = lambda: self.register_account(client_socket)
            self.back_btn["command"] = lambda: self.back_to_the_menu(client_socket)

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
        self.create_account.place(x=5, y=200)
        self.create_account_btn.place(x=10, y=230)

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

    def sign_up_lobby(self):
        self.current_lobby = "sign_up_lobby"
        self.close_login_lobby()
        self.title.pack(pady=50)
        self.enter_name1.pack(pady=20)
        self.enter_name_input.pack()
        self.enter_password1.pack(pady=5)
        self.enter_password_input.pack()
        self.confirm_password_enter.pack()
        self.confirm_password_input_enter.pack()
        self.lbl2_message.pack()
        self.register_account_btn.pack()
        self.back_btn.place(x=self.root.winfo_screenwidth() - 100, y=20)

    def close_login_lobby(self):
        self.lbl_welcome.pack_forget()
        self.enter_name.pack_forget()
        self.entry_username.pack_forget()
        self.enter_password.pack_forget()
        self.entry_password.pack_forget()
        self.lbl1_message.pack_forget()
        self.login_btn.pack_forget()
        self.create_account.place_forget()
        self.create_account_btn.place_forget()

    def close_sign_up_lobby(self):
        self.title.pack_forget()
        self.enter_name1.pack_forget()
        self.enter_name_input.pack_forget()
        self.enter_password1.pack_forget()
        self.enter_password_input.pack_forget()
        self.lbl2_message.pack_forget()
        self.register_account_btn.pack_forget()
        self.confirm_password_input_enter.pack_forget()
        self.confirm_password_enter.pack_forget()
        self.back_btn.place_forget()

    def register_account(self, conn):
        self.username, self.password, self.confirmed_password = self.enter_name_input.get(),\
                                                                self.enter_password_input.get(), \
                                                                self.confirm_password_input_enter.get()
        if self.username == "":
            self.lbl2_message["text"] = "the username isn't empty"
        elif not library_protocol.check_username_validation(self.username):
            self.lbl2_message["text"] = "the username must be built from characters between a-z, A-Z, 0-9 (including)"
        elif self.password == "":
            self.lbl2_message["text"] = "the password isn't empty"
        elif self.confirmed_password == "":
            self.lbl2_message["text"] = "the confirmed password isn't empty"
        elif self.password != self.confirmed_password:
            self.lbl2_message["text"] = "the password does not match the confirmed password"
        else:
            data, msg = client_commands["sign_up_cmd"], "{}#{}#{}".format(self.username, hashlib.sha256(
                                                                                 self.password.encode()).hexdigest(),
                                                                          hashlib.sha256(self.confirmed_password.encode(
                                                                          )).hexdigest())
            self.send_messages(conn, data, msg)

    def back_to_the_menu(self, conn):
        match self.current_lobby:
            case "sign_up_lobby":
                self.close_sign_up_lobby()
                self.login_lobby()


if __name__ == "__main__":
    ip = "127.0.0.1"
    port = 34254
    client = Client(ip, port)
    client.start()
