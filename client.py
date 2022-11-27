import hashlib
import library_protocol
import socket
import threading
import tkinter as tk
import traceback
from library_protocol import client_commands, server_commands
import time
import json

# constants
colors = ["firebrick4", "SteelBlue4", "chartreuse4", "#DBB600"]
dict_colors = {"firebrick4": "red", "SteelBlue4": "blue", "chartreuse4": "green", "#DBB600": "yellow"}
dict_colors1 = {"red": "firebrick4", "blue": "SteelBlue4", "green": "chartreuse4", "yellow": "#DBB600"}


def send_messages(conn, data, msg=""):
    message = library_protocol.build_message(data, msg)
    print(f"[Client] {message}\n--------------------------------\n")
    conn.sendall(message.encode())


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
        self.entry_username = tk.Entry(self.root, font="Arial 13", bg="DeepSkyBlue2", disabledbackground="DeepSkyBlue3")
        self.enter_password = tk.Label(self.root, text="Please enter your Password:", font="Arial 14", bg="#2596be")
        self.entry_password = tk.Entry(self.root, font="Arial 13", bg="DeepSkyBlue2", show="*",
                                       disabledbackground="DeepSkyBlue3")
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

        # main lobby
        self.lbl_welcome_main_lobby = tk.Label(self.root, bg="#2596be", font="Arial 16")
        self.profile_btn = tk.Button(self.root, text="View my profile", relief="solid", activebackground="DeepSkyBlue3",
                                     bg="DeepSkyBlue2", font="Arial 15")
        self.game_rooms_lobby_btn = tk.Button(self.root, text="Game rooms lobby", relief="solid",
                                              activebackground="DeepSkyBlue3", bg="DeepSkyBlue2", font="Arial 15")

        # profile lobby
        self.canvas = tk.Canvas(self.root, width=self.root.winfo_screenwidth(),
                                height=self.root.winfo_screenheight() - 200, background="#2596be",
                                highlightbackground="#2596be")
        # root, screen width, screen height
        self.lbl_profile_message = tk.Label(self.root, font="Arial 35", bg="#2596be")
        self.lbl_games_played = tk.Label(self.root, text="Games played: ", font="Arial 16", bg="grey")
        self.lbl_statistics = tk.Label(self.root, text="My statistics", font="Arial 22", bg="grey")
        self.lbl_games_wins = tk.Label(self.root, text="Win Games: ", font="Arial 16", bg="grey")
        self.lbl_account_data = tk.Label(self.root, text="My account data", font="Arial 22", bg="grey")

        # game rooms lobby
        self.scrollbar_frame = tk.Frame(self.root, highlightbackground="black", highlightcolor="black",
                                        highlightthickness=2, bg="#2596be")
        self.scrollbar = tk.Scrollbar(self.scrollbar_frame, orient=tk.VERTICAL)
        self.game_rooms_lobby_lbl = tk.Label(self.root, font="Arial 35", bg="#2596be", text="Game rooms lobby")
        self.game_rooms_lobby_canvas = tk.Canvas(self.scrollbar_frame, bg="#2596be", highlightbackground="#2596be",
                                                 highlightcolor="#2596be", highlightthickness=2,
                                                 height=self.root.winfo_screenheight() // 1.2,
                                                 width=self.root.winfo_screenwidth() // 2.543)
        self.game_rooms_lobby_canvas.configure(scrollregion=(300, 150, 900, 755))
        self.game_rooms_lobby_canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.refresh_button = tk.Button(self.root, bg="#70ad47", text="Refresh", relief="solid", font="Arial 18")
        self.create_lobby_game_room_button = tk.Button(self.root, bg="#70ad47", text="Create", relief="solid",
                                                       font="Arial 18")
        self.from_creating = False
        self.from_main_lobby = False
        self.is_active = False
        self.from_lobby_game_waiting_or_in_actual_game = False
        self.message_failed_join_error_game = tk.Label(self.root, bg="#2596be", font="Arial 16")

        # create lobby room menu
        self.lobby_name_game_room_lbl = tk.Label(self.root, font="Arial 25", bg="#2596be")  # 30 28 26
        self.game_room_lobby_create_canvas = tk.Canvas(self.root, bg="#d0cece",
                                                       width=self.root.winfo_screenwidth() // 2.742, height=300,
                                                       highlightcolor="black", highlightbackground="black")
        self.maximum_players_entry = tk.Entry(self.root, bg="#AFABAB", font="Arial 20")
        self.maximum_players_lbl = tk.Label(self.root, bg="#d0cece", font="Arial 20",
                                            text="Maximum participants: {2-4}")
        self.create_lobby_game_room_create_button = tk.Button(self.root, bg="#70ad47", text="Create lobby",
                                                              font="Arial 15", relief="solid")
        self.number_players_not_valid = tk.Label(self.root, bg="#d0cece", font="Arial 15",
                                                 text="The maximum players should be between 2 (include 2) to 4 ("
                                                      "include 4)")

        # waiting lobby room menu
        self.waiting_to_start_lbl = tk.Label(self.root, bg="#2596be", font="Arial 17")
        self.waiting_room_lobby_menu_canvas = tk.Canvas(self.root, bg="#d0cece",
                                                        width=self.root.winfo_screenwidth() // 2.133,
                                                        height=self.root.winfo_screenheight() // 2.7,
                                                        highlightcolor="black", highlightbackground="black")
        self.start_game_menu_button = tk.Button(self.root, bg="#70ad47", text="Start", font="Arial 15", relief="solid")
        self.participants_lbl = tk.Label(self.root, bg="#d0cece", font="Arial 17", text="Players:")
        self.name_leader = tk.Label(self.root, bg="#2596be", font="Arial 25")
        self.list_of_players = []
        self.temp_information_about_the_room = []
        self.is_first_time_getting_players = True

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
            self.profile_btn["command"] = lambda: self.profile_lobby(client_socket)
            self.game_rooms_lobby_btn["command"] = lambda: self.game_rooms_lobby_menu(client_socket)
            self.create_lobby_game_room_button["command"] = lambda: self.create_lobby_game_room()
            self.create_lobby_game_room_create_button["command"] = lambda: self.send_create_game_room_lobby(
                client_socket)
            self.start_game_menu_button["command"] = lambda: send_messages(client_socket,
                                                                           client_commands["start_game_cmd"])
            self.refresh_button["command"] = lambda: self.refresh_lobby_rooms(client_socket,
                                                                              client_commands["get_lobby_rooms_cmd"])

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
            print(traceback.format_exc())
            print("you have disconnected from the main server.")

    def handle_received_connection(self, conn, data):
        print(f"[Server] {data}")
        cmd, msg = library_protocol.disassemble_message(data)
        if cmd == server_commands["login_ok_cmd"]:
            self.login_try_counts = 0
            self.main_lobby()
        elif cmd == server_commands["login_failed_cmd"]:
            if msg == "":
                self.lbl1_message["text"] = f"login has failed. you have {2 - self.login_try_counts} attempts to login"
            else:
                self.lbl1_message["text"] = msg
            print("login failed")
            self.login_try_counts += 1
            if self.login_try_counts == 3:
                self.login_btn["state"] = tk.DISABLED
                self.entry_username["state"] = tk.DISABLED
                self.entry_password["state"] = tk.DISABLED
        elif cmd == server_commands["sign_up_ok_cmd"]:
            self.lbl2_message["text"] = "Register succeeded"
            time.sleep(1.2)
            self.close_sign_up_lobby()
            self.login_lobby()
        elif cmd == server_commands["sign_up_failed_cmd"]:
            self.lbl2_message["text"] = msg
        elif cmd == server_commands["get_profile_ok"]:
            games_played, games_win = msg.split("#")
            self.lbl_games_played["text"] = "Games played: " + games_played
            self.lbl_games_wins["text"] = "Win Games: " + games_win
        elif cmd == server_commands["create_room_game_lobby_ok_cmd"]:
            self.close_create_lobby_game_room()
            self.waiting_room_lobby_menu(list_of_names=[(self.username, colors[0])], conn=conn)
        elif cmd == server_commands["get_lr_ok_cmd"]:
            lobby_rooms = json.loads(msg)
            print(lobby_rooms)
            self.show_game_rooms(lobby_rooms, conn)
        elif cmd == server_commands["join_player_game_room_server_ok_cmd"]:
            msg = json.loads(msg)
            print(msg)
            self.back_btn["state"] = tk.DISABLED
            time.sleep(0.5)
            self.waiting_room_lobby_menu(list_of_names=msg, from_creating=False, conn=conn)
        elif cmd == server_commands["join_player_game_room_server_failed_cmd"]:
            self.message_failed_join_error_game["text"] = msg
            self.message_failed_join_error_game.place(x=self.root.winfo_screenwidth() // 2, y=115, anchor=tk.CENTER)
        elif cmd == server_commands["join_player_ok_cmd"]:
            msg = json.loads(msg)
            self.update_list_of_players(msg)
        elif cmd == server_commands["close_lobby_ok_cmd"]:
            self.back_to_the_menu(conn)
        elif cmd == server_commands["leave_player_ok_cmd"]:
            self.update_list_of_players(json.loads(msg))

    def login_lobby(self):
        self.current_lobby = "login"
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
            send_messages(conn, data, msg)

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
        self.back_btn.place(x=self.root.winfo_screenwidth() - 150, y=20)

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
        self.username, self.password, self.confirmed_password = self.enter_name_input.get(), \
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
            send_messages(conn, data, msg)

    def back_to_the_menu(self, conn):
        match self.current_lobby:
            case "sign_up_lobby":
                self.close_sign_up_lobby()
                self.login_lobby()
            case "main_lobby":
                self.close_main_lobby()
                send_messages(conn, client_commands["logout_cmd"])
                self.login_lobby()
            case "profile_lobby":
                self.close_profile_lobby()
                self.main_lobby()
            case "game_rooms_lobby":
                self.refresh_lobby_rooms(from_refresh=False)
                self.close_game_rooms_lobby_menu()
                self.main_lobby()
            case "creating_game_lobby_room":
                self.refresh_lobby_rooms(from_refresh=False)
                self.close_create_lobby_game_room()
                self.game_rooms_lobby_menu(conn)
            case "waiting_game_room_lobby":
                self.close_waiting_room_menu()
                self.back_btn["command"] = lambda: self.back_to_the_menu(conn)
                self.back_btn["text"] = "Back"
                self.game_rooms_lobby_menu(conn)

    def main_lobby(self):
        if self.current_lobby == "login":
            self.close_login_lobby()
        self.current_lobby = "main_lobby"
        self.lbl_welcome_main_lobby["text"] = f"Welcome {self.username} to the main lobby!"
        self.lbl_welcome_main_lobby.pack(side=tk.TOP, pady=20)
        self.back_btn.place(x=self.root.winfo_screenwidth() - 150, y=20)
        self.profile_btn.place(x=self.root.winfo_screenwidth() // 2 - 200, y=self.root.winfo_screenheight() // 2)
        self.game_rooms_lobby_btn.place(x=self.root.winfo_screenwidth() // 2 + 25,
                                        y=self.root.winfo_screenheight() // 2)

    def close_main_lobby(self):
        self.lbl_welcome_main_lobby.pack_forget()
        if self.current_lobby != "profile_lobby" and self.current_lobby != "game_rooms_lobby":
            self.back_btn.place_forget()
        self.profile_btn.place_forget()
        self.game_rooms_lobby_btn.place_forget()

    def profile_lobby(self, conn):
        self.current_lobby = "profile_lobby"
        self.close_main_lobby()
        self.lbl_profile_message["text"] = f"{self.username}'s Profile"
        self.lbl_profile_message.pack(side=tk.TOP)
        self.canvas.pack(pady=50)
        self.canvas.create_rectangle(int(self.root.winfo_screenwidth() * (1 / 5)), 50,
                                     self.root.winfo_screenwidth() - int(self.root.winfo_screenwidth() * (1 / 5)), 400,
                                     fill="grey", outline="black")
        self.lbl_statistics.place(x=self.root.winfo_screenwidth() // 2, y=160, anchor=tk.N)
        self.lbl_games_played.place(x=int(self.root.winfo_screenwidth() * (1 / 5)) + 30, y=250)
        self.lbl_games_wins.place(x=int(self.root.winfo_screenwidth() * (1 / 5)) + 30, y=350)
        send_messages(conn, client_commands["get_profile_cmd"])

    def close_profile_lobby(self):
        self.lbl_profile_message.pack_forget()
        self.canvas.pack_forget()
        self.lbl_statistics.place_forget()
        self.lbl_games_played.place_forget()
        self.lbl_games_wins.place_forget()
        self.lbl_account_data.place_forget()

    def on_mousewheel(self, event):
        self.game_rooms_lobby_canvas.yview_scroll(-1 * event.delta // 120,
                                                  "units")  # the speed of scrolling and the units of it?

    def game_rooms_lobby_menu(self, conn):
        self.current_lobby = "game_rooms_lobby"
        self.close_main_lobby()
        self.game_rooms_lobby_lbl.pack(side=tk.TOP, pady=25)
        self.scrollbar_frame.pack(fill=tk.BOTH, padx=300, pady=150)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.game_rooms_lobby_canvas.pack()
        self.refresh_button.place(x=300, y=self.root.winfo_screenheight() // 1.136)
        self.create_lobby_game_room_button.place(x=self.root.winfo_screenwidth() - 392,
                                                 y=self.root.winfo_screenheight() // 1.136)
        if not self.from_creating and not self.from_main_lobby and not self.from_lobby_game_waiting_or_in_actual_game:
            send_messages(conn, client_commands["get_lobby_rooms_cmd"])

    def close_game_rooms_lobby_menu(self):
        self.game_rooms_lobby_lbl.pack_forget()
        self.scrollbar_frame.pack_forget()
        self.scrollbar.pack_forget()
        self.game_rooms_lobby_canvas.pack_forget()
        self.create_lobby_game_room_button.place_forget()
        self.refresh_button.place_forget()
        self.message_failed_join_error_game.place_forget()

    def create_lobby_game_room(self):
        self.current_lobby = "creating_game_lobby_room"
        self.close_game_rooms_lobby_menu()
        self.maximum_players_entry.focus()
        self.lobby_name_game_room_lbl["text"] = f"Waiting room - {self.username}'s lobby"
        self.lobby_name_game_room_lbl.pack(padx=450, pady=20, side=tk.TOP)
        self.game_room_lobby_create_canvas.pack(pady=50)
        self.maximum_players_lbl.place(x=self.root.winfo_screenwidth() // 3.047, y=180)
        self.maximum_players_entry.place(x=self.root.winfo_screenwidth() // 3.047, y=225)
        self.create_lobby_game_room_create_button.place(x=self.root.winfo_screenwidth() // 2, y=380, anchor=tk.CENTER)

    def close_create_lobby_game_room(self):
        if self.current_lobby != "waiting_game_room_lobby":
            self.lobby_name_game_room_lbl.pack_forget()
        self.game_room_lobby_create_canvas.pack_forget()
        self.maximum_players_entry.place_forget()
        self.maximum_players_lbl.place_forget()
        self.create_lobby_game_room_create_button.place_forget()
        self.number_players_not_valid.place_forget()
        self.create_lobby_game_room_create_button["state"] = tk.NORMAL

    def send_create_game_room_lobby(self, conn):
        maximum_players1 = self.maximum_players_entry.get()
        print(maximum_players1)
        self.number_players_not_valid.place_forget()
        if maximum_players1 in ("2", "3", "4"):
            send_messages(conn, client_commands["create_game_room_lobby_cmd"], maximum_players1)
            self.create_lobby_game_room_create_button["state"] = tk.DISABLED
            self.back_btn["state"] = tk.DISABLED  # cannot go backwards
        else:
            self.number_players_not_valid.place(x=self.root.winfo_screenwidth() // 3.047, y=270)

    def waiting_room_lobby_menu(self, conn, list_of_names: list, from_creating=True):
        space = 0
        self.current_lobby = "waiting_game_room_lobby"
        if from_creating and conn is not None:  # what the display is for the creator of the room
            self.close_create_lobby_game_room()
            self.participants_lbl.place(x=self.root.winfo_screenwidth() // 2, y=280, anchor=tk.N)
            self.waiting_to_start_lbl.pack(padx=400, pady=40, side=tk.TOP)
            self.waiting_room_lobby_menu_canvas.pack(pady=150)
            self.back_btn["state"] = tk.NORMAL
            self.back_btn["text"] = "Close lobby"
            self.back_btn["command"] = lambda: self.leave_room_game_lobby(conn, list_of_names[0][0])  # name_creator
            self.start_game_menu_button["state"] = tk.DISABLED
            self.start_game_menu_button.place(x=self.root.winfo_screenwidth() // 2, y=550, anchor=tk.N)
            self.start_game_menu_button["command"] = lambda: send_messages(conn, client_commands["start_game_cmd"])
            self.waiting_to_start_lbl["text"] = f"Waiting for {list_of_names[0][0]} to start the game"
            for name_and_color in list_of_names:
                (name, color) = name_and_color[0], name_and_color[1]
                self.waiting_room_lobby_menu_canvas.create_text(int(self.waiting_room_lobby_menu_canvas["width"]) // 2,
                                                                70 + space, text=name, fill=color, font="Arial 17",
                                                                state=tk.DISABLED)
                space += 30
        else:  # the display for the other players
            # [name, name]
            self.back_btn["state"] = tk.NORMAL
            self.close_game_rooms_lobby_menu()
            self.back_btn["text"] = "Leave Room"
            self.participants_lbl.place(x=self.root.winfo_screenwidth() // 2, y=360, anchor=tk.N)
            self.name_leader["text"] = f"Waiting room - {list_of_names[0]}'s lobby"
            self.name_leader.pack(padx=450, pady=20, side=tk.TOP)
            self.waiting_to_start_lbl["text"] = f"Waiting for {list_of_names[0]} to start the game"
            self.waiting_to_start_lbl.pack(padx=400, pady=40, side=tk.TOP)
            self.waiting_room_lobby_menu_canvas.pack(pady=150)
            self.back_btn["command"] = lambda: self.leave_room_game_lobby(conn, list_of_names[0])  # name creator
            for index, names in enumerate(list_of_names):
                (name, color) = names, colors[index]
                self.waiting_room_lobby_menu_canvas.create_text(int(self.waiting_room_lobby_menu_canvas["width"]) // 2,
                                                                70 + space, text=names, fill=color, font="Arial 17",
                                                                state=tk.DISABLED)
                space += 30

    def leave_room_game_lobby(self, conn, creator_name: str):
        # error with the creator name somehow
        send_messages(conn, client_commands["leave_my_player_cmd"], creator_name)
        self.back_to_the_menu(conn)

    def show_game_rooms(self, game_rooms_dict, conn):
        if game_rooms_dict == {}:
            self.game_rooms_lobby_canvas.delete("all")
            self.game_rooms_lobby_canvas.create_text(675, 195, text="There are no game lobby rooms", font="Arial 16",
                                                     anchor=tk.CENTER, state=tk.DISABLED)
        else:
            space = 0
            for creator in game_rooms_dict.keys():
                max_players, players = game_rooms_dict[creator][0], game_rooms_dict[creator][1]
                rectangle1 = self.game_rooms_lobby_canvas.create_rectangle(353, 170 + space, 985, 300 + space,
                                                                           activewidth=3, width=2, fill="#AFABAB")
                self.game_rooms_lobby_canvas.create_text(370, 195 + space, text=f"{creator}'s lobby room",
                                                         font="Arial 16", fill="black", state=tk.DISABLED, anchor=tk.NW)
                self.game_rooms_lobby_canvas.create_text(370, 230 + space,
                                                         text=f"Number of players: {len(players)} out of "
                                                              f"{max_players}",
                                                         font="Arial 14", fill="black", state=tk.DISABLED, anchor=tk.NW)
                space += 170
                position1 = int(self.game_rooms_lobby_canvas["height"])
                self.game_rooms_lobby_canvas["height"] = position1 + space
                self.game_rooms_lobby_canvas.configure(scrollregion=(300, 150, 900, 150 + space))
                button_join_game = tk.Button(self.scrollbar_frame, text="Join", relief="solid", bg="#70ad47",
                                             font="Arial 15",
                                             command=lambda: send_messages(conn,
                                                                           client_commands["join_game_room_cmd"],
                                                                           creator))
                if len(game_rooms_dict[creator][1]) >= max_players:
                    button_join_game["state"] = tk.DISABLED
                button_join_game.place(x=500, y=170 + space)
                self.game_rooms_lobby_canvas.create_window(950, 100 + space, window=button_join_game)
                self.game_rooms_lobby_canvas.itemconfigure(rectangle1, state=tk.NORMAL)

    def update_list_of_players(self, new_list_of_players):
        if self.current_lobby == "waiting_game_room_lobby":
            space = 0
            self.waiting_room_lobby_menu_canvas.delete("all")
            for name, color in new_list_of_players:  # [[name, color], [name, color]]
                self.waiting_room_lobby_menu_canvas.create_text(int(self.waiting_room_lobby_menu_canvas["width"]) // 2,
                                                                70 + space, text=name, fill=color, font="Arial 17",
                                                                state=tk.DISABLED)
                space += 30
            self.list_of_players = new_list_of_players
            if len(new_list_of_players) >= 2:
                self.start_game_menu_button["state"] = tk.NORMAL
            else:
                self.start_game_menu_button["state"] = tk.DISABLED

    def close_waiting_room_menu(self):
        self.lobby_name_game_room_lbl.pack_forget()
        self.start_game_menu_button.place_forget()
        self.waiting_room_lobby_menu_canvas.delete("all")
        self.waiting_room_lobby_menu_canvas.pack_forget()
        self.waiting_to_start_lbl.pack_forget()
        self.participants_lbl.place_forget()
        self.name_leader.pack_forget()

    def refresh_lobby_rooms(self, conn=None, from_refresh=True):
        if from_refresh:
            self.message_failed_join_error_game.place_forget()  # even if the label is not placed it won't do an error
            self.game_rooms_lobby_canvas.delete("all")
            send_messages(conn, client_commands["get_lobby_rooms_cmd"])
        self.refresh_button["state"] = tk.DISABLED
        self.from_creating = True
        self.from_main_lobby = True
        self.from_lobby_game_waiting_or_in_actual_game = True
        if not self.is_active:
            self.root.after(5000,
                            lambda: self.set_refresh_button_enabled())  # self.refresh_button disabled for 5 seconds
            self.is_active = True

    def set_refresh_button_enabled(self):
        self.refresh_button["state"] = tk.NORMAL
        self.from_creating = False
        self.from_main_lobby = False
        self.is_active = False
        self.from_lobby_game_waiting_or_in_actual_game = False


if __name__ == "__main__":
    ip = "127.0.0.1"
    port = 34254
    client = Client(ip, port)
    client.start()
