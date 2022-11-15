import library_protocol
import socket
import sqlite3 as sql
import threading
import json
from library_protocol import client_commands, server_commands
import time

# data bases
wait_login = {}  # {client_socket: client_address, code, username}  # code and username are when the client succeeded
# to log in with username and password # or {client_socket: client_address, username}}
login_dict = {}  # {client_socket: wait_login[client_socket][0], username}


class Server(object):

    def __init__(self, ip1, port1):
        self.ip = ip1
        self.port = port1
        self.amount_clients = 0

    def start(self):
        try:
            print(f"The server starts in ip: {self.ip}, and port: {self.port}")
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind((self.ip, self.port))
            server_socket.listen()

            while True:
                if self.amount_clients == 0:
                    print("Waiting for a new client...")
                client_socket, client_address = server_socket.accept()  # blocks the running of the file
                self.amount_clients += 1
                wait_login[client_socket] = client_address
                print(f"A new client has connected! {client_address}\n--------------------------------\nAmount: "
                      f"{self.amount_clients}\n--------------------------------\n"
                      f"Waiting for login: {wait_login.values()}\n"
                      f"Already logged in: {login_dict.values()}\n--------------------------------\n")
                self.handle_client(client_socket)
        except socket.error as e:
            print(e)

    def handle_client(self, conn):
        client_handler = threading.Thread(target=self.handle_client_connection,
                                          args=(conn,))  # the comma is necessary
        client_handler.daemon = True
        client_handler.start()

    def handle_client_connection(self, conn):
        """Handles commands from the client connection"""
        con = sql.connect("database/accounts.db")
        try:
            while True:
                request = conn.recv(1024).decode()
                if request is None or request == "":
                    raise ConnectionError
                print(f"[Client {conn.getpeername()}] {request}")
                self.handle_client_commands(conn, request, con)

        except ConnectionError or OSError:
            if conn in wait_login.keys():
                del wait_login[conn]
            else:
                del login_dict[conn]
            print(f"client {conn.getpeername()} has exited.")
            conn.close()

        finally:
            if con:
                con.close()
                print(f"DB Connection has closed with that Client\n--------------------------")
            self.amount_clients -= 1

    def handle_client_commands(self, conn, request, con):
        cmd, msg = library_protocol.disassemble_message(request)
        to_send, msg_to_send = "", ""
        if cmd == client_commands["login_cmd"]:
            to_send, msg_to_send = self.check_login(conn, msg, con)
            to_send = server_commands["login_ok_cmd"] if to_send \
                else server_commands["login_failed_cmd"]
        elif cmd == client_commands["sign_up_cmd"]:
            to_send, msg_to_send = self.register_check(msg, con)
        elif cmd == client_commands["logout_cmd"]:
            try:
                wait_login[conn] = login_dict[conn][0]  # only the peer name
                del login_dict[conn]
                print("Logout from the account succeeded.\n--------------------------")
                return
            except KeyError:  # if the player is between the main server to the games rooms server
                return
        to_send = library_protocol.build_message(to_send, msg_to_send)
        print(f"[Server] -> [{conn.getpeername()}] {to_send}")
        conn.sendall(to_send.encode())

    def check_login(self, conn, msg, con):
        """
        checks the login attempt
        :rtype: bool
        :return: True - the login succeeded, False - the login failed
        """
        username_input, password_input = msg.split("#", 1)
        if (not library_protocol.check_username_validation(username_input)) or password_input == "" or\
                password_input is None:
            return False, ""
        if username_input in map(lambda client: client[-1], login_dict.values()):
            return False, "the account is already logged in"  # username is already logged in
        cur = con.cursor()
        cur.execute("SELECT * FROM Users WHERE Username = ? and Password = ?", (username_input, password_input))
        x = cur.fetchall()
        if x:
            login_dict[conn] = wait_login[conn], username_input
            del wait_login[conn]
            cur.close()
            return True, ""
        cur.close()
        return False, ""

    def register_check(self, msg, con):
        username, password, confirm_password = msg.split("#")
        if len(password) < 4 or len(confirm_password) < 4:
            return server_commands["sign_up_failed_cmd"], "The password is too short."
        elif password != confirm_password:
            return server_commands["sign_up_failed_cmd"], "The passwords does not match each other"
        if not library_protocol.check_username_validation(username):
            return server_commands["sign_up_failed_cmd"], "The username should be in letters a-z, A-Z, 0-9 include."
        cur = con.cursor()
        cur.execute("SELECT Username FROM Users WHERE Username = ?",
                    (username,))  # the comma is for making the parameter a tuple and not char
        if cur.fetchall():
            cur.close()
            return server_commands["sign_up_failed_cmd"], "The username is already taken."
        cur.execute(
            "INSERT INTO Users (Username, Password, wins, played_games) values (?, ?, ?, ?)",
            (username, password, 0, 0))
        con.commit()
        cur.close()
        return server_commands["sign_up_ok_cmd"], "registering has succeeded"


if __name__ == "__main__":
    ip = "0.0.0.0"
    port = 34254
    server = Server(ip, port)
    server.start()
