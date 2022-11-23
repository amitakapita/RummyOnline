import library_protocol
import socket
import sqlite3 as sql
import threading
import json
from library_protocol import client_commands, server_commands
import time
from player import Player

# data bases
wait_login = {}  # {client_socket: client_address, code, username}  # code and username are when the client succeeded
# to log in with username and password # or {client_socket: client_address, username}}
login_dict = {}  # {client_socket: wait_login[client_socket][0], username}
game_rooms_dict = {}  # {creator: [max_players, players, is_started]}
colors = ["firebrick4", "SteelBlue4", "chartreuse4", "#DBB600"]
dict_colors = {"firebrick4": "red", "SteelBlue4": "blue", "chartreuse4": "green", "#DBB600": "yellow"}
dict_colors1 = {"red": "firebrick4", "blue": "SteelBlue4", "green": "chartreuse4", "yellow": "#DBB600"}
game_room_players_dict = {}  # {creator: [Players: list]}


def check_login(conn, msg, con):
    """
    checks the login attempt
    :rtype: bool
    :return: True - the login succeeded, False - the login failed
    """
    username_input, password_input = msg.split("#", 1)
    if (not library_protocol.check_username_validation(username_input)) or password_input == "" or \
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


def register_check(msg, con):
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


def profile_info(conn, con):
    cur = con.cursor()
    cur.execute("SELECT played_games, wins FROM 'Users' WHERE Username = ?",
                (login_dict[conn][1],))  # the comma is for making the parameter a tuple and not char
    msg = cur.fetchall()
    cur.close()
    return server_commands["get_profile_ok"], f"{msg[0][0]}#{msg[0][1]}"


def lobby_rooms():
    lobby_rooms1 = json.dumps(game_rooms_dict)
    print(lobby_rooms1)
    return server_commands["get_lr_ok_cmd"], lobby_rooms1


def join_a_player_to_game_room(conn, creator):
    try:
        if game_rooms_dict[creator][0] <= len(game_rooms_dict[creator][1]) or game_rooms_dict[creator][2]:
            # full/started
            return server_commands["join_player_game_room_server_failed_cmd"], \
                   "game room lobby is full or the game has started"
        game_rooms_dict[creator][1].append(login_dict[conn][1])
        return server_commands["join_player_game_room_server_ok_cmd"], json.dumps(game_rooms_dict[creator][1])
    except KeyError:
        return server_commands["join_player_game_room_server_failed_cmd"], "no such game room lobby, try to refresh"


class Server(object):

    def __init__(self, ip1, port1):
        self.ip = ip1
        self.port = port1
        self.amount_clients = 0
        self.current_lobby_game = "waiting"  # waiting room/in game

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
                      f"Waiting for login: {list(wait_login.values())}\n"
                      f"Already logged in: {list(login_dict.values())}\n--------------------------------\n")
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
                if login_dict[conn][1] in game_rooms_dict.keys():  # there is a game room
                    del game_rooms_dict[login_dict[conn][1]]
                else:
                    for creator, game_room in game_rooms_dict.items():
                        # a player leaves the system and still in the game room
                        if login_dict[conn][1] in game_room[1]:
                            game_rooms_dict[creator][1].remove(login_dict[conn][1])
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
            to_send, msg_to_send = check_login(conn, msg, con)
            to_send = server_commands["login_ok_cmd"] if to_send \
                else server_commands["login_failed_cmd"]
        elif cmd == client_commands["sign_up_cmd"]:
            to_send, msg_to_send = register_check(msg, con)
        elif cmd == client_commands["logout_cmd"]:
            try:
                wait_login[conn] = login_dict[conn][0]  # only the peer name
                del login_dict[conn]
                print("Logout from the account succeeded.\n--------------------------")
                return
            except KeyError:  # if the player is between the main server to the games rooms server
                return
        elif cmd == client_commands["get_profile_cmd"]:
            to_send, msg_to_send = profile_info(conn, con)
        elif cmd == client_commands["create_game_room_lobby_cmd"]:
            if "2" <= msg <= "4":
                to_send = server_commands["create_room_game_lobby_ok_cmd"]
                game_rooms_dict[login_dict[conn][1]] = [int(msg), [login_dict[conn][1]], False]
                game_room_players_dict[login_dict[conn][1]] = [Player(color="red", conn=conn,
                                                                      player_name=login_dict[conn][1],
                                                                      creator=login_dict[conn][1])]
        elif cmd == client_commands["get_lobby_rooms_cmd"]:
            to_send, msg_to_send = lobby_rooms()
        elif cmd == client_commands["join_game_room_cmd"]:
            to_send, msg_to_send = join_a_player_to_game_room(conn, msg)
            to_send1 = library_protocol.build_message(to_send, msg_to_send)
            print(f"[Server] -> [{conn.getpeername()}] {to_send1}")
            conn.sendall(to_send1.encode())
            if to_send == server_commands["join_player_game_room_server_ok_cmd"]:
                print(f"{login_dict[conn][0]} has been switched to game room {msg}")
                game_rooms_dict[msg][1].append(login_dict[conn][1])  # adding player name
                game_room_players_dict[msg].append(Player(color=list(dict_colors1.keys())[
                    len(game_room_players_dict[msg])],
                                                   conn=conn, player_name=login_dict[conn][1], creator=msg))
            print(game_room_players_dict)
            self.send_information_of_players(msg)
            return
        to_send = library_protocol.build_message(to_send, msg_to_send)
        print(f"[Server] -> [{conn.getpeername()}] {to_send}")
        conn.sendall(to_send.encode())

    def send_information_of_players(self, game_room_name, is_leave=False):
        print(game_room_players_dict[game_room_name])
        if not is_leave:
            cmd_send = server_commands["join_player_ok_cmd"]
        else:
            cmd_send = server_commands["leave_player_ok_cmd"]
        msg_send = self.players_information(game_room_name)
        message = library_protocol.build_message(cmd_send, msg_send)
        player: Player
        for player in game_room_players_dict[game_room_name]:  # sends each player in the lobby
            conn = player.conn
            print(f"[Server] -> [Client {conn.getpeername()}] {message}")
            conn.sendall(message.encode())

    def players_information(self, game_room_name):
        try:
            list1 = []
            player1: Player
            for index, player1 in enumerate(game_room_players_dict[game_room_name]):
                if player1.color != colors[index] and self.current_lobby_game == "waiting":
                    player1.change_color(colors[index])
                    list1.append((player1.player_name, player1.color))
                elif self.current_lobby_game != "waiting" or player1.color == colors[index]:
                    list1.append((player1.player_name, player1.color))
            list1 = json.dumps(
                list1 if list1 != [] else [(player_name.player_name, player_name.color) for player_name in
                                           game_room_players_dict[game_room_name]])
            return list1
        except Exception as e1:
            print(e1)
            return ""


if __name__ == "__main__":
    ip = "0.0.0.0"
    port = 34254
    server = Server(ip, port)
    server.start()
